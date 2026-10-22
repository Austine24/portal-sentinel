from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.data.simulated import SimulatedSource
from app.db.base import get_session
from app.evidence.anchor import AnchorError
from app.evidence.canonical import onchain_incident_id
from app.portaldot.evm import EvmClient
from app.portaldot.rpc import JsonRpcClient
from app.domain.incidents import (
    AnchorRequest,
    EvidencePackage,
    IncidentOut,
    IncidentStatus,
    StatusChange,
    SyncResult,
)
from app.repositories import incidents as repo
from app.services import incidents as service
from app.services.detection import run_detection

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

SessionDep = Annotated[Session, Depends(get_session)]


def get_evm_client() -> EvmClient:
    settings = get_settings()
    return EvmClient(JsonRpcClient(settings.portaldot_evm_rpc_url, timeout=settings.portaldot_timeout_seconds))


EvmDep = Annotated[EvmClient, Depends(get_evm_client)]


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


@router.post("/{incident_id}/evidence/prepare", response_model=EvidencePackage)
def prepare_evidence(incident_id: int, session: SessionDep) -> EvidencePackage:
    """Freeze this incident's evidence package and return its hash. Safe to call twice."""
    row = repo.get(session, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    row = service.prepare_evidence(session, row, datetime.now(timezone.utc))
    return EvidencePackage(
        hash=row.evidence_hash,
        onchain_incident_id=onchain_incident_id(row.evidence_package),
        package=row.evidence_package,
    )


@router.get("/{incident_id}/evidence", response_model=EvidencePackage)
def get_evidence(incident_id: int, session: SessionDep) -> EvidencePackage:
    row = repo.get(session, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if row.evidence_package is None:
        raise HTTPException(status_code=404, detail="Evidence has not been prepared yet")
    return EvidencePackage(
        hash=row.evidence_hash,
        onchain_incident_id=onchain_incident_id(row.evidence_package),
        package=row.evidence_package,
    )


@router.post("/{incident_id}/evidence/anchor", response_model=IncidentOut)
def anchor_evidence(incident_id: int, request: AnchorRequest, session: SessionDep, evm: EvmDep) -> IncidentOut:
    """Confirms, against the chain, that the evidence was recorded by the given transaction, then links it."""
    registry_address = get_settings().registry_address
    if not registry_address:
        raise HTTPException(status_code=503, detail="No evidence registry is configured. Set REGISTRY_ADDRESS in backend/.env after deploying the contract.")
    row = repo.get(session, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        row = service.anchor_evidence(session, row, request.tx_hash, evm, registry_address, datetime.now(timezone.utc))
    except service.AnchorConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AnchorError as exc:
        raise HTTPException(status_code=409 if exc.retryable else 422, detail=str(exc)) from exc
    return service.to_out(row)
