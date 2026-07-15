"use client";

import type { FeatureFlag } from "@iievi/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge, Button, Input } from "@/components/linen";
import { api } from "@/lib/api";

const FLAGS_KEY = ["feature-flags"] as const;

/** Show at most this many tenant UUIDs inline; the rest collapse into a count. */
const TENANT_PREVIEW = 5;

export function FlagRow({ flag }: { flag: FeatureFlag }) {
  const queryClient = useQueryClient();
  const [tenantInput, setTenantInput] = useState("");

  // --- Optimistic global toggle -------------------------------------------
  const toggle = useMutation<FeatureFlag, Error, boolean, { previous: FeatureFlag[] | undefined }>({
    mutationFn: (next: boolean) => api.admin.flags.patch(flag.flag_key, { enabled_globally: next }),
    onMutate: async (next) => {
      await queryClient.cancelQueries({ queryKey: FLAGS_KEY });
      const previous = queryClient.getQueryData<FeatureFlag[]>(FLAGS_KEY);
      queryClient.setQueryData<FeatureFlag[]>(FLAGS_KEY, (old) =>
        old?.map((item) =>
          item.flag_key === flag.flag_key ? { ...item, enabled_globally: next } : item,
        ),
      );
      return { previous };
    },
    onError: (mutationError, _next, context) => {
      if (context?.previous) queryClient.setQueryData(FLAGS_KEY, context.previous);
      toast.error(mutationError instanceof Error ? mutationError.message : "Failed to update flag.");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: FLAGS_KEY });
    },
  });

  // --- Add a tenant to the allow-list -------------------------------------
  const addTenant = useMutation<FeatureFlag, Error, string>({
    mutationFn: (tenantId: string) =>
      api.admin.flags.patch(flag.flag_key, { add_enabled_tenants: [tenantId] }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FLAGS_KEY });
      toast.success("Tenant enabled.");
      setTenantInput("");
    },
    onError: (mutationError) => {
      toast.error(mutationError instanceof Error ? mutationError.message : "Failed to add tenant.");
    },
  });

  // --- Remove a tenant from the allow-list --------------------------------
  const removeTenant = useMutation<FeatureFlag, Error, string>({
    mutationFn: (tenantId: string) =>
      api.admin.flags.patch(flag.flag_key, { remove_enabled_tenants: [tenantId] }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FLAGS_KEY });
      toast.success("Tenant removed.");
    },
    onError: (mutationError) => {
      toast.error(
        mutationError instanceof Error ? mutationError.message : "Failed to remove tenant.",
      );
    },
  });

  // --- Remove the whole flag ----------------------------------------------
  const removeFlag = useMutation<void, Error, void>({
    mutationFn: () => api.admin.flags.remove(flag.flag_key),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FLAGS_KEY });
      toast.success(`Removed “${flag.flag_key}”.`);
    },
    onError: (mutationError) => {
      toast.error(mutationError instanceof Error ? mutationError.message : "Failed to remove flag.");
    },
  });

  const enabled = flag.enabled_globally;
  const tenants = flag.enabled_for_tenants;
  const previewTenants = tenants.slice(0, TENANT_PREVIEW);
  const overflow = tenants.length - previewTenants.length;

  const handleAddTenant = (event: React.FormEvent): void => {
    event.preventDefault();
    const id = tenantInput.trim();
    if (!id) return;
    addTenant.mutate(id);
  };

  const handleRemoveFlag = (): void => {
    if (window.confirm(`Remove feature flag “${flag.flag_key}”? This cannot be undone.`)) {
      removeFlag.mutate();
    }
  };

  return (
    <li className="border border-hairline bg-transparent p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <code className="font-mono text-body-md text-ink">{flag.flag_key}</code>
            {flag.minimum_plan ? (
              <Badge>min plan · {flag.minimum_plan}</Badge>
            ) : null}
          </div>
          {flag.description ? (
            <p className="mt-1 font-body text-body-sm text-graphite">{flag.description}</p>
          ) : (
            <p className="mt-1 font-body text-body-sm text-stone">No description</p>
          )}
        </div>

        {/* Global on/off switch */}
        <div className="flex items-center gap-3">
          <span className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {enabled ? "Global on" : "Global off"}
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            aria-label={`Toggle ${flag.flag_key} globally`}
            disabled={toggle.isPending}
            onClick={() => toggle.mutate(!enabled)}
            className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal disabled:opacity-50 ${
              enabled ? "border-signal bg-signal" : "border-hairline bg-neutral"
            }`}
          >
            <span
              aria-hidden="true"
              className={`inline-block h-4 w-4 rounded-full bg-surface transition-transform ${
                enabled ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Enabled tenants */}
      <div className="mt-5">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
          Enabled tenants ({tenants.length})
        </p>
        {tenants.length === 0 ? (
          <p className="mt-2 font-body text-body-sm text-stone">
            None — enable per-tenant below, or flip the global switch.
          </p>
        ) : (
          <ul className="mt-2 flex flex-wrap gap-2">
            {previewTenants.map((tenantId) => (
              <li
                key={tenantId}
                className="inline-flex items-center gap-1.5 border border-hairline px-2 py-0.5"
              >
                <span className="font-mono text-mono-sm text-ink">{tenantId}</span>
                <button
                  type="button"
                  aria-label={`Remove tenant ${tenantId}`}
                  disabled={removeTenant.isPending}
                  onClick={() => removeTenant.mutate(tenantId)}
                  className="text-stone transition-colors hover:text-signal disabled:opacity-50"
                >
                  <X aria-hidden="true" className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
            {overflow > 0 ? (
              <li className="inline-flex items-center font-mono text-mono-sm text-stone">
                +{overflow} more
              </li>
            ) : null}
          </ul>
        )}
      </div>

      {/* Per-flag actions */}
      <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
        <form onSubmit={handleAddTenant} className="flex items-end gap-3">
          <Input
            label="Enable for tenant"
            name={`add-tenant-${flag.flag_key}`}
            placeholder="tenant uuid…"
            value={tenantInput}
            onChange={(event) => setTenantInput(event.target.value)}
            fieldClassName="min-w-[240px]"
            className="font-mono text-mono-sm"
          />
          <Button type="submit" variant="ghost" disabled={addTenant.isPending || !tenantInput.trim()}>
            {addTenant.isPending ? "Adding…" : "Add"}
          </Button>
        </form>

        <button
          type="button"
          onClick={handleRemoveFlag}
          disabled={removeFlag.isPending}
          className="inline-flex items-center gap-1.5 font-body text-label-sm uppercase tracking-[0.14em] text-stone transition-colors hover:text-signal disabled:opacity-50"
        >
          <Trash2 aria-hidden="true" className="h-4 w-4" />
          {removeFlag.isPending ? "Removing…" : "Remove flag"}
        </button>
      </div>
    </li>
  );
}
