import { type ReactNode } from "react";

export function SectionLabel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <p className={`font-mono text-mono-sm uppercase tracking-[0.14em] text-stone ${className}`}>
      {children}
    </p>
  );
}
