from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime


class IncidentRow(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        # DB-level guard against duplicates: one incident per account per detection hour.
        UniqueConstraint("dedupe_key", name="uq_incidents_dedupe_key"),
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_account", "account"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dedupe_key: Mapped[str] = mapped_column(String(190))
    title: Mapped[str] = mapped_column(String(200))
    account: Mapped[str] = mapped_column(String(128))
    risk_score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(20), default="open")
    data_origin: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    factors: Mapped[list] = mapped_column(JSON)
    findings: Mapped[list] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)
    # Filled in later by the on-chain evidence flow.
    evidence_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence_tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence_block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_contract: Mapped[str | None] = mapped_column(String(42), nullable=True)
    evidence_anchored_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    evidence_package: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence_prepared_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    events: Mapped[list["IncidentEventRow"]] = relationship(
        back_populates="incident",
        order_by="IncidentEventRow.at, IncidentEventRow.id",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class IncidentEventRow(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"))
    at: Mapped[datetime] = mapped_column(UTCDateTime)
    text: Mapped[str] = mapped_column(String(500))

    incident: Mapped[IncidentRow] = relationship(back_populates="events")


class NetworkSnapshotRow(Base):
    __tablename__ = "network_snapshots"
    __table_args__ = (Index("ix_network_snapshots_taken_at", "taken_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taken_at: Mapped[datetime] = mapped_column(UTCDateTime)
    chain_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    best_block: Mapped[int] = mapped_column(Integer)
    finalized_block: Mapped[int] = mapped_column(Integer)
    finality_lag: Mapped[int] = mapped_column(Integer)
    window_blocks: Mapped[int] = mapped_column(Integer)
    missed_slots: Mapped[int] = mapped_column(Integer)
    authors: Mapped[dict] = mapped_column(JSON)
    distinct_authors: Mapped[int] = mapped_column(Integer)
    max_author_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    block_age_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    peers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_origin: Mapped[str] = mapped_column(String(16), default="live")
