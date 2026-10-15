import { Brain, FileCheck2, Radar, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { DemoBadge } from "../components/DemoBadge";
import { GlassCard } from "../components/GlassCard";
import { Page } from "../components/Page";

const FEATURES = [
  { icon: Radar, title: "Monitor", text: "Observe network and account activity continuously." },
  { icon: Brain, title: "Detect", text: "Rules plus an anomaly model highlight unusual behaviour." },
  { icon: ShieldAlert, title: "Investigate", text: "Every alert becomes an incident with explained risk factors." },
  { icon: FileCheck2, title: "Verify", text: "Anchor an evidence fingerprint on-chain for independent checking." },
];

export default function Landing() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <Page>
        <div className="text-center">
          <DemoBadge label="PROTOTYPE" />
          <h1 className="mt-6 bg-gradient-to-r from-cyan-300 via-sky-400 to-violet-400 bg-clip-text text-5xl font-bold text-transparent md:text-6xl">
            Portal Sentinel
          </h1>
          <p className="mt-4 text-xl text-slate-200">Security Intelligence for the Portaldot Ecosystem</p>
          <p className="mt-2 text-slate-400">Monitor. Detect. Investigate. Verify.</p>
          <div className="mt-8 flex justify-center gap-3">
            <Link
              to="/dashboard"
              className="rounded-xl bg-cyan-400/90 px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-[0_0_24px_rgba(34,211,238,0.4)] transition hover:bg-cyan-300"
            >
              Open dashboard
            </Link>
            <Link
              to="/incidents"
              className="rounded-xl border border-white/15 px-5 py-2.5 text-sm text-slate-200 transition hover:bg-white/5"
            >
              View incidents
            </Link>
          </div>
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <GlassCard key={title}>
              <Icon className="text-cyan-300" size={22} />
              <h3 className="mt-3 font-semibold text-white">{title}</h3>
              <p className="mt-1 text-sm text-slate-400">{text}</p>
            </GlassCard>
          ))}
        </div>

        <p className="mt-10 text-center text-xs text-slate-500">
          This prototype shows the intended interface using simulated data. It is not connected to Portaldot yet.
        </p>
      </Page>
    </div>
  );
}
