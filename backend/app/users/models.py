"""User model and role enum."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    creator = "creator"
    participant = "participant"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Nullable because a guest participant has no account: they give a name at the door
    # and are never asked for an address. Postgres allows any number of NULLs under a
    # unique index, so the constraint still does its job for everyone who does have one.
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"))
    # Who this account is at the identity provider, when one vouches for it: the `oid`
    # claim from Microsoft Entra, namespaced by issuer. Unique so two accounts can never
    # claim the same external identity, nullable because guests and seeded local accounts
    # have no provider. Kept out of the primary key deliberately — a row is referenced by
    # every answer its owner has given, and rekeying on a value the IdP owns would make
    # those references hostage to a tenant migration.
    external_subject: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    # Where to reach a guest about the report they filed — deliberately *not* `email`
    # and deliberately not unique. Putting it in `email` would either collide the second
    # time an address was used, or make an account reusable by anyone who could type the
    # address, which is a way into someone else's answers. This column identifies nobody
    # and grants nothing; it is contact detail and only that.
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    # Nullable, and it has to be: an account authenticated by an external identity
    # provider never has a password here, and neither do the rows that predate this
    # column. An account with no hash cannot log in locally — see auth/passwords.py,
    # which still does the work of checking so that fact is not visible from outside.
    #
    # Wide enough for an Argon2id PHC string with room for the cost parameters to grow.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
