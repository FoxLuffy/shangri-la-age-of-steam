"""Add main_quest table

Revision ID: a9d4e2c7b6f1
Revises: f1a8d3c6b2e9
Create Date: 2026-07-26 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a9d4e2c7b6f1'
down_revision: Union[str, Sequence[str], None] = 'f1a8d3c6b2e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "main_quest",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("stages", sa.JSON(), nullable=True),
        sa.Column("current_stage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["character_id"], ["character.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id"),
    )
    op.create_index("ix_main_quest_character_id", "main_quest", ["character_id"])


def downgrade() -> None:
    op.drop_index("ix_main_quest_character_id", table_name="main_quest")
    op.drop_table("main_quest")
