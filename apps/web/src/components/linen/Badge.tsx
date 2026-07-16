import { type ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  /** Optional status dot colour (hex). */
  color?: string | undefined;
  className?: string | undefined;
}

/** A bordered, mono-cased status pill. An optional coloured dot codes status. */
export function Badge({ children, color, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 border border-hairline px-2 py-0.5 font-mono text-mono-sm uppercase tracking-[0.1em] text-ink ${className}`}
    >
      {color ? (
        <span
          aria-hidden="true"
          className="h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: color }}
        />
      ) : null}
      {children}
    </span>
  );
}
