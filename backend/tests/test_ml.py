from datetime import timedelta

import numpy as np
import pytest

from app.data.simulated import BURST_ACCOUNT, SimulatedSource
from app.domain.models import Transaction
from app.ml.anomaly import IsolationForestDetector
from app.ml.features import deviation, hourly_grid, vector
from app.services.detection import run_detection
from tests.factories import NOW, tx


def simulated(seed=42):
    return SimulatedSource(NOW, seed=seed).fetch_transactions(NOW - timedelta(days=8), NOW)


# ---- features -------------------------------------------------------------

def test_quiet_hours_are_counted_as_zero_rows():
    window_start = NOW
    # one transaction 30 minutes before the window start, none in the other 3 hours
    grid = hourly_grid([tx(minutes_ago=30, value=5)], window_start, hours=4)
    assert grid.shape == (4, 4)
    assert grid[0, 0] == 1 and grid[0, 1] == 5          # the most recent hour holds it
    assert not grid[1:].any()                            # quiet hours stay zero


def test_vector_of_nothing_is_zeros():
    assert not vector([]).any()


def test_vector_counts_failures_and_peers():
    txs = [tx(5, 10, n=1), tx(6, 20, n=2).model_copy(update={"success": False, "recipient": "other"})]
    v = vector(txs)
    assert v[0] == 2 and v[1] == 30 and v[2] == 2 and v[3] == 0.5


def test_deviation_is_zero_at_baseline_and_positive_above():
    mean = np.array([2.0, 20.0, 2.0, 0.05])
    assert np.allclose(deviation(mean, mean), 0)
    assert deviation(np.array([20.0, 200.0, 20.0, 0.05]), mean)[0] > 2


# ---- detector -------------------------------------------------------------

def test_injected_burst_is_flagged_with_an_explanation():
    findings, status = IsolationForestDetector().fit_and_score(simulated(), NOW)
    assert status.trained and status.training_rows > 1000
    finding = findings[BURST_ACCOUNT]
    assert finding.rule_id == "ML-001"
    assert finding.evidence["anomaly_percentile"] >= 0.99
    assert finding.evidence["tx_count_vs_baseline"] > 10
    assert "baseline" in finding.summary
    assert 60 <= finding.strength <= 100


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_normal_accounts_are_not_flagged(seed):
    findings, _ = IsolationForestDetector().fit_and_score(simulated(seed), NOW)
    assert set(findings) <= {BURST_ACCOUNT}


def test_stays_silent_with_too_little_history():
    recent = [t for t in simulated() if t.timestamp > NOW - timedelta(hours=6)]
    findings, status = IsolationForestDetector().fit_and_score(recent, NOW)
    assert findings == {} and status.trained is False
    assert "history" in status.reason


def test_no_transactions_means_untrained():
    findings, status = IsolationForestDetector().fit_and_score([], NOW)
    assert findings == {} and status.trained is False


def test_results_are_deterministic():
    a, _ = IsolationForestDetector().fit_and_score(simulated(), NOW)
    b, _ = IsolationForestDetector().fit_and_score(simulated(), NOW)
    assert a[BURST_ACCOUNT].model_dump() == b[BURST_ACCOUNT].model_dump()


def test_near_silent_accounts_are_ignored():
    # five transactions needed; a lone transaction from a normally quiet account must not trigger
    txs = simulated()
    txs += [Transaction(tx_hash="demo-tx-x", sender="demo-wallet-Z", recipient="p", value=900.0,
                        timestamp=NOW - timedelta(minutes=5), data_origin="simulated")]
    findings, _ = IsolationForestDetector().fit_and_score(txs, NOW)
    assert "demo-wallet-Z" not in findings


# ---- integration ----------------------------------------------------------

def test_detection_combines_rules_and_model():
    assessments = run_detection(SimulatedSource(NOW), NOW)
    top = assessments[0]
    assert top.account == BURST_ACCOUNT
    assert {"SR-001", "SR-002", "ML-001"} <= {f.rule_id for f in top.findings}
    assert sum(f.weight for f in top.factors) == pytest.approx(100, abs=0.3)
    assert top.risk_score <= 100


def test_model_status_endpoint(client):
    body = client.get("/api/model/status").json()
    assert body["trained"] is True and body["training_rows"] > 1000
    assert body["data_origin"] == "simulated"
    assert body["features"] == ["tx_count", "total_value", "unique_counterparties", "failed_rate"]
    assert {r["rule_id"] for r in body["rules"]} == {"SR-001", "SR-002"}
    assert "not proof" in body["note"]


def test_incident_evidence_includes_model_finding_and_hashes(client):
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    prepared = client.post(f"/api/incidents/{incident_id}/evidence/prepare").json()
    rule_ids = {f["rule_id"] for f in prepared["package"]["findings"]}
    assert "ML-001" in rule_ids
    verified = client.post("/api/evidence/verify", json=prepared["package"]).json()
    assert verified["hash"] == prepared["hash"]


def test_percentile_threshold_is_actually_used():
    # The percentile can never exceed 1.0, so an unreachable threshold must suppress even the obvious burst.
    findings, status = IsolationForestDetector(trigger_percentile=1.0001).fit_and_score(simulated(), NOW)
    assert status.trained and findings == {}


def test_guards_alone_do_not_flag_without_the_model_agreeing():
    # With the guards removed but an unreachable percentile, still nothing is reported.
    detector = IsolationForestDetector(trigger_percentile=1.0001, min_window_txs=0, min_jump_log2=-99.0)
    findings, _ = detector.fit_and_score(simulated(), NOW)
    assert findings == {}
