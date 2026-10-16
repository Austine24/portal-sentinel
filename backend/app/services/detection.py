from datetime import datetime, timedelta

from app.data.source import DataSource
from app.domain.models import RiskAssessment
from app.risk.engine import assess
from app.security.engine import evaluate_all
from app.security.rules.burst import TransactionBurstRule
from app.security.rules.value_anomaly import ValueAnomalyRule

RULES = [TransactionBurstRule(), ValueAnomalyRule()]
FETCH_LOOKBACK = timedelta(days=8)


def run_detection(source: DataSource, now: datetime) -> list[RiskAssessment]:
    """transactions -> rules -> risk, for every account. Highest risk first."""
    txs = source.fetch_transactions(now - FETCH_LOOKBACK, now)
    findings = evaluate_all(txs, now, RULES)
    assessments = [
        a for account, fs in findings.items()
        if (a := assess(account, fs, now, source.origin)) is not None
    ]
    return sorted(assessments, key=lambda a: a.risk_score, reverse=True)
