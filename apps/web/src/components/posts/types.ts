import type { GeneratePostBody } from "@iievi/api-client";
import type { PostStatus } from "@iievi/types";

/**
 * The four platforms the /posts/generate endpoint accepts. Note this differs
 * from the general `Platform`/`SocialPlatform` union (which has `meta`/`whatsapp`
 * instead of `facebook`) — the post generator speaks the publish-target names.
 */
export type PostPlatform = GeneratePostBody["platform"];

/** The creative aspect ratios the generator supports. */
export type PostFormat = NonNullable<GeneratePostBody["format"]>;

/**
 * One generated post held in React state. There is NO list/persistence endpoint
 * (only generate + progress), so this whole gallery is session-scoped — it lives
 * only until the tab is closed or reloaded.
 */
export interface SessionPost {
  postId: string;
  platform: PostPlatform;
  topic: string;
  format: PostFormat;
  /** Last stage seen from GET /posts/{id}/progress; seeded optimistically. */
  stage: PostStatus;
}

export const POST_PLATFORMS: { value: PostPlatform; label: string; short: string }[] = [
  { value: "instagram", label: "Instagram", short: "IG" },
  { value: "facebook", label: "Facebook", short: "FB" },
  { value: "linkedin", label: "LinkedIn", short: "in" },
  { value: "tiktok", label: "TikTok", short: "TT" },
];

export const POST_FORMATS: { value: PostFormat; label: string; ratio: string }[] = [
  { value: "square", label: "Square · 1:1", ratio: "aspect-square" },
  { value: "portrait", label: "Portrait · 4:5", ratio: "aspect-[4/5]" },
  { value: "story", label: "Story · 9:16", ratio: "aspect-[9/16]" },
  { value: "landscape", label: "Landscape · 16:9", ratio: "aspect-[16/9]" },
];

const PLATFORM_LOOKUP = new Map(POST_PLATFORMS.map((p) => [p.value, p]));
const FORMAT_LOOKUP = new Map(POST_FORMATS.map((f) => [f.value, f]));

export function platformLabel(platform: PostPlatform): string {
  return PLATFORM_LOOKUP.get(platform)?.label ?? platform;
}

export function platformShort(platform: PostPlatform): string {
  return PLATFORM_LOOKUP.get(platform)?.short ?? "?";
}

export function formatRatioClass(format: PostFormat): string {
  return FORMAT_LOOKUP.get(format)?.ratio ?? "aspect-square";
}

/** Terminal stages stop polling and settle the multi-step indicator. */
export function isTerminalStage(stage: PostStatus): boolean {
  return stage === "published" || stage === "failed";
}

interface StageMeta {
  /** Friendly, human-readable label for the current stage. */
  label: string;
  /** Zero-based position in the [draft → published] happy path (failed = -1). */
  step: number;
}

/**
 * PostStatus → friendly copy + step index for the progress indicator.
 * The happy path is draft → scheduled → publishing → published (4 steps);
 * `failed` is an error state that sits outside the ladder.
 */
export const STAGE_META: Record<PostStatus, StageMeta> = {
  draft: { label: "Writing caption…", step: 0 },
  scheduled: { label: "Scheduled", step: 1 },
  publishing: { label: "Generating image & publishing…", step: 2 },
  published: { label: "Published ✓", step: 3 },
  failed: { label: "Failed", step: -1 },
};

/** The ordered happy-path stages rendered as the step ladder. */
export const STAGE_LADDER: PostStatus[] = ["draft", "scheduled", "publishing", "published"];
