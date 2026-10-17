# Demo script (3 minutes maximum)

The check-in and the final submission each need a demo video of at most 3 minutes that shows a real product and its
core functions. This script has two versions. Use **Version A** now. Switch segment 6 for **Version B** after the contract
is deployed and a real transaction exists.

## Before recording (10 minutes)

- [ ] Start MySQL in Laragon. Start the backend (`uvicorn app.main:app`) and the frontend (`npm run dev`).
- [ ] Open `http://localhost:5173/dashboard`. For a clean take, empty the table in HeidiSQL: `DELETE FROM incident_events; DELETE FROM incidents;`
- [ ] Have two terminals ready: one in the repo root, one in `contracts`.
- [ ] Hide anything secret: no `.env` open, no wallet seed, no password in the shell history on screen.
- [ ] Browser zoom 110 to 125 percent so text is readable. Record at 1080p. Do one practice run with a timer.
- [ ] Say "simulated" out loud when showing detection. Judges reward honesty and punish anything that looks faked.

## Version A: no on-chain step yet (about 2 minutes 50 seconds)

| Time | On screen | Say |
|---|---|---|
| 0:00 | Landing page, then dashboard | "Blockchains show you activity, but not what deserves your attention. Portal Sentinel is a security intelligence layer for the Portaldot ecosystem: it explains what is unusual, how risky it is, and lets you prove what you found." |
| 0:20 | Click **Run detection**. Point at the "DEMO / SIMULATED" badges | "Right now I am running on simulated transactions, labelled on every screen, because I am building against the Portaldot V3 testnet that opened this week. The detection pipeline sits behind an adapter, so live data plugs in without changing the rules." |
| 0:45 | Open the critical incident | "Sentinel flagged one account as critical, risk 96. Each account is compared with its own history, so a busy account is not flagged just for being busy." |
| 1:05 | Factor bars and the rule evidence panels | "Here is why. [Read the real numbers from the screen: in my test runs transaction frequency was roughly 36 times its usual rate and the largest transfer roughly 50 times its normal range.] Every factor, including an Isolation Forest anomaly model, shows its share of the score and the numbers behind it. This is anomalous behaviour that needs investigation. It is not proof of anything malicious." |
| 1:20 | Point at the line under the risk gauge, then open the **AI Intelligence** page briefly | "The anomaly model says this hour is more unusual than almost everything it learned from, and the page shows which features shifted. The model finds candidates; the numbers explain them." |
| 1:35 | Press **Mark investigating**; show the timeline | "An investigator takes the incident. The server only allows legal status changes, and every step is recorded in an audit timeline." |
| 1:50 | Press **Prepare evidence package**; **Show package** | "Now the part I care most about. Sentinel freezes the facts into a canonical record, with a random nonce, and computes a SHA-256 hash. Later status changes cannot alter it." |
| 2:10 | **Download JSON**; in the terminal run `python scripts\verify_evidence.py <file> <hash>` | "Anyone can verify it with a standalone script that shares no code with our backend." Expect **MATCH**. |
| 2:25 | Edit one number in the JSON, re-run | "Change a single number and verification fails." Expect **MISMATCH**. |
| 2:35 | In the `contracts` terminal run `npm test` | "The hash is designed to be anchored by this Solidity contract: owner-only, one record per incident. Nine tests pass, including the attacks I expect." |
| 2:50 | Roadmap slide or the architecture diagram | "Next: deploy the contract on the Portaldot testnet, record the first real evidence, and connect live data. Thank you." |

Be upfront in the submission text that the contract is written and tested but not yet deployed, and why (testnet endpoints
and tokens were published on 2026-10-16). Do not imply a deployment that has not happened.

## Version B: after deployment (replace the 2:35 to 2:50 rows)

| Time | On screen | Say |
|---|---|---|
| 2:35 | Press **Record evidence on-chain**; approve in the wallet | "I approve the record in my own wallet. Sentinel never sees my keys." |
| 2:50 | The transaction in the node console; the incident now showing the transaction hash | "Here it is on the Portaldot testnet. The incident links to the transaction, and `verify` on the contract confirms the hash." |

(The on-chain button is not built yet. Do not record Version B until it works end to end.)

## Never say or show

- "AI detected an attack" or "this wallet is malicious". Say "anomalous" and "requires investigation".
- "Live data" or "real transactions" while the badge says DEMO / SIMULATED.
- A contract address, transaction hash, or explorer page that is not real.
- Claims about the Isolation Forest until it is trained and tested.
