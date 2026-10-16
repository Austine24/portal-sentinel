import { useCallback } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DemoBadge } from "../components/DemoBadge";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { Page } from "../components/Page";
import { DEMO_FEATURE_CONTRIBUTIONS } from "../data/demo";
import { useAsync } from "../hooks/useAsync";
import { listIncidents } from "../lib/api";

export default function AiIntelligence() {
  const load = useCallback(() => listIncidents(), []);
  const { data, error, reload } = useAsync(load);
  const detections = data ?? [];

  return (
    <Page>
      <h1 className="text-2xl font-semibold text-white">AI Intelligence</h1>

      <GlassCard>
        <p className="text-sm text-slate-300">
          Portal Sentinel uses behavioural analysis to identify activity that deviates significantly from historical
          patterns. An anomaly is not automatically proof of malicious behaviour.
        </p>
      </GlassCard>

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <h2 className="text-sm font-medium text-slate-300">Model status</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Rule engine</dt><dd className="text-slate-200">Active (2 rules)</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Isolation Forest</dt><dd className="text-slate-200">Planned, not trained</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Training data</dt><dd className="text-slate-200">None yet</dd></div>
          </dl>
        </GlassCard>

        <GlassCard className="lg:col-span-2">
          <div className="mb-3 flex items-center gap-2">
            <h2 className="text-sm font-medium text-slate-300">Feature contribution (illustrative)</h2>
            <DemoBadge label="ILLUSTRATIVE DEMO DATA" />
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DEMO_FEATURE_CONTRIBUTIONS} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={11} unit="%" />
                <YAxis type="category" dataKey="feature" stroke="#94a3b8" fontSize={11} width={140} />
                <Tooltip
                  contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }}
                />
                <Bar dataKey="share" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Recent rule detections</h2>
        {error && <ErrorNotice message={error} onRetry={reload} />}
        {!error && detections.length === 0 && (
          <p className="text-sm text-slate-400">No detections yet. Run detection from the dashboard.</p>
        )}
        <ul className="divide-y divide-white/5">
          {detections.map((i) => (
            <li key={i.id} className="py-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-200">
                  {i.title} <span className="text-slate-500">({i.public_id})</span>
                </span>
                <span className="font-mono text-xs text-cyan-300">risk {i.risk_score}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {i.findings.map((f) => `${f.rule_id} strength ${f.strength}`).join(" · ")}
              </p>
            </li>
          ))}
        </ul>
      </GlassCard>
    </Page>
  );
}
