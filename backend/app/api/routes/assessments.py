from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.data.simulated import SimulatedSource
from app.domain.models import RiskAssessment
from app.risk.engine import assess
from app.security.engine import evaluate_all
from app.security.rules.burst import TransactionBurstRule
from app.security.rules.value_anomaly import ValueAnomalyRule

router = APIRouter(prefix="/api", tags=["assessments"])

RULES = [TransactionBurstRule(), ValueAnomalyRule()]


@router.get("/assessments", response_model=list[RiskAssessment])
def list_assessments() -> list[RiskAssessment]:
    """DEMO / SIMULATED until a live Portaldot data source is connected."""
    now = datetime.now(timezone.utc)
    source = SimulatedSource(now=now)
    txs = source.fetch_transactions(now - timedelta(days=8), now)
    findings = evaluate_all(txs, now, RULES)
    assessments = [
        a for account, fs in findings.items()
        if (a := assess(account, fs, now, source.origin)) is not None
    ]
    return sorted(assessments, key=lambda a: a.risk_score, reverse=True)
