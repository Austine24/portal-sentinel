from collections import defaultdict
from datetime import datetime, timedelta
from typing import Sequence

from app.domain.models import RuleFinding, Transaction
from app.security.rules.base import Rule, RuleContext


def evaluate_all(
    txs: Sequence[Transaction],
    now: datetime,
    rules: Sequence[Rule],
    window_hours: float = 1.0,
    lookback_hours: float = 168.0,
) -> dict[str, list[RuleFinding]]:
    """Split each sender's transactions into baseline vs recent window, then run every rule."""
    if not txs:
        return {}

    window_start = now - timedelta(hours=window_hours)
    lookback_start = window_start - timedelta(hours=lookback_hours)
    data_start = max(min(t.timestamp for t in txs), lookback_start)
    baseline_hours = max(0.0, (window_start - data_start).total_seconds() / 3600)

    by_account: dict[str, list[Transaction]] = defaultdict(list)
    for t in txs:
        by_account[t.sender].append(t)

    results: dict[str, list[RuleFinding]] = {}
    for account, items in by_account.items():
        window = [t for t in items if window_start <= t.timestamp <= now]
        baseline = [t for t in items if data_start <= t.timestamp < window_start]
        ctx = RuleContext(account, baseline, window, baseline_hours, window_hours)
        findings = [f for rule in rules if (f := rule.evaluate(ctx)) is not None]
        if findings:
            results[account] = findings
    return results
