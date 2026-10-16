import json
from typing import Any

from fastapi import APIRouter, HTTPException

from app.domain.incidents import VerifyResult
from app.evidence.canonical import evidence_hash

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

MAX_PACKAGE_BYTES = 64 * 1024


@router.post("/verify", response_model=VerifyResult)
def verify(package: dict[str, Any]) -> VerifyResult:
    """Recompute the hash of any package. Nothing is stored; anyone can check an anchored hash."""
    if len(json.dumps(package)) > MAX_PACKAGE_BYTES:
        raise HTTPException(status_code=413, detail="Package too large")
    try:
        return VerifyResult(hash=evidence_hash(package))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
