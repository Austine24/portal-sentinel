"""Talking to the SentinelEvidenceRegistry contract with plain ABI encoding (no web3 library needed:
every argument and result is a fixed 32-byte word). The ids below come from contracts/selectors.json,
and a test checks they still match."""
import re
from dataclasses import dataclass

SELECTORS = {
    "record": "0x47fb744f",
    "get": "0x8eaa6ac0",
    "verify": "0x4e8fee00",
    "owner": "0x8da5cb5b",
    "totalRecords": "0x125f8974",
}
EVENT_TOPIC = "0xb8629543d5bf0820b21378b385beb3ec97d553c727394b49351457f490e076a5"  # EvidenceRecorded

_BYTES32 = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class RegistryRecord:
    evidence_hash: str
    risk_score: int
    recorded_at: int
    recorder: str


def _word(value: str) -> str:
    if not _BYTES32.match(value):
        raise ValueError("expected a 32-byte hex value")
    return value[2:].lower()


def encode_verify(incident_id: str, evidence_hash: str) -> str:
    return SELECTORS["verify"] + _word(incident_id) + _word(evidence_hash)


def decode_bool(result: str) -> bool:
    data = bytes.fromhex(result[2:])
    if len(data) != 32:
        raise ValueError("unexpected answer length")
    return int.from_bytes(data, "big") == 1


def decode_record(result: str) -> RegistryRecord:
    data = bytes.fromhex(result[2:])
    if len(data) != 128:
        raise ValueError("unexpected answer length")
    return RegistryRecord(
        evidence_hash="0x" + data[0:32].hex(),
        risk_score=int.from_bytes(data[32:64], "big"),
        recorded_at=int.from_bytes(data[64:96], "big"),
        recorder="0x" + data[108:128].hex(),
    )


def find_recorded_event(logs: list[dict], registry: str, incident_id: str, evidence_hash: str) -> dict | None:
    """The EvidenceRecorded log emitted BY THE REGISTRY for exactly this incident id and hash."""
    for log in logs:
        topics = [t.lower() for t in log.get("topics", [])]
        if (
            log.get("address", "").lower() == registry.lower()
            and len(topics) == 4
            and topics[0] == EVENT_TOPIC
            and topics[1] == incident_id.lower()
            and topics[2] == evidence_hash.lower()
        ):
            data = bytes.fromhex(log["data"][2:])
            return {
                "risk_score": int.from_bytes(data[0:32], "big"),
                "recorded_at": int.from_bytes(data[32:64], "big"),
                "recorder": "0x" + topics[3][-40:],
            }
    return None
