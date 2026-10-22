"""Checks, against the chain itself, that an incident's evidence really was recorded on-chain.

The browser only tells us a transaction hash. We never trust that: we read the receipt and the
contract, and accept only if the registry emitted the right event for exactly this incident id,
hash and risk score, and the contract still reports the same hash."""
from dataclasses import dataclass
from typing import Protocol

from app.portaldot import registry


class AnchorError(Exception):
    """`retryable` means 'not confirmed yet, try again'; otherwise the transaction does not match."""

    def __init__(self, message: str, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class AnchorProof:
    tx_hash: str
    block_number: int
    contract: str
    recorder: str


class ChainReader(Protocol):
    def receipt(self, tx_hash: str) -> dict | None: ...
    def call(self, to: str, data: str) -> str: ...


def verify_anchor(
    chain: ChainReader, registry_address: str, tx_hash: str,
    incident_id: str, evidence_hash: str, risk_score: int,
) -> AnchorProof:
    receipt = chain.receipt(tx_hash)
    if receipt is None:
        raise AnchorError("Not confirmed yet: the transaction was not found on the node. Wait a few seconds and retry.", True)
    if receipt.get("status") != "0x1":
        raise AnchorError("The transaction failed on-chain (it reverted), so nothing was recorded.", False)
    if (receipt.get("to") or "").lower() != registry_address.lower():
        raise AnchorError("The transaction was not sent to the configured evidence registry.", False)

    event = registry.find_recorded_event(receipt.get("logs", []), registry_address, incident_id, evidence_hash)
    if event is None:
        raise AnchorError("The registry did not record this incident's id and evidence hash in that transaction.", False)
    if event["risk_score"] != risk_score:
        raise AnchorError("The recorded risk score differs from this incident's risk score.", False)

    if not registry.decode_bool(chain.call(registry_address, registry.encode_verify(incident_id, evidence_hash))):
        raise AnchorError("Not confirmed yet: the contract does not report this hash as recorded. Wait and retry.", True)

    return AnchorProof(
        tx_hash=tx_hash.lower(),
        block_number=int(receipt["blockNumber"], 16),
        contract=registry_address.lower(),
        recorder=event["recorder"],
    )
