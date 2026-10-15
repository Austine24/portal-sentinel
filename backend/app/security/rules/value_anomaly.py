import statistics

from app.domain.models import RuleFinding
from app.security.rules.base import RuleContext, strength_from_ratio


class ValueAnomalyRule:
    """SR-002: a transaction value far above the account's normal range."""

    rule_id = "SR-002"
    name = "Value Anomaly"

    def __init__(
        self,
        multiplier: float = 3.0,            # peak must exceed baseline p95 by this factor
        min_baseline_txs: int = 10,         # too little history = no opinion
        full_confidence_txs: int = 50,
    ):
        self.multiplier = multiplier
        self.min_baseline_txs = min_baseline_txs
        self.full_confidence_txs = full_confidence_txs

    def evaluate(self, ctx: RuleContext) -> RuleFinding | None:
        if len(ctx.baseline) < self.min_baseline_txs or not ctx.window:
            return None

        base_values = [t.value for t in ctx.baseline]
        p95 = statistics.quantiles(base_values, n=20)[18]
        peak = max(t.value for t in ctx.window)
        reference = max(p95, 1e-9)
        ratio = peak / reference
        if ratio < self.multiplier:
            return None

        confidence = min(1.0, len(ctx.baseline) / self.full_confidence_txs)
        return RuleFinding(
            rule_id=self.rule_id,
            name=self.name,
            strength=round(strength_from_ratio(ratio), 1),
            confidence=round(confidence, 2),
            summary=(
                f"Largest recent transaction is {ratio:.1f}x above this account's usual upper range "
                f"({peak:.2f} vs {reference:.2f})"
            ),
            evidence={
                "peak_value": round(peak, 4),
                "baseline_p95": round(reference, 4),
                "ratio": round(ratio, 2),
                "baseline_transactions": len(ctx.baseline),
            },
            suggestion="Check the recipient and purpose of the largest transfer in the window.",
        )
