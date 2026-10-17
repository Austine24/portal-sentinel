# Sentinel Evidence Registry (contract)

A minimal contract that records a tamper-evident fingerprint of a security incident.

**It stores:** an incident key, the SHA-256 hash of the evidence package, a risk score (0-100), the block timestamp, and the recording account.
**It never stores** incident details, addresses of investigated accounts, or anything sensitive. Those stay off-chain.

**What a record proves:** this exact evidence package existed at this time and was recorded by an authorised account.
**What it does not prove:** that the incident was real or malicious.

**Status: NOT deployed anywhere.** The Portaldot V3 testnet endpoints and tPOT funding are not available yet
(see `docs/PORTALDOT_VERIFIED_FACTS.md`, section H). Tested only on an in-memory EVM.

## Functions

| Function | Who | What |
|---|---|---|
| `record(incidentId, evidenceHash, riskScore)` | owner | Records evidence once per incident. Rejects zero ids, zero hashes, scores above 100 and duplicates. Emits `EvidenceRecorded`. |
| `get(incidentId)` | anyone | Returns the record, or reverts `NotFound`. |
| `verify(incidentId, evidenceHash)` | anyone | `true` only if recorded and the stored hash matches. |
| `transferOwnership(proposed)` / `acceptOwnership()` | owner / proposed | Two-step handover so control cannot be sent to a wrong or dead address. |

## How the backend maps to it

- `incidentId` = `onchain_incident_id` from the API = `SHA-256("portal-sentinel:incident:<public_id>:<nonce>")`
- `evidenceHash` = `hash` from the API (SHA-256 of the canonical evidence package)
- `riskScore` = `package.assessment.risk_score`

The nonce is inside the evidence package, so anyone holding the package can recompute both values, and nobody can predict
(and reserve) the id of an incident that has not been prepared yet.
Verify a package offline with `python scripts/verify_evidence.py package.json <hash>`.

## Run the tests

```powershell
cd contracts
npm install
npm test
```

Expected: `compiled SentinelEvidenceRegistry (...)`, then `# tests 9`, `# pass 9`, `# fail 0`.
The tests use the Solidity compiler packaged in npm (no downloads) and an in-memory EVM (ganache).
Covered: valid record and event, non-owner, duplicate, invalid input, boundary scores, unknown incident,
verify (match, tampered, unknown), and the full two-step ownership flow.
`npm install` reports advisories in ganache's own dependencies; ganache is a dev-only test tool and is never deployed.

## Try it by hand in Remix (optional, no install)

1. Open remix.ethereum.org, create `SentinelEvidenceRegistry.sol`, paste the contract.
2. Compiler 0.8.26, under Advanced Configurations set EVM version `paris`, compile.
3. Deploy with the environment **Remix VM**. This is a simulated chain, not Portaldot.
4. Call `record` with the `onchain_incident_id`, `hash` and risk score shown on an incident page.
5. Call `verify` with the same values (true), then with one changed character in the hash (false).

## Security notes

- One owner key controls recording. A stolen key could record false evidence, but cannot alter or delete existing records.
- No upgrade mechanism and no funds are held, on purpose: less to attack.
- Plain Solidity 0.8 (checked arithmetic), no assembly, no external calls, no `selfdestruct`.
- Gas for `record()` was about 94,000 on the test EVM. Gas on Portaldot is unknown.

## Still UNKNOWN for Portaldot V3 (do not assume)

- Whether plain EVM bytecode deploys directly, or contracts must be compiled for another target (for example PolkaVM via `resolc`).
  The contract is kept portable (no `PUSH0` thanks to `evmVersion: paris`, no assembly, no precompiles) to help either way.
- RPC URL, chain id, funding method, wallet configuration, how to read events, and whether an explorer exists.
