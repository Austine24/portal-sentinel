"""Core data shapes shared by every layer of Portal Sentinel."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

# Every record says where it came from, so the UI can never show simulated data as live.
DataOrigin = Literal["live", "simulated"]
RiskLevel = Literal["low", "guarded", "moderate", "high", "critical"]


class Transaction(BaseModel):
    tx_hash: str
    sender: str
    recipient: str | None = None
    value: float = Field(ge=0, description="Value in whole native-token units")
    timestamp: AwareDatetime
    success: bool = True
    data_origin: DataOrigin


class RuleFinding(BaseModel):
    rule_id: str
    name: str
    strength: float = Field(ge=0, le=100, description="How far beyond normal, 0-100")
    confidence: float = Field(ge=0, le=1, description="How much history backs this finding")
    summary: str
    evidence: dict[str, float | int | str]
    suggestion: str


class RiskFactor(BaseModel):
    label: str
    detail: str
    weight: float = Field(ge=0, le=100, description="Share of the risk score, percent")


class RiskAssessment(BaseModel):
    account: str
    risk_score: int = Field(ge=0, le=100)
    level: RiskLevel
    factors: list[RiskFactor]
    findings: list[RuleFinding]
    data_origin: DataOrigin
    evaluated_at: AwareDatetime
