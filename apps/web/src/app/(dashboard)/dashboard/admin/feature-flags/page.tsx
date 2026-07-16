"use client";

import type { FeatureFlag, Plan } from "@iievi/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldAlert, ToggleRight } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { FlagRow } from "@/components/admin/FlagRow";
import { Button, Card, Container, Input } from "@/components/linen";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const FLAGS_KEY = ["feature-flags"] as const;
const PLANS: readonly Plan[] = ["trial", "starter", "growth", "agency"];

// Backend-enforced flag_key shape: lowercase letters, digits, and . _ -
const FLAG_KEY_PATTERN = "[a-z0-9._-]+";

interface CreateState {
  flag_key: string;
  description: string;
  minimum_plan: "" | Plan;
  enabled_globally: boolean;
}

const INITIAL_CREATE: CreateState = {
  flag_key: "",
  description: "",
  minimum_plan: "",
  enabled_globally: false,
};

export default function FeatureFlagsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CreateState>(INITIAL_CREATE);

  const {
    data: flags,
    isPending,
    isError,
    error,
  } = useQuery<FeatureFlag[]>({
    queryKey: FLAGS_KEY,
    queryFn: () => api.admin.flags.list(),
    enabled: Boolean(user?.isAdmin),
  });

  const create = useMutation<FeatureFlag, Error, void>({
    mutationFn: () => {
      // Build the body conditionally so we never pass explicit `undefined` to
      // optional fields (exactOptionalPropertyTypes).
      const trimmedDescription = form.description.trim();
      return api.admin.flags.create({
        flag_key: form.flag_key.trim(),
        enabled_globally: form.enabled_globally,
        ...(trimmedDescription ? { description: trimmedDescription } : {}),
        ...(form.minimum_plan ? { minimum_plan: form.minimum_plan } : {}),
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FLAGS_KEY });
      toast.success(`Created “${form.flag_key.trim()}”.`);
      setForm(INITIAL_CREATE);
    },
    onError: (mutationError) => {
      toast.error(mutationError instanceof Error ? mutationError.message : "Failed to create flag.");
    },
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

  const canCreate = FLAG_KEY_RE.test(form.flag_key.trim());

  const handleCreate = (event: React.FormEvent): void => {
    event.preventDefault();
    if (!canCreate) {
      toast.error("Flag key must be lowercase letters, digits, or . _ -");
      return;
    }
    create.mutate();
  };

  return (
    <Container className="py-10 md:py-16">
      <header className="flex items-start gap-3">
        <ToggleRight aria-hidden="true" className="mt-1 h-6 w-6 shrink-0 text-signal" />
        <div>
          <h1 className="font-display text-headline-lg text-ink">Feature Flags</h1>
          <p className="mt-1 font-body text-body-sm text-graphite">
            Roll features out per-tenant, then globally.
          </p>
        </div>
      </header>

      {/* Create flag */}
      <Card variant="paper" className="mt-8">
        <h2 className="font-display text-headline-sm text-ink">Create flag</h2>
        <form onSubmit={handleCreate} className="mt-5 flex flex-wrap items-end gap-x-6 gap-y-4">
          <Input
            label="Flag key"
            name="flag_key"
            required
            pattern={FLAG_KEY_PATTERN}
            placeholder="new_feature.enabled"
            value={form.flag_key}
            onChange={(event) => setForm((prev) => ({ ...prev, flag_key: event.target.value }))}
            fieldClassName="min-w-[240px] flex-1"
            className="font-mono text-mono-sm"
            {...(form.flag_key.trim() && !canCreate
              ? { error: "Lowercase letters, digits, or . _ - only" }
              : {})}
          />
          <Input
            label="Description"
            name="description"
            placeholder="What does this gate?"
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            fieldClassName="min-w-[240px] flex-1"
          />
          <div className="flex min-w-[160px] flex-col gap-1">
            <label
              htmlFor="minimum_plan"
              className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
            >
              Minimum plan
            </label>
            <select
              id="minimum_plan"
              name="minimum_plan"
              value={form.minimum_plan}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, minimum_plan: event.target.value as "" | Plan }))
              }
              className="border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-body text-body-md text-ink outline-none transition-colors focus:border-b-2 focus:border-b-signal"
            >
              <option value="">None</option>
              {PLANS.map((plan) => (
                <option key={plan} value={plan}>
                  {plan}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 py-3 font-body text-body-sm text-ink">
            <input
              type="checkbox"
              checked={form.enabled_globally}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, enabled_globally: event.target.checked }))
              }
              className="h-4 w-4 accent-signal"
            />
            Enabled globally
          </label>
          <Button type="submit" disabled={create.isPending || !canCreate}>
            {create.isPending ? "Creating…" : "Create"}
          </Button>
        </form>
      </Card>

      {/* Flag list */}
      <div className="mt-10">
        {isPending ? (
          <p className="py-16 text-center font-body text-body-sm text-graphite">Loading flags…</p>
        ) : isError ? (
          <p className="py-16 text-center font-mono text-mono-sm text-signal" role="alert">
            {error instanceof Error ? error.message : "Failed to load feature flags."}
          </p>
        ) : (flags?.length ?? 0) === 0 ? (
          <p className="py-16 text-center font-body text-body-sm text-graphite">
            No feature flags yet — create one above.
          </p>
        ) : (
          <ul className="flex flex-col gap-4">
            {flags?.map((flag) => <FlagRow key={flag.flag_key} flag={flag} />)}
          </ul>
        )}
      </div>
    </Container>
  );
}

// Runtime counterpart of FLAG_KEY_PATTERN, anchored for full-string validation.
const FLAG_KEY_RE = /^[a-z0-9._-]+$/;
