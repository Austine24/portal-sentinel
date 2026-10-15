export type RiskLevel = "low" | "guarded" | "moderate" | "high" | "critical";

export type IncidentStatus =
  | "open"
  | "investigating"
  | "confirmed"
  | "resolved"
  | "false_positive";

export interface RiskFactor {
  label: string;
  detail: string;
  weight: number; // share of the risk score, 0-100
}

export interface TimelineEntry {
  at: string; // ISO date string
  text: string;
}

export interface Incident {
  id: string;
  title: string;
  subject: string;
  subjectType: "wallet" | "contract";
  riskScore: number; // 0-100
  anomalyScore: number; // 0-1, higher = more unusual
  detectedAt: string; // ISO date string
  status: IncidentStatus;
  rule: { id: string; name: string };
  summary: string;
  factors: RiskFactor[];
  timeline: TimelineEntry[];
  evidence: { anchored: boolean; txHash?: string };
}
