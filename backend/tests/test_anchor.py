"""Verification of on-chain evidence. Parsing is tested against REAL output from an in-memory EVM
(contracts/fixtures/registry_fixtures.json); the API tests reuse its structure with this incident's values."""
import copy
import json
from pathlib import Path

import pytest

from app.api.routes import incidents as routes
from app.core.config import Settings
from app.evidence.anchor import AnchorError, verify_anchor
from app.main import app
from app.portaldot import registry
from app.portaldot.rpc import RpcUnavailable

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"
FIX = json.loads((CONTRACTS / "fixtures" / "registry_fixtures.json").read_text())
SELECTORS = json.loads((CONTRACTS / "selectors.json").read_text())
REGISTRY = FIX["contract_address"]
TX = FIX["tx_hash"]
INCIDENT, HASH, SCORE = FIX["incident_id"], FIX["evidence_hash"], FIX["risk_score"]


class FakeChain:
    """Replays chain answers. `verify_ok` decides what the contract's verify() reports."""

    def __init__(self, receipt, verify_ok=True):
        self._receipt, self.verify_ok = receipt, verify_ok

    def receipt(self, tx_hash):
        return self._receipt

    def call(self, to, data):
        return FIX["calls"]["verify_true" if self.verify_ok else "verify_wrong_hash"]


# ---- the contract interface matches what the compiler produced -------------------------------

def test_selectors_and_event_topic_match_the_compiled_contract():
    for name, expected in registry.SELECTORS.items():
        assert SELECTORS["functions"][name]["selector"] == expected
    assert SELECTORS["events"]["EvidenceRecorded"]["topic0"] == registry.EVENT_TOPIC


def test_encoding_matches_real_calldata():
    assert registry.encode_verify(INCIDENT, HASH) == FIX["calldata"]["verify"]


def test_decoding_real_contract_answers():
    record = registry.decode_record(FIX["calls"]["get"])
    assert (record.evidence_hash, record.risk_score) == (HASH, SCORE)
    assert record.recorder == FIX["owner"].lower() and record.recorded_at > 1_700_000_000
    assert registry.decode_bool(FIX["calls"]["verify_true"]) is True
    assert registry.decode_bool(FIX["calls"]["verify_wrong_hash"]) is False
    assert registry.decode_bool(FIX["calls"]["verify_unknown"]) is False


def test_malformed_answers_are_refused():
    with pytest.raises(ValueError):
        registry.decode_bool("0x01")
    with pytest.raises(ValueError):
        registry.decode_record("0x" + "00" * 31)
    with pytest.raises(ValueError):
        registry.encode_verify("0x1234", HASH)


def test_event_is_found_in_the_real_receipt():
    event = registry.find_recorded_event(FIX["receipt"]["logs"], REGISTRY, INCIDENT, HASH)
    assert event["risk_score"] == SCORE and event["recorder"] == FIX["owner"].lower()


# ---- verify_anchor ---------------------------------------------------------------------------

def anchor(receipt=FIX["receipt"], registry_address=REGISTRY, incident=INCIDENT, hash_=HASH, score=SCORE, verify_ok=True):
    return verify_anchor(FakeChain(receipt, verify_ok), registry_address, TX, incident, hash_, score)


def test_a_real_successful_record_is_accepted():
    proof = anchor()
    assert proof.block_number == int(FIX["receipt"]["blockNumber"], 16)
    assert proof.contract == REGISTRY.lower() and proof.recorder == FIX["owner"].lower()


@pytest.mark.parametrize("case, kwargs, retryable", [
    ("transaction not found", {"receipt": None}, True),
    ("contract does not report it yet", {"verify_ok": False}, True),
    ("sent to another contract", {"registry_address": "0x" + "ab" * 20}, False),
    ("different incident id", {"incident": "0x" + "22" * 32}, False),
    ("different evidence hash", {"hash_": "0x" + "33" * 32}, False),
    ("different risk score", {"score": SCORE - 1}, False),
])
def test_anything_that_does_not_match_is_rejected(case, kwargs, retryable):
    with pytest.raises(AnchorError) as caught:
        anchor(**kwargs)
    assert caught.value.retryable is retryable, case


def test_a_reverted_transaction_is_rejected():
    reverted = copy.deepcopy(FIX["receipt"])
    reverted["status"] = "0x0"
    with pytest.raises(AnchorError, match="reverted") as caught:
        anchor(receipt=reverted)
    assert caught.value.retryable is False


def test_an_event_from_a_different_contract_is_not_accepted():
    forged = copy.deepcopy(FIX["receipt"])
    forged["logs"][0]["address"] = "0x" + "cd" * 20       # same event, emitted by someone else
    with pytest.raises(AnchorError):
        anchor(receipt=forged)


# ---- API orchestration (receipts synthesised from the real structure) --------------------------

def receipt_for(onchain_id, evidence_hash, score, **changes):
    receipt = copy.deepcopy(FIX["receipt"])
    log = receipt["logs"][0]
    log["topics"][1], log["topics"][2] = onchain_id, evidence_hash
    log["data"] = "0x" + score.to_bytes(32, "big").hex() + log["data"][2 + 64:]
    receipt.update(changes)
    return receipt


@pytest.fixture()
def anchored_setup(client, monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(registry_address=REGISTRY))
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    prepared = client.post(f"/api/incidents/{incident_id}/evidence/prepare").json()
    receipt = receipt_for(prepared["onchain_incident_id"], prepared["hash"], prepared["package"]["assessment"]["risk_score"])
    app.dependency_overrides[routes.get_evm_client] = lambda: FakeChain(receipt)
    return incident_id, receipt


def test_anchoring_records_the_proof_on_the_incident(client, anchored_setup):
    incident_id, _ = anchored_setup
    body = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX}).json()
    assert body["evidence"]["anchored"] is True and body["evidence"]["tx_hash"] == TX.lower()
    assert body["evidence"]["block"] == int(FIX["receipt"]["blockNumber"], 16)
    assert body["evidence"]["contract"] == REGISTRY.lower()
    assert any("anchored on-chain" in e["text"] for e in body["events"])


def test_anchoring_the_same_transaction_twice_is_harmless(client, anchored_setup):
    incident_id, _ = anchored_setup
    first = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX}).json()
    second = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    assert second.status_code == 200 and second.json()["evidence"] == first["evidence"]
    assert sum("anchored on-chain" in e["text"] for e in second.json()["events"]) == 1


def test_a_second_different_transaction_is_refused(client, anchored_setup):
    incident_id, _ = anchored_setup
    client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    other = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": "0x" + "9" * 64})
    assert other.status_code == 409 and "different transaction" in other.json()["detail"]


def test_a_mismatching_transaction_is_422_and_changes_nothing(client, anchored_setup):
    incident_id, receipt = anchored_setup
    app.dependency_overrides[routes.get_evm_client] = lambda: FakeChain(receipt_for("0x" + "44" * 32, "0x" + "55" * 32, 1))
    response = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    assert response.status_code == 422
    assert client.get(f"/api/incidents/{incident_id}").json()["evidence"]["anchored"] is False


def test_not_confirmed_yet_is_a_retryable_409(client, anchored_setup):
    incident_id, _ = anchored_setup
    app.dependency_overrides[routes.get_evm_client] = lambda: FakeChain(None)
    response = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    assert response.status_code == 409 and "Not confirmed yet" in response.json()["detail"]


def test_evidence_must_be_prepared_first(client, monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(registry_address=REGISTRY))
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    app.dependency_overrides[routes.get_evm_client] = lambda: FakeChain(FIX["receipt"])
    response = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    assert response.status_code == 409 and "Prepare" in response.json()["detail"]


def test_no_registry_configured_is_a_clear_503(client, monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(registry_address=""))
    response = client.post("/api/incidents/1/evidence/anchor", json={"tx_hash": TX})
    assert response.status_code == 503 and "REGISTRY_ADDRESS" in response.json()["detail"]


def test_bad_transaction_hash_format_is_422(client, monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(registry_address=REGISTRY))
    assert client.post("/api/incidents/1/evidence/anchor", json={"tx_hash": "0x1234"}).status_code == 422


def test_unknown_incident_is_404(client, monkeypatch):
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(registry_address=REGISTRY))
    app.dependency_overrides[routes.get_evm_client] = lambda: FakeChain(FIX["receipt"])
    assert client.post("/api/incidents/9999/evidence/anchor", json={"tx_hash": TX}).status_code == 404


def test_an_unreachable_node_is_a_clean_503(client, anchored_setup):
    incident_id, _ = anchored_setup

    class Down:
        def receipt(self, tx_hash):
            raise RpcUnavailable("HTTP 403")

        def call(self, to, data):
            raise RpcUnavailable("HTTP 403")

    app.dependency_overrides[routes.get_evm_client] = lambda: Down()
    response = client.post(f"/api/incidents/{incident_id}/evidence/anchor", json={"tx_hash": TX})
    assert response.status_code == 503 and "could not be reached" in response.json()["detail"]


def test_a_malformed_registry_address_is_refused_at_startup():
    with pytest.raises(ValueError):
        Settings(registry_address="0x1234")


def test_chain_config_reports_not_deployed_until_configured(client, monkeypatch):
    from app.api.routes import chain
    monkeypatch.setattr(chain, "get_settings", lambda: Settings(registry_address=""))
    body = client.get("/api/chain/config").json()
    assert body["registry_address"] is None and body["chain_id"] == 420420777 and body["native_symbol"] == "tPOT"
    monkeypatch.setattr(chain, "get_settings", lambda: Settings(registry_address=REGISTRY))
    assert client.get("/api/chain/config").json()["registry_address"] == REGISTRY
    assert client.get("/api/chain/config").json()["record_selector"] == registry.SELECTORS["record"]


def test_the_transaction_itself_must_target_the_registry():
    # Same genuine event, but the transaction was addressed to some other contract (for example a wrapper).
    # Only the destination differs, so this exercises that check on its own.
    wrapped = copy.deepcopy(FIX["receipt"])
    wrapped["to"] = "0x" + "ef" * 20
    with pytest.raises(AnchorError, match="not sent to the configured"):
        anchor(receipt=wrapped)
