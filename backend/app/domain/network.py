from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from app.domain.models import DataOrigin, RiskLevel, RuleFinding


class NetworkSnapshot(BaseModel):
    """What one look at the chain showed. Everything here is read from the node, nothing is simulated."""

    taken_at: AwareDatetime
    chain_name: str | None
    best_block: int
    finalized_block: int
    finality_lag: int = Field(ge=0, description="best minus finalized, in blocks")
    window_blocks: int = Field(ge=0, description="how many recent blocks were examined")
    missed_slots: int = Field(ge=0, description="empty slots between the examined blocks")
    authors: dict[str, int] = Field(description="author index -> blocks produced in the window")
    distinct_authors: int
    max_author_share: float | None
    block_age_s: float | None = Field(description="seconds since the newest block's slot (derived)")
    peers: int | None
    data_origin: Literal["live"] = "live"


class NetworkHealth(BaseModel):
    snapshot: NetworkSnapshot
    findings: list[RuleFinding]
    risk_score: int
    level: RiskLevel
    cached: bool
    note: str


class NetworkHistoryPoint(BaseModel):
    taken_at: AwareDatetime
    best_block: int
    finality_lag: int
    missed_slots: int
    distinct_authors: int
    max_author_share: float | None
    block_age_s: float | None
    data_origin: DataOrigin = "live"
