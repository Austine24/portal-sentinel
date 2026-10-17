# AI model: Isolation Forest anomaly signal (ML-001)

Status as of 2026-10-17. All results so far use **simulated** data. Nothing here has been validated on real Portaldot activity.

## What it is for

Rules catch patterns we thought of in advance (a burst, a large transfer). The model adds a second opinion that does not
depend on a hand-picked threshold: it asks whether an account's latest hour looks unusual compared with everything it has
learned, measured against that account's own normal. It is one signal among several. It never decides alone.

## How it works

1. **Describe each hour of each account with four features:** transactions per hour, total value per hour, distinct
   counterparties, and the share of failed transactions. Quiet hours count as zeros.
2. **Measure each hour against the account's own average.** Counts, values and counterparties use `log2((x+1)/(mean+1))`
   (+1 means double); failure rate uses a simple difference. A busy account is only unusual if it is busier than it normally is,
   so one model serves very different accounts. This fixes the problem seen in the early experiment, where a model trained on
   raw features flagged a quiet account just for being unlike the crowd.
3. **Train an Isolation Forest** (200 trees, fixed random seed) on those deviations from the last 7 days.
4. **Score the current hour** and convert the score to a **percentile** against the training scores: "more unusual than 99.7%
   of the past account-hours the model learned from."
5. **Report a finding only if all of these hold:** percentile at least 0.99, the account made at least 5 transactions in the
   window, and at least one feature really jumped (2x its usual level, or failure rate up by 0.2).
6. **Explain it:** the finding lists the largest shifts as "N times the usual" plus the evidence numbers.
   The finding's strength runs from 60 (just over the bar) to 100.

The model is retrained on every run and nothing is stored, so there is no model file to tamper with or go stale.

## Settings

| Setting | Value | Why |
|---|---|---|
| Minimum history | 24 hours | Less than this and the model stays silent and says why |
| Minimum training examples | 200 | Too few examples make percentiles meaningless |
| Trigger percentile | 0.99 | Flags roughly the top 1% of what it has seen |
| Minimum window transactions | 5 | Ignore near-silent accounts |
| Minimum jump | 2x usual, or +0.2 failure rate | A statistical oddity must also be a real change |
| Trees / seed | 200 / 42 | Deterministic, repeatable results |
| Risk weight | 0.6 (rules: 0.85 and 0.75) | The model is trusted a little less than the explicit rules |

## Evidence so far, and its limits

- On simulated data (8 accounts, 7 days, one injected burst) the burst account was flagged on all 8 random seeds tried and no
  other account was flagged.
- Automated tests cover feature construction, flagging, silence on normal accounts, silence with too little history,
  determinism, ignoring near-silent accounts, and that the percentile threshold is really applied. Deliberately breaking the
  code makes the relevant tests fail.
- **This is a weak test of accuracy.** The simulated accounts are stable and the burst is obvious. Real activity is messier. The
  thresholds are starting points and have not been tuned on real data, and the false-positive rate on a real chain is unknown.
- Percentiles are relative to the data seen in the last week. A quiet network makes "unusual" easier to reach, and a network that
  is always chaotic makes it harder. A testnet with little activity may not provide a useful baseline at all.
- It only detects deviation from an account's own past. An account that is malicious from its first transaction has no past to
  deviate from. The burst rule covers brand-new accounts with low confidence.
- **An anomaly is not proof of malicious behaviour.** Wording throughout the product says "anomalous" and "requires
  investigation", and a human decides.
