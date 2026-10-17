import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { before, describe, it } from "node:test";
import { createRequire } from "node:module";
import { BrowserProvider, ContractFactory, ZeroAddress, ZeroHash, sha256, toUtf8Bytes } from "ethers";

const ganache = createRequire(import.meta.url)("ganache");
const { abi, bytecode } = JSON.parse(readFileSync("build/SentinelEvidenceRegistry.json", "utf8"));

const id = (text) => sha256(toUtf8Bytes(`portal-sentinel:incident:${text}`));
const HASH_A = sha256(toUtf8Bytes("evidence A"));
const HASH_B = sha256(toUtf8Bytes("evidence B"));

let provider;
let owner, stranger, newOwner;

async function deploy() {
  const factory = new ContractFactory(abi, bytecode, owner);
  const contract = await factory.deploy();
  await contract.waitForDeployment();
  return contract;
}

// ethers decodes custom errors for us: err.revert.name / err.revert.args
const revertsWith = (name) => (err) => err?.revert?.name === name;

// The test node reports the revert reason on simulated calls but not when sending, so check both:
//   1. a simulated call fails with the exact custom error, and
//   2. the real transaction fails too (nothing is written).
async function expectRevert(contract, method, args, name, signer = owner) {
  const connected = contract.connect(signer);
  await assert.rejects(connected[method].staticCall(...args), revertsWith(name));
  await assert.rejects(connected[method](...args));
}

before(async () => {
  provider = new BrowserProvider(ganache.provider({ logging: { quiet: true }, chain: { hardfork: "shanghai" } }));
  [owner, stranger, newOwner] = await Promise.all([0, 1, 2].map((i) => provider.getSigner(i)));
});

describe("SentinelEvidenceRegistry", () => {
  it("records valid evidence, emits an event and stores the data", async () => {
    const c = await deploy();
    const incident = id("INC-1");
    const tx = await c.record(incident, HASH_A, 78);
    const receipt = await tx.wait();

    const event = receipt.logs.map((l) => c.interface.parseLog(l)).find((e) => e?.name === "EvidenceRecorded");
    assert.ok(event, "EvidenceRecorded event missing");
    assert.equal(event.args.incidentId, incident);
    assert.equal(event.args.evidenceHash, HASH_A);
    assert.equal(event.args.riskScore, 78n);
    assert.equal(event.args.recorder, await owner.getAddress());

    const stored = await c.get(incident);
    assert.equal(stored.evidenceHash, HASH_A);
    assert.equal(stored.riskScore, 78n);
    assert.equal(stored.recorder, await owner.getAddress());
    const block = await provider.getBlock(receipt.blockNumber);
    assert.equal(stored.recordedAt, BigInt(block.timestamp), "timestamp must come from the block");
    assert.equal(await c.totalRecords(), 1n);
    console.log(`      gas used by record(): ${receipt.gasUsed}`);
  });

  it("rejects a non-owner", async () => {
    const c = await deploy();
    await expectRevert(c, "record", [id("INC-2"), HASH_A, 50], "NotOwner", stranger);
    assert.equal(await c.totalRecords(), 0n);
  });

  it("rejects a duplicate incident and keeps the original record", async () => {
    const c = await deploy();
    const incident = id("INC-3");
    await (await c.record(incident, HASH_A, 40)).wait();
    await expectRevert(c, "record", [incident, HASH_B, 99], "AlreadyRecorded");
    assert.equal((await c.get(incident)).evidenceHash, HASH_A);
    assert.equal(await c.totalRecords(), 1n);
  });

  it("rejects invalid input", async () => {
    const c = await deploy();
    await expectRevert(c, "record", [id("INC-4"), HASH_A, 101], "InvalidRiskScore");
    await expectRevert(c, "record", [id("INC-4"), ZeroHash, 50], "EmptyHash");
    await expectRevert(c, "record", [ZeroHash, HASH_A, 50], "InvalidIncidentId");
    assert.equal(await c.totalRecords(), 0n);
  });

  it("accepts the boundary scores 0 and 100", async () => {
    const c = await deploy();
    await (await c.record(id("low"), HASH_A, 0)).wait();
    await (await c.record(id("high"), HASH_B, 100)).wait();
    assert.equal((await c.get(id("high"))).riskScore, 100n);
  });

  it("get reverts for an unknown incident", async () => {
    const c = await deploy();
    await assert.rejects(c.get(id("never")), revertsWith("NotFound"));
  });

  it("verify is true only for the exact recorded hash", async () => {
    const c = await deploy();
    const incident = id("INC-5");
    assert.equal(await c.verify(incident, HASH_A), false, "unknown incident must not verify");
    await (await c.record(incident, HASH_A, 60)).wait();
    assert.equal(await c.verify(incident, HASH_A), true);
    assert.equal(await c.verify(incident, HASH_B), false, "tampered evidence must not verify");
  });

  describe("two-step ownership", () => {
    it("only the owner can propose, and not to the zero address", async () => {
      const c = await deploy();
      await expectRevert(c, "transferOwnership", [await stranger.getAddress()], "NotOwner", stranger);
      await expectRevert(c, "transferOwnership", [ZeroAddress], "ZeroAddress");
    });

    it("only the proposed owner can accept; control then moves cleanly", async () => {
      const c = await deploy();
      const proposed = await newOwner.getAddress();
      await (await c.transferOwnership(proposed)).wait();
      assert.equal(await c.pendingOwner(), proposed);

      await expectRevert(c, "acceptOwnership", [], "NotPendingOwner", stranger);
      assert.equal(await c.owner(), await owner.getAddress(), "ownership must not move before acceptance");

      await (await c.connect(newOwner).acceptOwnership()).wait();
      assert.equal(await c.owner(), proposed);
      assert.equal(await c.pendingOwner(), ZeroAddress);

      await (await c.connect(newOwner).record(id("INC-6"), HASH_A, 30)).wait();
      await expectRevert(c, "record", [id("INC-7"), HASH_A, 30], "NotOwner", owner);
    });
  });
});
