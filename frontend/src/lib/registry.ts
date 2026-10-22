/** Builds the data for the contract's record(bytes32,bytes32,uint8) call. Every argument is one 32-byte word. */
const BYTES32 = /^0x[0-9a-fA-F]{64}$/;

const word = (hex: string): string => hex.slice(2).toLowerCase();

export function encodeRecord(selector: string, incidentId: string, evidenceHash: string, riskScore: number): string {
  if (!/^0x[0-9a-fA-F]{8}$/.test(selector)) throw new Error("Bad function selector from the server.");
  if (!BYTES32.test(incidentId) || !BYTES32.test(evidenceHash)) throw new Error("Incident id and evidence hash must be 32-byte hex values.");
  if (!Number.isInteger(riskScore) || riskScore < 0 || riskScore > 100) throw new Error("Risk score must be a whole number from 0 to 100.");
  return selector + word(incidentId) + word(evidenceHash) + riskScore.toString(16).padStart(64, "0");
}
