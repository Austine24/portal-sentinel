from datetime import datetime, timezone

from fastapi import APIRouter

from app.data.simulated import SimulatedSource
from app.domain.models import RiskAssessment
from app.services.detection import run_detection

router = APIRouter(prefix="/api", tags=["assessments"])


@router.get("/assessments", response_model=list[RiskAssessment])
def list_assessments() -> list[RiskAssessment]:
    """DEMO / SIMULATED until a live Portaldot data source is connected."""
    now = datetime.now(timezone.utc)
    return run_detection(SimulatedSource(now=now), now)
