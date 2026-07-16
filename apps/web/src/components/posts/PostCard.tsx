"use client";

import type { PostStatus } from "@iievi/types";

import { Badge } from "@/components/linen";
import { Skeleton } from "@/components/skeletons/Skeletons";

import { GenerationProgress } from "./GenerationProgress";
import {
  formatRatioClass,
  isTerminalStage,
  platformLabel,
  platformShort,
  type SessionPost,
} from "./types";

interface PostCardProps {
  post: SessionPost;
  layout: "grid" | "list";
  /** Keeps the parent's session-post state in sync with polled progress. */
  onStage: (postId: string, stage: PostStatus) => void;
  onOpen: (post: SessionPost) => void;
}

/**
 * A single generated post in the session gallery. Renders a creative shimmer
 * while the post is still being generated, else a neutral placeholder (there is
 * no media URL to show — the gallery is session-scoped, no list endpoint).
 */
export function PostCard({ post, layout, onStage, onOpen }: PostCardProps) {
  const generating = !isTerminalStage(post.stage) && post.stage !== "published";
  const failed = post.stage === "failed";
  const handleStage = (stage: PostStatus) => onStage(post.postId, stage);

  if (layout === "list") {
    return (
      <button
        type="button"
        onClick={() => onOpen(post)}
        className="flex w-full items-center gap-4 border border-hairline bg-surface p-4 text-left transition-colors hover:bg-neutral"
      >
        <div className="w-16 shrink-0">
          {generating ? (
            <Skeleton className="aspect-square w-full" />
          ) : (
            <div className="flex aspect-square w-full items-center justify-center border border-hairline bg-neutral">
              <span className="font-mono text-[9px] uppercase text-stone">
                {platformShort(post.platform)}
              </span>
            </div>
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <Badge>{platformLabel(post.platform)}</Badge>
          </div>
          <p className="truncate font-body text-body-sm text-ink">{post.topic}</p>
        </div>
        <div className="hidden w-48 shrink-0 sm:block">
          <GenerationProgress postId={post.postId} onStage={handleStage} hideCreative />
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(post)}
      className="flex flex-col gap-3 border border-hairline bg-surface p-4 text-left transition-colors hover:bg-neutral"
    >
      {generating ? (
        <Skeleton className={`${formatRatioClass(post.format)} w-full`} />
      ) : (
        <div
          className={`${formatRatioClass(post.format)} flex w-full items-center justify-center border border-hairline bg-neutral`}
        >
          <span className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {failed ? "Generation failed" : "Creative preview"}
          </span>
        </div>
      )}
      <div className="flex items-center justify-between gap-2">
        <Badge>{platformLabel(post.platform)}</Badge>
      </div>
      <p className="line-clamp-2 font-body text-body-sm text-ink">{post.topic}</p>
      <GenerationProgress postId={post.postId} onStage={handleStage} hideCreative />
    </button>
  );
}
