"use client";

import { type ReactNode } from "react";

interface TabsProps {
  options: { value: string; label: ReactNode }[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function Tabs({ options, value, onChange, className = "" }: TabsProps) {
  return (
    <div role="tablist" className={`flex flex-wrap gap-8 ${className}`}>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.value)}
            className={`font-body text-label-sm uppercase tracking-[0.14em] pb-2 border-b-2 transition-colors cursor-pointer ${
              active ? "border-signal text-ink" : "border-transparent text-stone hover:text-ink"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
