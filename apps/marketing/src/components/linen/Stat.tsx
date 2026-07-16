import { useEffect, useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";

interface StatProps {
  value: string; // e.g. "3s", "₹138", "92%", "10,000+"
  label: string;
}

// Parse a value into prefix + number + suffix for animation
function parseValue(value: string) {
  const match = value.match(/^([^\d.-]*)([\d.,]+)(.*)$/);
  if (!match) return { prefix: "", num: 0, suffix: value, isNumeric: false };
  const numStr = match[2].replace(/,/g, "");
  const num = Number(numStr);
  if (Number.isNaN(num)) return { prefix: "", num: 0, suffix: value, isNumeric: false };
  return { prefix: match[1], num, suffix: match[3], isNumeric: true, raw: match[2] };
}

function formatNumber(n: number, template: string) {
  if (template.includes(",")) return Math.round(n).toLocaleString("en-IN");
  if (template.includes(".")) return n.toFixed(1);
  return Math.round(n).toString();
}

export function Stat({ value, label }: StatProps) {
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
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const current = parsed.num * eased;
      setDisplay(`${parsed.prefix}${formatNumber(current, parsed.raw ?? "")}${parsed.suffix}`);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduce, value]);

  return (
    <div ref={ref} className="border-b border-hairline pb-4">
      <p className="font-display text-stat-numeral text-ink">{display}</p>
      <p className="font-mono text-mono-sm uppercase tracking-[0.04em] text-stone mt-2">{label}</p>
    </div>
  );
}
