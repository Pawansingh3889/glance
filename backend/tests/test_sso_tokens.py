"""Verifying tokens from the company identity provider.

These tests are about what must be *refused*. A verifier that accepts good tokens is easy
and proves little; the failures below — wrong audience, wrong issuer, wrong key, no
signature at all — are each a way into every answer in the database, and each one is a
mistake that leaves a working-looking system behind.

Signing keys are generated here, so nothing contacts Microsoft and no secret is committed.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth.tokens import (
    CompositeVerifier,
    InvalidTokenError,
    LocalJWT,
    OIDCTokenVerifier,
    build_issuer,
    build_verifier,
)
from app.config import Settings

ISSUER = "https://login.microsoftonline.com/tenant-id/v2.0"
AUDIENCE = "api://glance-client-id"
OID = "00000000-1111-2222-3333-444444444444"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _settings(**over) -> Settings:
    base = {
        "database_url": "postgresql+asyncpg://unused/unused",
        "auth_provider": "oidc",
        "jwt_secret": "test-only-signing-key-not-the-published-default",
        "oidc_issuer": ISSUER,
        "oidc_audience": AUDIENCE,
        "oidc_jwks_url": "https://login.microsoftonline.com/tenant-id/discovery/v2.0/keys",
    }
    return Settings(**{**base, **over})


def _token(key=_KEY, *, iss=ISSUER, aud=AUDIENCE, expires_in=600, alg="RS256", **claims) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": iss,
        "aud": aud,
        "sub": "app-specific-subject",
        "oid": OID,
        "email": "Ines.Barros@company.example",
        "name": "Ines Barros",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        **claims,
    }
    return jwt.encode(payload, key, algorithm=alg)


@pytest.fixture
def verifier(monkeypatch) -> OIDCTokenVerifier:
    """An OIDC verifier whose JWKS lookup returns our generated key, so the real
    signature check runs without a network call."""
    made = OIDCTokenVerifier(_settings())

    class _Key:
        key = _KEY.public_key()

    monkeypatch.setattr(type(made._keys), "get_signing_key_from_jwt", lambda self, t: _Key())
    return made


# ------------------------------------------------------------------ accepted


def test_a_valid_token_yields_an_external_principal(verifier):
    principal = verifier.principal(_token())

    assert principal.local_id is None
    assert principal.external_subject == f"{ISSUER}#{OID}"
    assert principal.email == "Ines.Barros@company.example"
    assert principal.display_name == "Ines Barros"


def test_the_subject_is_namespaced_by_issuer(verifier):
    """Two tenants can each hold an object with the same id. Unqualified, one tenant's
    user would resolve onto the other's account."""
    assert verifier.principal(_token()).external_subject.startswith(f"{ISSUER}#")


def test_oid_is_preferred_over_sub(verifier):
    """`sub` is only stable per application — recreating the app registration would
    change it and orphan every account. `oid` is stable across the tenant."""
    principal = verifier.principal(_token(sub="would-change", oid=OID))
    assert principal.external_subject.endswith(f"#{OID}")


def test_sub_is_used_when_there_is_no_oid(verifier):
    principal = verifier.principal(_token(oid=None, sub="only-a-sub"))
    assert principal.external_subject.endswith("#only-a-sub")


def test_a_missing_name_does_not_break_provisioning(verifier):
    principal = verifier.principal(_token(name=None, given_name=None))
    assert principal.display_name == "Unknown"


# ------------------------------------------------------------------ refused


def test_a_token_for_another_application_is_refused(verifier):
    """The whole tenant is signed with these keys. Without an audience check, a token
    minted for any other app in the directory verifies perfectly."""
    with pytest.raises(InvalidTokenError):
        verifier.principal(_token(aud="api://some-other-app"))


def test_a_token_from_another_tenant_is_refused(verifier):
    with pytest.raises(InvalidTokenError):
        verifier.principal(_token(iss="https://login.microsoftonline.com/somebody-else/v2.0"))


def test_a_token_signed_by_the_wrong_key_is_refused(verifier):
    with pytest.raises(InvalidTokenError):
        verifier.principal(_token(_OTHER_KEY))


def test_an_expired_token_is_refused(verifier):
    with pytest.raises(InvalidTokenError):
        verifier.principal(_token(expires_in=-30))


def test_an_unsigned_token_is_refused(verifier):
    """`algorithms` is an allow-list precisely so alg=none cannot be nominated by the
    caller. This is the classic JWT bypass."""
    unsigned = jwt.encode({"iss": ISSUER, "aud": AUDIENCE, "sub": "x", "oid": OID}, None, "none")
    with pytest.raises(InvalidTokenError):
        verifier.principal(unsigned)


def test_a_token_with_no_audience_claim_is_refused(verifier):
    with pytest.raises(InvalidTokenError):
        verifier.principal(_token(aud=None))


def test_rubbish_is_refused(verifier):
    with pytest.raises(InvalidTokenError):
        verifier.principal("not.a.token")


# ------------------------------------------------------------------ both issuers at once


def test_the_composite_sends_local_tokens_to_the_local_verifier(monkeypatch):
    """Guests carry tokens this service minted. Switching SSO on must not lock them out."""
    settings = _settings()
    local = LocalJWT(settings)
    from uuid import uuid4

    user_id = uuid4()
    token, _ = local.issue(user_id)

    composite = CompositeVerifier(local, OIDCTokenVerifier(settings), settings.jwt_issuer)
    assert composite.principal(token).local_id == user_id


def test_the_composite_sends_provider_tokens_to_the_oidc_verifier(verifier, monkeypatch):
    settings = _settings()
    composite = CompositeVerifier(LocalJWT(settings), verifier, settings.jwt_issuer)

    principal = composite.principal(_token())
    assert principal.external_subject == f"{ISSUER}#{OID}"


def test_an_unknown_issuer_still_has_to_pass_a_verifier(verifier):
    """Routing reads `iss` unverified, which is only safe because the chosen verifier
    then validates everything. A made-up issuer must not sail through."""
    settings = _settings()
    composite = CompositeVerifier(LocalJWT(settings), verifier, settings.jwt_issuer)

    with pytest.raises(InvalidTokenError):
        composite.principal(_token(iss="https://attacker.example"))


def test_build_verifier_keeps_both_paths_under_oidc():
    assert isinstance(build_verifier(_settings()), CompositeVerifier)


def test_build_verifier_is_local_only_without_sso():
    assert isinstance(build_verifier(_settings(auth_provider="local", oidc_issuer="")), LocalJWT)


def test_tokens_can_still_be_minted_under_oidc():
    """Guests have no account at the provider and never will, so the issuer must survive
    SSO being switched on — otherwise the incident form goes down with it."""
    assert isinstance(build_issuer(_settings()), LocalJWT)
