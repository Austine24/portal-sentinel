from datetime import datetime, timezone

from fastapi import APIRouter

from app.data.simulated import SimulatedSource
from app.domain.incidents import ModelStatusOut, RuleInfo
from app.ml.anomaly import RULE_NAME
from app.services.detection import RULES, run_detection_with_status

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/status", response_model=ModelStatusOut)
def model_status() -> ModelStatusOut:
    """Trains the model on the current data and reports what it learned from. DEMO / SIMULATED data."""
    now = datetime.now(timezone.utc)
    source = SimulatedSource(now=now)
    _, status = run_detection_with_status(source, now)
    return ModelStatusOut(
        model=RULE_NAME,
        trained=status.trained,
        reason=status.reason,
        training_rows=status.training_rows,
        accounts=status.accounts,
        features=list(status.features),
        trained_at=status.trained_at,
        rules=[RuleInfo(rule_id=r.rule_id, name=r.name) for r in RULES],
        data_origin=source.origin,
        note=(
            "Retrained on every run from the last 7 days; nothing is stored. "
            "An anomaly is not proof of malicious behaviour."
        ),
    )
