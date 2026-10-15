# Portaldot Hacker House 2026: Competition Spec

Last updated: 2026-10-08

Source: text of the DoraHacks event page (https://dorahacks.io/hackathon/portaldot-hacker-house-2026/detail), copied by the team member into the chat. Claude's tools cannot open that page (HTTP 405), so Claude has NOT independently fetched it.
Status key: **VERIFIED-ORGANIZER** = stated in the organizer's page text; **UNVERIFIED** = anything else; **UNKNOWN** = not stated anywhere we have.
Before every major decision, re-read the live page. If it differs from this file, the live page wins.

## 1. Key dates (UTC, with Lagos time = UTC+1)

| Event | UTC | Lagos | Status |
|---|---|---|---|
| Code-production period | Oct 14 to Nov 6 (no hour stated) | | VERIFIED-ORGANIZER |
| Kick-off meeting and workshop (Discord) | Oct 14, 12:00-14:00 | 13:00-15:00 | VERIFIED-ORGANIZER |
| **Check-in submission deadline** | **Oct 24, 12:00** | **Oct 24, 13:00** | VERIFIED-ORGANIZER |
| Feedback results | Oct 26, 16:00 | 17:00 | VERIFIED-ORGANIZER |
| Office-hour application deadline | Oct 30, 12:00 | 13:00 | VERIFIED-ORGANIZER |
| Office hours | Oct 31 - Nov 1 | | VERIFIED-ORGANIZER |
| **Final submission / code freeze** | **Nov 6, 04:00** | **Nov 6, 05:00 (early morning!)** | VERIFIED-ORGANIZER |
| Live demo day (Discord) | Nov 7-8 | | VERIFIED-ORGANIZER |
| Community Choice voting | Nov 8, 16:00 - Nov 9, 16:00 | | VERIFIED-ORGANIZER |
| Winners announced | Nov 10 | | VERIFIED-ORGANIZER |
| Winner info collection | Nov 11-13 | | VERIFIED-ORGANIZER |
| Reward distribution | Nov 13, 12:00 | 13:00 | VERIFIED-ORGANIZER |

### Our start rule (conservative)
The page says code must be primarily produced Oct 14 - Nov 6. An earlier community post said Oct 13 16:00 UTC; the organizer text does NOT confirm that. So:
- No competition-core code and no commits to the competition repo before **Oct 14, 00:00 UTC (Oct 14, 01:00 Lagos)**.
- Safest: start after the kick-off workshop (Oct 14, 14:00 UTC / 15:00 Lagos), where RPC and tooling details may be given.
- Plan to submit the final package on the evening of **Nov 5 (Lagos)**, because the deadline is Nov 6 at 05:00 Lagos.

## 2. Tracks (VERIFIED-ORGANIZER)
1. Modular Cloud & Middleware
2. Multi-Chain & Cross-Chain Infra
3. **Node Operations & Tooling**: "Node monitoring, automated staking, node data visualization, and network security analysis tools." <- Portal Sentinel
4. Ecosystem DApps

## 3. Prizes (VERIFIED-ORGANIZER)
Total 5,200 USDT (2,600 in USDT, 2,600 USDT-equivalent in POT). Grand Prize 1,000; Track First Place 800 each; Ecosystem DApps 2nd 500 and 3rd 300; Community Choice 200 (Discord vote, stackable, not part of judges' scoring). If a project wins Grand Prize and its track, the track award passes to the next project. Track awards may stay vacant below a quality threshold. Track 3 has first place only.

## 4. Participation requirements (VERIFIED-ORGANIZER)
- Teams or individuals able to build and maintain a product long term.
- Stack "includes but is not limited to Rust / ink!, Solidity, Web3 frontend, full-stack".
- Must use Portaldot V3.0 core features AND **deploy on the Portaldot testnet**.
- Code primarily produced Oct 14 - Nov 6. Submitting an existing complete project is not allowed.

## 5. Check-in submission (due Oct 24, 12:00 UTC, on DoraHacks)
Required:
- Current progress and outstanding items
- Public GitHub repo with complete README and continuously updated development records
- Product architecture diagram
- Portaldot testnet deployment info: contract address, transaction hash, explorer link if available
- Initial demo: live demo/DApp link OR a demo video of at most 3 minutes showing at least one core function
- Must already be a demonstrable prototype or core flow, not a concept. Simulated data is allowed in the demo, but real testnet interaction is encouraged. (Our own rule still applies: simulated data is labelled DEMO / SIMULATED.)

## 6. Office hours (optional)
Apply by Oct 30, 12:00 UTC with progress, repo, completed modules, testnet status, demo link if any, and questions (technical, product, tokenomics).

## 7. Final submission (by Nov 6, 04:00 UTC)
- Project name, team members, one-sentence overview
- Public GitHub repo, complete README, deployment instructions, project documentation, reproducible/runnable final code
- Testnet deployment information; contract address and transaction hash if applicable
- Runnable demo: web/DApp link or clear local deployment instructions in the README
- Demo video: at most 3 minutes, real product, core functions, shows Portaldot integration, publicly accessible link
- Pitch deck: PDF or public link covering the problem, why Portaldot is essential, proof of functionality, and reasons for continued support

## 8. Code compliance (VERIFIED-ORGANIZER)
- Repo public during the event.
- At least **3 valid commits** in the period.
- Code primarily produced in the period.
- **Core module final versions must not be committed all at once in the last 24 hours** before the deadline.
- Keep commit timelines and pull requests as evidence.
- After the deadline: code freeze. No substantial changes to core functionality, architecture or evaluation results. A serious bug fix must be reported to the organizer with a clear modification record.
- Open-source frameworks, official SDKs and third-party dependencies are allowed but **sources must be disclosed**.
- Intellectual property: our code stays ours; we grant the Foundation a non-exclusive license to display and promote the project. Third-party code/assets must be licensed and attributed; plagiarism can mean disqualification.

## 9. Judging (VERIFIED-ORGANIZER)
| Criterion | Weight | What they say they look at |
|---|---|---|
| Technical Feasibility | 30% | architecture, code completeness, real delivery, genuine sustained GitHub activity, testnet deployment with verifiable on-chain interactions |
| Innovation | 30% | new technical/product ideas; effective use of V3 features (WASM/EVM, modular architecture, multi-chain); value beyond existing solutions |
| Ecosystem Contribution | 20% | contribution to Portaldot infrastructure, developer tools, node ecosystem; open-source value; long-term collaboration |
| Business Potential | 20% | real market need, clear users, feasible business model and growth, team ability to continue |
Evaluation uses objective evidence: repo, commit timeline, testnet transactions, contract addresses, tx hashes, live demo.

## 10. Platforms
Application, submission and check-in on DoraHacks. Kick-off, workshop, office hours, demo day and voting on Discord. The page gives https://discord.gg/portaldot; the official website footer gives https://discord.gg/G33tVtCsNW. Check which one is the real server before posting anything.

## 11. What this means for Portal Sentinel
1. **Real deployment is mandatory.** The evidence contract must be on the testnet and demonstrable by the check-in on Oct 24 (10 days after the start). Contract plus testnet deployment comes BEFORE the polish.
2. **Check-in-ready minimum (Oct 24):** public repo with README and architecture diagram, one working core flow (Portaldot data -> detection -> incident), deployed contract address + tx hash, and a demo video of 3 minutes or less.
3. **Commit hygiene:** many small, honest commits across 3+ weeks; never a big dump in the last 24 hours.
4. **Scoring emphasis:** Technical 30% means verifiable on-chain interaction; Innovation 30% means using V3 features (a Solidity evidence contract plus possibly WASM); Ecosystem 20% means a node/network tool for Portaldot; Business 20% means clear users and a plausible model.
5. **The pitch must answer "why Portaldot is essential."** Sentinel must read Portaldot-specific data and anchor evidence on Portaldot.

## 12. Still UNKNOWN (not stated in the provided text)
V3 testnet RPC/WebSocket URL, chain ID, native token details, faucet, explorer and its API, wallet configuration, recommended Solidity tooling, DaaS interfaces, cross-chain interfaces. We do not assume any of these. They are expected at the Oct 14 kick-off workshop or on Discord.
