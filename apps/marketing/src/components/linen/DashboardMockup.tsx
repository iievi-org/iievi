import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useReducedMotion } from "framer-motion";
import {
  CalendarCheck,
  Megaphone,
  MessageSquare,
  Send,
  Star,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";

type Activity = {
  id: number;
  icon: LucideIcon;
  label: string;
  detail: string;
  age: string;
};

const POOL: Omit<Activity, "id" | "age">[] = [
  { icon: UserPlus, label: "New lead", detail: "Reema · Hair colour enquiry" },
  { icon: CalendarCheck, label: "Booking confirmed", detail: "4 PM with Priya · ₹2,800" },
  { icon: Send, label: "Post scheduled", detail: "Diwali offer · Instagram + Meta" },
  { icon: Megaphone, label: "Campaign live", detail: "Glow Weekend · ₹500/day · 4 channels" },
  { icon: Star, label: "Review collected", detail: "Anjali · 5★ · Google Maps" },
  { icon: MessageSquare, label: "Follow-up sent", detail: "12 lapsed customers · 30-day win-back" },
];

function ageLabel(secondsAgo: number) {
  if (secondsAgo < 5) return "now";
  if (secondsAgo < 60) return `${secondsAgo}s`;
  const m = Math.floor(secondsAgo / 60);
  return `${m}m`;
}

function useCountUp(target: number, active: boolean, duration = 1400) {
  const [value, setValue] = useState(0);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (!active) return;
    if (reduce) {
      setValue(target);
      return;
    }
    const start = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(target * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, duration, reduce]);
  return value;
}

export function DashboardMockup() {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const reduce = useReducedMotion();

  const leads = useCountUp(142, inView);
  const revenue = useCountUp(38400, inView);
  const cpl = useCountUp(94, inView); // ₹94 CPL

  // Live activity feed
  const [feed, setFeed] = useState<Activity[]>(() =>
    [3, 2, 1, 0].map((i) => ({
      id: i,
      icon: POOL.at(i)!.icon,
      label: POOL.at(i)!.label,
      detail: POOL.at(i)!.detail,
      age: ageLabel(i * 60 + 30),
    })),
  );
  const nextId = useRef(10);

  useEffect(() => {
    if (!inView || reduce) return;
    const interval = setInterval(() => {
      const pick = POOL.at(Math.floor(Math.random() * POOL.length))!;
      setFeed((prev) => {
        const aged = prev.map((a, i) => ({ ...a, age: ageLabel((i + 1) * 60) }));
        const nf: Activity = {
          id: nextId.current++,
          icon: pick.icon,
          label: pick.label,
          detail: pick.detail,
          age: "now",
        };
        return [nf, ...aged].slice(0, 4);
      });
    }, 3200);
    return () => clearInterval(interval);
  }, [inView, reduce]);

  // Sparkline
  const points = [12, 18, 14, 22, 19, 28, 24, 34, 31, 42, 38, 48];
  const max = Math.max(...points);
  const w = 140;
  const h = 36;
  const step = w / (points.length - 1);
  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${h - (p / max) * h}`)
    .join(" ");

  return (
    <div ref={ref} className="border border-hairline bg-neutral">
      {/* Browser chrome */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-hairline">
        <span className="w-2.5 h-2.5 rounded-full bg-hairline/40" />
        <span className="w-2.5 h-2.5 rounded-full bg-hairline/40" />
        <span className="w-2.5 h-2.5 rounded-full bg-hairline/40" />
        <span className="ml-3 font-mono text-mono-sm text-stone">
          {t("app.iievi.in/dashboard")}
        </span>
        <span className="ml-auto inline-flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse" />
          <span className="font-mono text-mono-sm text-stone uppercase tracking-[0.14em]">
            {t("Live")}
          </span>
        </span>
      </div>

      {/* Today stats */}
      <div className="px-5 pt-5 pb-4 border-b border-hairline">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
          {t("Today")}
        </p>
        <div className="mt-3 grid grid-cols-3 gap-3">
          <div>
            <p className="font-display text-[28px] leading-none text-ink tabular-nums">
              {Math.round(leads)}
            </p>
            <p className="font-mono text-mono-sm text-stone mt-1.5">{t("Leads")}</p>
          </div>
          <div>
            <p className="font-display text-[28px] leading-none text-ink tabular-nums">
              ₹{Math.round(revenue).toLocaleString("en-IN")}
            </p>
            <p className="font-mono text-mono-sm text-stone mt-1.5">{t("Revenue")}</p>
          </div>
          <div>
            <p className="font-display text-[28px] leading-none text-ink tabular-nums">
              ₹{Math.round(cpl)}
            </p>
            <p className="font-mono text-mono-sm text-stone mt-1.5">{t("CPL ↓")}</p>
          </div>
        </div>
      </div>

      {/* Live activity */}
      <div className="px-5 py-4 border-b border-hairline">
        <div className="flex items-center justify-between">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {t("Live activity")}
          </p>
          <p className="font-mono text-mono-sm text-stone">{t("Auto-updating")}</p>
        </div>

        <div className="mt-3 flex flex-col gap-px bg-hairline/40 min-h-[176px]">
          <AnimatePresence initial={false} mode="popLayout">
            {feed.map((item) => {
              const Icon = item.icon;

              return (
                <motion.div
                  key={item.id}
                  layout="position"
                  initial={reduce ? false : { opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={reduce ? undefined : { opacity: 0 }}
                  transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                  className="bg-neutral"
                >
                  <div className="flex items-center gap-3 px-3 py-2.5">
                    <span className="inline-flex items-center justify-center w-6 h-6 border border-hairline text-ink shrink-0">
                      <Icon size={12} strokeWidth={1.75} />
                    </span>

                    <div className="flex-1 min-w-0">
                      <p className="font-body text-body-sm text-ink truncate">
                        <span className="text-signal">●</span> {item.label}
                        <span className="text-stone"> — </span>
                        <span className="text-graphite">{item.detail}</span>
                      </p>
                    </div>

                    <span className="font-mono text-mono-sm text-stone shrink-0">{item.age}</span>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
      {/* Sparkline */}
      <div className="flex items-end justify-between gap-4 px-5 py-4">
        <div>
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {t("This week")}
          </p>
          <p className="mt-1 font-display text-headline-sm text-ink">{t("+34% vs last")}</p>
        </div>
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
          <motion.path
            d={pathD}
            fill="none"
            stroke="currentColor"
            strokeWidth={1.25}
            className="text-ink"
            initial={reduce ? false : { pathLength: 0 }}
            animate={inView ? { pathLength: 1 } : { pathLength: 0 }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
          <motion.circle
            cx={(points.length - 1) * step}
            cy={h - ((points.at(-1) || 0) / max) * h}
            r={2.5}
            className="fill-signal"
            initial={reduce ? false : { opacity: 0 }}
            animate={inView ? { opacity: 1 } : { opacity: 0 }}
            transition={{ delay: 1, duration: 0.3 }}
          />
        </svg>
      </div>
    </div>
  );
}
