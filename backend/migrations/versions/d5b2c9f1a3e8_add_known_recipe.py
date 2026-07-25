"""Add known_recipe table

Revision ID: d5b2c9f1a3e8
Revises: c3a1f0e2d4b7
Create Date: 2026-07-25 21:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5b2c9f1a3e8'
down_revision: Union[str, Sequence[str], None] = 'c3a1f0e2d4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "known_recipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("discovered_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["character.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipe.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "recipe_id"),
    )
    op.create_index("ix_known_recipe_character_id", "known_recipe", ["character_id"])
    op.create_index("ix_known_recipe_recipe_id", "known_recipe", ["recipe_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_known_recipe_recipe_id", table_name="known_recipe")
    op.drop_index("ix_known_recipe_character_id", table_name="known_recipe")
    op.drop_table("known_recipe")
