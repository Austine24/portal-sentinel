import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { OriginBadge } from "../components/OriginBadge";
import { Page } from "../components/Page";
import { SeverityBadge } from "../components/SeverityBadge";
import { useAsync } from "../hooks/useAsync";
import { listIncidents } from "../lib/api";
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
  const load = useCallback(() => listIncidents(filter === "all" ? undefined : filter), [filter]);
  const { data, error, loading, reload } = useAsync(load);
  const rows = data ?? [];

  return (
    <Page>
      <h1 className="text-2xl font-semibold text-white">Incident Center</h1>

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

      {error && <ErrorNotice message={error} onRetry={reload} />}

      <GlassCard className="overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Incident</th>
              <th className="px-4 py-3">Account</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Detected</th>
              <th className="px-4 py-3">Data</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id} className="border-b border-white/5 transition hover:bg-white/[0.03]">
                <td className="px-4 py-3 font-mono text-xs text-cyan-300">
                  <Link to={`/incidents/${i.id}`}>{i.public_id}</Link>
                </td>
                <td className="px-4 py-3 text-slate-200">{i.title}</td>
                <td className="px-4 py-3 text-slate-400">{i.account}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 text-slate-200">{i.risk_score}</span>
                    <SeverityBadge score={i.risk_score} />
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-300">{STATUS_LABEL[i.status]}</td>
                <td className="px-4 py-3 text-slate-500">{new Date(i.detected_at).toLocaleString()}</td>
                <td className="px-4 py-3"><OriginBadge origin={i.data_origin} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <p className="p-6 text-sm text-slate-400">Loading...</p>}
        {!loading && !error && rows.length === 0 && (
          <p className="p-6 text-sm text-slate-400">No incidents with this status. Run detection from the dashboard.</p>
        )}
      </GlassCard>
    </Page>
  );
}
