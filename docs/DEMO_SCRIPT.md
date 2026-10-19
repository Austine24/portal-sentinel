# Demo script (3 minutes maximum)

The check-in and the final submission each need a demo video of at most 3 minutes that shows a real product and its core
functions. **Version A** below works today. After the contract is deployed and a real transaction exists, swap the
contract segment for **Version B**.

## Before recording (10 minutes)

- [ ] Start MySQL in Laragon, then the backend (`uvicorn app.main:app`) and the frontend (`npm run dev`).
- [ ] Open `http://localhost:5173/dashboard`. For a clean take, empty the demo incidents in HeidiSQL: `DELETE FROM incident_events; DELETE FROM incidents;`
- [ ] Open the Network page once, so the top bar shows "connected" and a few snapshots exist.
- [ ] Two terminals ready: one in the repo root, one in `contracts`.
- [ ] Hide anything secret: no `.env` open, no wallet seed, no password in the shell history on screen.
- [ ] Browser zoom 110 to 125 percent, record at 1080p, do one timed practice run.
- [ ] Say "simulated" out loud when you show simulated transactions, and "live" when you show the network page.

## Version A: no on-chain step yet (about 2 minutes 55 seconds)

| Time | On screen | Say |
|---|---|---|
| 0:00 | Landing page, then the dashboard | "Blockchains show you activity, but not what deserves your attention. Portal Sentinel is a security intelligence layer for the Portaldot ecosystem: it watches the network, explains what is unusual and how risky it is, and lets you prove what you found." |
| 0:15 | **Network** page. Point at the LIVE badge | "This page is live data from the Portaldot V3 testnet, read-only. Sentinel decodes block production: who produced the recent blocks, how far finality lags, and whether any slots were missed. If a validator goes quiet, finality stalls or blocks stop, Sentinel raises an alert with the evidence." |
| 0:40 | Dashboard, press **Run detection**. Point at the DEMO / SIMULATED badges | "The testnet carries almost no transactions yet, so for account behaviour I run on simulated transactions, labelled on every screen. The pipeline sits behind an adapter, so live transactions plug in without changing the rules." |
| 0:55 | Open the critical incident; show factor bars and rule evidence | "Sentinel flags one account as critical. Each account is compared with its own history. [Read the real numbers from the screen.] Every factor, including an Isolation Forest anomaly model, shows its share of the score and the numbers behind it. This is anomalous behaviour that needs investigation, not proof of anything malicious." |
| 1:25 | Line under the risk gauge; briefly the **AI Intelligence** page | "The model says this hour is more unusual than almost everything it learned from, and the page shows which features shifted. The model finds candidates; the numbers explain them." |
| 1:40 | **Mark investigating**, then **Prepare evidence package**, **Show package** | "An investigator takes the incident; the server only allows legal status changes. Then Sentinel freezes the facts into a canonical record with a random nonce and computes a SHA-256 hash. Later status changes cannot alter it." |
| 2:00 | **Download JSON**; run `python scripts\verify_evidence.py <file> <hash>` | "Anyone can verify it with a standalone script that shares no code with our backend." Expect **MATCH**. |
| 2:15 | Edit one number in the JSON and re-run | "Change a single number and verification fails." Expect **MISMATCH**. |
| 2:25 | In `contracts`, run `npm test` | "The hash is meant to be anchored by this Solidity contract: owner-only, one record per incident. Nine tests pass, including the attacks I expect." |
| 2:40 | The architecture diagram | "Next: deploy the contract on the Portaldot testnet, record the first real evidence, and ingest live transactions. Thank you." |

Be upfront in the submission text that the contract is written and tested but not yet deployed, and why. Do not imply a deployment that has not happened.

## Version B: after deployment (replace the 2:25 to 2:40 rows)

| Time | On screen | Say |
|---|---|---|
| 2:25 | Press **Record evidence on-chain**; approve in the wallet | "I approve the record in my own wallet. Sentinel never sees my keys." |
| 2:40 | The transaction in the node console (testnet selected); the incident showing the hash | "Here it is on the Portaldot testnet. The incident links to the transaction, and `verify` on the contract confirms the hash." |

(The on-chain button is not built yet. Do not record Version B until it works end to end.)

## Never say or show

- "AI detected an attack" or "this wallet is malicious". Say "anomalous" and "requires investigation".
- "Live transactions" while the transaction badge says DEMO / SIMULATED. The network page is live; the transactions are not.
- A contract address, transaction hash or explorer page that is not real.
- The console left on the **Live** network when you mean the testnet. Select **PortaldotV3 Testnet**.
- Claims about the Isolation Forest's accuracy. Say it is tested and explainable, and still needs tuning on real data.
