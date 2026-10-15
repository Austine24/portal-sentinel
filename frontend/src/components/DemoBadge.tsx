export function DemoBadge({ label = "DEMO / SIMULATED" }: { label?: string }) {
  return (
    <span className="inline-flex items-center rounded-md border border-amber-400/40 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-amber-300">
      {label}
    </span>
  );
}
