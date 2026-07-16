"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Container } from "@/components/linen";
import { ConnectedAccounts } from "@/components/settings/ConnectedAccounts";
import { NotificationsSection } from "@/components/settings/NotificationsSection";
import { ProfileSection } from "@/components/settings/ProfileSection";
import { TeamSection } from "@/components/settings/TeamSection";

// In Next 14 App Router, dynamic `params` is a plain object prop on the page —
// no Promise, no `use()`. Type it directly.
interface SettingsSectionPageProps {
  params: { section: string };
}

type SectionKey = "profile" | "accounts" | "notifications" | "team";

const SECTIONS: { key: SectionKey; label: string }[] = [
  { key: "profile", label: "Profile" },
  { key: "accounts", label: "Accounts" },
  { key: "notifications", label: "Notifications" },
  { key: "team", label: "Team" },
];

const VALID = new Set<SectionKey>(["profile", "accounts", "notifications", "team"]);

function isSection(value: string): value is SectionKey {
  return VALID.has(value as SectionKey);
}

export default function SettingsSectionPage({ params }: SettingsSectionPageProps) {
  const pathname = usePathname();
  const known = isSection(params.section);
  // Unknown section falls back to the profile panel (with a gentle note above it).
  const active: SectionKey = known ? (params.section as SectionKey) : "profile";

  return (
    <Container className="py-10 md:py-14">
      <header className="mb-8">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Account</p>
        <h1 className="mt-2 font-display text-headline-lg text-ink">Settings</h1>
        <p className="mt-3 max-w-prose font-body text-body-md text-graphite">
          Manage your business profile, connected accounts, and how iievi keeps you in the loop.
        </p>
      </header>

      {/* Horizontal tab-style section nav */}
      <nav aria-label="Settings sections" className="mb-10 border-b border-hairline">
        <ul className="-mb-px flex flex-wrap gap-8">
          {SECTIONS.map((section) => {
            const href = `/dashboard/settings/${section.key}` as Route;
            const isActive = pathname === href;
            return (
              <li key={section.key}>
                <Link
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  className={`inline-flex border-b-2 pb-3 font-body text-label-sm uppercase tracking-[0.14em] transition-colors ${
                    isActive
                      ? "border-signal text-ink"
                      : "border-transparent text-stone hover:text-ink"
                  }`}
                >
                  {section.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {!known ? (
        <p className="mb-8 border border-hairline bg-neutral px-4 py-3 font-body text-body-sm text-graphite">
          Unknown section &ldquo;{params.section}&rdquo; — showing your profile instead.
        </p>
      ) : null}

      {active === "profile" ? <ProfileSection /> : null}
      {active === "accounts" ? <ConnectedAccounts /> : null}
      {active === "notifications" ? <NotificationsSection /> : null}
      {active === "team" ? <TeamSection /> : null}
    </Container>
  );
}
