import type { DataOrigin } from "../types";
import { DemoBadge } from "./DemoBadge";

export function OriginBadge({ origin }: { origin: DataOrigin }) {
  if (origin === "simulated") return <DemoBadge />;
  return (
    <span className="inline-flex items-center rounded-md border border-emerald-400/40 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-emerald-300">
      LIVE
    </span>
  );
}
