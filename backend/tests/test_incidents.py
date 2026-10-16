from datetime import timedelta

import pytest

from app.domain.models import RiskAssessment, RiskFactor, RuleFinding
from app.services import incidents as service
from tests.factories import NOW


def assessment(account="demo-wallet-A", score=78) -> RiskAssessment:
    finding = RuleFinding(rule_id="SR-001", name="Transaction Burst", strength=80, confidence=1.0,
                          summary="12.4x above baseline", evidence={"ratio": 12.4}, suggestion="review")
    return RiskAssessment(account=account, risk_score=score, level="high",
                          factors=[RiskFactor(label="Transaction Burst", detail="12.4x", weight=100)],
                          findings=[finding], data_origin="simulated", evaluated_at=NOW)


def test_sync_creates_one_incident_with_timeline(session):
    result = service.sync_from_assessments(session, [assessment()], NOW)
    assert (result.created, result.skipped) == (1, 0)
    row = session.get(service.IncidentRow, 1)
    assert row.status == "open" and row.data_origin == "simulated"
    assert "SR-001" in row.events[0].text


def test_sync_twice_does_not_duplicate(session):
    service.sync_from_assessments(session, [assessment()], NOW)
    result = service.sync_from_assessments(session, [assessment()], NOW + timedelta(minutes=5))
    assert (result.created, result.skipped) == (0, 1)


def test_low_scores_create_no_incident(session):
    result = service.sync_from_assessments(session, [assessment(score=25)], NOW)
    assert (result.created, result.skipped) == (0, 1)


def test_valid_transition_records_an_event(session):
    service.sync_from_assessments(session, [assessment()], NOW)
    row = session.get(service.IncidentRow, 1)
    service.change_status(session, row, "investigating", "taking this one", NOW)
    assert row.status == "investigating"
    assert "taking this one" in row.events[-1].text


def test_invalid_transition_is_refused_and_changes_nothing(session):
    service.sync_from_assessments(session, [assessment()], NOW)
    row = session.get(service.IncidentRow, 1)
    with pytest.raises(service.InvalidTransition):
        service.change_status(session, row, "resolved", None, NOW)
    assert row.status == "open"
