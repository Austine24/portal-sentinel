import { useCallback, useEffect } from "react";
import { useAsync } from "../hooks/useAsync";
import { refreshNetwork } from "../lib/api";

const REFRESH_MS = 60_000;

/** Top-bar indicator. It also keeps taking snapshots while the app is open, which builds the history the rules compare against. */
export function ConnectionStatus() {
  const load = useCallback(() => refreshNetwork(), []);
  const { data, error, loading, reload } = useAsync(load);

  useEffect(() => {
    const id = setInterval(reload, REFRESH_MS);
    return () => clearInterval(id);
  }, [reload]);

  let dot = "bg-slate-500";
  let text = "checking...";
  if (error) {
    dot = "bg-rose-400";
    text = "unreachable";
  } else if (data) {
    const alerts = data.findings.length;
    dot = alerts > 0 ? "bg-amber-400" : "bg-emerald-400";
    text = `connected, block ${data.snapshot.best_block.toLocaleString()}${alerts > 0 ? `, ${alerts} alert${alerts > 1 ? "s" : ""}` : ""}`;
  }

  return (
    <div className="flex items-center gap-3 text-sm text-slate-300">
      <span className={`inline-block h-2 w-2 rounded-full ${dot}`} />
      Portaldot testnet: <span className="text-slate-400">{loading && !data ? "checking..." : text}</span>
    </div>
  );
}
