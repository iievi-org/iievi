"use client";

import { Clock, Sparkles, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { Badge, Button, Pill, Tooltip } from "@/components/linen";
import { Skeleton } from "@/components/skeletons/Skeletons";

import { GenerationProgress } from "./GenerationProgress";
import { PlatformPreview, PlatformPreviewLabel } from "./PlatformPreview";
import { formatRatioClass, isTerminalStage, platformLabel, STAGE_META, type SessionPost } from "./types";

interface PostApprovalModalProps {
  post: SessionPost;
  onClose: () => void;
}

type ScheduleMode = "now" | "custom" | "best";

/** Local ISO string (no seconds) for the min= of a "future only" datetime input. */
function nowLocalIso(): string {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export function PostApprovalModal({ post, onClose }: PostApprovalModalProps) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);

  // Caption + hashtags are edited LOCALLY only. There is no update/save endpoint,
  // so the "autosave" below persists to component state, not the server.
  const [caption, setCaption] = useState(`${post.topic}\n\n`);
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [tagDraft, setTagDraft] = useState("");
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const [scheduleMode, setScheduleMode] = useState<ScheduleMode>("now");
  const [customAt, setCustomAt] = useState("");

  const terminal = isTerminalStage(post.stage);
  const showShimmer = !terminal && post.stage !== "published";
  const minCustom = useMemo(() => nowLocalIso(), []);

  // Escape closes; focus moves into the dialog; body scroll is locked.
  useEffect(() => {
    dialogRef.current?.focus();
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  // 1-second debounced "autosave" of the caption to LOCAL state only (no endpoint).
  useEffect(() => {
    const id = window.setTimeout(() => setSavedAt(Date.now()), 1000);
    return () => window.clearTimeout(id);
  }, [caption]);

  const addTag = () => {
    const cleaned = tagDraft.trim().replace(/^#+/, "").replace(/\s+/g, "");
    if (!cleaned) return;
    setHashtags((prev) => (prev.includes(cleaned) ? prev : [...prev, cleaned]));
    setTagDraft("");
  };

  const removeTag = (tag: string) => setHashtags((prev) => prev.filter((t) => t !== tag));

  const onTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    }
  };

  // STUB: there is no approve/schedule endpoint yet.
  const handleApprove = () => {
    toast("Post approval is being wired up", {
      description: "Approve & schedule ships when the backend endpoint lands.",
    });
  };

  const stageMeta = STAGE_META[post.stage];

  return (
    <div
      role="presentation"
      onClick={onClose}
      className="fixed inset-0 z-50 flex justify-center overflow-y-auto p-0 sm:p-6"
      style={{ backgroundColor: "rgba(20,17,13,0.55)" }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="relative flex min-h-full w-full max-w-5xl flex-col border border-hairline bg-surface outline-none sm:min-h-0"
      >
        {/* Header */}
        <div className="flex items-center justify-between gap-4 border-b border-hairline px-6 py-4">
          <div className="flex items-center gap-3">
            <Badge>{platformLabel(post.platform)}</Badge>
            <h2 id={titleId} className="font-display text-headline-sm text-ink">
              Review &amp; schedule
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="inline-flex h-9 w-9 items-center justify-center border border-hairline text-graphite transition-colors hover:bg-ink hover:text-surface"
          >
            <X size={16} strokeWidth={1.5} aria-hidden="true" />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-8 p-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          {/* Left: creative + live preview frame */}
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Creative</p>
              <div className="mx-auto w-full max-w-[400px]">
                {showShimmer ? (
                  <Skeleton className={`${formatRatioClass(post.format)} w-full`} />
                ) : (
                  <div
                    className={`${formatRatioClass(post.format)} flex w-full items-center justify-center border border-hairline bg-neutral`}
                  >
                    <span className="px-6 text-center font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                      {post.stage === "published"
                        ? "Creative ready"
                        : "Creative placeholder"}
                    </span>
                  </div>
                )}
              </div>
              {/* Live generation status for this post. */}
              <GenerationProgress postId={post.postId} hideCreative />
            </div>

            <div className="flex flex-col gap-2">
              <PlatformPreviewLabel platform={post.platform} />
              <div className="mx-auto w-full max-w-[400px]">
                <PlatformPreview
                  platform={post.platform}
                  caption={caption}
                  hashtags={hashtags}
                  loading={showShimmer}
                />
              </div>
            </div>
          </div>

          {/* Right: caption editor, hashtags, scheduling */}
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="approval-caption"
                  className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
                >
                  Caption
                </label>
                {savedAt ? (
                  <span className="font-mono text-mono-sm text-stone">Saved locally</span>
                ) : null}
              </div>
              <textarea
                id="approval-caption"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                rows={5}
                className="resize-none border border-hairline bg-neutral px-3 py-2.5 font-body text-body-sm text-ink outline-none transition-colors focus:border-signal"
              />
              <p className="font-mono text-mono-sm text-stone">
                Edits autosave to this session only — there&apos;s no caption endpoint yet.
              </p>
            </div>

            {/* Hashtag chips */}
            <div className="flex flex-col gap-2">
              <p className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
                Hashtags
              </p>
              {hashtags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {hashtags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1.5 rounded-full border border-hairline px-3 py-1 font-mono text-mono-sm text-ink"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        aria-label={`Remove #${tag}`}
                        className="text-stone transition-colors hover:text-signal"
                      >
                        <X size={12} strokeWidth={2} aria-hidden="true" />
                      </button>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="font-body text-body-sm text-stone">No hashtags yet.</p>
              )}
              <div className="flex items-center gap-2">
                <input
                  value={tagDraft}
                  onChange={(e) => setTagDraft(e.target.value)}
                  onKeyDown={onTagKeyDown}
                  placeholder="Add a hashtag"
                  aria-label="Add a hashtag"
                  className="flex-1 bg-transparent font-body text-body-sm text-ink outline-none transition-colors placeholder:text-stone border-0 border-b border-hairline px-0 py-2 focus:border-b-2 focus:border-b-signal"
                />
                <Button type="button" variant="ghost" onClick={addTag}>
                  Add
                </Button>
              </div>
            </div>

            {/* Scheduling picker */}
            <div className="flex flex-col gap-2">
              <p className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
                Schedule
              </p>
              <div className="flex flex-wrap gap-2">
                <ScheduleOption
                  active={scheduleMode === "now"}
                  onClick={() => setScheduleMode("now")}
                >
                  Now
                </ScheduleOption>
                <ScheduleOption
                  active={scheduleMode === "custom"}
                  onClick={() => setScheduleMode("custom")}
                >
                  Custom
                </ScheduleOption>
                <Tooltip label="Coming soon — needs the recommended-time API">
                  <button
                    type="button"
                    disabled
                    aria-disabled="true"
                    className="inline-flex items-center gap-2 rounded-full border border-hairline px-3 py-1.5 font-body text-label-sm uppercase tracking-[0.14em] text-stone opacity-50"
                  >
                    <Clock size={14} strokeWidth={1.5} aria-hidden="true" />
                    Best time
                  </button>
                </Tooltip>
              </div>

              {scheduleMode === "custom" ? (
                <input
                  type="datetime-local"
                  value={customAt}
                  min={minCustom}
                  onChange={(e) => setCustomAt(e.target.value)}
                  aria-label="Custom schedule time"
                  className="bg-transparent font-body text-body-md text-ink outline-none transition-colors border-0 border-t border-b border-hairline px-0 py-3 focus:border-b-2 focus:border-b-signal"
                />
              ) : scheduleMode === "best" ? null : (
                <p className="font-mono text-mono-sm text-stone">
                  Publishes as soon as approval is available.
                </p>
              )}
            </div>

            <div className="mt-auto flex flex-col gap-3 border-t border-hairline pt-6">
              <div className="flex flex-wrap items-center gap-3">
                <Button type="button" onClick={handleApprove}>
                  <Sparkles size={16} strokeWidth={1.5} aria-hidden="true" />
                  Approve &amp; schedule
                </Button>
                {/* [CANVA_NEXT_UPDATE] Edit in Canva */}
                <Tooltip label="Coming soon — Canva editing lands with the next update">
                  <Button type="button" variant="ghost" disabled aria-disabled="true">
                    Edit in Canva
                  </Button>
                </Tooltip>
                <Button type="button" variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
              </div>
              <p className="font-mono text-mono-sm text-stone">
                Approval is a stub — current stage: {stageMeta.label}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScheduleOption({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  if (active) {
    return (
      <Pill variant="ink" className="cursor-pointer">
        <button type="button" onClick={onClick} className="uppercase">
          {children}
        </button>
      </Pill>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-full border border-hairline px-3 py-1.5 font-body text-label-sm uppercase tracking-[0.14em] text-ink transition-colors hover:bg-neutral"
    >
      {children}
    </button>
  );
}
