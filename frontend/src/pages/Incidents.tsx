import { useState } from "react";
import { Link } from "react-router-dom";
import { DemoBadge } from "../components/DemoBadge";
import { GlassCard } from "../components/GlassCard";
import { Page } from "../components/Page";
import { SeverityBadge } from "../components/SeverityBadge";
import { DEMO_INCIDENTS } from "../data/demo";
import { STATUS_LABEL } from "../lib/risk";
import type { IncidentStatus } from "../types";

type Filter = IncidentStatus | "all";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "investigating", label: "Investigating" },
  { value: "confirmed", label: "Confirmed" },
  { value: "resolved", label: "Resolved" },
  { value: "false_positive", label: "False positive" },
];

export default function Incidents() {
  const [filter, setFilter] = useState<Filter>("all");
  const rows = DEMO_INCIDENTS.filter((i) => filter === "all" || i.status === filter);

  return (
    <Page>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">Incident Center</h1>
        <DemoBadge />
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-full border px-3 py-1 text-xs transition ${
              filter === f.value
                ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-200"
                : "border-white/10 text-slate-400 hover:bg-white/5"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <GlassCard className="overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Incident</th>
              <th className="px-4 py-3">Subject</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Detected</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id} className="border-b border-white/5 transition hover:bg-white/[0.03]">
                <td className="px-4 py-3 font-mono text-xs text-cyan-300">
                  <Link to={`/incidents/${i.id}`}>{i.id}</Link>
                </td>
                <td className="px-4 py-3 text-slate-200">{i.title}</td>
                <td className="px-4 py-3 text-slate-400">{i.subject}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 text-slate-200">{i.riskScore}</span>
                    <SeverityBadge score={i.riskScore} />
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-300">{STATUS_LABEL[i.status]}</td>
                <td className="px-4 py-3 text-slate-500">{new Date(i.detectedAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="p-6 text-sm text-slate-400">No incidents with this status.</p>}
      </GlassCard>
    </Page>
  );
}
