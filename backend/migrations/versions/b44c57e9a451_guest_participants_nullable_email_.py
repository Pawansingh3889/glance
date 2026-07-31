"""guest participants: nullable email, contact_email

A participant no longer has an account. They give a name at the door, optionally an
address to be reached on, and answer. That needs two changes here:

- ``email`` becomes nullable, because a guest has none. Postgres permits any number of
  NULLs under a unique index, so the constraint still holds for everyone who does.
- ``contact_email`` is added: where to reach a guest about the report they filed. It is
  deliberately separate from ``email`` and deliberately not unique — reusing ``email``
  would either collide the second time an address was given, or make an existing account
  reachable by anyone who could type its address.

Revision ID: b44c57e9a451
Revises: bbe01a8a9655
Create Date: 2026-07-31 02:55:57.535405

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b44c57e9a451"
down_revision: str | None = "bbe01a8a9655"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("contact_email", sa.String(length=320), nullable=True))
    op.alter_column("users", "email", existing_type=sa.VARCHAR(length=320), nullable=True)


def downgrade() -> None:
    # Guests exist precisely because email became nullable, so restoring NOT NULL cannot
    # succeed while any remain. Deleting them is not an option this migration will take
    # on itself: a guest row owns the incident reports and survey answers that guest
    # filed, and removing it would take those with it. Say so and stop.
    guests = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM users WHERE email IS NULL"))
        .scalar_one()
    )
    if guests:
        raise RuntimeError(
            f"{guests} guest participant(s) have no email, so users.email cannot go back "
            "to NOT NULL. Their answers and incident reports belong to those rows — give "
            "them addresses or remove them deliberately before downgrading."
        )
    op.alter_column("users", "email", existing_type=sa.VARCHAR(length=320), nullable=False)
    op.drop_column("users", "contact_email")
