from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import NetworkSnapshotRow
from app.domain.network import NetworkSnapshot


def add(session: Session, snapshot: NetworkSnapshot) -> NetworkSnapshotRow:
    row = NetworkSnapshotRow(**snapshot.model_dump(mode="python"))
    session.add(row)
    session.commit()
    return row


def latest(session: Session) -> NetworkSnapshotRow | None:
    return session.scalars(
        select(NetworkSnapshotRow).order_by(NetworkSnapshotRow.taken_at.desc(), NetworkSnapshotRow.id.desc()).limit(1)
    ).first()


def between(session: Session, start: datetime, end: datetime, exclude_id: int | None, limit: int = 300):
    """Snapshots taken in [start, end), oldest first."""
    query = select(NetworkSnapshotRow).where(
        NetworkSnapshotRow.taken_at >= start, NetworkSnapshotRow.taken_at < end
    )
    if exclude_id is not None:
        query = query.where(NetworkSnapshotRow.id != exclude_id)
    return list(session.scalars(query.order_by(NetworkSnapshotRow.taken_at).limit(limit)))


def recent(session: Session, limit: int) -> list[NetworkSnapshotRow]:
    rows = session.scalars(
        select(NetworkSnapshotRow).order_by(NetworkSnapshotRow.taken_at.desc(), NetworkSnapshotRow.id.desc()).limit(limit)
    )
    return list(reversed(list(rows)))   # oldest first, ready for a chart
