from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, Field

from app.domain.models import DataOrigin, RiskFactor, RiskLevel, RuleFinding

IncidentStatus = Literal["open", "investigating", "confirmed", "resolved", "false_positive"]

# Which status may follow which. The server is the authority; the UI only mirrors this.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"investigating", "false_positive"},
    "investigating": {"confirmed", "false_positive", "open"},
    "confirmed": {"resolved", "investigating"},
    "resolved": {"investigating"},
    "false_positive": {"open"},
}


class IncidentEvent(BaseModel):
    at: AwareDatetime
    text: str


class Evidence(BaseModel):
    prepared: bool
    hash: str | None = None
    anchored: bool
    tx_hash: str | None = None


class EvidencePackage(BaseModel):
    hash: str
    package: dict[str, Any]


class VerifyResult(BaseModel):
    hash: str


class IncidentOut(BaseModel):
    id: int
    public_id: str
    title: str
    account: str
    risk_score: int
    level: RiskLevel
    status: IncidentStatus
    data_origin: DataOrigin
    summary: str
    factors: list[RiskFactor]
    findings: list[RuleFinding]
    detected_at: AwareDatetime
    updated_at: AwareDatetime
    events: list[IncidentEvent]
    evidence: Evidence
    allowed_next: list[IncidentStatus]


class StatusChange(BaseModel):
    status: IncidentStatus
    note: str | None = Field(default=None, max_length=300)


class SyncResult(BaseModel):
    created: int
    skipped: int
    data_origin: DataOrigin
