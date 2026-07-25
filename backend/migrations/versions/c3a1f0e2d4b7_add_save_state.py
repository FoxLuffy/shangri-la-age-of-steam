"""Add save_state table

Revision ID: c3a1f0e2d4b7
Revises: b206b660a4ae
Create Date: 2026-07-25 20:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3a1f0e2d4b7'
down_revision: Union[str, Sequence[str], None] = 'b206b660a4ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "save_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["character.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_save_state_character_id", "save_state", ["character_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_save_state_character_id", table_name="save_state")
    op.drop_table("save_state")
