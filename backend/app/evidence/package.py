import secrets
from datetime import datetime, timezone
from typing import Any

from app.db.models import IncidentRow
from app.evidence.canonical import SCHEMA, normalize


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_nonce() -> str:
    # Random value inside the package, so the hash cannot be guessed from the other fields.
    return secrets.token_hex(16)


def build_package(row: IncidentRow, nonce: str) -> dict[str, Any]:
    """Only facts that never change after detection. Status and timeline are excluded on purpose."""
    return normalize({
        "schema": SCHEMA,
        "incident": {
            "id": row.id,
            "public_id": f"INC-{row.id:05d}",
            "account": row.account,
            "detected_at": _iso(row.detected_at),
            "data_origin": row.data_origin,
        },
        "assessment": {"risk_score": row.risk_score, "level": row.level},
        "findings": [
            {
                "rule_id": f["rule_id"],
                "name": f["name"],
                "strength": f["strength"],
                "confidence": f["confidence"],
                "evidence": f["evidence"],
            }
            for f in row.findings
        ],
        "nonce": nonce,
    })
