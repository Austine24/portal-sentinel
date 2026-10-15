# Portal Sentinel Roadmap

Last updated: 2026-10-08. Times are Lagos (UTC+1) unless marked UTC.
Rules source: docs/HACKATHON_SPEC.md. Technical facts: docs/PORTALDOT_VERIFIED_FACTS.md.
Anything that depends on an UNKNOWN fact is marked (BLOCKED BY: ...).

## 0. The calendar that drives everything
| Date | Event |
|---|---|
| Oct 8-13 | Prep window: learning, planning, docs. NO competition code. |
| Oct 14, 13:00-15:00 | Kick-off workshop (Discord). Start building after it. |
| **Oct 24, 13:00** | **Check-in deadline** (prototype + testnet deployment + README + architecture diagram + 3-min demo) |
| Oct 30, 13:00 | Office-hour application deadline |
| Oct 31 - Nov 1 | Office hours |
| **Nov 6, 05:00** | **Final submission and code freeze** (plan to finish Nov 5 evening) |
| Nov 7-8 | Live demo day |

## 1. Product scope

### MVP (must exist by final submission)
1. Real Portaldot V3 testnet connection and real block/transaction data
2. Storage in MySQL
3. Three good security rules (burst, value anomaly, new-contract exposure)
4. Isolation Forest anomaly score with human-readable reasons
5. Risk score (configurable weights) with explanation
6. Incident creation and a status workflow
7. Solidity evidence contract on testnet; wallet-signed "Record Evidence On-Chain"
8. Dashboard with incident detail page
9. A controlled testnet scenario script that makes real transactions to trigger the demo

### Should have
Wallet intelligence page, alerts list, network health page, tests, security hardening.

### Stretch (only after MVP works)
Contract intelligence, notifications, DaaS, cross-chain, WASM monitoring, validator signals.

### Cut list (what we drop first if time runs short)
Landing-page animations -> contract intelligence page -> notifications -> wallet intelligence depth -> fancy charts. Never cut: real data, evidence on-chain, explanations.

## 2. Architecture decisions (recommendations)

| Decision | Options | Recommendation | Depends on |
|---|---|---|---|
| Chain access | A) Ethereum-style JSON-RPC (web3.py) B) Substrate API (substrate-interface) | Build a thin "Portaldot adapter" interface; implement ONE backend first. Likely A if V3 exposes an Ethereum RPC; decide at the kick-off. | (BLOCKED BY: V3 RPC type, URL, chain ID) |
| Contract language | Solidity vs ink! | Solidity first (simplest, organizer lists it, no Rust/WSL). ink! only if Solidity deployment fails. | (BLOCKED BY: deployment workflow) |
| Wallet | MetaMask-style vs Portaldot extension | Use whichever the workshop documents. | (BLOCKED BY: wallet config) |
| Backend to chain | Python-only vs Node helper | Python for collection and analysis; the browser wallet handles signing (we never hold keys). | |
| Database | MySQL (XAMPP) | Keep. Add it to PATH or use its full path. | |
| Anomaly detection | Isolation Forest over per-account time-window features | Keep. Needs a baseline (see risk R2). | |
| Job scheduling | Cron/Celery vs simple asyncio loop | Simple asyncio polling loop. | |

## 3. Phases (mapped to dates)

### Phase P: Prep, Oct 8-13 (no competition code)
Goal: arrive at Oct 14 able to move fast.
- Join the official Discord; confirm the real invite; apply/register on DoraHacks if required (check for an approval step).
- Learn (disposable folders only): TypeScript + React basics, FastAPI basics, Solidity contract anatomy, Ethereum vs Substrate accounts, pandas feature-engineering basics, Isolation Forest basics.
- Draft the architecture diagram (paper or Excalidraw), the threat model, and database table sketches.
- Write rule specs on paper: inputs, thresholds, explanation text.
- Prepare README, commit-plan and demo-script skeletons in a local folder (not committed to the public repo yet).
Deliverable: your own words can explain the pipeline end to end.

### Phase 1: Foundation, Oct 14-17
- After the kick-off: confirm RPC, chain ID, faucet, tooling; update PORTALDOT_VERIFIED_FACTS.md with real VERIFIED rows.
- Create the public repo; commit docs, `.gitignore`, `.env.example`.
- Scaffold backend (FastAPI + health endpoint) and frontend (Vite + React + TS + Tailwind) shell.
- Fund a testnet account from the faucet; connect and read the latest block.
- **Deploy the Solidity evidence contract to the testnet (a minimal version) and record address + tx hash.**
Deliverable: Portaldot connection, one deployed contract, 5+ honest commits.

### Phase 2: Check-in package, Oct 18-23
- Collector -> normalizer -> MySQL for blocks and transactions.
- Rules 1 and 2 (burst, value anomaly) with explanations.
- Minimal dashboard: network status, recent transactions, alerts list.
- Architecture diagram into the repo; README with run instructions.
- Record the 3-minute check-in video; submit on DoraHacks by **Oct 24 at 11:00 (2 hours of buffer)**.
Deliverable: check-in submission with real testnet interaction.

### Phase 3: Intelligence, Oct 25-31
- Feature extraction, Isolation Forest, explanations.
- Risk engine with configurable weights.
- Incident model, API and UI (list, detail, status changes).
- Apply for office hours by Oct 30 13:00 if blocked by anything.
Deliverable: detection -> risk -> incident works on real data.

### Phase 4: Evidence, Nov 1-3
- Evidence package, hashing, wallet signing, contract call, store tx hash on the incident, verification view.
- Scenario generator script that produces real anomalous testnet traffic.
- Contract tests; backend rule/risk tests.
Deliverable: the full 14-step demo works end to end.

### Phase 5: Hardening and package, Nov 4-5
- Security pass (validation, CORS, rate limits, secrets scan, dependency audit).
- UI polish; error states; every simulated element labelled.
- Docs finalised; pitch deck; demo video; dependency/source disclosure list.
- Submit on the evening of **Nov 5**; stop making core changes after that.

## 4. Commit discipline
- Small commits through the whole period (aim for 40+). Conventional commit messages.
- Final core versions are never committed in one lump during the last 24 hours.
- Disclose third-party libraries/SDKs in the README.
- No history rewriting; keep PRs or branches where natural.

## 5. Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | V3 testnet RPC/faucet unstable or unclear | Medium | Very high | Ask at the kick-off; use office hours; Discord; start with the smallest possible chain read |
| R2 | Testnet has too little activity to baseline an anomaly model | High | High | Backfill historical blocks; build the controlled scenario generator; state clearly in the demo that the scenario is a controlled test |
| R3 | Solidity deployment or wallet signing is awkward | Medium | High | Deploy in the first 3 days; fall back to ink! only if needed |
| R4 | Check-in is 10 days away | Certain | High | Phase 2 scope is deliberately small; the contract is deployed in Phase 1 |
| R5 | Solo workload | High | High | Follow the cut list; no stretch features before MVP |
| R6 | Python 3.14 package incompatibility (chain libraries) | Low-Medium | Medium | Dry-run each new package in the venv before relying on it |
| R7 | Demo looks fake | Medium | High | Only real data; label simulated items DEMO / SIMULATED |
| R8 | Early-morning deadline (05:00 Lagos) | Certain | Medium | Submit Nov 5 evening |

## 6. Definition of done for the final submission
- Public repo with README, deployment instructions, architecture diagram, docs
- Testnet contract address, tx hash and explorer evidence (if an explorer exists)
- Runnable demo (link or clear local instructions), 3-minute video, pitch deck
- At least 3 commits spread over the period, with continuous history
- Every simulated element labelled; every claim in the pitch verifiable
