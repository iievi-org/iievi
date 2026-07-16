import { type ReactNode } from "react";

/**
 * Minimal CSS-only tooltip: shown on hover/focus of the wrapped trigger.
 * The label is also exposed to assistive tech via the trigger's own aria-label.
 */
export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <span className="group/tt relative inline-flex">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-50 mt-1 -translate-x-1/2 whitespace-nowrap border border-hairline bg-ink px-2 py-1 font-mono text-mono-sm text-surface opacity-0 transition-opacity duration-150 group-hover/tt:opacity-100 group-focus-within/tt:opacity-100"
      >
        {label}
      </span>
    </span>
  );
}
