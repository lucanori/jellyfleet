"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-10-31 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("combination_name", sa.String(length=255), nullable=False),
        sa.Column("father_server", sa.String(length=255), nullable=False),
        sa.Column("child_server", sa.String(length=255), nullable=False),
        sa.Column("domains", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=True),
        sa.Column("actions_count", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_runs_id"), "sync_runs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_runs_id"), table_name="sync_runs")
    op.drop_table("sync_runs")
