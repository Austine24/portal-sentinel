"""create network_snapshots

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-18
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "network_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("taken_at", sa.DateTime(), nullable=False),
        sa.Column("chain_name", sa.String(64), nullable=True),
        sa.Column("best_block", sa.Integer(), nullable=False),
        sa.Column("finalized_block", sa.Integer(), nullable=False),
        sa.Column("finality_lag", sa.Integer(), nullable=False),
        sa.Column("window_blocks", sa.Integer(), nullable=False),
        sa.Column("missed_slots", sa.Integer(), nullable=False),
        sa.Column("authors", sa.JSON(), nullable=False),
        sa.Column("distinct_authors", sa.Integer(), nullable=False),
        sa.Column("max_author_share", sa.Float(), nullable=True),
        sa.Column("block_age_s", sa.Float(), nullable=True),
        sa.Column("peers", sa.Integer(), nullable=True),
        sa.Column("data_origin", sa.String(16), nullable=False),
    )
    op.create_index("ix_network_snapshots_taken_at", "network_snapshots", ["taken_at"])


def downgrade() -> None:
    op.drop_index("ix_network_snapshots_taken_at", table_name="network_snapshots")
    op.drop_table("network_snapshots")
