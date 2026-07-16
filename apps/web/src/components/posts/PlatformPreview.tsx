"use client";

import { Heart, MessageCircle, Repeat2, Send, Share2, ThumbsUp } from "lucide-react";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/skeletons/Skeletons";

import { platformLabel, type PostPlatform } from "./types";

/**
 * Static, non-interactive mockups that approximate how a generated post reads on
 * each network. These are visual placeholders only — no live embed, no SDK — so
 * they lean entirely on Linen tokens + neutral greys (no brand colours) to stay
 * on-system while still evoking the real feed chrome.
 */
interface PlatformPreviewProps {
  platform: PostPlatform;
  caption: string;
  hashtags: string[];
  /** Business/handle shown in the header row. */
  authorName?: string;
  /** While true the creative shows a shimmer instead of the placeholder art. */
  loading?: boolean;
}

function Avatar({ short }: { short: string }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-hairline bg-neutral font-mono text-[10px] uppercase text-graphite"
    >
      {short}
    </span>
  );
}

/** The creative surface (image stand-in), or a shimmer while generating. */
function Creative({ loading, ratio }: { loading: boolean; ratio: string }) {
  if (loading) return <Skeleton className={`${ratio} w-full`} />;
  return (
    <div
      className={`${ratio} flex w-full items-center justify-center border-y border-hairline bg-neutral`}
    >
      <span className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
        Creative preview
      </span>
    </div>
  );
}

function CaptionBlock({ caption, hashtags }: { caption: string; hashtags: string[] }) {
  return (
    <p className="font-body text-body-sm text-ink">
      {caption || <span className="text-stone">Your caption will appear here…</span>}
      {hashtags.length > 0 ? (
        <>
          {" "}
          <span className="text-graphite">
            {hashtags.map((tag) => `#${tag}`).join(" ")}
          </span>
        </>
      ) : null}
    </p>
  );
}

function EngagementIcon({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-mono-sm text-stone" aria-hidden="true">
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </span>
  );
}

function FrameShell({ children }: { children: ReactNode }) {
  return <div className="w-full border border-hairline bg-surface">{children}</div>;
}

const ICON = { size: 16, strokeWidth: 1.5 } as const;

/** Facebook — square-ish header, caption above the media, reaction bar below. */
function FacebookFrame({ caption, hashtags, authorName, loading }: Required<PlatformPreviewProps>) {
  return (
    <FrameShell>
      <div className="flex items-center gap-3 p-3">
        <Avatar short="FB" />
        <div className="min-w-0">
          <p className="truncate font-body text-body-sm font-medium text-ink">{authorName}</p>
          <p className="font-mono text-mono-sm text-stone">Sponsored · Just now</p>
        </div>
      </div>
      <div className="px-3 pb-3">
        <CaptionBlock caption={caption} hashtags={hashtags} />
      </div>
      <Creative loading={loading} ratio="aspect-[16/9]" />
      <div className="flex items-center justify-around border-t border-hairline px-3 py-2.5">
        <EngagementIcon icon={<ThumbsUp {...ICON} />} label="Like" />
        <EngagementIcon icon={<MessageCircle {...ICON} />} label="Comment" />
        <EngagementIcon icon={<Share2 {...ICON} />} label="Share" />
      </div>
    </FrameShell>
  );
}

/** Instagram — media first, action row, then caption with the handle inline. */
function InstagramFrame({ caption, hashtags, authorName, loading }: Required<PlatformPreviewProps>) {
  return (
    <FrameShell>
      <div className="flex items-center gap-3 p-3">
        <Avatar short="IG" />
        <p className="min-w-0 flex-1 truncate font-body text-body-sm font-medium text-ink">
          {authorName}
        </p>
        <span aria-hidden="true" className="font-mono text-mono-sm text-stone">
          •••
        </span>
      </div>
      <Creative loading={loading} ratio="aspect-square" />
      <div className="flex items-center gap-4 px-3 pt-3">
        <Heart {...ICON} aria-hidden="true" className="text-ink" />
        <MessageCircle {...ICON} aria-hidden="true" className="text-ink" />
        <Send {...ICON} aria-hidden="true" className="text-ink" />
      </div>
      <div className="px-3 pb-3 pt-2">
        <p className="font-body text-body-sm text-ink">
          <span className="font-medium">{authorName.replace(/\s+/g, "").toLowerCase()}</span>{" "}
          <span className="text-graphite">
            {caption || "Your caption will appear here…"}
            {hashtags.length > 0 ? ` ${hashtags.map((t) => `#${t}`).join(" ")}` : ""}
          </span>
        </p>
      </div>
    </FrameShell>
  );
}

/** LinkedIn — professional header with subline, caption above media, repost bar. */
function LinkedInFrame({ caption, hashtags, authorName, loading }: Required<PlatformPreviewProps>) {
  return (
    <FrameShell>
      <div className="flex items-center gap-3 p-3">
        <Avatar short="in" />
        <div className="min-w-0">
          <p className="truncate font-body text-body-sm font-medium text-ink">{authorName}</p>
          <p className="truncate font-mono text-mono-sm text-stone">
            Small business · Promoted
          </p>
        </div>
      </div>
      <div className="px-3 pb-3">
        <CaptionBlock caption={caption} hashtags={hashtags} />
      </div>
      <Creative loading={loading} ratio="aspect-[16/9]" />
      <div className="flex items-center justify-around border-t border-hairline px-3 py-2.5">
        <EngagementIcon icon={<ThumbsUp {...ICON} />} label="Like" />
        <EngagementIcon icon={<MessageCircle {...ICON} />} label="Comment" />
        <EngagementIcon icon={<Repeat2 {...ICON} />} label="Repost" />
        <EngagementIcon icon={<Send {...ICON} />} label="Send" />
      </div>
    </FrameShell>
  );
}

export function PlatformPreview({
  platform,
  caption,
  hashtags,
  authorName = "Your business",
  loading = false,
}: PlatformPreviewProps) {
  const props: Required<PlatformPreviewProps> = {
    platform,
    caption,
    hashtags,
    authorName,
    loading,
  };
  switch (platform) {
    case "facebook":
      return <FacebookFrame {...props} />;
    case "instagram":
      return <InstagramFrame {...props} />;
    case "linkedin":
      return <LinkedInFrame {...props} />;
    case "tiktok":
      // TikTok has no bespoke frame yet; the Instagram-style vertical card is the
      // closest neutral approximation for a full-bleed short-form creative.
      return <InstagramFrame {...props} />;
    default:
      return null;
  }
}

/** A small labelled wrapper used above the frame in the approval modal. */
export function PlatformPreviewLabel({ platform }: { platform: PostPlatform }) {
  return (
    <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
      {platformLabel(platform)} preview
    </p>
  );
}
