// Compiles contracts/*.sol with the solc compiler packaged in node_modules (no downloads).
// evmVersion "paris" avoids the PUSH0 opcode so the bytecode runs on older EVMs too.
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const solc = createRequire(import.meta.url)("solc");
const NAME = "SentinelEvidenceRegistry";
const source = readFileSync(`contracts/${NAME}.sol`, "utf8");

const input = {
  language: "Solidity",
  sources: { [`${NAME}.sol`]: { content: source } },
  settings: {
    evmVersion: "paris",
    optimizer: { enabled: true, runs: 200 },
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));
const problems = (output.errors ?? []).filter((e) => e.severity === "error");
const warnings = (output.errors ?? []).filter((e) => e.severity === "warning");
warnings.forEach((w) => console.warn(w.formattedMessage));
if (problems.length > 0) {
  problems.forEach((p) => console.error(p.formattedMessage));
  process.exit(1);
}

const contract = output.contracts[`${NAME}.sol`][NAME];
mkdirSync("build", { recursive: true });
writeFileSync(
  `build/${NAME}.json`,
  JSON.stringify({ abi: contract.abi, bytecode: "0x" + contract.evm.bytecode.object }, null, 2),
);
console.log(`compiled ${NAME} (${contract.evm.bytecode.object.length / 2} bytes, solc ${solc.version()})`);
