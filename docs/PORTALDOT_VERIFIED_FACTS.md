# Portaldot Verified Facts

Last updated: 2026-10-08 (revised after the organizer page text was provided)
Policy: nothing here is assumed. Status levels:

- **VERIFIED**: read from an official Portaldot source (site, docs, GitHub org) on the date above.
- **UNVERIFIED**: found only in secondary sources (news, third-party repos, outreach text). DO NOT BUILD AROUND THIS YET.
- **UNKNOWN**: no reliable information found. DO NOT BUILD AROUND THIS YET.

IMPORTANT SCOPE NOTE: every VERIFIED item below comes from the official developer docs ("Portaldot Developer v1", copyright 2025) and official site. These pages do NOT mention V3, EVM or Solidity. They describe the chain documented there. Whether the V3 testnet behaves the same is UNKNOWN until an official V3 source is read.

Official sources used:
- S1 https://www.portaldot.world/ (official site; footer links to S2-S6)
- S2 https://portaldot-dev.readthedocs.io/en/latest/ (official developer docs, v1)
- S3 https://portaldot-dev.readthedocs.io/en/latest/chain-info.html
- S4 https://portaldot-dev.readthedocs.io/en/latest/python-sdk/index.html and Install page
- S5 https://github.com/portaldotVolunteer/Portaldot (official GitHub, Substrate-based node source)
- S6 https://portalscan.portaldot.io/ (explorer; page needs JavaScript, contents NOT read)
- S8 Organizer text of the DoraHacks Hacker House page, copied by the team member (not fetched by Claude). Treated as VERIFIED-ORGANIZER.
- S7 https://discord.gg/G33tVtCsNW and https://x.com/PortaldotL0 (official community links from S1; not read)

---

## A. VERIFIED (documented chain)

### A1 Substrate-based chain
- FACT: Portaldot is a Substrate-based blockchain.
- SOURCE: S5 README, S2 Introduction
- SOURCE TYPE: official
- STATUS: VERIFIED
- CONFIDENCE: high
- AFFECTS SENTINEL: we can use standard Substrate JSON-RPC concepts (blocks, extrinsics, events, storage).

### A2 Mainnet WebSocket
- FACT: wss://mainnet.portaldot.io, ss58_format 42
- SOURCE: S3
- SOURCE TYPE: official docs
- STATUS: VERIFIED
- CONFIDENCE: high for the documented chain (not tested by us yet)
- AFFECTS SENTINEL: candidate read-only data source for lab experiments. TESTED? No.

### A3 Token
- FACT: token POT, 14 decimals
- SOURCE: S3
- SOURCE TYPE: official docs
- STATUS: VERIFIED
- CONFIDENCE: high
- AFFECTS SENTINEL: all value maths must divide by 10^14, not 10^18. Matters for the value-anomaly rule.

### A4 Local development node
- FACT: official local dev node binaries exist for Ubuntu and macOS. On Windows the docs recommend WSL.
- SOURCE: S3
- SOURCE TYPE: official docs
- STATUS: VERIFIED
- CONFIDENCE: high
- AFFECTS SENTINEL: a Windows lab with a local node needs WSL. NOT INSTALLED, decision deferred.

### A5 Official Python SDK
- FACT: docs say `pip install substrate-interface`; connect with SubstrateInterface(url="wss://mainnet.portaldot.io", ss58_format=42, type_registry_preset='default'); local node ws://127.0.0.1:9944. Docs cover query storage, extrinsics, runtime APIs, block header subscription, storage subscription, ink! contract interfacing.
- SOURCE: S4 (Install page source, Examples and Usages index)
- SOURCE TYPE: official docs
- STATUS: VERIFIED (the documentation says this)
- CONFIDENCE: medium-high. Python 3.14 compatibility of substrate-interface and its dependencies is UNKNOWN, test with pip --dry-run first.
- AFFECTS SENTINEL: our FastAPI collector can be pure Python with this library. No Node needed for data collection.

### A6 Runtime pallets documented
- FACT: the Module Interface storage docs list pallets including assets, babe, balances, contracts, electionProviderMultiPhase, grandpa, identity, imOnline, multisig, offences, proxy, scheduler, session, staking, system, timestamp, transactionPayment, treasury, vesting.
- SOURCE: S2 Module Interface > Storage
- SOURCE TYPE: official docs
- STATUS: VERIFIED (as documented; not queried live)
- CONFIDENCE: medium
- AFFECTS SENTINEL: staking, session, imOnline and offences are real node-operations signals (validator liveness, offences). This fits Track 3 very well and does not depend on smart contracts. The documented list shows a `contracts` pallet and NO evm/revive pallet.

### A7 Smart contract engine in the documented chain
- FACT: official site says "ink! smart contracts" and "Rust core"; SDK docs include "Create and call ink! contract".
- SOURCE: S1, S4
- SOURCE TYPE: official
- STATUS: VERIFIED (for the documented chain)
- CONFIDENCE: medium
- AFFECTS SENTINEL: if V3 adds no Solidity, the evidence contract must be ink!/WASM. Rust and WSL would then become necessary.

### A8 Wallet
- FACT: a Portaldot browser extension (Chrome Web Store) and an Android APK are linked from the official site.
- SOURCE: S1
- SOURCE TYPE: official
- STATUS: VERIFIED (links exist; not installed or tested)
- CONFIDENCE: medium
- AFFECTS SENTINEL: a Substrate-style wallet extension, not MetaMask. The signing flow is NOT yet understood. UNKNOWN: whether it works with V3.

### A9 Explorer exists
- FACT: portalscan.portaldot.io is the official explorer link.
- SOURCE: S1
- STATUS: VERIFIED that it exists; which network it shows is UNKNOWN
- AFFECTS SENTINEL: possible "explorer proof" in the demo.

### A10 V3.0 supports both WASM and EVM, plus ERC-20 / ERC-721
- FACT: the organizer says V3.0 is "fully compatible with the EVM contract ecosystem, supporting both WASM and EVM contract execution, as well as ERC-20 / ERC-721".
- SOURCE: S8
- SOURCE TYPE: organizer page text (relayed by the team member)
- STATUS: VERIFIED-ORGANIZER
- CONFIDENCE: high that it is claimed officially; details of tooling still UNKNOWN
- AFFECTS SENTINEL: the Solidity/EVM path is now officially allowed ("Rust / ink!, Solidity" are listed stacks). Rust and WSL are NOT required unless we choose ink!. This also means the v1 docs (A5-A7) may describe an older runtime than the V3 testnet.

### A11 Testnet deployment is required
- FACT: projects must use V3 core features and complete deployment on the Portaldot testnet; check-in needs contract address and tx hash.
- SOURCE: S8
- STATUS: VERIFIED-ORGANIZER
- AFFECTS SENTINEL: the evidence contract is a hard requirement, due at check-in on Oct 24.

### A12 Track 3 scope
- FACT: "Node monitoring, automated staking, node data visualization, and network security analysis tools."
- SOURCE: S8
- STATUS: VERIFIED-ORGANIZER
- AFFECTS SENTINEL: "network security analysis tools" matches Sentinel directly.

---

## B. UNVERIFIED (secondary only) - DO NOT BUILD AROUND THIS YET

- B1 (RESOLVED, see A10) V3 EVM + WASM support is stated by the organizer.
- B2 V3 GitHub repositories to be published "early October". Not found on the official GitHub org page (12 commits, no V3 material seen).
- B3 V3 testnet: Solidity via pallet-revive and ink! via pallet-contracts, no Solidity explorer, address mapping needed. Source: one third-party project README.
- B4 Portaldot testnet "unavailable" at times. Source: same third-party README.
- B5 Contracts pallet is old (Substrate 3.0 era) and breaks modern ink! tooling. Source: third-party notes. May be about the old chain.
- B6 (RESOLVED, see A10) ERC-20/ERC-721 stated by the organizer.

## C. UNKNOWN - DO NOT BUILD AROUND THIS YET

| Item | Status |
|---|---|
| V3 testnet RPC / WebSocket | UNKNOWN (expected at Oct 14 kick-off or Discord) |
| Chain ID (EVM) | UNKNOWN |
| Faucet | UNKNOWN |
| Solidity deployment workflow and recommended tooling | UNKNOWN |
| Explorer API | UNKNOWN |
| DaaS API/interfaces (site only has marketing text) | UNKNOWN |
| Cross-chain (iBridge) technical interface | UNKNOWN |
| Hacker House participant resources | UNKNOWN (DoraHacks page not readable by my tools) |
| Official Discord contents | UNKNOWN (not read) |

## D. Site claims we do NOT trust
- Developers page shows `npm install @portaldot/sdk` with an apiKey and /api/v1/worlds endpoints. It does not match the documented Python SDK. Treat as marketing template. UNVERIFIED.
- Homepage metrics ("0K+ TPS", "$0.0B+") look like placeholders. Not data.

## E. Impact on Portal Sentinel (current thinking, not decisions)
1. Data collection and rules/AI can start from the documented Substrate interface (Python), independent of the contract language.
2. EVM/Solidity is now officially supported (A10), but the exact deployment workflow, RPC and chain ID are UNKNOWN. Do not install Foundry/Hardhat until the kick-off workshop names the recommended tooling.
3. Track 3 fit is strong via validator/node signals (staking, session, imOnline, offences) if the V3 chain still has them. Check with a read-only lab.

## F. Lab ideas (read-only, safe before the build period; each needs approval)
- L1: connect to wss://mainnet.portaldot.io with substrate-interface and print chain name, runtime version, latest block. No keys, no transactions.
- L2: list the pallets and events actually present in live metadata. Compare with A6.
- L3: pip --dry-run check for substrate-interface on Python 3.14.

---

## G. SUPERSEDED: V3 testnet endpoint reports and test log (added Oct 14, 2026)

Superseded by section I. The feso-apps.xyz endpoints below are confirmed retired by the organizers.

Status added by the team on Oct 14: **WORKING ASSUMPTION (pending confirmation)** = we build on it, it is NOT verified, and it flips to TESTED only when a real call succeeds, or to REFUTED when a test fails.

Source of the reported values: GitHub repo ItsCogumellum/portaldot-v3-testnet-guide. It describes itself as the official guide "provided by the Portaldot team", but it sits on a personal account with 2 commits and no stars. Source type: UNOFFICIAL MIRROR OF A CLAIMED OFFICIAL DOCUMENT.

| Item | Reported value | Status | Test result |
|---|---|---|---|
| EVM JSON-RPC | https://testnetv3-eth-rpc.feso-apps.xyz | WORKING ASSUMPTION | **FAILED Oct 14**: nslookup returns "Non-existent domain" from both the local ISP resolver and Google 8.8.8.8 while google.com resolves. The name does not currently exist in DNS. NOT a local network fault. |
| EVM chain ID | 420420777 | WORKING ASSUMPTION | Untestable until an RPC responds |
| Substrate WebSocket | wss://testnetv3-node.feso-apps.xyz | WORKING ASSUMPTION | Not yet tested (hostname lookup pending) |
| Node explorer / console | https://node-console.feso-apps.xyz/ | WORKING ASSUMPTION | Not yet tested |
| Token | tPOTv3, 14 decimals | WORKING ASSUMPTION | Untested |
| Contract engine | Solidity via the Substrate `Revive` pallet; calls through `reviveApi` and `Revive.call`; EVM address (H160) maps to a Substrate account | WORKING ASSUMPTION (consistent with organizer text that V3 supports EVM) | Untested |
| Funding | Send test tokens from the node explorer to the mapped Substrate address of your EVM address; no faucet is named | WORKING ASSUMPTION | Faucet: UNKNOWN |
| Explorer for EVM side | MetaMask block-explorer field left empty in the guide | WORKING ASSUMPTION | none |

### What this means
1. Our EVM RPC value is currently unusable. Do not hard-code it anywhere.
2. Next checks: nslookup of the other three hostnames; read the endpoint list in the official explorer's network selector (portalscan.portaldot.io); ask in the official Discord for the current V3 testnet endpoints and faucet.
3. Until an endpoint responds, anything on-chain is blocked, and all prototype data stays labelled DEMO / SIMULATED.
4. Safety: the guide's Hardhat example reads a PRIVATE_KEY. Only ever use a brand-new throwaway wallet that holds nothing but testnet tokens.

---

## H. Official organizer response and further tests (Oct 14, 2026)

Source: reply from the Portaldot technical team in the official Discord, relayed by the team member (not fetched by Claude). Source type: ORGANIZER STATEMENT. Status: **VERIFIED-ORGANIZER**.

| Item | Organizer statement | Effect on Portal Sentinel |
|---|---|---|
| EVM RPC and chain ID | The previously shared endpoint appears inaccessible. No verified replacement RPC or confirmed chain ID yet. | G-table RPC and chain ID rows are now REFUTED/UNAVAILABLE. Do not use them. |
| Substrate WebSocket | Still awaiting confirmation of the official V3 WebSocket. Do not substitute an older devnet endpoint without checking runtime compatibility. | No chain connection is possible yet. |
| tPOT V3 distribution | Had not started at last update. Plan: requests handled through Discord every 24 hours once launched. Channel and supported address formats still to be confirmed. | No funded wallet yet, so no contract deployment yet. |
| Block explorer | No verified V3 testnet explorer URL yet. | Explorer link for check-in is "if available". |

Our own DNS tests (Oct 14, using 8.8.8.8): testnetv3-eth-rpc.feso-apps.xyz, testnetv3-node.feso-apps.xyz and node-console.feso-apps.xyz all return "Non-existent domain". The parent domain feso-apps.xyz exists.

Consequences:
- All blockchain-dependent work is blocked until the organizers publish endpoints and start tPOT distribution. This is a confirmed organizer-side delay, not a team failure. Keep a screenshot of the Discord reply as evidence.
- Everything that does not need the chain proceeds: detection core, risk engine, API, UI, tests. Data stays labelled DEMO / SIMULATED (field `data_origin`).
- Check-in on Oct 24 (12:00 UTC) asks for a testnet contract address and transaction hash. If the testnet is still unavailable, say so plainly in the submission, attach the organizer's statement, and ask the organizers how they want blocked teams to handle it.


---

## I. Official V3 testnet details published (Oct 16, 2026)

Source: (a) an official Discord announcement titled "PortaldotV3 Testnet: Updated Network Info & Testnet Token Distribution", and (b) a reply from the Portaldot technical team to the team member's question. Both relayed by the team member, not fetched by Claude. Source type: ORGANIZER ANNOUNCEMENT. Status: **VERIFIED-ORGANIZER** (not yet TESTED by us; see the test log below).

| Item | Value | Status |
|---|---|---|
| EVM JSON-RPC | https://test-evm-rpc-v3.portaldot.dev | VERIFIED-ORGANIZER |
| EVM chain ID | 420420777 (unchanged from the retired endpoints) | VERIFIED-ORGANIZER |
| Substrate WebSocket | wss://test-node-v3.portaldot.dev | VERIFIED-ORGANIZER |
| Official node explorer / console | https://node-console.portaldot.dev | VERIFIED-ORGANIZER |
| Previous endpoints (feso-apps.xyz) | No longer in use | VERIFIED-ORGANIZER |
| tPOT distribution | First batch going to registered participants. If a native POT address was submitted at registration, nothing more is needed for now. Otherwise open a Discord support ticket with a registration screenshot and the native POT address (starts with `5`, not an EVM `0x` address). | VERIFIED-ORGANIZER |
| Wallet safety | Never share a seed phrase or private key | VERIFIED-ORGANIZER |

### Test log
| Date | Test | Result |
|---|---|---|
| Oct 16 | Claude fetched the RPC URL with a plain GET | HTTP 405 (expected for a JSON-RPC server that wants POST). The host resolves and a server answers. This is weak evidence only. |
| Oct 16 | Claude fetched the node console URL | Page loads, titled "Portaldot Node Console" (JavaScript app, content not read) |
| (pending) | `python scripts/check_chain.py https://test-evm-rpc-v3.portaldot.dev 420420777` run by the team member | TO BE RECORDED |

### Still UNKNOWN (ask the team)
- How to deploy a Solidity contract with a funded native `5...` account: through MetaMask (which address receives funds, and how does the EVM `0x` address map to it?) or through extrinsics in the node console?
- Whether plain EVM bytecode deploys directly, or contracts must be compiled for another target.
- Whether the EVM side has a transaction explorer, or only the node console.
- The native token ticker and decimals on V3 (the earlier guide said tPOTv3 with 14 decimals; unconfirmed).
