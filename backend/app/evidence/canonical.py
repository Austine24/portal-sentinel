"""Canonical form and hash of an evidence package.

Anyone must be able to recompute the same hash from the same package, in any language.
So the rules are fixed and simple:
  - floats become strings with 6 decimals (languages print floats differently)
  - object keys are sorted, no whitespace, UTF-8
  - hash = SHA-256 of those bytes, shown as 0x + 64 hex characters
"""
import hashlib
import json
from typing import Any

SCHEMA = "portal-sentinel/evidence/v1"
MAX_DEPTH = 8


def normalize(value: Any, _depth: int = 0) -> Any:
    if _depth > MAX_DEPTH:
        raise ValueError("evidence package is nested too deeply")
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, dict):
        return {str(k): normalize(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(v, _depth + 1) for v in value]
    raise TypeError(f"unsupported value in evidence package: {type(value).__name__}")


def canonical_bytes(package: dict[str, Any]) -> bytes:
    return json.dumps(
        normalize(package), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def evidence_hash(package: dict[str, Any]) -> str:
    return "0x" + hashlib.sha256(canonical_bytes(package)).hexdigest()
