// Tests the deploy script's guards against an in-memory EVM (chain id 1337). Nothing here touches Portaldot.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, readFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { after, before, describe, it } from "node:test";
import { JsonRpcProvider, Wallet } from "ethers";

const ganache = createRequire(import.meta.url)("ganache");
const PORT = 8597;
const RPC = `http://127.0.0.1:${PORT}`;
// the well-known first key of ganache's deterministic wallet: public test data, never a real key
const TEST_KEY = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d";
const RECORD = "deployments/chain-1337.json";

let server, provider;
before(async () => {
  server = ganache.server({ logging: { quiet: true }, wallet: { deterministic: true }, chain: { chainId: 1337 } });
  await server.listen(PORT);
  provider = new JsonRpcProvider(RPC, undefined, { staticNetwork: true });
  if (existsSync(RECORD)) rmSync(RECORD);
});
after(async () => {
  await server.close();
  if (existsSync(RECORD)) rmSync(RECORD);
});

function run(args, env = {}) {
  return new Promise((resolve) => {
    const child = spawn("node", ["scripts/deploy.mjs", ...args], { env: { ...process.env, DEPLOYER_PRIVATE_KEY: "", ...env } });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (out += d));
    child.on("close", (code) => resolve({ code, out }));
  });
}

describe("deploy script guards", () => {
  it("refuses to run without a key and says how to set one", async () => {
    const { code, out } = await run(["--rpc", RPC, "--chain-id", "1337"]);
    assert.equal(code, 1);
    assert.match(out, /DEPLOYER_PRIVATE_KEY is not set/);
  });

  it("rejects a malformed key without echoing it", async () => {
    const secret = "not-a-real-key-but-pretend-it-is-secret";
    const { code, out } = await run(["--rpc", RPC, "--chain-id", "1337"], { DEPLOYER_PRIVATE_KEY: secret });
    assert.equal(code, 1);
    assert.match(out, /not a 64-character hex/);
    assert.ok(!out.includes(secret), "the key must never be printed");
  });

  it("refuses when the node is a different network than expected", async () => {
    const { code, out } = await run(["--rpc", RPC], { DEPLOYER_PRIVATE_KEY: TEST_KEY }); // default expects 420420777
    assert.equal(code, 1);
    assert.match(out, /Chain id mismatch: this node reports 1337 but 420420777 was expected/);
  });

  it("refuses an account with no balance", async () => {
    const { code, out } = await run(["--rpc", RPC, "--chain-id", "1337"], { DEPLOYER_PRIVATE_KEY: Wallet.createRandom().privateKey });
    assert.equal(code, 1);
    assert.match(out, /no spendable balance/);
  });

  it("a dry run checks everything but sends nothing", async () => {
    const blockBefore = await provider.getBlockNumber();
    const { code, out } = await run(["--rpc", RPC, "--chain-id", "1337"], { DEPLOYER_PRIVATE_KEY: TEST_KEY });
    assert.equal(code, 0, out);
    assert.match(out, /DRY RUN/);
    assert.equal(await provider.getBlockNumber(), blockBefore, "no transaction may be sent");
    assert.ok(!existsSync(RECORD));
  });

  it("deploys with --confirm, leaves owner = deployer, and saves only public details", async () => {
    const { code, out } = await run(["--rpc", RPC, "--chain-id", "1337", "--confirm"], { DEPLOYER_PRIVATE_KEY: TEST_KEY });
    assert.equal(code, 0, out);
    const record = JSON.parse(readFileSync(RECORD, "utf8"));
    assert.match(record.contractAddress, /^0x[0-9a-fA-F]{40}$/);
    assert.match(record.deploymentTxHash, /^0x[0-9a-fA-F]{64}$/);
    assert.equal(record.deployer, new Wallet(TEST_KEY).address);
    assert.ok(!JSON.stringify(record).includes(TEST_KEY.slice(2)), "the key must not be saved");
    assert.ok(!out.includes(TEST_KEY.slice(2)), "the key must not be printed");
    assert.ok((await provider.getCode(record.contractAddress)).length > 10, "contract code must exist");
  });
});
