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
from app.evidence.anchor import AnchorError, ChainReader, verify_anchor
from app.evidence.canonical import evidence_hash, onchain_incident_id
from app.evidence.package import build_package, new_nonce
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
        evidence=Evidence(
            prepared=row.evidence_package is not None,
            hash=row.evidence_hash,
            anchored=row.evidence_tx_hash is not None,
            tx_hash=row.evidence_tx_hash,
            block=row.evidence_block,
            contract=row.evidence_contract,
        ),
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


def prepare_evidence(session: Session, row: IncidentRow, now: datetime) -> IncidentRow:
    """Freeze the evidence package once. Calling again changes nothing (idempotent)."""
    if row.evidence_package is not None:
        return row
    package = build_package(row, new_nonce())
    row.evidence_package = package
    row.evidence_hash = evidence_hash(package)
    row.evidence_prepared_at = now
    repo.add_event(row, f"Evidence package prepared (hash {row.evidence_hash[:10]}...{row.evidence_hash[-6:]})", now)
    row.updated_at = now
    session.commit()
    return row


class AnchorConflict(Exception):
    pass


def anchor_evidence(
    session: Session, row: IncidentRow, tx_hash: str, chain: ChainReader, registry_address: str, now: datetime
) -> IncidentRow:
    """Records on the incident that its evidence is on-chain, but only after verifying it on-chain."""
    if row.evidence_package is None:
        raise AnchorConflict("Prepare the evidence package first.")
    if row.evidence_tx_hash is not None:
        if row.evidence_tx_hash == tx_hash.lower():
            return row                                     # same transaction again: nothing to do
        raise AnchorConflict("This incident's evidence is already anchored by a different transaction.")

    package = row.evidence_package
    proof = verify_anchor(                                 # raises AnchorError when it does not check out
        chain, registry_address, tx_hash,
        onchain_incident_id(package), row.evidence_hash, int(package["assessment"]["risk_score"]),
    )
    row.evidence_tx_hash = proof.tx_hash
    row.evidence_block = proof.block_number
    row.evidence_contract = proof.contract
    row.evidence_anchored_at = now
    row.updated_at = now
    repo.add_event(row, f"Evidence anchored on-chain in block {proof.block_number} (tx {proof.tx_hash[:10]}...{proof.tx_hash[-6:]})", now)
    session.commit()
    return row
