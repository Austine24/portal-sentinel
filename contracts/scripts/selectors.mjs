// Writes selectors.json: the 4-byte function ids and the event topic that the backend and frontend rely on.
import { readFileSync, writeFileSync } from "node:fs";
import { Interface } from "ethers";

const { abi } = JSON.parse(readFileSync("build/SentinelEvidenceRegistry.json", "utf8"));
const iface = new Interface(abi);
const functions = {};
for (const name of ["record", "get", "verify", "owner", "pendingOwner", "totalRecords", "transferOwnership", "acceptOwnership"]) {
  const fragment = iface.getFunction(name);
  functions[name] = { signature: fragment.format("sighash"), selector: fragment.selector };
}
const event = iface.getEvent("EvidenceRecorded");
const out = { contract: "SentinelEvidenceRegistry", functions, events: { EvidenceRecorded: { signature: event.format("sighash"), topic0: event.topicHash } } };
writeFileSync("selectors.json", JSON.stringify(out, null, 2) + "\n");
console.log(JSON.stringify(out, null, 2));
