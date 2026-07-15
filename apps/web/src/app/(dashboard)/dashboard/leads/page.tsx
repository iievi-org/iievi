"use client";

import type { LeadStatus, Platform } from "@iievi/types";
import { ChevronLeft, Inbox } from "lucide-react";
import type { Route } from "next";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useMemo, useState, type UIEvent } from "react";

import { ConversationPanel } from "@/components/leads/ConversationPanel";
import { LeadCard } from "@/components/leads/LeadCard";
import { LeadFilters } from "@/components/leads/LeadFilters";
import { LeadListSkeleton } from "@/components/skeletons/Skeletons";
import { useLeadsInfinite } from "@/hooks/useLeadsInfinite";

function LeadsInbox() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedId = searchParams.get("lead");

  const [statuses, setStatuses] = useState<Set<LeadStatus>>(new Set());
  const [platforms, setPlatforms] = useState<Set<Platform>>(new Set());
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const server = useMemo(() => {
    const s: { created_after?: string; created_before?: string } = {};
    if (from) s.created_after = new Date(from).toISOString();
    if (to) s.created_before = new Date(`${to}T23:59:59`).toISOString();
    return s;
  }, [from, to]);

  const query = useLeadsInfinite(server);
  const allLeads = useMemo(() => query.data?.pages.flatMap((p) => p.leads) ?? [], [query.data]);
  const visible = useMemo(
    () =>
      allLeads.filter(
        (l) =>
          (statuses.size === 0 || statuses.has(l.status)) &&
          (platforms.size === 0 || platforms.has(l.platform)),
      ),
    [allLeads, statuses, platforms],
  );

  const setLeadParam = useCallback(
    (id: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (id) params.set("lead", id);
      else params.delete("lead");
      const qs = params.toString();
      router.replace((qs ? `/dashboard/leads?${qs}` : "/dashboard/leads") as Route);
    },
    [router, searchParams],
  );

  const onScroll = (e: UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    if (
      el.scrollHeight - el.scrollTop - el.clientHeight < 200 &&
      query.hasNextPage &&
      !query.isFetchingNextPage
    ) {
      void query.fetchNextPage();
    }
  };

  const toggleStatus = (s: LeadStatus) =>
    setStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  const togglePlatform = (p: Platform) =>
    setPlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
  const clear = () => {
    setStatuses(new Set());
    setPlatforms(new Set());
    setFrom("");
    setTo("");
  };

  return (
    <div className="flex h-[calc(100dvh-4rem)] overflow-hidden md:h-dvh">
      {/* Lead list */}
      <section
        className={`w-full flex-col border-r border-hairline md:flex md:w-96 ${
          selectedId ? "hidden md:flex" : "flex"
        }`}
      >
        <LeadFilters
          statuses={statuses}
          platforms={platforms}
          from={from}
          to={to}
          onToggleStatus={toggleStatus}
          onTogglePlatform={togglePlatform}
          onDateChange={(which, value) => (which === "from" ? setFrom(value) : setTo(value))}
          onClear={clear}
        />
        <div className="min-h-0 flex-1 overflow-y-auto" onScroll={onScroll}>
          {query.isLoading ? (
            <LeadListSkeleton />
          ) : visible.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-20 text-center">
              <Inbox size={28} strokeWidth={1.25} className="text-stone" aria-hidden="true" />
              <p className="font-body text-body-sm text-graphite">
                {allLeads.length === 0 ? "No leads yet." : "No leads match these filters."}
              </p>
            </div>
          ) : (
            visible.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                active={lead.id === selectedId}
                onSelect={() => setLeadParam(lead.id)}
              />
            ))
          )}
          {query.isFetchingNextPage ? (
            <p className="py-4 text-center font-mono text-mono-sm text-stone">Loading more…</p>
          ) : null}
        </div>
      </section>

      {/* Conversation */}
      <section className={`min-w-0 flex-1 flex-col ${selectedId ? "flex" : "hidden md:flex"}`}>
        {selectedId ? (
          <>
            <button
              type="button"
              onClick={() => setLeadParam(null)}
              className="flex items-center gap-1 border-b border-hairline px-4 py-3 font-body text-body-sm text-graphite md:hidden"
            >
              <ChevronLeft size={16} aria-hidden="true" />
              Back to leads
            </button>
            <div className="min-h-0 flex-1">
              <ConversationPanel leadId={selectedId} />
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-center">
            <Inbox size={32} strokeWidth={1.25} className="text-stone" aria-hidden="true" />
            <p className="font-body text-body-sm text-graphite">
              Select a lead to view the conversation.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

export default function LeadsPage() {
  return (
    <Suspense fallback={<LeadListSkeleton />}>
      <LeadsInbox />
    </Suspense>
  );
}
