"""Add crafting specialization (recipe branch/tier + crafting_proficiency)

Revision ID: e7c4a2b9f1d0
Revises: d5b2c9f1a3e8
Create Date: 2026-07-25 22:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7c4a2b9f1d0'
down_revision: Union[str, Sequence[str], None] = 'd5b2c9f1a3e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("recipe", sa.Column("branch", sa.String(), nullable=True))
    op.add_column("recipe", sa.Column("tier", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "crafting_proficiency",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("branch", sa.String(), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["character.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "branch"),
    )
    op.create_index("ix_crafting_proficiency_character_id", "crafting_proficiency", ["character_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_crafting_proficiency_character_id", table_name="crafting_proficiency")
    op.drop_table("crafting_proficiency")
    op.drop_column("recipe", "tier")
    op.drop_column("recipe", "branch")
