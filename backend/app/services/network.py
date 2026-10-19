import threading
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import NetworkSnapshotRow
from app.domain.network import NetworkHealth, NetworkSnapshot
from app.portaldot.collector import HeaderCache, collect_snapshot
from app.portaldot.rpc import JsonRpcClient
from app.repositories import network as repo
from app.risk.engine import assess
from app.security.network_rules import evaluate_network

HISTORY = timedelta(hours=24)
NOTE = (
    "Read-only data from the Portaldot testnet node. Block times are derived from slot numbers "
    "(6 s per slot). A short sample of recent blocks; do not over-read it."
)

# One process-wide cache and lock: the public RPC should be asked as little as possible.
_cache = HeaderCache()
_lock = threading.Lock()


def to_snapshot(row: NetworkSnapshotRow) -> NetworkSnapshot:
    return NetworkSnapshot(
        taken_at=row.taken_at, chain_name=row.chain_name, best_block=row.best_block,
        finalized_block=row.finalized_block, finality_lag=row.finality_lag,
        window_blocks=row.window_blocks, missed_slots=row.missed_slots, authors=row.authors,
        distinct_authors=row.distinct_authors, max_author_share=row.max_author_share,
        block_age_s=row.block_age_s, peers=row.peers, data_origin=row.data_origin,
    )


def health_for(session: Session, row: NetworkSnapshotRow, cached: bool) -> NetworkHealth:
    history = [
        to_snapshot(r)
        for r in repo.between(session, row.taken_at - HISTORY, row.taken_at, exclude_id=row.id)
    ]
    snapshot = to_snapshot(row)
    findings = evaluate_network(snapshot, history)
    assessment = assess("network", findings, snapshot.taken_at, "live")
    return NetworkHealth(
        snapshot=snapshot,
        findings=findings,
        risk_score=assessment.risk_score if assessment else 0,
        level=assessment.level if assessment else "low",
        cached=cached,
        note=NOTE,
    )


def refresh(
    session: Session, client: JsonRpcClient, window: int, min_refresh_seconds: float, now: datetime
) -> NetworkHealth:
    """Takes a fresh snapshot unless a recent one exists (protects the public node from being hammered)."""
    with _lock:
        newest = repo.latest(session)
        if newest is not None and (now - newest.taken_at).total_seconds() < min_refresh_seconds:
            return health_for(session, newest, cached=True)
        snapshot = collect_snapshot(client, _cache, window, now)
        row = repo.add(session, snapshot)
        return health_for(session, row, cached=False)


def reset_cache() -> None:
    """For tests."""
    _cache._blocks.clear()
