"use client";

import { useInView, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

interface Parsed {
  prefix: string;
  num: number;
  suffix: string;
  isNumeric: boolean;
  raw: string;
}

function parseValue(value: string): Parsed {
  const match = value.match(/^([^\d.-]*)([\d.,]+)(.*)$/);
  if (!match) return { prefix: "", num: 0, suffix: value, isNumeric: false, raw: "" };
  const prefix = match[1] ?? "";
  const raw = match[2] ?? "";
  const suffix = match[3] ?? "";
  const num = Number(raw.replace(/,/g, ""));
  if (Number.isNaN(num)) return { prefix: "", num: 0, suffix: value, isNumeric: false, raw: "" };
  return { prefix, num, suffix, isNumeric: true, raw };
}

function formatNumber(n: number, template: string): string {
  if (template.includes(",")) return Math.round(n).toLocaleString("en-IN");
  if (template.includes(".")) return n.toFixed(1);
  return Math.round(n).toString();
}

/** A big display numeral that counts up on scroll into view (Indian locale). */
export function Stat({ value, label }: { value: string; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const reduce = useReducedMotion();
  const parsed = parseValue(value);
  const [display, setDisplay] = useState(
    parsed.isNumeric ? `${parsed.prefix}0${parsed.suffix}` : value,
  );

  useEffect(() => {
    if (!inView || !parsed.isNumeric) {
      if (!parsed.isNumeric) setDisplay(value);
      return;
    }
    if (reduce) {
      setDisplay(value);
      return;
    }
    const duration = 1400;
    const start = performance.now();
    let raf = 0;
    const tick = (t: number): void => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(`${parsed.prefix}${formatNumber(parsed.num * eased, parsed.raw)}${parsed.suffix}`);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, reduce, value]);

  return (
    <div ref={ref} className="border-b border-hairline pb-4">
      <p className="font-display text-stat-numeral text-ink">{display}</p>
      <p className="font-mono text-mono-sm uppercase tracking-[0.04em] text-stone mt-2">{label}</p>
    </div>
  );
}
