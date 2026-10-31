// Deploys SentinelEvidenceRegistry to an EVM network, with guards. A fallback for when a browser IDE is unavailable.
//
//   node scripts/deploy.mjs            -> DRY RUN: checks everything, sends nothing
//   node scripts/deploy.mjs --confirm  -> really deploys
//   options: --rpc <url>  --chain-id <n>  --legacy
//
// The private key is read ONLY from the DEPLOYER_PRIVATE_KEY environment variable of this terminal window.
// It is never written to a file and never printed. Use a throwaway TESTNET account, never your main wallet.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { ContractFactory, FetchRequest, JsonRpcProvider, Network, Wallet, formatEther } from "ethers";

const USER_AGENT = "portal-sentinel-deploy/0.1 (testnet deployment)";

function fail(message, hint) {
  console.error(`\nERROR: ${message}`);
  if (hint) console.error(hint);
  process.exit(1);
}

function parse(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith("--")) fail(`unexpected argument: ${argv[i]}`);
    const name = argv[i].slice(2);
    out[name] = ["confirm", "legacy"].includes(name) ? true : argv[++i];
  }
  return out;
}

const args = parse(process.argv.slice(2));
const RPC = args.rpc ?? "https://test-evm-rpc-v3.portaldot.dev";
const CHAIN_ID = Number(args["chain-id"] ?? 420420777);
if (!Number.isInteger(CHAIN_ID) || CHAIN_ID <= 0) fail("--chain-id must be a positive whole number");

const rawKey = process.env.DEPLOYER_PRIVATE_KEY;
if (!rawKey) {
  fail(
    "DEPLOYER_PRIVATE_KEY is not set in this terminal window.",
    "Set it for this window only (docs/DEPLOYMENT.md, Option B). It is never saved to a file.",
  );
}
if (!/^(0x)?[0-9a-fA-F]{64}$/.test(rawKey.trim())) {
  fail("DEPLOYER_PRIVATE_KEY is not a 64-character hex private key. (Its value is not shown here.)");
}
const key = rawKey.trim().startsWith("0x") ? rawKey.trim() : `0x${rawKey.trim()}`;

if (!existsSync("build/SentinelEvidenceRegistry.json")) fail("build/SentinelEvidenceRegistry.json is missing.", "Run: npm run compile");
const { abi, bytecode } = JSON.parse(readFileSync("build/SentinelEvidenceRegistry.json", "utf8"));

try {
  const request = new FetchRequest(RPC);
  request.setHeader("User-Agent", USER_AGENT);
  const provider = new JsonRpcProvider(request, Network.from(CHAIN_ID), { staticNetwork: Network.from(CHAIN_ID) });

  // Guard 1: the node must really be the network we think it is.
  const reported = Number(BigInt(await provider.send("eth_chainId", [])));
  if (reported !== CHAIN_ID) {
    fail(`Chain id mismatch: this node reports ${reported} but ${CHAIN_ID} was expected. Nothing was sent.`,
      "You may be pointed at the wrong network. The Portaldot V3 testnet is 420420777.");
  }

  const wallet = new Wallet(key, provider);
  const balance = await provider.getBalance(wallet.address);
  console.log(`RPC            : ${RPC}`);
  console.log(`chain id       : ${reported} (matches)`);
  console.log(`deployer       : ${wallet.address}`);
  console.log(`spendable      : ${formatEther(balance)} (18-decimal Ethereum view)`);
  console.log(`bytecode       : ${(bytecode.length - 2) / 2} bytes`);

  // Guard 2: no funds, no point.
  if (balance === 0n) {
    fail("The deployer has no spendable balance on this network. Nothing was sent.",
      "Fund it first: python scripts/evm_funding_address.py <deployer 0x address> --check");
  }
  if (!args.confirm) {
    console.log("\nDRY RUN. Everything checks out and nothing was sent. Re-run with --confirm to deploy.");
    process.exit(0);
  }

  const factory = new ContractFactory(abi, bytecode, wallet);
  const overrides = {};
  if (args.legacy) {
    overrides.type = 0;
    overrides.gasPrice = BigInt(await provider.send("eth_gasPrice", []));
  }
  console.log("\nSending the deployment transaction...");
  const contract = await factory.deploy(overrides);
  const tx = contract.deploymentTransaction();
  console.log(`deployment tx  : ${tx.hash}`);

  const receipt = await Promise.race([
    tx.wait(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("Timed out after 3 minutes waiting for the receipt. Check the transaction hash above later.")), 180000)),
  ]);
  const address = await contract.getAddress();
  const code = await provider.getCode(address);
  if (receipt.status !== 1 || code === "0x") fail("The transaction was mined but no contract code exists at the address. Deployment failed.");

  const owner = await contract.owner();
  const total = await contract.totalRecords();
  console.log(`contract       : ${address}`);
  console.log(`block          : ${receipt.blockNumber}`);
  console.log(`owner          : ${owner}`);
  console.log(`records stored : ${total}`);

  mkdirSync("deployments", { recursive: true });
  const file = CHAIN_ID === 420420777 ? "deployments/portaldot-testnet.json" : `deployments/chain-${CHAIN_ID}.json`;
  writeFileSync(file, JSON.stringify({
    contract: "SentinelEvidenceRegistry", network: CHAIN_ID === 420420777 ? "Portaldot V3 Testnet" : `chain ${CHAIN_ID}`,
    chainId: CHAIN_ID, rpc: RPC, contractAddress: address, deploymentTxHash: tx.hash,
    blockNumber: receipt.blockNumber, deployer: wallet.address, deployedAt: new Date().toISOString(),
    compiler: "solc 0.8.26, evmVersion paris, optimizer 200 runs",
  }, null, 2) + "\n");
  console.log(`\nSaved public deployment details to contracts/${file} (no secrets in it).`);
  console.log("\nNext steps:");
  console.log(`  1. Put this line in backend/.env :  REGISTRY_ADDRESS=${address}`);
  console.log(`  2. python scripts/check_registry.py ${address}`);
  console.log("  3. Clear the key from this window:  Remove-Item Env:DEPLOYER_PRIVATE_KEY");
  process.exit(0);
} catch (error) {
  const text = String(error?.shortMessage ?? error?.message ?? error).replaceAll(key, "[hidden]");
  console.error(`\nERROR: ${text.slice(0, 600)}`);
  if (/insufficient funds|gas/i.test(text)) console.error("Hint: the deployer may need more tPOT. Try again with --legacy if the error mentions gas fees.");
  if (/invalid opcode|code|revert|rejected/i.test(text)) console.error("Hint: this may mean the chain needs a different compile target. Stop and send the exact error text.");
  process.exit(1);
}
