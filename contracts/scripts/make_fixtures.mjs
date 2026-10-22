// Deploys the contract to an in-memory EVM, records one piece of evidence, and saves the REAL JSON-RPC
// answers (receipt, eth_call results). The backend tests replay these, so they test against genuine EVM output.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { BrowserProvider, ContractFactory, Interface } from "ethers";

const ganache = createRequire(import.meta.url)("ganache");
const { abi, bytecode } = JSON.parse(readFileSync("build/SentinelEvidenceRegistry.json", "utf8"));
const raw = ganache.provider({ logging: { quiet: true }, chain: { hardfork: "shanghai" }, wallet: { deterministic: true } });
const provider = new BrowserProvider(raw);
const owner = await provider.getSigner(0);

const contract = await (await new ContractFactory(abi, bytecode, owner).deploy()).waitForDeployment();
const address = await contract.getAddress();

const incidentId = "0x05831adf72f5c868dbac808bcdb93fde3ad0151eb3f528faf863784da9491e13";
const evidenceHash = "0x8f8cca3ef142ce593cb2dd64e8f68f52f0cb4572cd7a577b520b85fdce53108c";
const tx = await contract.record(incidentId, evidenceHash, 96);
const receipt = await tx.wait();

const iface = new Interface(abi);
const rpc = (method, params) => raw.request({ method, params });
const call = (data) => rpc("eth_call", [{ to: address, data }, "latest"]);
const wrong = "0x" + "11".repeat(32);

const fixtures = {
  note: "Real JSON-RPC output from an in-memory EVM (ganache). Regenerate with: node scripts/make_fixtures.mjs",
  contract_address: address,
  owner: await owner.getAddress(),
  incident_id: incidentId, evidence_hash: evidenceHash, risk_score: 96,
  tx_hash: tx.hash,
  receipt: await rpc("eth_getTransactionReceipt", [tx.hash]),
  transaction: await rpc("eth_getTransactionByHash", [tx.hash]),
  calls: {
    verify_true: await call(iface.encodeFunctionData("verify", [incidentId, evidenceHash])),
    verify_wrong_hash: await call(iface.encodeFunctionData("verify", [incidentId, wrong])),
    verify_unknown: await call(iface.encodeFunctionData("verify", [wrong, evidenceHash])),
    get: await call(iface.encodeFunctionData("get", [incidentId])),
    owner: await call(iface.encodeFunctionData("owner")),
    total: await call(iface.encodeFunctionData("totalRecords")),
  },
  calldata: {
    record: iface.encodeFunctionData("record", [incidentId, evidenceHash, 96]),
    verify: iface.encodeFunctionData("verify", [incidentId, evidenceHash]),
    get: iface.encodeFunctionData("get", [incidentId]),
  },
};
mkdirSync("fixtures", { recursive: true });
writeFileSync("fixtures/registry_fixtures.json", JSON.stringify(fixtures, null, 2) + "\n");
console.log("record calldata :", fixtures.calldata.record);
console.log("get() returned  :", fixtures.calls.get);
console.log("receipt status  :", fixtures.receipt.status, "logs:", fixtures.receipt.logs.length, "block:", fixtures.receipt.blockNumber);
process.exit(0);
