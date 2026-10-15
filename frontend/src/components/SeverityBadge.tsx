import { LEVEL_LABEL, LEVEL_STYLE, riskLevel } from "../lib/risk";

export function SeverityBadge({ score }: { score: number }) {
  const level = riskLevel(score);
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${LEVEL_STYLE[level].badge}`}
    >
      {LEVEL_LABEL[level]}
    </span>
  );
}
