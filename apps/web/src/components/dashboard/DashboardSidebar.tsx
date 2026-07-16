"use client";

import { LogOut, Plus } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge, ThemeToggle, Tooltip } from "@/components/linen";
import { ConnectionIndicator } from "@/components/realtime/ConnectionIndicator";
import { Skeleton } from "@/components/skeletons/Skeletons";
import { useCapabilities } from "@/hooks/useCapabilities";
import { useLogout } from "@/hooks/useLogout";
import { useProfile } from "@/hooks/useProfile";
import { useUnreadLeads } from "@/hooks/useUnreadLeads";
import { useAuth } from "@/lib/auth-context";
import { PLAN_LABELS } from "@/lib/status";

import { ADMIN_ITEMS, type NavItem, NAV_ITEMS } from "./nav";

interface RecentChat {
  id: string;
  title: string;
}

function useRecentChats(): RecentChat[] {
  const [items, setItems] = useState<RecentChat[]>([]);
  useEffect(() => {
    try {
      const raw = localStorage.getItem("iievi:recent-chats");
      if (raw) setItems((JSON.parse(raw) as RecentChat[]).slice(0, 5));
    } catch {
      /* ignore malformed storage */
    }
  }, []);
  return items;
}

export function DashboardSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { hasFeature, capabilities } = useCapabilities();
  const profile = useProfile();
  const unread = useUnreadLeads();
  const logout = useLogout();
  const recent = useRecentChats();

  const businessName = profile.data?.business_profile?.business_name;
  const plan = capabilities?.plan ?? user?.plan;

  function renderItem(item: NavItem) {
    const gated = item.feature !== undefined && !hasFeature(item.feature);
    const active = pathname.startsWith(item.href);
    const Icon = item.icon;
    const badgeCount = item.badge === "leads" ? unread : 0;
    const inner = (
      <>
        <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
        <span className="flex-1">{item.label}</span>
        {badgeCount > 0 ? (
          <span
            aria-label={`${badgeCount} new`}
            className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-signal px-1.5 font-mono text-[11px] text-surface"
          >
            {badgeCount > 99 ? "99+" : badgeCount}
          </span>
        ) : null}
      </>
    );

    if (gated) {
      return (
        <Tooltip key={item.href} label="Upgrade to unlock">
          <span
            aria-disabled="true"
            className="flex w-full cursor-not-allowed items-center gap-3 px-3 py-2 font-body text-body-sm text-stone opacity-60"
          >
            {inner}
          </span>
        </Tooltip>
      );
    }
    return (
      <Link
        key={item.href}
        href={item.href}
        aria-current={active ? "page" : undefined}
        className={`flex items-center gap-3 px-3 py-2 font-body text-body-sm transition-colors ${
          active ? "bg-ink text-surface" : "text-graphite hover:text-ink"
        }`}
      >
        {inner}
      </Link>
    );
  }

  return (
    <aside className="hidden w-[280px] shrink-0 flex-col border-r border-hairline bg-neutral md:flex">
      {/* Logo + business name */}
      <div className="flex items-center justify-between gap-2 border-b border-hairline px-6 py-5">
        <div className="min-w-0">
          <span className="block font-display text-headline-sm leading-none text-ink">IIEVI</span>
          {profile.isLoading ? (
            <Skeleton className="mt-2 h-3 w-28" />
          ) : businessName ? (
            <span className="mt-1 block truncate font-body text-label-sm uppercase tracking-[0.12em] text-stone">
              {businessName}
            </span>
          ) : null}
        </div>
        <ThemeToggle />
      </div>

      {/* New Chat */}
      <div className="px-3 pt-3">
        <Link
          href="/dashboard/chat"
          className="flex items-center justify-center gap-2 border border-ink bg-ink px-3 py-2 font-body text-label-sm uppercase tracking-[0.12em] text-surface transition-colors hover:bg-surface hover:text-ink"
        >
          <Plus size={15} strokeWidth={1.75} aria-hidden="true" />
          New Chat
        </Link>
      </div>

      {/* Recent sessions */}
      {recent.length > 0 ? (
        <div className="px-3 pt-4">
          <p className="px-3 pb-1 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            Recent
          </p>
          <ul className="flex flex-col">
            {recent.map((c) => (
              <li key={c.id}>
                <Link
                  href="/dashboard/chat"
                  className="block truncate px-3 py-1.5 font-body text-body-sm text-graphite hover:text-ink"
                >
                  {c.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Primary nav */}
      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Primary">
        {NAV_ITEMS.map(renderItem)}

        {user?.isAdmin ? (
          <>
            <p className="px-3 pb-1 pt-4 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
              Admin
            </p>
            {ADMIN_ITEMS.map(renderItem)}
          </>
        ) : null}
      </nav>

      {/* User / plan / logout */}
      <div className="flex flex-col gap-3 border-t border-hairline px-6 py-4">
        <div className="flex items-center justify-between">
          {plan ? <Badge>{PLAN_LABELS[plan] ?? plan}</Badge> : <Skeleton className="h-5 w-16" />}
          {user?.role ? (
            <span className="font-mono text-mono-sm uppercase tracking-[0.12em] text-stone">
              {user.role}
            </span>
          ) : null}
        </div>
        <div className="flex items-center justify-between">
          <ConnectionIndicator />
          <button
            type="button"
            onClick={() => void logout()}
            className="inline-flex items-center gap-1.5 font-body text-body-sm text-graphite transition-colors hover:text-signal"
          >
            <LogOut size={14} strokeWidth={1.5} aria-hidden="true" />
            Log out
          </button>
        </div>
      </div>
    </aside>
  );
}
