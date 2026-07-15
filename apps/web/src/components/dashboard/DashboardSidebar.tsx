"use client";

import { BarChart3, CreditCard, ImageIcon, MessageSquare, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/linen";
import { ConnectionIndicator } from "@/components/realtime/ConnectionIndicator";
import { useAuth } from "@/lib/auth-context";

const NAV = [
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/leads", label: "Leads", icon: Users },
  { href: "/dashboard/posts", label: "Posts", icon: ImageIcon },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
] as const;

export function DashboardSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-hairline bg-neutral md:flex">
      <div className="flex items-center justify-between border-b border-hairline px-6 py-5">
        <span className="font-display text-headline-sm text-ink">IIEVI</span>
        <ThemeToggle />
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Primary">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 px-3 py-2 font-body text-body-sm transition-colors ${
                active ? "bg-ink text-surface" : "text-graphite hover:text-ink"
              }`}
            >
              <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-hairline px-6 py-4">
        <ConnectionIndicator />
        {user ? <span className="sr-only">Signed in</span> : null}
      </div>
    </aside>
  );
}
