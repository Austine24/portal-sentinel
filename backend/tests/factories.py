from datetime import datetime, timedelta, timezone

from app.domain.models import Transaction
from app.security.rules.base import RuleContext

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


def tx(minutes_ago: float, value: float = 10.0, sender: str = "demo-wallet-T", n: int = 0) -> Transaction:
    return Transaction(
        tx_hash=f"demo-tx-t{n}-{minutes_ago}",
        sender=sender,
        recipient="demo-peer",
        value=value,
        timestamp=NOW - timedelta(minutes=minutes_ago),
        data_origin="simulated",
    )


def context(baseline_count: int, window_count: int, baseline_hours: float = 48.0,
            baseline_value: float = 10.0, window_value: float = 10.0) -> RuleContext:
    # spread baseline txs over the earlier period, window txs over the last hour
    baseline = [tx(60 + (i + 1) * (baseline_hours * 60 / max(baseline_count, 1)) % (baseline_hours * 60),
                   baseline_value + (i % 5), n=i) for i in range(baseline_count)]
    window = [tx(1 + (i % 58), window_value, n=1000 + i) for i in range(window_count)]
    return RuleContext("demo-wallet-T", baseline, window, baseline_hours, 1.0)
