import { Activity, AlertTriangle, Radar, ShieldAlert } from "lucide-react";
import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DemoBadge } from "../components/DemoBadge";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { KpiCard } from "../components/KpiCard";
import { Page } from "../components/Page";
import { SeverityBadge } from "../components/SeverityBadge";
import { DEMO_ANOMALY_TREND } from "../data/demo";
import { useAsync } from "../hooks/useAsync";
import { listIncidents, syncIncidents } from "../lib/api";
import { STATUS_LABEL } from "../lib/risk";

export default function Dashboard() {
  const load = useCallback(() => listIncidents(), []);
  const { data, error, loading, reload } = useAsync(load);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  async function runDetection() {
    setSyncing(true);
    setSyncError(null);
    try {
      const result = await syncIncidents();
      setSyncMessage(`Detection finished: ${result.created} new, ${result.skipped} skipped (${result.data_origin} data).`);
      reload();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Detection failed.");
    } finally {
      setSyncing(false);
    }
  }

  const incidents = data ?? [];
  const active = incidents.filter((i) => i.status === "open" || i.status === "investigating").length;
  const highOrAbove = incidents.filter((i) => i.risk_score >= 60).length;

  return (
    <Page>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-white">Sentinel Overview</h1>
          <DemoBadge />
        </div>
        <button
          onClick={runDetection}
          disabled={syncing}
          className="rounded-xl bg-cyan-400/90 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 disabled:opacity-50"
        >
          {syncing ? "Running..." : "Run detection (simulated data)"}
        </button>
      </div>

      {syncMessage && <p className="text-sm text-slate-300">{syncMessage}</p>}
      {syncError && <ErrorNotice message={syncError} />}
      {error && <ErrorNotice message={error} onRetry={reload} />}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Active incidents" value={loading ? "..." : active} hint="Open or investigating" icon={<ShieldAlert size={20} />} />
        <KpiCard label="High or critical" value={loading ? "..." : highOrAbove} hint="Risk score 60 and above" icon={<AlertTriangle size={20} />} />
        <KpiCard label="Total incidents" value={loading ? "..." : incidents.length} hint="Stored in the database" icon={<Radar size={20} />} />
        <KpiCard label="Block height" value="Unavailable" hint="Not connected to Portaldot yet" icon={<Activity size={20} />} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <div className="mb-4 flex items-center gap-2">
            <h2 className="text-sm font-medium text-slate-300">Anomaly trend, last 24 hours</h2>
            <DemoBadge label="ILLUSTRATIVE DEMO DATA" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={DEMO_ANOMALY_TREND}>
                <defs>
                  <linearGradient id="anomalyFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis dataKey="hour" stroke="#64748b" fontSize={11} interval={3} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Area type="monotone" dataKey="anomalies" stroke="#22d3ee" strokeWidth={2} fill="url(#anomalyFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Recent incidents</h2>
          {!loading && incidents.length === 0 && !error && (
            <p className="text-sm text-slate-400">No incidents yet. Press "Run detection".</p>
          )}
          <ul className="space-y-3">
            {incidents.slice(0, 4).map((i) => (
              <li key={i.id}>
                <Link to={`/incidents/${i.id}`} className="block rounded-xl p-2 transition hover:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm text-slate-200">{i.title}</span>
                    <SeverityBadge score={i.risk_score} />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {i.public_id} · {STATUS_LABEL[i.status]}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </Page>
  );
}
