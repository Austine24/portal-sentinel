import { LEVEL_LABEL, LEVEL_STYLE, riskLevel } from "../lib/risk";

export function RiskGauge({ score }: { score: number }) {
  const level = riskLevel(score);
  const color = LEVEL_STYLE[level].hex;
  const clamped = Math.max(0, Math.min(100, score));
  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          pathLength={100}
          strokeDasharray={`${clamped} ${100 - clamped}`}
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold text-white">{score}</span>
        <span className="text-xs text-slate-400">{LEVEL_LABEL[level]} risk</span>
      </div>
    </div>
  );
}
