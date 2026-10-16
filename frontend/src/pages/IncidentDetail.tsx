import { ArrowLeft, Link2 } from "lucide-react";
import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ErrorNotice } from "../components/ErrorNotice";
import { GlassCard } from "../components/GlassCard";
import { OriginBadge } from "../components/OriginBadge";
import { Page } from "../components/Page";
import { RiskGauge } from "../components/RiskGauge";
import { SeverityBadge } from "../components/SeverityBadge";
import { useAsync } from "../hooks/useAsync";
import { changeStatus, getIncident } from "../lib/api";
import { STATUS_LABEL } from "../lib/risk";
import type { Incident, IncidentStatus } from "../types";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const incidentId = Number(id);
  const load = useCallback(() => getIncident(incidentId), [incidentId]);
  const { data, error, loading, reload } = useAsync(load);

  // After a status change the API returns the fresh incident; show it straight away.
  const [updated, setUpdated] = useState<Incident | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const incident = updated && updated.id === incidentId ? updated : data;

  async function move(status: IncidentStatus) {
    setBusy(true);
    setActionError(null);
    try {
      setUpdated(await changeStatus(incidentId, status));
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not change status.");
    } finally {
      setBusy(false);
    }
  }

  const back = (
    <Link to="/incidents" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
      <ArrowLeft size={14} /> Incidents
    </Link>
  );

  if (!Number.isInteger(incidentId)) {
    return <Page>{back}<p className="text-slate-300">Invalid incident id.</p></Page>;
  }
  if (loading && !incident) {
    return <Page>{back}<p className="text-slate-400">Loading...</p></Page>;
  }
  if (error || !incident) {
    return <Page>{back}<ErrorNotice message={error ?? "Incident not found."} onRetry={reload} /></Page>;
  }

  return (
    <Page>
      {back}

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-white">{incident.title}</h1>
        <SeverityBadge score={incident.risk_score} />
        <OriginBadge origin={incident.data_origin} />
      </div>
      <p className="font-mono text-xs text-slate-500">
        {incident.public_id} · {STATUS_LABEL[incident.status]} · {incident.findings.map((f) => f.rule_id).join(", ")}
      </p>

      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="flex flex-col items-center justify-center gap-3">
          <RiskGauge score={incident.risk_score} />
          <p className="text-center text-xs text-slate-500">Account: {incident.account}</p>
          <p className="text-center text-xs text-slate-500">Anomaly model score: not available yet (model not trained)</p>
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
                    style={{ width: `${Math.min(100, f.weight)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>

      <GlassCard>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Rule evidence</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {incident.findings.map((f) => (
            <div key={f.rule_id} className="rounded-xl border border-white/10 p-3">
              <p className="text-sm text-slate-200">
                {f.rule_id} {f.name}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                strength {f.strength} · confidence {f.confidence}
              </p>
              <dl className="mt-2 space-y-1 text-xs">
                {Object.entries(f.evidence).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-4">
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="text-slate-300">{String(value)}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-2 text-xs text-slate-400">Suggested next step: {f.suggestion}</p>
            </div>
          ))}
        </div>
      </GlassCard>

      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <h2 className="mb-3 text-sm font-medium text-slate-300">Investigation</h2>
          <div className="flex flex-wrap gap-2">
            {incident.allowed_next.map((next) => (
              <button
                key={next}
                disabled={busy}
                onClick={() => move(next)}
                className="rounded-full border border-cyan-400/40 px-3 py-1 text-xs text-cyan-200 transition hover:bg-cyan-400/10 disabled:opacity-50"
              >
                Mark {STATUS_LABEL[next].toLowerCase()}
              </button>
            ))}
          </div>
          {actionError && <div className="mt-3"><ErrorNotice message={actionError} /></div>}

          <h2 className="mb-3 mt-6 text-sm font-medium text-slate-300">Timeline</h2>
          <ol className="space-y-3 border-l border-white/10 pl-4">
            {incident.events.map((t, index) => (
              <li key={`${t.at}-${index}`}>
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
            <div className="flex justify-between"><dt>Transaction</dt><dd>{incident.evidence.tx_hash ?? "none"}</dd></div>
          </dl>
          <button
            disabled
            title="Wallet and contract are not connected yet"
            className="mt-4 w-full cursor-not-allowed rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-500"
          >
            Record evidence on-chain (not connected yet)
          </button>
        </GlassCard>
      </div>
    </Page>
  );
}
