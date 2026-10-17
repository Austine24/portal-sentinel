from datetime import datetime, timedelta

from app.data.source import DataSource
from app.domain.models import RiskAssessment
from app.ml.anomaly import IsolationForestDetector, ModelStatus
from app.risk.engine import assess
from app.security.engine import evaluate_all
from app.security.rules.burst import TransactionBurstRule
from app.security.rules.value_anomaly import ValueAnomalyRule

RULES = [TransactionBurstRule(), ValueAnomalyRule()]
DETECTOR = IsolationForestDetector()
FETCH_LOOKBACK = timedelta(days=8)


def run_detection_with_status(source: DataSource, now: datetime) -> tuple[list[RiskAssessment], ModelStatus]:
    """transactions -> rules + anomaly model -> risk, for every account. Highest risk first."""
    txs = source.fetch_transactions(now - FETCH_LOOKBACK, now)
    findings = evaluate_all(txs, now, RULES)
    model_findings, status = DETECTOR.fit_and_score(txs, now)
    for account, finding in model_findings.items():
        findings.setdefault(account, []).append(finding)

    assessments = [
        a for account, fs in findings.items()
        if (a := assess(account, fs, now, source.origin)) is not None
    ]
    return sorted(assessments, key=lambda a: a.risk_score, reverse=True), status


def run_detection(source: DataSource, now: datetime) -> list[RiskAssessment]:
    return run_detection_with_status(source, now)[0]
