import type { ReactNode } from "react";
import { GlassCard } from "./GlassCard";

interface KpiCardProps {
  label: string;
  value: string | number;
  hint?: string;
  icon: ReactNode;
}

export function KpiCard({ label, value, hint, icon }: KpiCardProps) {
  return (
    <GlassCard>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        <div className="rounded-xl bg-cyan-400/10 p-2 text-cyan-300">{icon}</div>
      </div>
    </GlassCard>
  );
}
