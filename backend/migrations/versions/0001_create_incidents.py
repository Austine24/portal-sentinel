"""create incidents and incident_events

Revision ID: 0001
Revises:
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dedupe_key", sa.String(190), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("account", sa.String(128), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("data_origin", sa.String(16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("evidence_hash", sa.String(80), nullable=True),
        sa.Column("evidence_tx_hash", sa.String(80), nullable=True),
        sa.UniqueConstraint("dedupe_key", name="uq_incidents_dedupe_key"),
    )
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_account", "incidents", ["account"])

    op.create_table(
        "incident_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "incident_id",
            sa.Integer(),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("incident_events")
    op.drop_index("ix_incidents_account", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_table("incidents")
