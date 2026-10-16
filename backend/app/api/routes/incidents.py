from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.data.simulated import SimulatedSource
from app.db.base import get_session
from app.domain.incidents import IncidentOut, IncidentStatus, StatusChange, SyncResult
from app.repositories import incidents as repo
from app.services import incidents as service
from app.services.detection import run_detection

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    session: SessionDep,
    status: IncidentStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[IncidentOut]:
    return [service.to_out(r) for r in repo.list_incidents(session, status, limit)]


@router.post("/sync", response_model=SyncResult)
def sync_incidents(session: SessionDep) -> SyncResult:
    """Run detection and record new incidents. DEMO / SIMULATED until a live source exists."""
    now = datetime.now(timezone.utc)
    assessments = run_detection(SimulatedSource(now=now), now)
    return service.sync_from_assessments(session, assessments, now)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, session: SessionDep) -> IncidentOut:
    row = repo.get(session, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return service.to_out(row)


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def change_incident_status(incident_id: int, change: StatusChange, session: SessionDep) -> IncidentOut:
    row = repo.get(session, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        row = service.change_status(
            session, row, change.status, change.note, datetime.now(timezone.utc)
        )
    except service.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return service.to_out(row)
