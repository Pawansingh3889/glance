"""Registering and signing in.

Self-signup creates **participants only**. A survey is answered by whoever is sent the
link, so participants have to be able to arrive on their own; a creator can publish
surveys and read everyone's answers, so that role is granted deliberately — by seed, or
by promoting an account — never claimed at a signup form. Accepting a role from the
request body would make the whole role check theatre.
"""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import hash_password, needs_rehash, verify_password
from app.auth.schemas import GuestRequest, RegisterRequest
from app.auth.tokens import TokenIssuer
from app.errors import ConflictError, UnauthorizedError
from app.users.models import User, UserRole
from app.users.repository import UserRepository

logger = logging.getLogger("app.auth")

# One message for "no such account" and "wrong password" both. Distinguishing them
# turns the login endpoint into a way to test whether an address has an account here,
# which for a survey tool is a disclosure in itself.
_REJECTED = "Email or password is incorrect."


class AuthService:
    def __init__(self, session: AsyncSession, issuer: TokenIssuer) -> None:
        self.session = session
        self.issuer = issuer
        self.users = UserRepository(session)

    async def register(self, data: RegisterRequest) -> tuple[User, str, int]:
        email = data.email.strip().lower()
        user = User(
            email=email,
            display_name=data.display_name,
            role=UserRole.participant,
            password_hash=hash_password(data.password),
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            # Checking first and inserting after is a race: two requests for the same
            # address both find nothing and both insert. The unique index is the only
            # thing that actually decides, so let it, and translate what it says.
            await self.session.rollback()
            raise ConflictError("An account with that email already exists.") from None

        await self.session.refresh(user)
        token, expires_in = self.issuer.issue(user.id)
        return user, token, expires_in

    async def start_guest(self, data: GuestRequest) -> tuple[User, str, int]:
        """Admit a participant who has no account.

        Every call mints a *new* row, even when the same address is given twice. Looking
        an address up and reusing what it found would turn this endpoint into a way to
        assume an existing identity — type a colleague's address, receive a token for
        their account, read their answers — and no password is being checked here to
        stop it. A fresh row grants access to nothing but itself.

        The address, when given, is stored as contact detail (``contact_email``) and
        never as ``email``: it identifies nobody and is not unique.
        """
        user = User(
            email=None,
            contact_email=str(data.email).strip().lower() if data.email else None,
            display_name=data.display_name,
            role=UserRole.participant,
            # No hash, so this row can never be used to log in locally. The only way to
            # hold it is to be handed the token issued right here.
            password_hash=None,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        token, expires_in = self.issuer.issue(user.id)
        logger.info("guest admitted user=%s contactable=%s", user.id, bool(user.contact_email))
        return user, token, expires_in

    async def login(self, email: str, password: str) -> tuple[User, str, int]:
        user = await self.users.get_by_email(email)
        # verify_password is called even when no user matched — it hashes against a
        # dummy so the two paths take comparable time. Returning early here would make
        # "no such account" the fast answer and hand out an enumeration oracle.
        if not verify_password(password, user.password_hash if user else None) or user is None:
            logger.info("failed login for %r", email.strip().lower())
            raise UnauthorizedError(_REJECTED)

        if user.password_hash and needs_rehash(user.password_hash):
            # The cost parameters moved on since this was stored. Now is the only
            # moment the plaintext exists to re-hash with, so take it.
            user.password_hash = hash_password(password)
            await self.session.commit()

        token, expires_in = self.issuer.issue(user.id)
        return user, token, expires_in
