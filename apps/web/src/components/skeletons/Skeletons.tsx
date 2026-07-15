/**
 * Loading skeletons (Prompt 8 Step 11). Each matches the dimensions of its
 * loaded content to prevent layout shift, and uses a subtle pulse (no gradient
 * — Linen forbids them) as the shimmer. Use as Suspense fallbacks.
 */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden="true" className={`animate-pulse bg-neutral ${className}`} />;
}

/** Lead inbox list. */
export function LeadListSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="flex flex-col divide-y divide-hairline" aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-4 py-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-3 w-64" />
          </div>
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

/** Conversation thread bubbles. */
export function ConversationSkeleton({ bubbles = 5 }: { bubbles?: number }) {
  return (
    <div className="flex flex-col gap-4" aria-busy="true">
      {Array.from({ length: bubbles }, (_, i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? "justify-start" : "justify-end"}`}>
          <Skeleton className={`h-12 ${i % 2 === 0 ? "w-2/3" : "w-1/2"}`} />
        </div>
      ))}
    </div>
  );
}

/** Post creative grid. */
export function PostGridSkeleton({ items = 6 }: { items?: number }) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
      {Array.from({ length: items }, (_, i) => (
        <div key={i} className="flex flex-col gap-3 border border-hairline p-4">
          <Skeleton className="aspect-square w-full" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

/** Analytics chart card. */
export function AnalyticsChartSkeleton() {
  return (
    <div className="flex flex-col gap-4 border border-hairline p-6" aria-busy="true">
      <Skeleton className="h-3 w-32" />
      <Skeleton className="h-48 w-full" />
      <div className="flex gap-4">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}
