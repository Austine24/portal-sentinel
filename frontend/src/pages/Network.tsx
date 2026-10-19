import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { KpiCard } from "../components/KpiCard";
import { OriginBadge } from "../components/OriginBadge";
import { Page } from "../components/Page";
import { SeverityBadge } from "../components/SeverityBadge";
import { useAsync } from "../hooks/useAsync";
import { getNetworkHistory, refreshNetwork } from "../lib/api";

const AUTO_MS = 30_000;

export default function NetworkPage() {
  const load = useCallback(async () => {
    const health = await refreshNetwork();
    const history = await getNetworkHistory(60);
    return { health, history };
  }, []);
  const { data, error, loading, reload } = useAsync(load);
  const [auto, setAuto] = useState(false);

  useEffect(() => {
    if (!auto) return;
    const id = setInterval(reload, AUTO_MS);
    return () => clearInterval(id);
  }, [auto, reload]);

  const snap = data?.health.snapshot;
  const authors = snap ? Object.entries(snap.authors).sort(([a], [b]) => Number(a) - Number(b)) : [];
  const produced = authors.reduce((sum, [, count]) => sum + count, 0);
  const chart = (data?.history ?? []).map((p) => ({
    time: new Date(p.taken_at).toLocaleTimeString(),
    "Finality lag": p.finality_lag,
    "Missed slots": p.missed_slots,
  }));

  return (
    <Page>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-white">Network Health</h1>
          {snap && <OriginBadge origin={snap.data_origin} />}
          {data && <SeverityBadge score={data.health.risk_score} />}
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
            Auto-refresh every 30 s
          </label>
          <button
            onClick={reload}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-cyan-400/90 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {error && <ErrorNotice message={error} onRetry={reload} />}
      {loading && !data && <p className="text-sm text-slate-400">Reading the Portaldot testnet...</p>}

      {snap && data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Best block" value={snap.best_block.toLocaleString()} hint={snap.chain_name ?? "chain name unavailable"} icon={<span className="text-xs">#</span>} />
            <KpiCard label="Finalized" value={snap.finalized_block.toLocaleString()} hint={`finality lag ${snap.finality_lag} blocks`} icon={<span className="text-xs">✓</span>} />
            <KpiCard label="Newest block age" value={snap.block_age_s === null ? "n/a" : `${snap.block_age_s.toFixed(0)} s`} hint="derived from the slot number" icon={<span className="text-xs">⏱</span>} />
            <KpiCard label="Missed slots" value={snap.missed_slots} hint={`in the last ${snap.window_blocks} blocks`} icon={<span className="text-xs">∅</span>} />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <GlassCard>
              <h2 className="mb-3 text-sm font-medium text-slate-300">Who produced the last {snap.window_blocks} blocks</h2>
              {authors.length === 0 && <p className="text-sm text-slate-400">Author information is not available for this chain.</p>}
              <ul className="space-y-3">
                {authors.map(([index, count]) => (
                  <li key={index}>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-200">Block author #{index}</span>
                      <span className="text-slate-500">{count} blocks ({produced ? Math.round((count / produced) * 100) : 0}%)</span>
                    </div>
                    <div className="mt-1 h-1.5 rounded-full bg-white/10">
                      <div className="h-1.5 rounded-full bg-gradient-to-r from-cyan-400 to-violet-400" style={{ width: `${produced ? (count / produced) * 100 : 0}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[11px] text-slate-500">
                {snap.distinct_authors} distinct author{snap.distinct_authors === 1 ? "" : "s"} observed
                {snap.peers !== null ? `. The queried node reports ${snap.peers} peer${snap.peers === 1 ? "" : "s"}.` : "."}
              </p>
            </GlassCard>

            <GlassCard className="lg:col-span-2">
              <h2 className="mb-3 text-sm font-medium text-slate-300">Health alerts</h2>
              {data.health.findings.length === 0 ? (
                <p className="text-sm text-emerald-300">
                  No alerts. Finality is {snap.finality_lag} blocks behind, {snap.missed_slots} slots were missed, and every
                  block author seen earlier is still producing.
                </p>
              ) : (
                <ul className="space-y-3">
                  {data.health.findings.map((f) => (
                    <li key={f.rule_id} className="rounded-xl border border-amber-400/30 bg-amber-400/5 p-3">
                      <p className="text-sm text-slate-200">{f.rule_id} {f.name} <span className="text-xs text-slate-500">strength {f.strength}, confidence {f.confidence}</span></p>
                      <p className="mt-1 text-xs text-slate-400">{f.summary}</p>
                      <p className="mt-1 text-xs text-slate-500">Next step: {f.suggestion}</p>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-[11px] text-slate-500">{data.health.note}</p>
            </GlassCard>
          </div>

          <GlassCard>
            <h2 className="mb-3 text-sm font-medium text-slate-300">History ({chart.length} snapshot{chart.length === 1 ? "" : "s"})</h2>
            {chart.length < 2 ? (
              <p className="text-sm text-slate-400">History builds as snapshots are taken. Leave the app open or press Refresh again.</p>
            ) : (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chart}>
                    <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                    <Line type="monotone" dataKey="Finality lag" stroke="#22d3ee" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Missed slots" stroke="#fb923c" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </GlassCard>
        </>
      )}
    </Page>
  );
}
