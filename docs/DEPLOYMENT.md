# Deployment runbook: evidence registry on the Portaldot V3 testnet

Status as of 2026-10-21. Check-in deadline: 2026-10-24 12:00 UTC (13:00 Lagos).

Everything below is **unverified until its checkpoint passes**. Each checkpoint says what to do if it fails. Stop at the first failure and send the exact output; do not improvise.

## Rules that do not bend
- **Testnet only.** In the node console always select **PortaldotV3 Testnet**, never "Live".
- **A separate deployer account.** Create a new MetaMask account only for this. Do not use or import your main wallet.
- **Never paste a seed phrase or private key anywhere**: not here, not in Remix, not in a file, not in the repo, not in a support ticket.
- **Small amounts first.** The first transfer is 5 tPOT, not 500.

## Phase 1: wallet and network (10 minutes)
1. Install MetaMask from the Chrome Web Store (publisher: MetaMask). Open it and create or unlock a wallet.
2. Account menu, **Add account**, name it `Sentinel Deployer`. Copy its address (starts with `0x`; this is public).
3. Settings, Networks, **Add a network manually**:

| Field | Value |
|---|---|
| Network name | Portaldot V3 Testnet |
| RPC URL | https://test-evm-rpc-v3.portaldot.dev |
| Chain ID | 420420777 |
| Currency symbol | tPOT |
| Block explorer URL | https://node-console.portaldot.dev/?rpc=wss%3A%2F%2Ftest-node-v3.portaldot.dev |

**Checkpoint 1:** the network saves with no error and the balance shows 0 tPOT. If MetaMask says it cannot fetch the chain id, stop and send me the message.

## Phase 2: fund the deployer (15 minutes)
An `0x` account is funded by sending tPOT to its "fallback" account. That is general behaviour of this kind of chain and is **not yet confirmed for Portaldot**. The check below tests it with a small amount.

1. Run: `python scripts\evm_funding_address.py 0xYOUR_DEPLOYER_ADDRESS`
   It prints a `5...` address labelled "Send tPOT to this 5... address". Copy it.
2. Open the node console, select **PortaldotV3 Testnet** (top left, TEST NETWORKS, Switch).
3. Accounts, Accounts, find your account, press **send**. Paste the `5...` address as the recipient, amount **5**, unit **tPOT**, Make Transfer, approve in the Portaldot extension.
4. Wait 30 seconds, then run: `python scripts\evm_funding_address.py 0xYOUR_DEPLOYER_ADDRESS --check`

**Checkpoint 2:** it prints `RESULT: both views see funds`, and MetaMask shows a non-zero balance.
- Result says the Substrate side sees funds but the Ethereum side does not, or still zero after 2 minutes: **STOP. Send nothing more.** Paste the output. The 5 tPOT is a small testnet loss, and it tells us the fallback-account assumption is wrong.

## Phase 3: deploy with Remix (15 minutes)
1. Open https://remix.ethereum.org. Create `SentinelEvidenceRegistry.sol` and paste the contents of `contracts/contracts/SentinelEvidenceRegistry.sol`.
2. Solidity compiler tab: version **0.8.26** (any 0.8.2x works), Advanced Configurations: **EVM Version = paris**, **Enable optimization = 200**. Compile.
3. Deploy and run tab: Environment **Injected Provider - MetaMask**. Check that MetaMask is on Portaldot V3 Testnet and the account is `Sentinel Deployer`. Deploy, then approve in MetaMask.

**Checkpoint 3:** Remix logs success and lists the contract under "Deployed Contracts". Copy the **contract address** and the **deployment transaction hash** (MetaMask, Activity, the transaction, copy hash).
- In Remix, expand the contract: `owner` should equal your deployer address and `totalRecords` should be 0.
- Then run: `python scripts\check_registry.py 0xYOUR_CONTRACT` and expect "code at address: yes", the owner, and "records stored: 0".

| If you see | Likely meaning | Do this |
|---|---|---|
| insufficient funds / gas | Not enough tPOT in the deployer | Send another 5 tPOT, repeat Phase 2 step 3 |
| invalid opcode, code rejected, revert without a reason | The chain may need a different compile target (for example PolkaVM) | **STOP.** Send me the exact error text. We switch compile path |
| MetaMask cannot fetch / network error | The RPC refused the browser | Send me the exact message |
| Remix cannot estimate gas | Estimation unsupported | Send me the message; we try a manual gas limit |

## Phase 4: connect Sentinel and record real evidence (10 minutes)
1. In `backend\.env` add one line: `REGISTRY_ADDRESS=0xYOUR_CONTRACT`
2. `cd backend`, `alembic upgrade head` (applies migration 0004), restart `uvicorn app.main:app --reload`.
3. In Sentinel: **Run detection**, open the incident, **Prepare evidence package**, press **Record evidence on-chain**, approve in MetaMask. Use the **same account that deployed** the contract; only the owner can record, and any other account reverts with `NotOwner`.
4. Wait for "Verified against the chain: the registry recorded this incident's id, hash and risk score in block N".

**Checkpoint 4:** the Evidence panel shows Anchored, the contract, the transaction hash and the block.
- Independent proof: **Show package**, copy the "On-chain incident id" and the hash, then run
  `python scripts\check_registry.py 0xYOUR_CONTRACT --incident 0xON_CHAIN_ID --hash 0xHASH`
  and expect `verify(id, hash) : True` with the stored hash and risk score.

## Phase 5: capture proof for the check-in
- Contract address, deployment transaction hash, record transaction hash, block number.
- Screenshots: MetaMask confirmation, the Anchored panel, the `check_registry.py` output.
- Fill in `docs/CHECKIN_DRAFT.md` and update `docs/PORTALDOT_VERIFIED_FACTS.md` with what was actually observed.

## What is already proven, and what is not
Proven by tests: the contract's behaviour (9 tests), the browser's calldata (byte-identical to a real EVM library's), and Sentinel's server-side verification, which was run against a real in-memory EVM over HTTP with a real deployment and a real `record()` call.

Not proven until you run it: that Portaldot accepts standard EVM bytecode, that the fallback-account funding works, that MetaMask talks to the public RPC, and the wallet pop-up flow in the browser.
