"""Network-health rules. They watch the chain itself, not accounts.

Thresholds are starting points chosen from what the Portaldot testnet shows when healthy
(finality lag 2 to 3 blocks, no missed slots, blocks every 6 s). They are not tuned on incidents.
"""
from typing import Sequence

from app.domain.models import RuleFinding
from app.domain.network import NetworkSnapshot

# NH-001 finality lag, in blocks
LAG_WARN, LAG_CRITICAL = 8, 30
# NH-002 share of slots that produced no block
MISSED_WARN, MISSED_CRITICAL = 0.10, 0.50
# NH-003 seconds since the newest block (a slot is 6 s)
AGE_WARN, AGE_CRITICAL = 30.0, 150.0
# NH-004 an author needs this many examined blocks before silence means anything
MIN_WINDOW_FOR_SILENCE = 30
FULL_CONFIDENCE_HISTORY = 20
STRENGTH_AT_WARN = 40.0   # a finding that just passes its warning level scores 40, the critical level 100


def _strength(value: float, warn: float, critical: float) -> float:
    span = max(1e-9, critical - warn)
    return round(STRENGTH_AT_WARN + (100 - STRENGTH_AT_WARN) * min(1.0, max(0.0, (value - warn) / span)), 1)


def evaluate_network(current: NetworkSnapshot, history: Sequence[NetworkSnapshot]) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if current.finality_lag >= LAG_WARN:
        findings.append(RuleFinding(
            rule_id="NH-001", name="Finality Lag",
            strength=_strength(current.finality_lag, LAG_WARN, LAG_CRITICAL), confidence=1.0,
            summary=f"Finalization is {current.finality_lag} blocks behind the best block (2 to 3 is normal on this testnet)",
            evidence={"best_block": current.best_block, "finalized_block": current.finalized_block,
                      "finality_lag": current.finality_lag},
            suggestion="Check whether validators are online and whether the node you query is healthy and synced.",
        ))

    total_slots = current.window_blocks + current.missed_slots
    if total_slots and current.missed_slots / total_slots >= MISSED_WARN:
        share = current.missed_slots / total_slots
        findings.append(RuleFinding(
            rule_id="NH-002", name="Missed Slots",
            strength=_strength(share, MISSED_WARN, MISSED_CRITICAL),
            confidence=round(min(1.0, current.window_blocks / 30), 2),
            summary=f"{current.missed_slots} of {total_slots} recent slots produced no block ({share * 100:.0f}%)",
            evidence={"missed_slots": current.missed_slots, "window_blocks": current.window_blocks,
                      "missed_share": round(share, 3)},
            suggestion="A validator may be offline or struggling. Compare with the author distribution.",
        ))

    if current.block_age_s is not None and current.block_age_s >= AGE_WARN:
        findings.append(RuleFinding(
            rule_id="NH-003", name="Block Production Stalled",
            strength=_strength(current.block_age_s, AGE_WARN, AGE_CRITICAL), confidence=0.8,
            summary=f"The newest block is {current.block_age_s:.0f} seconds old (slots are 6 s apart)",
            evidence={"block_age_s": current.block_age_s, "best_block": current.best_block},
            suggestion="The chain may have stalled, or the node you query may have fallen behind. Check another endpoint.",
        ))

    earlier: set[str] = set()
    for snapshot in history:
        earlier.update(snapshot.authors)
    silent = sorted(earlier - set(current.authors), key=int)
    if silent and current.window_blocks >= MIN_WINDOW_FOR_SILENCE and current.authors:
        findings.append(RuleFinding(
            rule_id="NH-004", name="Block Author Silent",
            strength=70.0, confidence=round(min(1.0, len(history) / FULL_CONFIDENCE_HISTORY), 2),
            summary=(f"Author index {', '.join(silent)} produced none of the last {current.window_blocks} blocks "
                     f"but was active in earlier snapshots"),
            evidence={"silent_authors": ", ".join(silent), "window_blocks": current.window_blocks,
                      "snapshots_compared": len(history)},
            suggestion="A validator may have gone offline or been removed. Confirm in the node console.",
        ))

    return findings
