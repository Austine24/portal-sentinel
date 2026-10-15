import type { Incident } from "../types";

// ============================================================
// DEMO / SIMULATED DATA. NOT from Portaldot or any blockchain.
// Replace with real API data as the backend comes online.
// ============================================================

export const DEMO_INCIDENTS: Incident[] = [
  {
    id: "DEMO-001",
    title: "Transaction burst from a single wallet",
    subject: "demo-wallet-A",
    subjectType: "wallet",
    riskScore: 78,
    anomalyScore: 0.79,
    detectedAt: "2026-10-14T13:40:00Z",
    status: "open",
    rule: { id: "SR-001", name: "Transaction Burst" },
    summary:
      "Activity deviates strongly from this wallet's own history. This is anomalous behaviour that requires investigation, not proof of malicious intent.",
    factors: [
      { label: "Transaction frequency", detail: "12.4x above the wallet's historical baseline", weight: 40 },
      { label: "Transaction value", detail: "5.8x above the usual range", weight: 25 },
      { label: "New contract exposure", detail: "First interaction with 9 contracts in one hour", weight: 20 },
      { label: "Failed transactions", detail: "Failure rate 30% vs 3% usual", weight: 15 },
    ],
    timeline: [
      { at: "2026-10-14T13:31:00Z", text: "Burst begins: transactions per minute rise sharply" },
      { at: "2026-10-14T13:40:00Z", text: "Rule SR-001 triggered; anomaly model scored the hour 0.79" },
      { at: "2026-10-14T13:41:00Z", text: "Incident DEMO-001 created with status Open" },
    ],
    evidence: { anchored: false },
  },
  {
    id: "DEMO-002",
    title: "Unusual value movement",
    subject: "demo-wallet-B",
    subjectType: "wallet",
    riskScore: 63,
    anomalyScore: 0.66,
    detectedAt: "2026-10-14T11:12:00Z",
    status: "investigating",
    rule: { id: "SR-002", name: "Value Anomaly" },
    summary: "A single transfer is far above this wallet's normal range.",
    factors: [
      { label: "Transaction value", detail: "9.1x above the usual maximum", weight: 60 },
      { label: "New counterparty", detail: "Recipient never seen before", weight: 40 },
    ],
    timeline: [
      { at: "2026-10-14T11:12:00Z", text: "Rule SR-002 triggered" },
      { at: "2026-10-14T11:30:00Z", text: "Investigator took the incident" },
    ],
    evidence: { anchored: false },
  },
  {
    id: "DEMO-003",
    title: "Sudden spread across many contracts",
    subject: "demo-contract-X",
    subjectType: "contract",
    riskScore: 47,
    anomalyScore: 0.58,
    detectedAt: "2026-10-14T09:05:00Z",
    status: "open",
    rule: { id: "SR-003", name: "New Contract Exposure" },
    summary: "Interaction pattern with this contract changed compared with earlier days.",
    factors: [
      { label: "Unique callers", detail: "4.2x the usual daily count", weight: 55 },
      { label: "Call burst", detail: "Calls concentrated in 20 minutes", weight: 45 },
    ],
    timeline: [{ at: "2026-10-14T09:05:00Z", text: "Rule SR-003 triggered" }],
    evidence: { anchored: false },
  },
  {
    id: "DEMO-004",
    title: "Off-hours activity",
    subject: "demo-wallet-C",
    subjectType: "wallet",
    riskScore: 31,
    anomalyScore: 0.44,
    detectedAt: "2026-10-13T23:50:00Z",
    status: "false_positive",
    rule: { id: "SR-005", name: "Activity Timing" },
    summary: "Activity outside this wallet's usual hours. Marked as a false positive after review.",
    factors: [{ label: "Time-of-day pattern", detail: "Active at hours with no earlier activity", weight: 100 }],
    timeline: [
      { at: "2026-10-13T23:50:00Z", text: "Rule SR-005 triggered" },
      { at: "2026-10-14T08:00:00Z", text: "Closed as false positive" },
    ],
    evidence: { anchored: false },
  },
  {
    id: "DEMO-005",
    title: "Repeated failed transactions",
    subject: "demo-wallet-D",
    subjectType: "wallet",
    riskScore: 84,
    anomalyScore: 0.88,
    detectedAt: "2026-10-14T12:20:00Z",
    status: "confirmed",
    rule: { id: "SR-006", name: "Repeated Failures" },
    summary: "A long run of failed calls to the same contract.",
    factors: [
      { label: "Failure rate", detail: "92% of calls failed vs 4% usual", weight: 70 },
      { label: "Call frequency", detail: "6.7x above baseline", weight: 30 },
    ],
    timeline: [
      { at: "2026-10-14T12:20:00Z", text: "Rule SR-006 triggered" },
      { at: "2026-10-14T12:45:00Z", text: "Confirmed by investigator" },
    ],
    evidence: { anchored: false },
  },
];

// DEMO / SIMULATED hourly anomaly counts for the last 24 hours
export const DEMO_ANOMALY_TREND = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, "0")}:00`,
  anomalies: [1, 0, 2, 1, 1, 0, 0, 3, 2, 1, 2, 4, 2, 1, 3, 2, 5, 3, 2, 6, 4, 3, 7, 9][i],
  risk: [12, 8, 18, 14, 12, 7, 6, 28, 22, 15, 24, 38, 25, 17, 33, 27, 46, 35, 26, 55, 42, 36, 62, 78][i],
}));

// DEMO / SIMULATED feature contributions for the AI page
export const DEMO_FEATURE_CONTRIBUTIONS = [
  { feature: "Transactions per hour", share: 34 },
  { feature: "Total value per hour", share: 27 },
  { feature: "Unique counterparties", share: 19 },
  { feature: "Failed-transaction rate", share: 12 },
  { feature: "Time-of-day pattern", share: 8 },
];
