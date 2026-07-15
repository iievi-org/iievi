/**
 * A single labelled usage bar: metric name, used/limit numerals, and a Linen
 * progress track. The fill is `bg-ink` normally and `bg-signal` once the metric
 * is at (or within 80% of) its limit — the same "you're running low" signal the
 * upgrade modal keys off. A null limit renders as "Unlimited" with a full,
 * calm ink bar.
 */

interface UsageBarProps {
  label: string;
  used: number;
  /** Monthly quota, or null for unlimited plans. */
  limit: number | null;
  /** True when remaining allowance for this metric is exhausted. */
  atLimit: boolean;
}

const WARN_RATIO = 0.8;

export function UsageBar({ label, used, limit, atLimit }: UsageBarProps) {
  const unlimited = limit === null;
  const ratio = unlimited || limit === 0 ? 0 : Math.min(used / limit, 1);
  const nearLimit = !unlimited && (atLimit || ratio >= WARN_RATIO);
  const pct = unlimited ? 100 : Math.round(ratio * 100);
  const fill = nearLimit ? "bg-signal" : "bg-ink";

  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <span className="font-mono text-mono-sm uppercase tracking-[0.1em] text-graphite">
          {label}
        </span>
        <span className="font-mono text-mono-sm text-ink tabular-nums">
          <span className="text-ink">{used.toLocaleString("en-IN")}</span>
          <span className="text-stone">
            {" / "}
            {unlimited ? "Unlimited" : limit.toLocaleString("en-IN")}
          </span>
        </span>
      </div>
      <div
        className="mt-2 h-1.5 w-full overflow-hidden bg-neutral"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={unlimited ? undefined : limit}
        aria-valuenow={used}
      >
        <div
          className={`h-full ${fill} transition-[width] duration-500`}
          style={{ width: `${unlimited ? 100 : pct}%` }}
        />
      </div>
    </div>
  );
}
