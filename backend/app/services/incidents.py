from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import IncidentRow
from app.domain.incidents import (
    ALLOWED_TRANSITIONS,
    Evidence,
    IncidentEvent,
    IncidentOut,
    SyncResult,
)
from app.domain.models import RiskAssessment, RiskFactor, RuleFinding
from app.repositories import incidents as repo

# Assessments below this score are noise: they are shown nowhere and create no incident.
INCIDENT_MIN_SCORE = 40


class InvalidTransition(Exception):
    pass


def to_out(row: IncidentRow) -> IncidentOut:
    return IncidentOut(
        id=row.id,
        public_id=f"INC-{row.id:05d}",
        title=row.title,
        account=row.account,
        risk_score=row.risk_score,
        level=row.level,
        status=row.status,
        data_origin=row.data_origin,
        summary=row.summary,
        factors=[RiskFactor(**f) for f in row.factors],
        findings=[RuleFinding(**f) for f in row.findings],
        detected_at=row.detected_at,
        updated_at=row.updated_at,
        events=[IncidentEvent(at=e.at, text=e.text) for e in row.events],
        evidence=Evidence(anchored=row.evidence_tx_hash is not None, tx_hash=row.evidence_tx_hash),
        allowed_next=sorted(ALLOWED_TRANSITIONS[row.status]),
    )


def sync_from_assessments(
    session: Session, assessments: list[RiskAssessment], now: datetime
) -> SyncResult:
    created = skipped = 0
    origin = assessments[0].data_origin if assessments else "simulated"

    for a in assessments:
        if a.risk_score < INCIDENT_MIN_SCORE or repo.has_active_incident(session, a.account):
            skipped += 1
            continue

        top = max(a.findings, key=lambda f: f.strength)
        row = IncidentRow(
            dedupe_key=f"{a.account}|{now.strftime('%Y-%m-%dT%H')}",
            title=f"{top.name} on {a.account}",
            account=a.account,
            risk_score=a.risk_score,
            level=a.level,
            status="open",
            data_origin=a.data_origin,
            summary=(
                "Behaviour deviates from this account's own baseline. This is anomalous activity "
                "that requires investigation, not proof of malicious intent."
            ),
            factors=[f.model_dump(mode="json") for f in a.factors],
            findings=[f.model_dump(mode="json") for f in a.findings],
            detected_at=a.evaluated_at,
            updated_at=now,
        )
        rules = ", ".join(f.rule_id for f in a.findings)
        repo.add_event(row, f"Incident created from automated detection ({rules})", now)
        try:
            with session.begin_nested():
                repo.add(session, row)
            created += 1
        except IntegrityError:
            skipped += 1  # the same account was already recorded this hour

    session.commit()
    return SyncResult(created=created, skipped=skipped, data_origin=origin)


def change_status(
    session: Session, row: IncidentRow, new_status: str, note: str | None, now: datetime
) -> IncidentRow:
    if new_status not in ALLOWED_TRANSITIONS[row.status]:
        raise InvalidTransition(f"cannot move from '{row.status}' to '{new_status}'")
    text = f"Status changed from {row.status} to {new_status}"
    if note:
        text += f": {note}"
    repo.add_event(row, text, now)
    row.status = new_status
    row.updated_at = now
    session.commit()
    return row
