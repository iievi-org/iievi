import { type ReactNode } from "react";

interface PillProps {
  children: ReactNode;
  variant?: "outline" | "ink" | "signal";
  className?: string;
}

export function Pill({ children, variant = "outline", className = "" }: PillProps) {
  const styles = {
    outline: "bg-transparent border border-hairline text-ink",
    ink: "bg-ink text-surface border border-ink",
    signal: "bg-signal text-surface border border-signal",
  }[variant];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 font-body text-label-sm uppercase tracking-[0.14em] ${styles} ${className}`}
    >
      {children}
    </span>
  );
}
