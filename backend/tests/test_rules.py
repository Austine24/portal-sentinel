from app.security.rules.burst import TransactionBurstRule
from app.security.rules.value_anomaly import ValueAnomalyRule
from tests.factories import context


def test_burst_fires_when_rate_far_above_baseline():
    # baseline ~1 tx/hour for 48h, then 40 txs in the last hour
    finding = TransactionBurstRule().evaluate(context(baseline_count=48, window_count=40))
    assert finding is not None
    assert finding.rule_id == "SR-001"
    assert finding.evidence["ratio"] >= 5
    assert 0 < finding.strength <= 100
    assert "above this account's baseline" in finding.summary


def test_burst_ignores_normal_activity():
    assert TransactionBurstRule().evaluate(context(baseline_count=48, window_count=2)) is None


def test_burst_ignores_small_counts_even_with_high_ratio():
    # 10 txs is below min_window_count (20)
    assert TransactionBurstRule().evaluate(context(baseline_count=0, window_count=10)) is None


def test_burst_has_low_confidence_with_little_history():
    finding = TransactionBurstRule().evaluate(
        context(baseline_count=0, window_count=30, baseline_hours=2.0)
    )
    assert finding is not None
    assert finding.confidence < 0.5


def test_value_anomaly_fires_on_large_transfer():
    ctx = context(baseline_count=40, window_count=3, baseline_value=10, window_value=200)
    finding = ValueAnomalyRule().evaluate(ctx)
    assert finding is not None
    assert finding.rule_id == "SR-002"
    assert finding.evidence["ratio"] >= 3


def test_value_anomaly_ignores_normal_values():
    ctx = context(baseline_count=40, window_count=3, baseline_value=10, window_value=11)
    assert ValueAnomalyRule().evaluate(ctx) is None


def test_value_anomaly_has_no_opinion_without_baseline():
    ctx = context(baseline_count=3, window_count=3, window_value=500)
    assert ValueAnomalyRule().evaluate(ctx) is None
