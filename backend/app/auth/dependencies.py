"""Resolving the caller from a bearer token.

This used to trust an ``X-User-Id`` header outright: whoever sent the request chose
whose it was. That was an explicit development simplification, and the note beside it
promised the swap would touch one dependency and no routes. It did — every route is
unchanged, and the role gates are the same two functions they always were.

Authorization still lives in the services, not here. These dependencies answer "who is
this, and are they broadly the right sort of user"; ownership questions — whether *this*
creator may read *that* template — stay where they already were.
"""

import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import InvalidTokenError, Principal, TokenVerifier, build_verifier
from app.config import get_settings
from app.db.session import get_session
from app.errors import ForbiddenError, UnauthorizedError
from app.users.models import User, UserRole
from app.users.repository import UserRepository

# auto_error=False so a missing header arrives here as None instead of becoming
# Starlette's own 403 with a bare {"detail": ...} body. Every failure below is a 401 in
# this service's error shape, and "sent no credentials" is not a 403.
_bearer = HTTPBearer(auto_error=False)

logger = logging.getLogger("app.auth")


def get_token_verifier() -> TokenVerifier:
    """A dependency so it can be overridden in tests, and swapped by configuration."""
    return build_verifier(get_settings())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verifier: TokenVerifier = Depends(get_token_verifier),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token.")
    try:
        principal = verifier.principal(credentials.credentials)
    except InvalidTokenError:
        # Deliberately the same message for expired, tampered, malformed and
        # wrong-issuer. Telling them apart helps whoever is probing the endpoint and
        # nobody else — the caller's remedy is to log in again in every case.
        raise UnauthorizedError("Token is not valid.") from None

    users = UserRepository(session)

    # The user is loaded on every request rather than trusted from the token's claims.
    # A token therefore cannot carry a role its holder no longer has, and deleting an
    # account takes effect at once instead of whenever the token happens to expire.
    if principal.local_id is not None:
        user = await users.get(principal.local_id)
        if user is None:
            raise UnauthorizedError("Token is not valid.")
        return user

    if principal.external_subject is None:
        raise UnauthorizedError("Token is not valid.")
    return await _resolve_external(session, users, principal)


async def _resolve_external(
    session: AsyncSession, users: UserRepository, principal: Principal
) -> User:
    """Find, or on first sight create, the local row behind an identity-provider token.

    The role granted here is ``creator``, because reaching this branch at all means the
    company directory vouched for the person. **Who is allowed to reach it is decided at
    the identity provider, not here** — in Entra that is the enterprise application's
    "User assignment required" setting plus the app-role or group assignment. Without
    that, every account in the tenant that can obtain a token becomes a creator, and a
    creator reads every answer in the database.
    """
    existing = await users.get_by_external_subject(principal.external_subject or "")
    if existing is not None:
        return existing

    user = User(
        external_subject=principal.external_subject,
        # The address is recorded for display, but identity is the external subject —
        # matching on email instead would let a renamed or recycled mailbox at the
        # provider take over an existing account.
        email=principal.email,
        display_name=principal.display_name or "Unknown",
        role=UserRole.creator,
        password_hash=None,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # Two first requests for the same person can race, and the address may already
        # belong to a seeded local account. The unique indexes decide; re-read and use
        # whatever actually landed.
        await session.rollback()
        settled = await users.get_by_external_subject(principal.external_subject or "")
        if settled is None:
            raise UnauthorizedError("Token is not valid.") from None
        return settled
    await session.refresh(user)
    logger.info("provisioned sso user=%s from %s", user.id, principal.external_subject)
    return user


async def require_creator(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.creator:
        raise ForbiddenError("This action requires a creator account.")
    return user


async def require_participant(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.participant:
        raise ForbiddenError("Only participants can take surveys.")
    return user
