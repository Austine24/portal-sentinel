"""add evidence package columns to incidents

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("evidence_package", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("evidence_prepared_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "evidence_prepared_at")
    op.drop_column("incidents", "evidence_package")
