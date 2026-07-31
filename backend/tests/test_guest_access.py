"""Participants arriving without an account.

The floor has to be able to answer a survey and report a hazard without being issued
credentials first. What these tests hold is the boundary that makes that safe: a guest
token is a participant token and nothing more, and the address a guest optionally leaves
is contact detail — never a way to reach an account, theirs or anyone else's.
"""

import pytest
from sqlalchemy import select

from app.auth.schemas import GuestRequest
from app.auth.service import AuthService
from app.auth.tokens import LocalJWT
from app.config import Settings
from app.errors import UnauthorizedError
from app.users.models import User, UserRole


@pytest.fixture
def issuer() -> LocalJWT:
    return LocalJWT(
        Settings(
            database_url="postgresql+asyncpg://unused/unused",
            jwt_secret="test-only-signing-key-not-the-published-default",
        )
    )


async def test_a_guest_is_admitted_with_just_a_name(session, issuer):
    user, token, expires_in = await AuthService(session, issuer).start_guest(
        GuestRequest(display_name="Marta K")
    )

    assert user.role is UserRole.participant
    assert user.display_name == "Marta K"
    assert user.email is None
    assert user.contact_email is None
    assert token and expires_in > 0


async def test_the_token_identifies_the_guest(session, issuer):
    user, token, _ = await AuthService(session, issuer).start_guest(
        GuestRequest(display_name="Marta K")
    )
    assert issuer.subject(token) == user.id


async def test_an_address_is_stored_as_contact_detail_not_identity(session, issuer):
    """The address must not land in ``email``: that column is unique and is what an
    account is found by, so putting it there would make the guest row addressable."""
    user, _, _ = await AuthService(session, issuer).start_guest(
        GuestRequest(display_name="Marta K", email="Marta.K@Example.com")
    )

    assert user.email is None
    assert user.contact_email == "marta.k@example.com"  # normalised


async def test_the_same_address_twice_makes_two_separate_guests(session, issuer):
    """No lookup-and-reuse. If the second call returned the first guest's row, anyone who
    could type an address would be handed that person's answers."""
    svc = AuthService(session, issuer)
    first, _, _ = await svc.start_guest(GuestRequest(display_name="Marta K", email="m@example.com"))
    second, _, _ = await svc.start_guest(
        GuestRequest(display_name="Someone Else", email="m@example.com")
    )

    assert first.id != second.id
    assert second.display_name == "Someone Else"


async def test_many_guests_coexist_despite_the_unique_email_index(session, issuer):
    """Postgres allows any number of NULLs under a unique index; this is the property the
    whole design leans on, so it is asserted rather than assumed."""
    svc = AuthService(session, issuer)
    for n in range(5):
        await svc.start_guest(GuestRequest(display_name=f"Guest {n}"))

    guests = (await session.execute(select(User).where(User.email.is_(None)))).scalars().all()
    assert len(guests) == 5


async def test_a_guest_row_cannot_be_logged_into(session, issuer):
    """It has no password hash, so the local login path must refuse it — including when
    the contact address is used as the username."""
    svc = AuthService(session, issuer)
    await svc.start_guest(GuestRequest(display_name="Marta K", email="m@example.com"))

    with pytest.raises(UnauthorizedError):
        await svc.login("m@example.com", "any-password-at-all")


async def test_a_guest_is_never_a_creator(session, issuer):
    """The role is set here, not taken from the request. A guest endpoint that could mint
    a creator would hand out every survey and every answer in the database."""
    user, _, _ = await AuthService(session, issuer).start_guest(
        GuestRequest(display_name="Marta K")
    )
    assert user.role is UserRole.participant


@pytest.mark.parametrize("name", ["", "   "])
async def test_a_blank_name_is_refused(name):
    """A report has to have someone's name on it."""
    with pytest.raises(ValueError):
        GuestRequest(display_name=name)


async def test_a_malformed_address_is_refused():
    with pytest.raises(ValueError):
        GuestRequest(display_name="Marta K", email="not-an-address")
