"use client";

import type { AdminLogsResponse, AuditLogEntry } from "@iievi/types";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, FileClock, Search, ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";

import { LevelBadge } from "@/components/admin/LevelBadge";
import { Container, Input } from "@/components/linen";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] as const;

interface Filters {
  tenant_id: string;
  from_date: string; // datetime-local value
  to_date: string; // datetime-local value
  level: string;
  limit: number;
}

/** Mirrors the api-client's `AdminLogsParams` (optional, without `undefined`). */
interface LogsParams {
  tenant_id?: string;
  from_date?: string;
  to_date?: string;
  level?: string;
  limit?: number;
}

const INITIAL_FILTERS: Filters = {
  tenant_id: "",
  from_date: "",
  to_date: "",
  level: "",
  limit: 100,
};

/** A `datetime-local` value ("2026-07-15T13:45") → ISO 8601, or undefined if empty. */
function toIso(value: string): string | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

/** Render a log timestamp; falls back to a dash for entries without one. */
function formatTimestamp(ts?: string): string {
  if (!ts) return "—";
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return ts;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function AuditLogsPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);

  // Build the params via conditional spread so unset filters are simply absent
  // (rather than explicitly `undefined`) — this satisfies exactOptionalPropertyTypes
  // against AdminLogsParams' optional-without-`undefined` fields. The api-client's
  // `qs` helper would strip empty/undefined values anyway.
  const params = useMemo<LogsParams>(() => {
    const tenantId = filters.tenant_id.trim();
    const fromIso = toIso(filters.from_date);
    const toIsoValue = toIso(filters.to_date);
    return {
      limit: filters.limit,
      ...(tenantId ? { tenant_id: tenantId } : {}),
      ...(fromIso ? { from_date: fromIso } : {}),
      ...(toIsoValue ? { to_date: toIsoValue } : {}),
      ...(filters.level ? { level: filters.level } : {}),
    };
  }, [filters]);

  const {
    data,
    isPending,
    isError,
    error,
  } = useQuery<AdminLogsResponse>({
    queryKey: ["admin-logs", params],
    queryFn: () => api.admin.logs(params),
    staleTime: 0, // logs are live — never serve stale
    enabled: Boolean(user?.isAdmin),
  });

  if (!user) {
    return (
      <Container className="py-16">
        <p className="font-body text-body-sm text-graphite">Loading…</p>
      </Container>
    );
  }

  if (!user.isAdmin) {
    return (
      <Container className="py-16">
        <div className="flex flex-col items-center justify-center gap-3 border border-hairline bg-neutral px-6 py-20 text-center">
          <ShieldAlert aria-hidden="true" className="h-8 w-8 text-stone" />
          <p className="font-display text-headline-sm text-ink">Restricted</p>
          <p className="font-body text-body-sm text-graphite">Platform admins only.</p>
        </div>
      </Container>
    );
  }

  const logs = data?.logs ?? [];

  return (
    <Container className="py-10 md:py-16">
      <header className="flex items-start gap-3">
        <FileClock aria-hidden="true" className="mt-1 h-6 w-6 shrink-0 text-signal" />
        <div>
          <h1 className="font-display text-headline-lg text-ink">Audit Logs</h1>
          <p className="mt-1 font-body text-body-sm text-graphite">
            Searchable application logs across tenants — the forensic trail.
          </p>
        </div>
      </header>

      {/* Filter bar */}
      <form
        className="mt-8 flex flex-wrap items-end gap-x-6 gap-y-4 border border-hairline bg-neutral p-5"
        onSubmit={(event) => event.preventDefault()}
      >
        <Input
          label="Tenant ID"
          name="tenant_id"
          placeholder="uuid…"
          value={filters.tenant_id}
          onChange={(event) => setFilters((prev) => ({ ...prev, tenant_id: event.target.value }))}
          fieldClassName="min-w-[220px] flex-1"
          className="font-mono text-mono-sm"
        />
        <Input
          label="From"
          name="from_date"
          type="datetime-local"
          value={filters.from_date}
          onChange={(event) => setFilters((prev) => ({ ...prev, from_date: event.target.value }))}
          fieldClassName="min-w-[200px]"
        />
        <Input
          label="To"
          name="to_date"
          type="datetime-local"
          value={filters.to_date}
          onChange={(event) => setFilters((prev) => ({ ...prev, to_date: event.target.value }))}
          fieldClassName="min-w-[200px]"
        />
        <div className="flex min-w-[140px] flex-col gap-1">
          <label
            htmlFor="level"
            className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
          >
            Level
          </label>
          <select
            id="level"
            name="level"
            value={filters.level}
            onChange={(event) => setFilters((prev) => ({ ...prev, level: event.target.value }))}
            className="border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-body text-body-md text-ink outline-none transition-colors focus:border-b-2 focus:border-b-signal"
          >
            <option value="">All</option>
            {LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>
        <Input
          label="Limit"
          name="limit"
          type="number"
          min={1}
          max={1000}
          value={filters.limit}
          onChange={(event) =>
            setFilters((prev) => ({
              ...prev,
              limit: Math.max(1, Number(event.target.value) || 1),
            }))
          }
          fieldClassName="min-w-[100px]"
        />
      </form>

      {/* Result count */}
      <div className="mt-8 flex items-center gap-2 border-b border-hairline pb-3">
        <Search aria-hidden="true" className="h-4 w-4 text-stone" />
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
          {isPending ? "Searching…" : `${data?.count ?? logs.length} results`}
        </p>
      </div>

      {/* States */}
      {isPending ? (
        <p className="py-16 text-center font-body text-body-sm text-graphite">Loading logs…</p>
      ) : isError ? (
        <p className="py-16 text-center font-mono text-mono-sm text-signal" role="alert">
          {error instanceof Error ? error.message : "Failed to load logs."}
        </p>
      ) : logs.length === 0 ? (
        <p className="py-16 text-center font-body text-body-sm text-graphite">
          No log entries for these filters.
        </p>
      ) : (
        <div className="mt-2 border border-hairline">
          {/* Header row */}
          <div className="hidden grid-cols-[180px_120px_160px_1fr_24px] items-center gap-4 border-b border-hairline bg-neutral px-4 py-3 md:grid">
            {["Timestamp", "Level", "Module", "Message", ""].map((col, i) => (
              <span
                key={col || `col-${i}`}
                className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone"
              >
                {col}
              </span>
            ))}
          </div>
          <ul>
            {logs.map((entry, index) => (
              <LogRow key={`${entry.timestamp ?? "log"}-${index}`} entry={entry} />
            ))}
          </ul>
        </div>
      )}
    </Container>
  );
}

function LogRow({ entry }: { entry: AuditLogEntry }) {
  const [open, setOpen] = useState(false);
  // NOTE: The spec's audit-log diff (old_values/new_values) is NOT exposed by
  // GET /admin/logs — that endpoint queries Axiom application logs, not the DB
  // `audit_log` table. So the expander shows the full structured log entry
  // (all fields, including any extra keys) rather than a before/after diff.
  const pretty = JSON.stringify(entry, null, 2);

  return (
    <li className="border-b border-hairline last:border-b-0">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
        className="grid w-full grid-cols-[1fr_24px] items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-neutral md:grid-cols-[180px_120px_160px_1fr_24px]"
      >
        <span className="font-mono text-mono-sm text-graphite">
          {formatTimestamp(entry.timestamp)}
        </span>
        <span className="hidden md:inline-flex">
          <LevelBadge level={entry.level} />
        </span>
        <span className="hidden truncate font-mono text-mono-sm text-stone md:block">
          {entry.module ?? "—"}
        </span>
        <span className="hidden truncate font-body text-body-sm text-ink md:block">
          {entry.message ?? "—"}
        </span>
        <ChevronDown
          aria-hidden="true"
          className={`h-4 w-4 shrink-0 justify-self-end text-stone transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Compact metadata for mobile (columns are hidden there) */}
      <div className="flex flex-wrap items-center gap-2 px-4 pb-3 md:hidden">
        <LevelBadge level={entry.level} />
        <span className="truncate font-body text-body-sm text-ink">{entry.message ?? "—"}</span>
      </div>

      {open && (
        <div className="px-4 pb-4">
          <pre className="overflow-auto border border-hairline bg-neutral p-4 font-mono text-mono-sm text-ink">
            {pretty}
          </pre>
        </div>
      )}
    </li>
  );
}
