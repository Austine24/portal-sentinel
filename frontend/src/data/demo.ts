// ============================================================
// DEMO / SIMULATED DATA. NOT from Portaldot or any blockchain.
// Incidents now come from the API. Only chart data without a backend source remains here.
// ============================================================

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
