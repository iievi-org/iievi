"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCapabilities } from "@/hooks/useCapabilities";
import { useUnreadLeads } from "@/hooks/useUnreadLeads";

import { MOBILE_TABS } from "./nav";

/** Bottom tab bar for < 768px. The active tab gets a filled pill. */
export function MobileTabBar() {
  const pathname = usePathname();
  const { hasFeature } = useCapabilities();
  const unread = useUnreadLeads();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 flex border-t border-hairline bg-neutral md:hidden"
    >
      {MOBILE_TABS.map((item) => {
        const gated = item.feature !== undefined && !hasFeature(item.feature);
        const active = pathname.startsWith(item.href);
        const Icon = item.icon;
        const showBadge = item.badge === "leads" && unread > 0;

        const content = (
          <>
            <span
              className={`relative flex items-center justify-center rounded-full px-4 py-1.5 transition-colors ${
                active ? "bg-ink text-surface" : "text-graphite"
              }`}
            >
              <Icon size={18} strokeWidth={1.5} aria-hidden="true" />
              {showBadge ? (
                <span
                  aria-hidden="true"
                  className="absolute right-2 top-0.5 h-2 w-2 rounded-full bg-signal"
                />
              ) : null}
            </span>
            <span className="font-body text-[10px] uppercase tracking-[0.08em]">{item.label}</span>
          </>
        );

        if (gated) {
          return (
            <span
              key={item.href}
              aria-disabled="true"
              className="flex flex-1 flex-col items-center gap-0.5 py-2 text-stone opacity-50"
            >
              {content}
            </span>
          );
        }
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className="flex flex-1 flex-col items-center gap-0.5 py-2"
          >
            {content}
          </Link>
        );
      })}
    </nav>
  );
}
