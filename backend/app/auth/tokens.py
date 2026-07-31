"""Access tokens, behind a port.

Two things are deliberately separate here:

``TokenVerifier`` answers one question — *which user is this request from?* — and is the
only thing the request path depends on. ``TokenIssuer`` mints tokens and exists only for
the local provider, because when somebody else's identity provider issues them there is
nothing here to mint.

That split is the whole point of the seam. ARCHITECTURE.md AD-7 argues for ports at every
adopted boundary, and identity is the one this service is most likely to have chosen for
it: a customer with SSO will not accept a second password store. Moving to OIDC should be
writing ``OIDCTokenVerifier`` and changing a setting, not touching a route.

The verifier returns a *subject*, never a ``User``. Roles and account state are read from
the database on every request, so a token cannot carry a stale role, and revoking someone
does not mean waiting for their token to expire.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

import jwt

from app.config import Settings


class InvalidTokenError(Exception):
    """The token is missing, malformed, expired, or not signed by us.

    One type for every failure, and the message never says which. "Expired" versus
    "bad signature" is free information for someone probing the endpoint, and the
    caller's remedy — log in again — is identical either way.
    """


@dataclass(frozen=True)
class Principal:
    """Who a token says its bearer is.

    Two shapes, because two things issue tokens here. A locally-minted token names a row
    we already have, so it carries ``local_id``. A token from the identity provider names
    somebody in *their* directory, so it carries ``external_subject`` plus whatever the
    provider told us about them — and the row may not exist yet.

    Never both. ``local_id`` set means the id was signed by us and can be trusted as a
    primary key; ``external_subject`` set means it has to be looked up or provisioned.
    """

    local_id: UUID | None = None
    external_subject: str | None = None
    email: str | None = None
    display_name: str | None = None


class TokenVerifier(Protocol):
    def principal(self, token: str) -> Principal:
        """Who this token asserts its bearer is, or raise InvalidTokenError."""
        ...


class TokenIssuer(Protocol):
    def issue(self, user_id: UUID) -> tuple[str, int]:
        """Return (token, seconds_until_expiry)."""
        ...


class LocalJWT:
    """Issues and verifies our own HS256 tokens.

    Symmetric signing is right here and would be wrong under OIDC. The same process
    signs and checks, so there is no second party needing a public key, and HS256
    avoids shipping key management nobody asked for. An external issuer will be
    asymmetric, which is exactly why verification sits behind the port.
    """

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret
        self._issuer = settings.jwt_issuer
        self._ttl = timedelta(minutes=settings.jwt_ttl_minutes)

    def issue(self, user_id: UUID) -> tuple[str, int]:
        now = datetime.now(UTC)
        expires = now + self._ttl
        token = jwt.encode(
            {"sub": str(user_id), "iss": self._issuer, "iat": now, "exp": expires},
            self._secret,
            algorithm="HS256",
        )
        return token, int(self._ttl.total_seconds())

    def subject(self, token: str) -> UUID:
        try:
            # algorithms is an allow-list, not a hint. Omitting it lets a caller
            # choose "none" and hand over an unsigned token of their own devising.
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Token is not valid.") from exc

        try:
            return UUID(str(claims["sub"]))
        except ValueError as exc:
            raise InvalidTokenError("Token subject is not a user id.") from exc

    def principal(self, token: str) -> Principal:
        return Principal(local_id=self.subject(token))


class OIDCTokenVerifier:
    """Verifies access tokens issued by an OpenID Connect provider — Microsoft Entra ID
    in the deployment this was written for.

    The dangerous failure here is not rejecting a good token; it is accepting a bad one.
    Three checks carry that weight and none is optional:

    - **Signature, against the issuer's published keys.** ``PyJWKClient`` fetches the
      JWKS over TLS and caches it, selecting by the token's ``kid`` and refetching on an
      unknown one so a key rotation is not an outage.
    - **``aud``.** Entra signs tokens for every application in the tenant with the same
      keys. Without an audience check, a token minted for some *other* app in the same
      directory verifies perfectly and would be accepted here.
    - **``iss``.** Pinned to the configured issuer, so a token from a different tenant —
      or a different provider entirely — cannot be presented.

    ``algorithms`` is an allow-list. Omitting it would let a caller nominate ``none`` and
    hand over a token they wrote themselves.
    """

    # Entra signs with RS256. Naming it rather than accepting whatever the token asks for
    # is the point; this list is a policy, not a capability advertisement.
    _ALGORITHMS = ["RS256"]

    def __init__(self, settings: Settings) -> None:
        self._issuer = settings.oidc_issuer
        self._audience = settings.oidc_audience
        # Constructed once: it owns the key cache, so a per-request client would refetch
        # the JWKS on every call and turn the IdP into a hard dependency of every request.
        self._keys = jwt.PyJWKClient(settings.oidc_jwks_url, cache_keys=True)

    def principal(self, token: str) -> Principal:
        try:
            key = self._keys.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=self._ALGORITHMS,
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except (jwt.PyJWTError, jwt.exceptions.PyJWKClientError) as exc:
            raise InvalidTokenError("Token is not valid.") from exc

        # `oid` is stable for a person across every application in the tenant; `sub` is
        # only stable per application, so it would change if the app registration were
        # ever recreated and orphan the account. Prefer oid, fall back to sub.
        external = str(claims.get("oid") or claims["sub"])
        # Namespaced by issuer: two tenants can each have an object with the same id, and
        # an unqualified value would let one tenant's user land on the other's row.
        return Principal(
            external_subject=f"{self._issuer}#{external}",
            email=_first_str(claims, "email", "preferred_username", "upn"),
            display_name=_first_str(claims, "name", "given_name") or "Unknown",
        )


def _first_str(claims: dict[str, object], *names: str) -> str | None:
    for name in names:
        value = claims.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


class CompositeVerifier:
    """Accepts tokens from either issuer, and asks exactly one of them.

    Both are live at once by design: creators sign in through the company directory,
    while participants are admitted as guests with a token this service mints. A single
    verifier cannot cover both.

    Routing reads the token's ``iss`` claim *without verifying it* — which is safe only
    because the claim decides nothing except which verifier runs, and whichever one runs
    then validates the token in full, signature included. An unrecognised or unreadable
    issuer goes to the local verifier, which will reject it.
    """

    def __init__(self, local: TokenVerifier, external: TokenVerifier, local_issuer: str) -> None:
        self._local = local
        self._external = external
        self._local_issuer = local_issuer

    def principal(self, token: str) -> Principal:
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            issuer = str(unverified.get("iss", ""))
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Token is not valid.") from exc
        chosen = self._local if issuer == self._local_issuer else self._external
        return chosen.principal(token)


def build_verifier(settings: Settings) -> TokenVerifier:
    local = LocalJWT(settings)
    if settings.auth_provider == "oidc":
        # Not "OIDC instead of local" but "OIDC as well as": guest participants still
        # carry tokens this service issued, and dropping the local verifier here would
        # lock the entire floor out the moment SSO was switched on.
        return CompositeVerifier(local, OIDCTokenVerifier(settings), settings.jwt_issuer)
    return local


def build_issuer(settings: Settings) -> TokenIssuer:
    """Always local, in both modes.

    Under ``oidc`` the identity provider is authoritative for *creators*, and this
    service has no password login for them. It still mints tokens for guest participants,
    who have no account at the provider and never will — so refusing to build an issuer
    would take the incident form and the survey runner down with it.
    """
    return LocalJWT(settings)
