"use client";

import type { NotificationPreferences } from "@iievi/types";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/linen";
import { api } from "@/lib/api";

// NOTE: the API client exposes no GET for notification preferences (only
// PATCH /users/notification-preferences via api.notifications.updatePreferences).
// We therefore initialise the form from sensible defaults; a future GET can
// hydrate these once the endpoint exists.
const DEFAULTS: Pick<
  NotificationPreferences,
  | "in_app_enabled"
  | "email_enabled"
  | "whatsapp_enabled"
  | "quiet_hours_start"
  | "quiet_hours_end"
  | "quiet_hours_days"
> = {
  in_app_enabled: true,
  email_enabled: true,
  whatsapp_enabled: false,
  quiet_hours_start: null,
  quiet_hours_end: null,
  quiet_hours_days: [],
};

/** 0 = Monday … 6 = Sunday, matching the backend's ISO weekday convention. */
const WEEKDAYS: { value: number; label: string }[] = [
  { value: 0, label: "Mon" },
  { value: 1, label: "Tue" },
  { value: 2, label: "Wed" },
  { value: 3, label: "Thu" },
  { value: 4, label: "Fri" },
  { value: 5, label: "Sat" },
  { value: 6, label: "Sun" },
];

const CHANNELS: {
  key: "in_app_enabled" | "email_enabled" | "whatsapp_enabled";
  label: string;
  hint: string;
}[] = [
  { key: "in_app_enabled", label: "In-app", hint: "Bell notifications inside iievi." },
  { key: "email_enabled", label: "Email", hint: "Digests and important alerts by email." },
  { key: "whatsapp_enabled", label: "WhatsApp", hint: "Urgent alerts on WhatsApp." },
];

export function NotificationsSection() {
  const [inApp, setInApp] = useState(DEFAULTS.in_app_enabled);
  const [email, setEmail] = useState(DEFAULTS.email_enabled);
  const [whatsapp, setWhatsapp] = useState(DEFAULTS.whatsapp_enabled);
  const [quietStart, setQuietStart] = useState(DEFAULTS.quiet_hours_start ?? "");
  const [quietEnd, setQuietEnd] = useState(DEFAULTS.quiet_hours_end ?? "");
  const [quietDays, setQuietDays] = useState<number[]>(DEFAULTS.quiet_hours_days);

  const channelValue = (key: (typeof CHANNELS)[number]["key"]): boolean =>
    key === "in_app_enabled" ? inApp : key === "email_enabled" ? email : whatsapp;

  const setChannel = (key: (typeof CHANNELS)[number]["key"], next: boolean) => {
    if (key === "in_app_enabled") setInApp(next);
    else if (key === "email_enabled") setEmail(next);
    else setWhatsapp(next);
  };

  const toggleDay = (day: number) => {
    setQuietDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort((a, b) => a - b),
    );
  };

  const save = useMutation({
    mutationFn: () => {
      // Build with conditional spread so we never send explicit `undefined`
      // (exactOptionalPropertyTypes). Empty time strings become `null`.
      const payload: Partial<NotificationPreferences> = {
        in_app_enabled: inApp,
        email_enabled: email,
        whatsapp_enabled: whatsapp,
        quiet_hours_start: quietStart ? quietStart : null,
        quiet_hours_end: quietEnd ? quietEnd : null,
        quiet_hours_days: quietDays,
      };
      return api.notifications.updatePreferences(payload);
    },
    onSuccess: () => toast.success("Notification preferences saved"),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Couldn't save preferences"),
  });

  return (
    <div className="flex max-w-2xl flex-col gap-10">
      {/* Channels */}
      <section aria-labelledby="channels-heading">
        <h3 id="channels-heading" className="font-display text-headline-sm text-ink">
          Channels
        </h3>
        <p className="mt-1 font-body text-body-sm text-stone">
          Choose where iievi reaches you.
        </p>
        <ul className="mt-5 flex flex-col divide-y divide-hairline border-y border-hairline">
          {CHANNELS.map((channel) => {
            const on = channelValue(channel.key);
            return (
              <li key={channel.key} className="flex items-center justify-between gap-4 py-4">
                <div className="min-w-0">
                  <p className="font-body text-body-md text-ink">{channel.label}</p>
                  <p className="font-body text-body-sm text-stone">{channel.hint}</p>
                </div>
                <Switch
                  checked={on}
                  onChange={(next) => setChannel(channel.key, next)}
                  label={`${channel.label} notifications`}
                />
              </li>
            );
          })}
        </ul>
      </section>

      {/* Quiet hours */}
      <section aria-labelledby="quiet-heading">
        <h3 id="quiet-heading" className="font-display text-headline-sm text-ink">
          Quiet hours
        </h3>
        <p className="mt-1 font-body text-body-sm text-stone">
          Pause non-urgent notifications during these times.
        </p>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label
              htmlFor="quiet_start"
              className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
            >
              From
            </label>
            <input
              id="quiet_start"
              type="time"
              value={quietStart}
              onChange={(event) => setQuietStart(event.target.value)}
              className="border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-mono text-mono-sm text-ink outline-none transition-colors focus:border-b-2 focus:border-b-signal"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label
              htmlFor="quiet_end"
              className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
            >
              To
            </label>
            <input
              id="quiet_end"
              type="time"
              value={quietEnd}
              onChange={(event) => setQuietEnd(event.target.value)}
              className="border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-mono text-mono-sm text-ink outline-none transition-colors focus:border-b-2 focus:border-b-signal"
            />
          </div>
        </div>

        <fieldset className="mt-6">
          <legend className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
            On these days
          </legend>
          <div className="mt-3 flex flex-wrap gap-2">
            {WEEKDAYS.map((day) => {
              const selected = quietDays.includes(day.value);
              return (
                <button
                  key={day.value}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => toggleDay(day.value)}
                  className={`min-w-[3rem] border px-3 py-2 font-body text-label-sm uppercase tracking-[0.1em] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal ${
                    selected
                      ? "border-ink bg-ink text-surface"
                      : "border-hairline text-graphite hover:border-ink hover:text-ink"
                  }`}
                >
                  {day.label}
                </button>
              );
            })}
          </div>
        </fieldset>
      </section>

      <div>
        <Button type="button" onClick={() => save.mutate()} disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save preferences"}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Accessible switch
// ---------------------------------------------------------------------------

function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal ${
        checked ? "border-signal bg-signal" : "border-hairline bg-neutral"
      }`}
    >
      <span
        aria-hidden="true"
        className={`inline-block h-4 w-4 rounded-full bg-surface transition-transform ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}
