from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_session
from app.domain.network import NetworkHealth, NetworkHistoryPoint
from app.portaldot.rpc import JsonRpcClient
from app.repositories import network as repo
from app.services import network as service

router = APIRouter(prefix="/api/network", tags=["network"])

SessionDep = Annotated[Session, Depends(get_session)]


def get_rpc_client() -> JsonRpcClient:
    settings = get_settings()
    return JsonRpcClient(settings.portaldot_substrate_http_url, timeout=settings.portaldot_timeout_seconds)


ClientDep = Annotated[JsonRpcClient, Depends(get_rpc_client)]


@router.post("/refresh", response_model=NetworkHealth)
def refresh(session: SessionDep, client: ClientDep) -> NetworkHealth:
    """Reads the live testnet (read-only) and stores a snapshot. Rate-limited by a minimum interval."""
    settings = get_settings()
    return service.refresh(
        session, client, settings.network_window_blocks,
        settings.network_min_refresh_seconds, datetime.now(timezone.utc),
    )


@router.get("/latest", response_model=NetworkHealth)
def latest(session: SessionDep) -> NetworkHealth:
    row = repo.latest(session)
    if row is None:
        raise HTTPException(status_code=404, detail="No network snapshot yet. Press Refresh.")
    return service.health_for(session, row, cached=True)


@router.get("/history", response_model=list[NetworkHistoryPoint])
def history(session: SessionDep, limit: Annotated[int, Query(ge=1, le=500)] = 60) -> list[NetworkHistoryPoint]:
    return [
        NetworkHistoryPoint(
            taken_at=r.taken_at, best_block=r.best_block, finality_lag=r.finality_lag,
            missed_slots=r.missed_slots, distinct_authors=r.distinct_authors,
            max_author_share=r.max_author_share, block_age_s=r.block_age_s, data_origin=r.data_origin,
        )
        for r in repo.recent(session, limit)
    ]
