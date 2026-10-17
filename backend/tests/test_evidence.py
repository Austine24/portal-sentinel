import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from app.evidence.canonical import canonical_bytes, evidence_hash
from app.services import incidents as service
from tests.factories import NOW
from tests.test_incidents import assessment

VECTOR = Path(__file__).parent / "evidence_vector.json"
# Fixed on 2026-10-16. Python, an independent Node implementation and scripts/verify_evidence.py agreed on it.
# If this test fails, the canonical form changed and every previously anchored hash would stop verifying.
VECTOR_HASH = "0x8f8cca3ef142ce593cb2dd64e8f68f52f0cb4572cd7a577b520b85fdce53108c"


def test_known_vector_never_changes():
    assert evidence_hash(json.loads(VECTOR.read_text(encoding="utf-8"))) == VECTOR_HASH


def test_key_order_does_not_matter():
    a = {"x": 1, "y": {"b": 2, "a": 3}}
    b = {"y": {"a": 3, "b": 2}, "x": 1}
    assert canonical_bytes(a) == canonical_bytes(b)
    assert evidence_hash(a) == evidence_hash(b)


def test_floats_are_written_as_fixed_strings():
    assert canonical_bytes({"v": 0.1 + 0.2}) == b'{"v":"0.300000"}'


def test_any_change_changes_the_hash():
    base = {"account": "demo-wallet-A", "score": 90}
    assert evidence_hash(base) != evidence_hash({**base, "score": 91})
    assert evidence_hash(base) != evidence_hash({**base, "account": "demo-wallet-B"})


def _incident(session):
    service.sync_from_assessments(session, [assessment()], NOW)
    return session.get(service.IncidentRow, 1)


def test_prepare_freezes_the_package_and_is_idempotent(session):
    row = _incident(session)
    service.prepare_evidence(session, row, NOW)
    first_hash, first_package = row.evidence_hash, dict(row.evidence_package)
    service.prepare_evidence(session, row, NOW + timedelta(hours=1))
    assert row.evidence_hash == first_hash
    assert row.evidence_package == first_package
    assert sum("Evidence package prepared" in e.text for e in row.events) == 1


def test_hash_survives_later_status_changes(session):
    row = _incident(session)
    service.prepare_evidence(session, row, NOW)
    before = evidence_hash(row.evidence_package)
    service.change_status(session, row, "investigating", "looking", NOW)
    assert evidence_hash(row.evidence_package) == before == row.evidence_hash


def test_package_excludes_mutable_fields(session):
    row = _incident(session)
    service.prepare_evidence(session, row, NOW)
    text = json.dumps(row.evidence_package)
    assert "status" not in text and "events" not in text
    assert row.evidence_package["incident"]["data_origin"] == "simulated"
    assert len(row.evidence_package["nonce"]) == 32


def test_api_prepare_then_verify_roundtrip(client):
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]

    prepared = client.post(f"/api/incidents/{incident_id}/evidence/prepare").json()
    assert prepared["hash"].startswith("0x") and len(prepared["hash"]) == 66

    again = client.post(f"/api/incidents/{incident_id}/evidence/prepare").json()
    assert again == prepared

    assert client.get(f"/api/incidents/{incident_id}/evidence").json() == prepared
    verified = client.post("/api/evidence/verify", json=prepared["package"]).json()
    assert verified["hash"] == prepared["hash"]

    tampered = {**prepared["package"], "assessment": {"risk_score": 1, "level": "low"}}
    assert client.post("/api/evidence/verify", json=tampered).json()["hash"] != prepared["hash"]

    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["evidence"]["prepared"] is True
    assert detail["evidence"]["hash"] == prepared["hash"]


def test_evidence_not_prepared_is_404(client):
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    assert client.get(f"/api/incidents/{incident_id}/evidence").status_code == 404
    assert client.post("/api/incidents/9999/evidence/prepare").status_code == 404


def test_verify_rejects_oversized_packages(client):
    assert client.post("/api/evidence/verify", json={"blob": "x" * 70_000}).status_code == 413


def test_standalone_script_agrees_with_backend():
    script = Path(__file__).resolve().parents[2] / "scripts" / "verify_evidence.py"
    result = subprocess.run(
        [sys.executable, str(script), str(VECTOR), VECTOR_HASH], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MATCH" in result.stdout


VECTOR_INCIDENT_ID = "0x05831adf72f5c868dbac808bcdb93fde3ad0151eb3f528faf863784da9491e13"  # also computed independently in Node on 2026-10-16


def test_onchain_incident_id_known_vector():
    from app.evidence.canonical import onchain_incident_id

    assert onchain_incident_id(json.loads(VECTOR.read_text(encoding="utf-8"))) == VECTOR_INCIDENT_ID


def test_api_exposes_onchain_incident_id(client):
    from app.evidence.canonical import onchain_incident_id

    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    body = client.post(f"/api/incidents/{incident_id}/evidence/prepare").json()
    assert body["onchain_incident_id"] == onchain_incident_id(body["package"])
    assert len(body["onchain_incident_id"]) == 66
