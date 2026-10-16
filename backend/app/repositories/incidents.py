from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IncidentEventRow, IncidentRow

ACTIVE_STATUSES = ("open", "investigating")


def get(session: Session, incident_id: int) -> IncidentRow | None:
    return session.get(IncidentRow, incident_id)


def list_incidents(session: Session, status: str | None, limit: int) -> list[IncidentRow]:
    query = select(IncidentRow).order_by(IncidentRow.detected_at.desc(), IncidentRow.id.desc())
    if status is not None:
        query = query.where(IncidentRow.status == status)
    return list(session.scalars(query.limit(limit)))


def has_active_incident(session: Session, account: str) -> bool:
    query = select(IncidentRow.id).where(
        IncidentRow.account == account, IncidentRow.status.in_(ACTIVE_STATUSES)
    ).limit(1)
    return session.scalars(query).first() is not None


def add(session: Session, row: IncidentRow) -> None:
    session.add(row)
    session.flush()  # raises IntegrityError here if the dedupe key already exists


def add_event(row: IncidentRow, text: str, at: datetime) -> None:
    row.events.append(IncidentEventRow(at=at, text=text))
