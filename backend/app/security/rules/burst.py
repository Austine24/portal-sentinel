from app.domain.models import RuleFinding
from app.security.rules.base import RuleContext, strength_from_ratio


class TransactionBurstRule:
    """SR-001: transaction frequency far above the account's own baseline."""

    rule_id = "SR-001"
    name = "Transaction Burst"

    def __init__(
        self,
        min_window_count: int = 20,         # ignore tiny activity, whatever the ratio
        min_ratio: float = 5.0,             # how many times above baseline counts as a burst
        rate_floor_per_hour: float = 0.5,   # stops divide-by-zero for brand-new accounts
        full_confidence_hours: float = 24.0,
    ):
        self.min_window_count = min_window_count
        self.min_ratio = min_ratio
        self.rate_floor = rate_floor_per_hour
        self.full_confidence_hours = full_confidence_hours

    def evaluate(self, ctx: RuleContext) -> RuleFinding | None:
        count = len(ctx.window)
        if count < self.min_window_count or ctx.window_hours <= 0:
            return None

        current_rate = count / ctx.window_hours
        baseline_rate = (
            len(ctx.baseline) / ctx.baseline_hours if ctx.baseline_hours > 0 else 0.0
        )
        reference = max(baseline_rate, self.rate_floor)
        ratio = current_rate / reference
        if ratio < self.min_ratio:
            return None

        confidence = min(1.0, ctx.baseline_hours / self.full_confidence_hours)
        return RuleFinding(
            rule_id=self.rule_id,
            name=self.name,
            strength=round(strength_from_ratio(ratio), 1),
            confidence=round(confidence, 2),
            summary=(
                f"Transaction frequency is {ratio:.1f}x above this account's baseline "
                f"({current_rate:.1f}/hour now vs {reference:.1f}/hour usual)"
            ),
            evidence={
                "window_transactions": count,
                "current_rate_per_hour": round(current_rate, 2),
                "baseline_rate_per_hour": round(reference, 2),
                "ratio": round(ratio, 2),
                "baseline_hours": round(ctx.baseline_hours, 1),
            },
            suggestion=(
                "Review the account's recent counterparties and compare with its earlier activity. "
                "A burst can be legitimate (batch payments, airdrop claims)."
            ),
        )
