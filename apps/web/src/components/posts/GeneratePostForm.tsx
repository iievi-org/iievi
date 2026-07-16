"use client";

import type { GeneratePostBody } from "@iievi/api-client";
import type { GeneratePostResponse } from "@iievi/types";
import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/linen";
import { api } from "@/lib/api";

import { POST_FORMATS, POST_PLATFORMS, type PostFormat, type PostPlatform, type SessionPost } from "./types";

interface GeneratePostFormProps {
  /** Called with the seeded session post once generation is queued (HTTP 202). */
  onQueued: (post: SessionPost) => void;
}

const TOPIC_MIN = 3;
const TOPIC_MAX = 280;

/** Shared field-label styling (mirrors the Linen Input label). */
const labelCls = "font-body text-label-sm uppercase tracking-[0.14em] text-stone";
const selectCls =
  "bg-transparent text-ink font-body text-body-md border-0 border-t border-b border-hairline px-0 py-3 outline-none focus:border-b-2 focus:border-b-signal transition-colors";

export function GeneratePostForm({ onQueued }: GeneratePostFormProps) {
  const [platform, setPlatform] = useState<PostPlatform>("instagram");
  const [topic, setTopic] = useState("");
  const [format, setFormat] = useState<PostFormat>("square");
  const [scheduleLocal, setScheduleLocal] = useState("");
  const [touched, setTouched] = useState(false);

  const trimmedTopic = topic.trim();
  const topicError =
    touched && trimmedTopic.length < TOPIC_MIN
      ? `Add at least ${TOPIC_MIN} characters describing the post.`
      : null;

  const mutation = useMutation<GeneratePostResponse, unknown, GeneratePostBody>({
    mutationFn: (payload) => api.posts.generate(payload),
    onSuccess: (data) => {
      onQueued({
        postId: data.post_id,
        platform,
        topic: trimmedTopic,
        format,
        stage: "draft",
      });
      toast.success("Post queued — generating now.");
      setTopic("");
      setScheduleLocal("");
      setTouched(false);
    },
    onError: () => {
      toast.error("Couldn't start generation. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (trimmedTopic.length < TOPIC_MIN) return;

    // exactOptionalPropertyTypes: only include optional keys when they have a
    // value — never pass `undefined` to an optional field.
    const payload: GeneratePostBody = {
      platform,
      topic: trimmedTopic,
      format,
      ...(scheduleLocal ? { scheduled_at: new Date(scheduleLocal).toISOString() } : {}),
    };
    mutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6 border border-hairline bg-neutral p-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label htmlFor="post-platform" className={labelCls}>
            Platform
          </label>
          <select
            id="post-platform"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as PostPlatform)}
            className={selectCls}
          >
            {POST_PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="post-format" className={labelCls}>
            Format
          </label>
          <select
            id="post-format"
            value={format}
            onChange={(e) => setFormat(e.target.value as PostFormat)}
            className={selectCls}
          >
            {POST_FORMATS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="post-topic" className={labelCls}>
          Topic
        </label>
        <textarea
          id="post-topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onBlur={() => setTouched(true)}
          rows={3}
          maxLength={TOPIC_MAX}
          placeholder="e.g. A weekend promo on our deep-clean package for busy families."
          aria-invalid={topicError ? true : undefined}
          className="resize-none bg-transparent font-body text-body-md text-ink outline-none transition-colors placeholder:text-stone border-0 border-t border-b border-hairline px-0 py-3 focus:border-b-2 focus:border-b-signal"
        />
        <div className="flex items-center justify-between">
          {topicError ? (
            <p className="font-mono text-mono-sm text-signal" role="alert">
              {topicError}
            </p>
          ) : (
            <span aria-hidden="true" />
          )}
          <span className="font-mono text-mono-sm text-stone">
            {trimmedTopic.length}/{TOPIC_MAX}
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="post-schedule" className={labelCls}>
          Schedule (optional)
        </label>
        <input
          id="post-schedule"
          type="datetime-local"
          value={scheduleLocal}
          onChange={(e) => setScheduleLocal(e.target.value)}
          className={selectCls}
        />
        <p className="font-mono text-mono-sm text-stone">
          Leave blank to generate immediately.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={mutation.isPending}>
          <Sparkles size={16} strokeWidth={1.5} aria-hidden="true" />
          {mutation.isPending ? "Queuing…" : "Generate post"}
        </Button>
      </div>
    </form>
  );
}
