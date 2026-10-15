import type { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

export function GlassCard({ children, className = "" }: GlassCardProps) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-[0_0_40px_-12px_rgba(34,211,238,0.25)] backdrop-blur-md ${className}`}
    >
      {children}
    </div>
  );
}
