import { ArrowLeft, Link2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { DemoBadge } from "../components/DemoBadge";
import { GlassCard } from "../components/GlassCard";
import { Page } from "../components/Page";
import { RiskGauge } from "../components/RiskGauge";
import { SeverityBadge } from "../components/SeverityBadge";
import { DEMO_INCIDENTS } from "../data/demo";
import { STATUS_LABEL } from "../lib/risk";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const incident = DEMO_INCIDENTS.find((i) => i.id === id);

  if (!incident) {
    return (
      <Page>
        <p className="text-slate-300">Incident not found.</p>
        <Link to="/incidents" className="text-cyan-300">
          Back to incidents
        </Link>
      </Page>
    );
  }

  return (
    <Page>
      <Link to="/incidents" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
        <ArrowLeft size={14} /> Incidents
      </Link>

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">{incident.title}</h1>
        <SeverityBadge score={incident.riskScore} />
        <DemoBadge />
      </div>
      <p className="font-mono text-xs text-slate-500">
        {incident.id} · {incident.rule.id} {incident.rule.name} · {STATUS_LABEL[incident.status]}
      </p>

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="flex flex-col items-center justify-center gap-3">
          <RiskGauge score={incident.riskScore} />
          <p className="text-xs text-slate-400">Anomaly score {incident.anomalyScore.toFixed(2)} (0 to 1)</p>
          <p className="text-center text-xs text-slate-500">
            Subject: {incident.subject} ({incident.subjectType})
          </p>
        </GlassCard>

        <GlassCard className="lg:col-span-2">
          <h2 className="text-sm font-medium text-slate-300">Why this was flagged</h2>
          <p className="mt-2 text-sm text-slate-400">{incident.summary}</p>
          <ul className="mt-4 space-y-3">
            {incident.factors.map((f) => (
              <li key={f.label}>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-200">{f.label}</span>
                  <span className="text-slate-500">{f.weight}% of score</span>
                </div>
                <p className="text-xs text-slate-400">{f.detail}</p>
                <div className="mt-1 h-1.5 rounded-full bg-white/10">
                  <div
                    className="h-1.5 rounded-full bg-gradient-to-r from-cyan-400 to-violet-400"
                    style={{ width: `${f.weight}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <h2 className="mb-3 text-sm font-medium text-slate-300">Timeline</h2>
          <ol className="space-y-3 border-l border-white/10 pl-4">
            {incident.timeline.map((t) => (
              <li key={t.at + t.text}>
                <p className="text-xs text-slate-500">{new Date(t.at).toLocaleString()}</p>
                <p className="text-sm text-slate-200">{t.text}</p>
              </li>
            ))}
          </ol>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <Link2 size={16} className="text-cyan-300" /> On-chain evidence
          </div>
          <p className="mt-3 text-sm text-slate-400">
            Status:{" "}
            <span className={incident.evidence.anchored ? "text-emerald-300" : "text-slate-200"}>
              {incident.evidence.anchored ? "Anchored" : "Not anchored"}
            </span>
          </p>
          <dl className="mt-3 space-y-1 text-xs text-slate-500">
            <div className="flex justify-between"><dt>Evidence hash</dt><dd>computed when anchoring</dd></div>
            <div className="flex justify-between"><dt>Contract</dt><dd>not deployed yet</dd></div>
            <div className="flex justify-between"><dt>Transaction</dt><dd>none</dd></div>
          </dl>
          <button
            disabled
            title="Wallet and contract are not connected in this prototype"
            className="mt-4 w-full cursor-not-allowed rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-500"
          >
            Record evidence on-chain (not connected yet)
          </button>
        </GlassCard>
      </div>
    </Page>
  );
}
