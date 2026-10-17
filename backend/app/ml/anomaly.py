"""Isolation Forest anomaly signal (rule id ML-001).

How it works, in plain terms:
  1. For every account, describe each past hour with four features and measure how far it sat
     from that account's own average. This gives thousands of examples of "normal wiggle".
  2. An Isolation Forest learns which wiggles are common. Unusual points get isolated in
     fewer random splits, which gives them a higher anomaly score.
  3. The current hour is scored the same way, and the score is turned into a PERCENTILE:
     "more unusual than 99.6% of the past account-hours the model learned from" (each of those
     hours measured against its own account's normal). Percentiles are easy to explain.
  4. A finding is reported only if the percentile is very high, the account was actually active,
     and at least one feature really did jump. The model finds candidates; the numbers explain them.

The model is retrained on every run from the last week of data. Nothing is stored, and it is
deterministic (fixed random seed). An anomaly is not proof of malicious behaviour.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

from app.domain.models import RuleFinding, Transaction
from app.ml.features import FEATURES, deviation, hourly_grid, times_baseline, vector

STRENGTH_AT_TRIGGER = 60.0  # a finding that just clears the bar scores 60, the maximum 100
RULE_ID = "ML-001"
RULE_NAME = "Anomaly Model (Isolation Forest)"


@dataclass(frozen=True)
class ModelStatus:
    trained: bool
    reason: str | None
    training_rows: int
    accounts: int
    features: tuple[str, ...]
    trained_at: datetime | None


class IsolationForestDetector:
    rule_id = RULE_ID
    name = RULE_NAME

    def __init__(
        self,
        min_baseline_hours: int = 24,    # less history than this and the model stays silent
        min_training_rows: int = 200,
        min_window_txs: int = 5,         # ignore near-silent accounts
        trigger_percentile: float = 0.99,
        min_jump_log2: float = 1.0,      # at least one feature must be 2x its usual level
        min_failed_rate_jump: float = 0.2,
        full_confidence_rows: int = 500,
        n_estimators: int = 200,
        random_state: int = 42,
    ):
        self.min_baseline_hours = min_baseline_hours
        self.min_training_rows = min_training_rows
        self.min_window_txs = min_window_txs
        self.trigger_percentile = trigger_percentile
        self.min_jump_log2 = min_jump_log2
        self.min_failed_rate_jump = min_failed_rate_jump
        self.full_confidence_rows = full_confidence_rows
        self.n_estimators = n_estimators
        self.random_state = random_state

    def _untrained(self, reason: str) -> tuple[dict[str, RuleFinding], ModelStatus]:
        return {}, ModelStatus(False, reason, 0, 0, FEATURES, None)

    def fit_and_score(
        self,
        txs: Sequence[Transaction],
        now: datetime,
        window_hours: float = 1.0,
        lookback_hours: float = 168.0,
    ) -> tuple[dict[str, RuleFinding], ModelStatus]:
        if not txs:
            return self._untrained("no transactions")

        window_start = now - timedelta(hours=window_hours)
        data_start = max(min(t.timestamp for t in txs), window_start - timedelta(hours=lookback_hours))
        baseline_hours = int((window_start - data_start) / timedelta(hours=1))
        if baseline_hours < self.min_baseline_hours:
            return self._untrained(f"only {baseline_hours} hours of history (need {self.min_baseline_hours})")

        by_account: dict[str, list[Transaction]] = {}
        for t in txs:
            by_account.setdefault(t.sender, []).append(t)

        # 1. build each account's baseline and its training examples
        baselines: dict[str, np.ndarray] = {}
        rows: list[np.ndarray] = []
        for account, items in by_account.items():
            grid = hourly_grid(items, window_start, baseline_hours)
            if not grid[:, 0].any():          # no baseline activity at all: nothing to compare with
                continue
            mean = grid.mean(axis=0)
            baselines[account] = mean
            rows.extend(deviation(row, mean) for row in grid)

        if len(rows) < self.min_training_rows:
            return self._untrained(f"only {len(rows)} training examples (need {self.min_training_rows})")

        # 2. train
        matrix = np.vstack(rows)
        model = IsolationForest(
            n_estimators=self.n_estimators, contamination="auto", random_state=self.random_state
        ).fit(matrix)
        train_scores = np.sort(-model.score_samples(matrix))   # higher = more unusual

        # 3. score each account's current window
        findings: dict[str, RuleFinding] = {}
        for account, mean in baselines.items():
            window = [t for t in by_account[account] if window_start <= t.timestamp <= now]
            if len(window) < self.min_window_txs:
                continue
            x = vector(window, window_hours)
            d = deviation(x, mean)
            score = float(-model.score_samples(d.reshape(1, -1))[0])
            percentile = float(np.searchsorted(train_scores, score, side="right") / len(train_scores))

            jumped = d[:3].max() >= self.min_jump_log2 or d[3] >= self.min_failed_rate_jump
            if percentile < self.trigger_percentile or not jumped:
                continue
            findings[account] = self._finding(percentile, x, mean, len(rows), baseline_hours, len(window))

        status = ModelStatus(True, None, len(rows), len(baselines), FEATURES, datetime.now(timezone.utc))
        return findings, status

    def _finding(self, percentile, x, mean, rows, baseline_hours, window_txs) -> RuleFinding:
        ratios = times_baseline(x, mean)
        span = max(1e-9, 1.0 - self.trigger_percentile)
        strength = STRENGTH_AT_TRIGGER + (100 - STRENGTH_AT_TRIGGER) * min(1.0, (percentile - self.trigger_percentile) / span)

        jumps = sorted(
            ((FEATURES[i], float(ratios[i])) for i in range(3) if ratios[i] >= 2.0),
            key=lambda pair: pair[1], reverse=True,
        )[:3]
        share = "all" if percentile >= 0.9995 else f"{percentile * 100:.1f}%"
        shifts = ", ".join(f"{name} {ratio:.1f}x baseline" for name, ratio in jumps) or "failure rate rose"
        return RuleFinding(
            rule_id=RULE_ID,
            name=RULE_NAME,
            strength=round(strength, 1),
            confidence=round(min(1.0, rows / self.full_confidence_rows), 2),
            summary=(
                f"The model rates this hour as more unusual than {share} of the {rows} past account-hours "
                f"it learned from (each compared with its own account's normal). Largest shifts: {shifts}"
            ),
            evidence={
                "anomaly_percentile": round(percentile, 4),
                "training_rows": rows,
                "baseline_hours": baseline_hours,
                "window_transactions": window_txs,
                "tx_count_vs_baseline": round(float(ratios[0]), 2),
                "total_value_vs_baseline": round(float(ratios[1]), 2),
                "unique_counterparties_vs_baseline": round(float(ratios[2]), 2),
                "failed_rate_baseline": round(float(mean[3]), 3),
                "failed_rate_now": round(float(x[3]), 3),
            },
            suggestion=(
                "Compare the shifted features with the account's usual pattern. The model flags unusual "
                "behaviour only; confirm with the rule evidence and the transactions themselves."
            ),
        )
