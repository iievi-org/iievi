"use client";

import type { PostStatus } from "@iievi/types";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { Skeleton } from "@/components/skeletons/Skeletons";
import { api } from "@/lib/api";

import { isTerminalStage, STAGE_LADDER, STAGE_META } from "./types";

interface GenerationProgressProps {
  postId: string;
  /** Lets the parent mirror the latest stage into its session-post state. */
  onStage?: (stage: PostStatus) => void;
  /** Hide the creative shimmer (e.g. when a card already renders one). */
  hideCreative?: boolean;
}

/**
 * Polls GET /posts/{id}/progress every 2s until a terminal stage, mapping the
 * PostStatus to a friendly multi-step indicator. While the post is mid-flight it
 * also shows a shimmer standing in for the creative being generated.
 */
export function GenerationProgress({ postId, onStage, hideCreative = false }: GenerationProgressProps) {
  const query = useQuery({
    queryKey: ["post-progress", postId],
    queryFn: () => api.posts.progress(postId),
    refetchInterval: (q) => {
      const s = q.state.data?.stage;
      return s === "published" || s === "failed" ? false : 2000;
    },
  });

  const stage = query.data?.stage;

  useEffect(() => {
    if (stage) onStage?.(stage);
  }, [stage, onStage]);

  // Before the first poll resolves, treat the post as still in "draft".
  const current: PostStatus = stage ?? "draft";
  const meta = STAGE_META[current];
  const terminal = isTerminalStage(current);
  const failed = current === "failed";

  return (
    <div className="flex flex-col gap-3">
      {!hideCreative && !terminal ? (
        <Skeleton className="aspect-square w-full" />
      ) : null}

      {/* Accessible multi-step ladder. aria-live announces stage changes. */}
      <div
        role="status"
        aria-live="polite"
        aria-label={`Post generation: ${meta.label}`}
        className="flex flex-col gap-2"
      >
        <ol className="flex items-center gap-1.5" aria-hidden="true">
          {STAGE_LADDER.map((ladderStage) => {
            const stageMeta = STAGE_META[ladderStage];
            const reached = !failed && meta.step >= stageMeta.step;
            const isNow = !failed && current === ladderStage;
            return (
              <li
                key={ladderStage}
                className={`h-1 flex-1 transition-colors ${
                  failed
                    ? "bg-signal"
                    : reached
                      ? isNow && !terminal
                        ? "animate-pulse bg-signal"
                        : "bg-ink"
                      : "bg-hairline"
                }`}
              />
            );
          })}
        </ol>
        <p
          className={`font-mono text-mono-sm uppercase tracking-[0.14em] ${
            failed ? "text-signal" : terminal ? "text-ink" : "text-graphite"
          }`}
        >
          {query.isError ? "Couldn't read progress — retrying…" : meta.label}
        </p>
      </div>
    </div>
  );
}
