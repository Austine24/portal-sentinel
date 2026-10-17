"""Turn transactions into numbers a model can use.

Each account is described hour by hour with four features, and every hour is then
compared with THAT account's own average. A busy account is only unusual if it is
busier than it normally is, so one model can serve very different accounts.
"""
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Sequence

import numpy as np

from app.domain.models import Transaction

FEATURES = ("tx_count", "total_value", "unique_counterparties", "failed_rate")
COUNT_FLOOR = 0.5  # used when a baseline average is near zero, so ratios stay finite


def vector(txs: Sequence[Transaction], hours: float = 1.0) -> np.ndarray:
    """Per-hour feature vector for a group of transactions (zeros when there are none)."""
    if not txs:
        return np.zeros(len(FEATURES))
    failed = sum(1 for t in txs if not t.success)
    peers = {t.recipient for t in txs if t.recipient is not None}
    return np.array([
        len(txs) / hours,
        sum(t.value for t in txs) / hours,
        float(len(peers)),
        failed / len(txs),
    ])


def hourly_grid(txs: Sequence[Transaction], window_start: datetime, hours: int) -> np.ndarray:
    """One row per hour for the `hours` hours before window_start. Quiet hours are rows of zeros."""
    buckets: dict[int, list[Transaction]] = defaultdict(list)
    for t in txs:
        age_hours = (window_start - t.timestamp) / timedelta(hours=1)
        if 0 < age_hours <= hours:
            buckets[math.ceil(age_hours) - 1].append(t)
    return np.vstack([vector(buckets.get(k, [])) for k in range(hours)])


def deviation(x: np.ndarray, baseline_mean: np.ndarray) -> np.ndarray:
    """How far an hour sits from the account's own average.

    Counts, values and counterparties: log2 of the ratio (+1 so zeros are fine), so +1 means double.
    Failure rate: simple difference, since it is already between 0 and 1.
    """
    ratios = np.log2((x[:3] + 1.0) / (baseline_mean[:3] + 1.0))
    return np.append(ratios, x[3] - baseline_mean[3])


def times_baseline(x: np.ndarray, baseline_mean: np.ndarray) -> np.ndarray:
    """Human-readable 'N times the usual' for the three count-like features."""
    return x[:3] / np.maximum(baseline_mean[:3], COUNT_FLOOR)
