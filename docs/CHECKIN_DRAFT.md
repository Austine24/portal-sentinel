# Check-in submission draft (DoraHacks, due 2026-10-24 12:00 UTC)

Fill every [FILL IN]. Delete any sentence that is not true when you submit. Do not claim a deployment that has not happened.

## Project
**Portal Sentinel**: security intelligence for the Portaldot ecosystem. Track: Node Operations & Tooling.
One sentence: Portal Sentinel watches the Portaldot network and account behaviour, explains what is unusual and how risky it is, and anchors a verifiable fingerprint of each incident's evidence on-chain.

## Current project progress
- **Live network-health monitoring** on the Portaldot V3 testnet: block authors, finality lag, missed slots and stalled production, read-only, with four alert rules (NH-001 to NH-004).
- **Detection and risk engine**: two explainable rules plus an Isolation Forest anomaly model compare each account with its own history, and combine into an explained risk score. Currently run on simulated transactions because the testnet carries almost no activity (0 transactions in 30 blocks when checked); every simulated record is labelled DEMO / SIMULATED.
- **Incident workflow** stored in MySQL: legal status transitions, audit timeline, duplicate protection.
- **Evidence packages**: frozen canonical JSON, SHA-256 hash, an independent verifier script, and an on-chain incident id.
- **Evidence registry contract** (Solidity): owner-only, one record per incident, two-step ownership. 9 tests pass, and deliberately broken versions are caught.
- **Server-side on-chain verification**: Sentinel confirms a transaction against the chain (receipt, event, contract state) before marking evidence anchored. Tested against a real EVM.
- 179 automated tests; every simulated element is labelled.

## Testnet deployment information
[FILL IN ONE of the two versions]

**If deployed:**
- Network: Portaldot V3 Testnet (chain id 420420777)
- Registry contract address: [FILL IN]
- Deployment transaction hash: [FILL IN]
- First evidence record transaction hash: [FILL IN] (block [FILL IN])
- Explorer: the node console (https://node-console.portaldot.dev, testnet selected) shows the chain; Ethereum-style transaction hashes are verified with `scripts/check_registry.py` in the repository.

**If not yet deployed (state this plainly):**
The contract is written and tested but not yet deployed. The testnet endpoints were announced on 2026-10-16 and test tokens reached our wallet on [FILL IN DATE]. The first public RPC value we found was retired, and the organizers' technical team confirmed on 2026-10-14 that endpoints, funding and an explorer were not yet available (statement saved). [FILL IN what is blocking now and the exact error, if any.]

## Outstanding items
- Live transaction ingestion (the testnet is nearly empty, so we will generate labelled test activity).
- Wallet flow end to end on the testnet [remove if done].
- API authentication and hardening before any public deployment.
- Tuning the rule and model thresholds on real activity.
- A second registry recorder role (today one owner key records).

## Links
- Public GitHub repository: https://github.com/Austine24/portal-sentinel
- README: in the repository root. Architecture diagram: `docs/architecture.svg` and `docs/evidence-flow.svg`.
- Development records: the commit history, plus `docs/PORTALDOT_VERIFIED_FACTS.md`, which records what is verified, tested or still unknown.

## Demo (at most 3 minutes)
[FILL IN video link]. Script: `docs/DEMO_SCRIPT.md`. Shows live network health, incident investigation with explained risk, evidence hashing with an independent MATCH / MISMATCH check, and [the on-chain record, if done].

## Honest limits to mention if asked
Transaction data is simulated; thresholds are untuned on real data; no API authentication yet; one owner key controls recording.
