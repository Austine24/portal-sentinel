import { useCallback } from "react";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { OriginBadge } from "../components/OriginBadge";
import { Page } from "../components/Page";
import { useAsync } from "../hooks/useAsync";
import { getModelStatus, listIncidents } from "../lib/api";

const SHIFT_FIELDS: { key: string; label: string }[] = [
  { key: "tx_count_vs_baseline", label: "Transactions per hour" },
  { key: "total_value_vs_baseline", label: "Total value per hour" },
  { key: "unique_counterparties_vs_baseline", label: "Distinct counterparties" },
];

export default function AiIntelligence() {
  const loadStatus = useCallback(() => getModelStatus(), []);
  const loadIncidents = useCallback(() => listIncidents(), []);
  const status = useAsync(loadStatus);
  const incidents = useAsync(loadIncidents);

  const detections = incidents.data ?? [];
  // the newest incident that the anomaly model flagged
  const latest = detections.find((i) => i.findings.some((f) => f.rule_id === "ML-001"));
  const finding = latest?.findings.find((f) => f.rule_id === "ML-001");
  const shifts = SHIFT_FIELDS.map(({ key, label }) => {
    const value = finding?.evidence[key];
    return { label, value: typeof value === "number" ? value : null };
  });
  const maxLog = Math.max(1, ...shifts.map((s) => Math.log10((s.value ?? 1) + 1)));

  return (
    <Page>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">AI Intelligence</h1>
        {status.data && <OriginBadge origin={status.data.data_origin} />}
      </div>

      <GlassCard>
        <p className="text-sm text-slate-300">
          Portal Sentinel uses behavioural analysis to identify activity that deviates significantly from historical
          patterns. An anomaly is not automatically proof of malicious behaviour.
        </p>
      </GlassCard>

      {status.error && <ErrorNotice message={status.error} onRetry={status.reload} />}

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <h2 className="text-sm font-medium text-slate-300">Model status</h2>
          {status.loading && !status.data && <p className="mt-3 text-sm text-slate-400">Training...</p>}
          {status.data && (
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Rules active</dt><dd className="text-slate-200">{status.data.rules.length}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Isolation Forest</dt><dd className="text-slate-200">{status.data.trained ? "Trained" : "Not trained"}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Training examples</dt><dd className="text-slate-200">{status.data.training_rows}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Accounts learned from</dt><dd className="text-slate-200">{status.data.accounts}</dd></div>
              {status.data.reason && <p className="text-xs text-amber-300">{status.data.reason}</p>}
              <p className="pt-2 text-xs text-slate-500">{status.data.note}</p>
            </dl>
          )}
        </GlassCard>

        <GlassCard className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-medium text-slate-300">
            Why the model flagged the latest detection
            {latest && <span className="ml-2 font-mono text-xs text-slate-500">{latest.public_id}</span>}
          </h2>
          {!finding && <p className="text-sm text-slate-400">No detection flagged by the model yet. Run detection from the dashboard.</p>}
          {finding && (
            <>
              <p className="mb-4 text-xs text-slate-400">{finding.summary}</p>
              <ul className="space-y-3">
                {shifts.map((s) => (
                  <li key={s.label}>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-200">{s.label}</span>
                      <span className="font-mono text-cyan-300">{s.value === null ? "n/a" : `${s.value}x usual`}</span>
                    </div>
                    <div className="mt-1 h-1.5 rounded-full bg-white/10">
                      <div
                        className="h-1.5 rounded-full bg-gradient-to-r from-cyan-400 to-violet-400"
                        style={{ width: `${s.value === null ? 0 : (Math.log10(s.value + 1) / maxLog) * 100}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[11px] text-slate-500">Bars use a logarithmic scale so very large and moderate shifts are both visible.</p>
            </>
          )}
        </GlassCard>
      </div>

      <GlassCard>
        <div className="mb-3 flex items-center gap-2">
          <h2 className="text-sm font-medium text-slate-300">Recent detections</h2>
          {detections[0] && <OriginBadge origin={detections[0].data_origin} />}
        </div>
        {incidents.error && <ErrorNotice message={incidents.error} onRetry={incidents.reload} />}
        {!incidents.error && detections.length === 0 && (
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
