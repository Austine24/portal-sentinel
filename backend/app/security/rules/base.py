import math
from dataclasses import dataclass
from typing import Protocol, Sequence

from app.domain.models import RuleFinding, Transaction

# A finding's strength rises by this many points each time the observed value doubles
# relative to the account's own normal. 20 means 5x normal ~ 46, 12x ~ 72, 32x = 100.
STRENGTH_PER_DOUBLING = 20.0


@dataclass(frozen=True)
class RuleContext:
    account: str
    baseline: Sequence[Transaction]   # this account's earlier behaviour
    window: Sequence[Transaction]     # the recent period under inspection
    baseline_hours: float             # how much history the baseline covers
    window_hours: float


class Rule(Protocol):
    rule_id: str
    name: str

    def evaluate(self, ctx: RuleContext) -> RuleFinding | None: ...


def strength_from_ratio(ratio: float) -> float:
    if ratio <= 1:
        return 0.0
    return max(0.0, min(100.0, STRENGTH_PER_DOUBLING * math.log2(ratio)))
