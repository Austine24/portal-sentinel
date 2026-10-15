import type { IncidentStatus, RiskLevel } from "../types";

// Portal Sentinel's own analytical bands. Not a scientifically validated score.
export function riskLevel(score: number): RiskLevel {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "moderate";
  if (score >= 20) return "guarded";
  return "low";
}

export const LEVEL_LABEL: Record<RiskLevel, string> = {
  low: "Low",
  guarded: "Guarded",
  moderate: "Moderate",
  high: "High",
  critical: "Critical",
};

// Full class names so Tailwind can see them at build time.
export const LEVEL_STYLE: Record<
  RiskLevel,
  { badge: string; hex: string }
> = {
  low: { badge: "bg-emerald-500/10 text-emerald-300 border-emerald-400/30", hex: "#34d399" },
  guarded: { badge: "bg-sky-500/10 text-sky-300 border-sky-400/30", hex: "#38bdf8" },
  moderate: { badge: "bg-amber-500/10 text-amber-300 border-amber-400/30", hex: "#fbbf24" },
  high: { badge: "bg-orange-500/10 text-orange-300 border-orange-400/30", hex: "#fb923c" },
  critical: { badge: "bg-rose-500/10 text-rose-300 border-rose-400/30", hex: "#fb7185" },
};

export const STATUS_LABEL: Record<IncidentStatus, string> = {
  open: "Open",
  investigating: "Investigating",
  confirmed: "Confirmed",
  resolved: "Resolved",
  false_positive: "False positive",
};
