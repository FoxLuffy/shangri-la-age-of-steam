"""Add mod_rating table

Revision ID: f1a8d3c6b2e9
Revises: e7c4a2b9f1d0
Create Date: 2026-07-26 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a8d3c6b2e9'
down_revision: Union[str, Sequence[str], None] = 'e7c4a2b9f1d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "mod_rating",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mod_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("review", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mod_id", "user_id"),
    )
    op.create_index("ix_mod_rating_mod_id", "mod_rating", ["mod_id"])
    op.create_index("ix_mod_rating_user_id", "mod_rating", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_mod_rating_user_id", table_name="mod_rating")
    op.drop_index("ix_mod_rating_mod_id", table_name="mod_rating")
    op.drop_table("mod_rating")
