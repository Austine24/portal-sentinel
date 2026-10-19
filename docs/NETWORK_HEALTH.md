# Network health monitoring

Status as of 2026-10-18. This is the part of Portal Sentinel that runs on **live Portaldot testnet data** today.
It matches the node-operations track: monitoring the chain itself, not only accounts.

## What is read, and from where
Read-only JSON-RPC over HTTPS to the testnet node (`https://test-node-v3.portaldot.dev`). Nothing is signed or sent.
Requests carry a descriptive User-Agent, because the public endpoint sits behind Cloudflare and rejects Python's default one.

| Signal | How it is obtained |
|---|---|
| Best and finalized block, finality lag | `chain_getHeader`, `chain_getFinalizedHead` |
| Who produced each block | The block header's BABE pre-runtime digest (author index and slot), decoded by `app/portaldot/headers.py`. Confirmed against real testnet headers on 2026-10-18. |
| Missed slots | Gaps between the slot numbers of consecutive blocks |
| Newest block age | **Derived:** slot number x 6 seconds, compared with the clock (a slot matched wall-clock time within minutes on 2026-10-18; not read from the runtime) |
| Peers | `system_health` of the queried node (optional; some nodes disable it) |

To be gentle on the public node, requests are batched, and blocks already seen are cached, so a refresh normally downloads only the new blocks.
The API also refuses to hit the node more than once per 10 seconds, and returns the stored snapshot instead.

## Rules

| Rule | Fires when | Notes |
|---|---|---|
| NH-001 Finality Lag | finality lag of 8 blocks or more | 2 to 3 blocks is normal on this testnet; 30 or more scores as critical |
| NH-002 Missed Slots | 10% or more of recent slots produced no block | a validator may be offline |
| NH-003 Block Production Stalled | newest block 30 seconds or older | could also mean the queried node is lagging |
| NH-004 Block Author Silent | an author seen in earlier snapshots (last 24 h) produced none of the last 30 or more blocks | needs history, so it only works after snapshots accumulate |

Each finding has a strength (40 at the warning level up to 100), a confidence, evidence numbers and a suggested next step,
and feeds the same risk engine and wording as account findings.

## Honest limits
- The thresholds are starting points chosen from what the testnet looks like when healthy. They have not been tested against a real outage.
- On 2026-10-18 the testnet showed two block authors alternating roughly 50/50, finality lag 2 to 3 blocks and no missed slots in 20 blocks.
  That is a small sample. Two authors is normal for a small testnet and is not by itself an alert.
- Author numbers are indexes into the validator set, not addresses. Mapping them to addresses would need a storage read that has not been built.
- Data comes from one node. If that node is lagging or has few peers, the snapshot reflects that node.
- The history only grows while the backend is running and something requests refreshes (the app does this every 60 seconds while open).
