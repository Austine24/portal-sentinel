import { Activity, AlertTriangle, Radar, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DemoBadge } from "../components/DemoBadge";
import { GlassCard } from "../components/GlassCard";
import { KpiCard } from "../components/KpiCard";
import { Page } from "../components/Page";
import { SeverityBadge } from "../components/SeverityBadge";
import { DEMO_ANOMALY_TREND, DEMO_INCIDENTS } from "../data/demo";
import { STATUS_LABEL } from "../lib/risk";

export default function Dashboard() {
  const active = DEMO_INCIDENTS.filter((i) => i.status === "open" || i.status === "investigating");
  const highOrAbove = DEMO_INCIDENTS.filter((i) => i.riskScore >= 60).length;
  const anomalies24h = DEMO_ANOMALY_TREND.reduce((sum, p) => sum + p.anomalies, 0);
  const recent = [...DEMO_INCIDENTS]
    .sort((a, b) => b.detectedAt.localeCompare(a.detectedAt))
    .slice(0, 4);

  return (
    <Page>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">Sentinel Overview</h1>
        <DemoBadge />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Active incidents" value={active.length} hint="Open or investigating" icon={<ShieldAlert size={20} />} />
        <KpiCard label="High or critical" value={highOrAbove} hint="Risk score 60 and above" icon={<AlertTriangle size={20} />} />
        <KpiCard label="Anomalies (24h)" value={anomalies24h} hint="Flagged by rules or model" icon={<Radar size={20} />} />
        <KpiCard label="Block height" value="Unavailable" hint="Not connected to Portaldot yet" icon={<Activity size={20} />} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Anomaly trend, last 24 hours</h2>
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
          <ul className="space-y-3">
            {recent.map((i) => (
              <li key={i.id}>
                <Link to={`/incidents/${i.id}`} className="block rounded-xl p-2 transition hover:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm text-slate-200">{i.title}</span>
                    <SeverityBadge score={i.riskScore} />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {i.id} · {STATUS_LABEL[i.status]}
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
