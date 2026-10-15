import pytest

from app.domain.models import RuleFinding
from app.risk.engine import RiskConfig, assess, risk_level
from tests.factories import NOW


def finding(rule_id: str, strength: float) -> RuleFinding:
    return RuleFinding(rule_id=rule_id, name=f"Rule {rule_id}", strength=strength, confidence=1.0,
                       summary=f"summary {rule_id}", evidence={}, suggestion="check")


@pytest.mark.parametrize("score,level", [
    (0, "low"), (19, "low"), (20, "guarded"), (39, "guarded"), (40, "moderate"),
    (59, "moderate"), (60, "high"), (79, "high"), (80, "critical"), (100, "critical"),
])
def test_risk_bands(score, level):
    assert risk_level(score) == level


def test_no_findings_means_no_assessment():
    assert assess("demo-wallet-T", [], NOW, "simulated") is None


def test_more_findings_never_lower_the_score():
    one = assess("a", [finding("SR-001", 60)], NOW, "simulated")
    two = assess("a", [finding("SR-001", 60), finding("SR-002", 40)], NOW, "simulated")
    assert two.risk_score >= one.risk_score


def test_score_is_capped_at_100():
    big = [finding("SR-001", 100), finding("SR-002", 100), finding("SR-X", 100)]
    result = assess("a", big, NOW, "simulated", RiskConfig(default_weight=1.0))
    assert result.risk_score <= 100


def test_factor_weights_sum_to_100():
    result = assess("a", [finding("SR-001", 70), finding("SR-002", 30)], NOW, "simulated")
    assert sum(f.weight for f in result.factors) == pytest.approx(100, abs=0.2)


def test_weights_are_configurable():
    low = RiskConfig(rule_weights={"SR-001": 0.1})
    high = RiskConfig(rule_weights={"SR-001": 1.0})
    f = [finding("SR-001", 80)]
    assert assess("a", f, NOW, "simulated", low).risk_score < assess("a", f, NOW, "simulated", high).risk_score


def test_origin_is_carried_through():
    assert assess("a", [finding("SR-001", 50)], NOW, "simulated").data_origin == "simulated"
