// Key-free diagnostic: asks the testnet node WHY a deployment fails.
// It needs NO private key. It only sends read-only RPC calls (eth_estimateGas / eth_call).
import { readFileSync } from "node:fs";

const RPC = "https://test-evm-rpc-v3.portaldot.dev";
const FROM = "0x7daB6e3E7049c8371E962BEfC2bA4D8b4e56cf0A"; // public deployer address
const { bytecode } = JSON.parse(readFileSync("build/SentinelEvidenceRegistry.json", "utf8"));

async function rpc(method, params) {
  const res = await fetch(RPC, {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "portal-sentinel-diagnose/0.1" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  const text = await res.text();
  return `HTTP ${res.status}: ${text.slice(0, 600)}`;
}

console.log("--- gasPrice");
console.log(await rpc("eth_gasPrice", []));
console.log("--- nonce");
console.log(await rpc("eth_getTransactionCount", [FROM, "latest"]));
console.log("--- estimateGas for the real contract (" + (bytecode.length - 2) / 2 + " bytes)");
console.log(await rpc("eth_estimateGas", [{ from: FROM, data: bytecode }]));
console.log("--- eth_call (simulated deploy)");
console.log(await rpc("eth_call", [{ from: FROM, data: bytecode }, "latest"]));
console.log("--- estimateGas for a tiny contract that just returns (control test)");
console.log(await rpc("eth_estimateGas", [{ from: FROM, data: "0x600a600c600039600a6000f3602a60005260206000f3" }]));
