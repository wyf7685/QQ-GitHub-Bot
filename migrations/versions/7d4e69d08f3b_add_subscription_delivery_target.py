"""add subscription delivery target

Revision ID: 7d4e69d08f3b
Revises: 14ab5b50ede5
Create Date: 2026-09-06

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7d4e69d08f3b"
down_revision: str | Sequence[str] | None = "14ab5b50ede5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "subscription",
        sa.Column(
            "delivery_target",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("subscription", "delivery_target")
