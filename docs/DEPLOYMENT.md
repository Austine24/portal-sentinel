# Deployment runbook: evidence registry on the Portaldot V3 testnet

Status as of 2026-10-23. Check-in deadline: 2026-10-24 12:00 UTC (13:00 Lagos).

**Progress:** Phase 1 PASSED and Phase 2 PASSED (2026-10-22, by the team member). Phase 3 is next.

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

**Checkpoint 1 (PASSED):** the network saves with no error and the balance shows 0 tPOT. If MetaMask says it cannot fetch the chain id, stop and send me the message.

## Phase 2: fund the deployer (15 minutes)
An `0x` account is funded by sending tPOT to its "fallback" account. That is general behaviour of this kind of chain and is **not yet confirmed for Portaldot**. The check below tests it with a small amount.

1. Run: `python scripts\evm_funding_address.py 0xYOUR_DEPLOYER_ADDRESS`
   It prints a `5...` address labelled "Send tPOT to this 5... address". Copy it.
2. Open the node console, select **PortaldotV3 Testnet** (top left, TEST NETWORKS, Switch).
3. Accounts, Accounts, find your account, press **send**. Paste the `5...` address as the recipient, amount **5**, unit **tPOT**, Make Transfer, approve in the Portaldot extension.
4. Wait 30 seconds, then run: `python scripts\evm_funding_address.py 0xYOUR_DEPLOYER_ADDRESS --check`

**Checkpoint 2 (PASSED):** it prints `RESULT: both views see funds`, and MetaMask shows a non-zero balance.
- Result says the Substrate side sees funds but the Ethereum side does not, or still zero after 2 minutes: **STOP. Send nothing more.** Paste the output. The 5 tPOT is a small testnet loss, and it tells us the fallback-account assumption is wrong.

## Phase 3: deploy the contract (15 minutes). Pick ONE option.

### Option A: Remix in the browser (keys stay inside MetaMask)
**Type the address exactly: `https://remix.ethereum.org`.** (`app.remix.live`, which timed out for you on two devices, is not the Ethereum Remix IDE.)
If it will not load: try mobile data on the PC (phone hotspot), or set the PC's DNS to 1.1.1.1. If it still fails after about 5 minutes, **go to Option B**. Do not keep fighting the website.

1. Create `SentinelEvidenceRegistry.sol` and paste the contents of `contracts/contracts/SentinelEvidenceRegistry.sol`.
2. Solidity compiler tab: version **0.8.26** (any 0.8.2x works), Advanced Configurations: **EVM Version = paris**, **Enable optimization = 200**. Compile.
3. Deploy and run tab: Environment **Injected Provider - MetaMask**. Check that MetaMask is on Portaldot V3 Testnet and the account is `Sentinel Deployer`. Deploy, then approve in MetaMask.

### Option B: deploy script from your own computer (no website needed)
This uses the tools you already installed. It sends the transaction with the **deployer's private key**, so the rules below matter more than ever.
- Use ONLY the `Sentinel Deployer` key. It holds testnet tokens only. Never use or export your main wallet.
- The key is typed into one terminal window, hidden, and is never saved to a file or printed. Never paste it into chat, Discord, a file in the repo, or a screenshot.
- Export it in MetaMask: pick `Sentinel Deployer`, the three-dot menu next to the account name, **Account details**, **Show private key**, enter your MetaMask password, copy it.

```powershell
cd C:\dev\portal-sentinel\contracts
npm install
npm run compile
$secure = Read-Host "Paste the DEPLOYER private key (it will be hidden)" -AsSecureString
$env:DEPLOYER_PRIVATE_KEY = [System.Net.NetworkCredential]::new("", $secure).Password
node scripts\deploy.mjs
```
**Expected (dry run, nothing sent):** `chain id : 420420777 (matches)`, your deployer address, a spendable balance of about 4.9, and `DRY RUN. Everything checks out and nothing was sent.`
If the address printed is not `0x7daB6e3E7049c8371E962BEfC2bA4D8b4e56cf0A`, STOP: you pasted the wrong key.

Then deploy for real, and clear the key from the window:
```powershell
node scripts\deploy.mjs --confirm
Remove-Item Env:DEPLOYER_PRIVATE_KEY
```
**Expected:** the deployment transaction hash, `contract : 0x...`, a block number, `owner` equal to your deployer, `records stored : 0`, and a saved file `contracts\deployments\portaldot-testnet.json` (public details only).
If the error mentions gas fees, retry with `node scripts\deploy.mjs --confirm --legacy`.

**Checkpoint 3 (either option):** you have a contract address and a deployment transaction hash.
- Run: `python scripts\check_registry.py 0xYOUR_CONTRACT` and expect "code at address: yes", the owner, and "records stored: 0".

| If you see | Likely meaning | Do this |
|---|---|---|
| insufficient funds / gas | Not enough tPOT in the deployer | Send another 5 tPOT (Phase 2 step 3) |
| invalid opcode, code rejected, revert without a reason | The chain may need a different compile target (for example PolkaVM) | **STOP.** Send me the exact error text. We switch compile path |
| Chain id mismatch | Wrong network or node | Do not override it. Send me the message |
| MetaMask or script cannot reach the RPC | The RPC refused the client | Send me the exact message |

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
