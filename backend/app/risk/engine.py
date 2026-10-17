"""Portal Sentinel's analytical risk model. Not a scientifically validated score."""
from dataclasses import dataclass, field
from datetime import datetime
from math import prod

from app.domain.models import DataOrigin, RiskAssessment, RiskFactor, RiskLevel, RuleFinding


@dataclass(frozen=True)
class RiskConfig:
    # How much each rule is trusted, 0 to 1. Tune these without touching any code logic.
    rule_weights: dict[str, float] = field(
        default_factory=lambda: {"SR-001": 0.85, "SR-002": 0.75, "ML-001": 0.6}
    )
    default_weight: float = 0.5


def risk_level(score: int) -> RiskLevel:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "moderate"
    if score >= 20:
        return "guarded"
    return "low"


def assess(
    account: str,
    findings: list[RuleFinding],
    evaluated_at: datetime,
    data_origin: DataOrigin,
    config: RiskConfig = RiskConfig(),
) -> RiskAssessment | None:
    """Combine findings with a noisy-OR: each finding adds risk without ever passing 100."""
    if not findings:
        return None

    contributions = [
        config.rule_weights.get(f.rule_id, config.default_weight) * f.strength / 100
        for f in findings
    ]
    combined = 1 - prod(1 - c for c in contributions)
    score = round(100 * combined)

    total = sum(contributions)
    factors = [
        RiskFactor(
            label=f.name,
            detail=f.summary,
            weight=round(100 * c / total, 1) if total > 0 else 0.0,
        )
        for f, c in zip(findings, contributions)
    ]
    return RiskAssessment(
        account=account,
        risk_score=score,
        level=risk_level(score),
        factors=factors,
        findings=findings,
        data_origin=data_origin,
        evaluated_at=evaluated_at,
    )
