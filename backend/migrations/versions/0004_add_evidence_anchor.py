"""add on-chain anchor columns to incidents

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("evidence_block", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("evidence_contract", sa.String(42), nullable=True))
    op.add_column("incidents", sa.Column("evidence_anchored_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "evidence_anchored_at")
    op.drop_column("incidents", "evidence_contract")
    op.drop_column("incidents", "evidence_block")
