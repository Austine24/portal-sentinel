from datetime import datetime, timedelta, timezone

import pytest

from app.domain.network import NetworkSnapshot
from app.security.network_rules import evaluate_network

T0 = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def snap(lag=3, window=60, missed=0, authors=None, age=6.0, minutes_ago=0) -> NetworkSnapshot:
    authors = authors if authors is not None else {"0": 30, "1": 30}
    produced = sum(authors.values())
    return NetworkSnapshot(
        taken_at=T0 - timedelta(minutes=minutes_ago), chain_name="Test", best_block=1000,
        finalized_block=1000 - lag, finality_lag=lag, window_blocks=window, missed_slots=missed,
        authors=authors, distinct_authors=len(authors),
        max_author_share=round(max(authors.values()) / produced, 4) if produced else None,
        block_age_s=age, peers=1,
    )


def ids(findings):
    return [f.rule_id for f in findings]


def test_a_healthy_network_has_no_findings():
    assert evaluate_network(snap(), [snap(minutes_ago=m) for m in (5, 10)]) == []


@pytest.mark.parametrize("lag, fires", [(7, False), (8, True), (30, True)])
def test_finality_lag_threshold(lag, fires):
    assert ("NH-001" in ids(evaluate_network(snap(lag=lag), []))) is fires


def test_finality_lag_strength_runs_from_40_to_100():
    low = evaluate_network(snap(lag=8), [])[0].strength
    high = evaluate_network(snap(lag=60), [])[0].strength
    assert low == 40.0 and high == 100.0


def test_missed_slots_threshold():
    assert "NH-002" not in ids(evaluate_network(snap(window=55, missed=5), []))   # 8%
    assert "NH-002" in ids(evaluate_network(snap(window=50, missed=10), []))      # 17%


def test_stalled_block_production():
    assert "NH-003" not in ids(evaluate_network(snap(age=29.0), []))
    finding = next(f for f in evaluate_network(snap(age=90.0), []) if f.rule_id == "NH-003")
    assert 40 < finding.strength < 100


def test_a_silent_author_is_found_only_with_history_and_enough_blocks():
    history = [snap(minutes_ago=m) for m in (5, 10, 15)]
    now = snap(authors={"0": 60})
    assert "NH-004" in ids(evaluate_network(now, history))
    assert "NH-004" not in ids(evaluate_network(now, []))                          # nothing to compare with
    assert "NH-004" not in ids(evaluate_network(snap(window=10, authors={"0": 10}), history))   # too few blocks


def test_silence_confidence_grows_with_history():
    few = evaluate_network(snap(authors={"0": 60}), [snap(minutes_ago=5)])[-1].confidence
    many = evaluate_network(snap(authors={"0": 60}), [snap(minutes_ago=m) for m in range(1, 30)])[-1].confidence
    assert few < many == 1.0


def test_an_author_that_was_never_active_is_not_silent():
    assert evaluate_network(snap(authors={"0": 60}), [snap(authors={"0": 60}, minutes_ago=5)]) == []
