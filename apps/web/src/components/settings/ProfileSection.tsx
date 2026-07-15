"use client";

import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import type { ServiceItem } from "@iievi/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { toast } from "sonner";

import { Button, Input } from "@/components/linen";
import { useProfile } from "@/hooks/useProfile";
import { api } from "@/lib/api";

import { AccordionPanel } from "./Accordion";
import { SortableServiceRow } from "./SortableServiceRow";

const PROFILE_KEY = ["profile"] as const;

type PanelKey = "business" | "services" | "brand";

function errMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export function ProfileSection() {
  const { data: profile, isLoading, isError } = useProfile();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState<PanelKey | null>("business");

  const toggle = (panel: PanelKey) => setOpen((prev) => (prev === panel ? null : panel));

  if (isLoading) {
    return (
      <p className="font-body text-body-sm text-stone" role="status">
        Loading your profile…
      </p>
    );
  }
  if (isError || !profile) {
    return (
      <p className="border border-hairline bg-neutral px-4 py-3 font-body text-body-sm text-signal">
        We couldn&rsquo;t load your profile. Please refresh and try again.
      </p>
    );
  }

  const businessProfile = profile.business_profile;
  const services = businessProfile?.services.items ?? [];

  return (
    <div className="flex flex-col gap-4">
      <AccordionPanel
        title="Business Info"
        summary={businessProfile?.business_name ?? "Not set yet"}
        open={open === "business"}
        onToggle={() => toggle("business")}
      >
        <BusinessInfoPanel
          initialName={businessProfile?.business_name ?? ""}
          initialDescription={businessProfile?.description ?? ""}
          queryClient={queryClient}
        />
      </AccordionPanel>

      <AccordionPanel
        title="Services"
        summary={`${services.length} ${services.length === 1 ? "service" : "services"}`}
        open={open === "services"}
        onToggle={() => toggle("services")}
      >
        <ServicesPanel services={services} queryClient={queryClient} />
      </AccordionPanel>

      <AccordionPanel
        title="Brand Identity"
        summary="Colours used across generated posts"
        open={open === "brand"}
        onToggle={() => toggle("brand")}
      >
        <BrandIdentityPanel
          colors={profile.brand_kit?.colors ?? {}}
          queryClient={queryClient}
        />
      </AccordionPanel>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 1. Business Info
// ---------------------------------------------------------------------------

function BusinessInfoPanel({
  initialName,
  initialDescription,
  queryClient,
}: {
  initialName: string;
  initialDescription: string;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);

  // Re-sync local state if the underlying profile changes (e.g. after invalidate).
  useEffect(() => setName(initialName), [initialName]);
  useEffect(() => setDescription(initialDescription), [initialDescription]);

  const save = useMutation({
    mutationFn: () =>
      api.profiles.update({ business_name: name.trim(), description: description.trim() }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_KEY });
      toast.success("Business info saved");
    },
    onError: (error) => toast.error(errMessage(error, "Couldn't save business info")),
  });

  const dirty = name.trim() !== initialName.trim() || description.trim() !== initialDescription.trim();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) {
      toast.error("Business name can't be empty");
      return;
    }
    save.mutate();
  };

  return (
    <form onSubmit={submit} className="flex max-w-2xl flex-col gap-6">
      <Input
        label="Business name"
        name="business_name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="e.g. Sattva Care"
      />

      <div className="flex flex-col gap-1">
        <label
          htmlFor="business_description"
          className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
        >
          Description
        </label>
        <textarea
          id="business_description"
          name="business_description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={4}
          placeholder="What does your business do, and for whom?"
          className="resize-y border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-body text-body-md text-ink outline-none transition-colors placeholder:text-stone focus:border-b-2 focus:border-b-signal"
        />
      </div>

      <div>
        <Button type="submit" disabled={save.isPending || !dirty}>
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// 2. Services (drag-drop reorder + add/delete)
// ---------------------------------------------------------------------------

function ServicesPanel({
  services,
  queryClient,
}: {
  services: ServiceItem[];
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  // NOTE: There is NO reorder-persistence endpoint (the API exposes only
  // POST /profiles/services and DELETE /profiles/services/{index}). Drag reorder
  // is therefore VISUAL / LOCAL ONLY — `order` is client state and is reset to
  // the server's order whenever the profile refetches.
  const [order, setOrder] = useState<number[]>(() => services.map((_, i) => i));

  useEffect(() => {
    setOrder(services.map((_, i) => i));
  }, [services]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setOrder((prev) => {
      const from = prev.indexOf(Number(active.id));
      const to = prev.indexOf(Number(over.id));
      if (from === -1 || to === -1) return prev;
      return arrayMove(prev, from, to);
    });
  };

  const deleteService = useMutation({
    // The index passed to the API is the *original* index into services[].
    mutationFn: (index: number) => api.profiles.deleteService(index),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_KEY });
      toast.success("Service removed");
    },
    onError: (error) => toast.error(errMessage(error, "Couldn't remove service")),
  });

  return (
    <div className="flex flex-col gap-6">
      {services.length === 0 ? (
        <p className="font-body text-body-sm text-stone">
          No services yet. Add one below so iievi can quote prices in conversations.
        </p>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={onDragEnd}
        >
          <SortableContext
            items={order.map((i) => String(i))}
            strategy={verticalListSortingStrategy}
          >
            <ul className="flex flex-col gap-2">
              {order.map((originalIndex) => {
                const service = services[originalIndex];
                if (!service) return null;
                return (
                  <SortableServiceRow
                    key={originalIndex}
                    id={String(originalIndex)}
                    service={service}
                    onDelete={() => deleteService.mutate(originalIndex)}
                    deleting={deleteService.isPending}
                  />
                );
              })}
            </ul>
          </SortableContext>
        </DndContext>
      )}

      <AddServiceForm queryClient={queryClient} />
    </div>
  );
}

function AddServiceForm({ queryClient }: { queryClient: ReturnType<typeof useQueryClient> }) {
  const [name, setName] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [unit, setUnit] = useState("");
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setName("");
    setPriceMin("");
    setPriceMax("");
    setUnit("");
    setError(null);
  };

  const add = useMutation({
    mutationFn: (item: ServiceItem) => api.profiles.addService(item),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_KEY });
      toast.success("Service added");
      reset();
    },
    onError: (mutationError) => toast.error(errMessage(mutationError, "Couldn't add service")),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Give the service a name.");
      return;
    }
    const min = Number(priceMin);
    const max = Number(priceMax);
    if (!Number.isFinite(min) || !Number.isFinite(max) || min < 0 || max < 0) {
      setError("Enter valid prices in rupees.");
      return;
    }
    if (max < min) {
      setError("Maximum price must be at least the minimum.");
      return;
    }

    // ₹ → paise (integer).
    add.mutate({
      name: trimmedName,
      price_min_paise: Math.round(min * 100),
      price_max_paise: Math.round(max * 100),
      unit: unit.trim(),
    });
  };

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-4 border border-hairline bg-neutral p-5"
      aria-label="Add a service"
    >
      <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Add service</p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Name"
          name="new_service_name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="e.g. Deep tissue massage"
          fieldClassName="sm:col-span-2"
        />
        <Input
          label="Min price (₹)"
          name="new_service_price_min"
          type="number"
          min={0}
          inputMode="numeric"
          value={priceMin}
          onChange={(event) => setPriceMin(event.target.value)}
          placeholder="1500"
        />
        <Input
          label="Max price (₹)"
          name="new_service_price_max"
          type="number"
          min={0}
          inputMode="numeric"
          value={priceMax}
          onChange={(event) => setPriceMax(event.target.value)}
          placeholder="2500"
        />
        <Input
          label="Unit"
          name="new_service_unit"
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
          placeholder="e.g. session"
          fieldClassName="sm:col-span-2"
        />
      </div>

      {error ? (
        <p className="font-mono text-mono-sm text-signal" role="alert">
          {error}
        </p>
      ) : null}

      <div>
        <Button type="submit" variant="ghost" disabled={add.isPending}>
          <Plus aria-hidden="true" size={16} strokeWidth={1.75} />
          {add.isPending ? "Adding…" : "Add service"}
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// 3. Brand Identity (live preview)
// ---------------------------------------------------------------------------

/** Read a colour from the untyped colors JSONB, falling back to a default hex. */
function colorOf(colors: Record<string, unknown>, key: string, fallback: string): string {
  const value = colors[key];
  return typeof value === "string" && value.trim() !== "" ? value : fallback;
}

function BrandIdentityPanel({
  colors,
  queryClient,
}: {
  colors: Record<string, unknown>;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const initial = {
    primary: colorOf(colors, "primary", "#14110d"),
    secondary: colorOf(colors, "secondary", "#6b6459"),
    accent: colorOf(colors, "accent", "#c2410c"),
  };
  const [primary, setPrimary] = useState(initial.primary);
  const [secondary, setSecondary] = useState(initial.secondary);
  const [accent, setAccent] = useState(initial.accent);

  useEffect(() => setPrimary(initial.primary), [initial.primary]);
  useEffect(() => setSecondary(initial.secondary), [initial.secondary]);
  useEffect(() => setAccent(initial.accent), [initial.accent]);

  const save = useMutation({
    mutationFn: () => api.profiles.update({ colors: { primary, secondary, accent } }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_KEY });
      toast.success("Brand colours saved");
    },
    onError: (error) => toast.error(errMessage(error, "Couldn't save brand colours")),
  });

  const swatches: { key: "primary" | "secondary" | "accent"; label: string; value: string; set: (v: string) => void }[] =
    [
      { key: "primary", label: "Primary", value: primary, set: setPrimary },
      { key: "secondary", label: "Secondary", value: secondary, set: setSecondary },
      { key: "accent", label: "Accent", value: accent, set: setAccent },
    ];

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
      {/* Colour inputs */}
      <div className="flex flex-col gap-5">
        {swatches.map((swatch) => (
          <ColorField
            key={swatch.key}
            id={`brand-${swatch.key}`}
            label={swatch.label}
            value={swatch.value}
            onChange={swatch.set}
          />
        ))}

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Button type="button" onClick={() => save.mutate()} disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save colours"}
          </Button>

          {/* [CANVA_NEXT_UPDATE] Sync Canva Brand Kit */}
          <Button type="button" variant="ghost" disabled aria-disabled="true">
            Sync Brand Kit
          </Button>
        </div>
      </div>

      {/* Live preview panel — recolours in real time as the inputs change */}
      <div className="border border-hairline bg-neutral p-6">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Live preview</p>

        <div className="mt-4 flex gap-3">
          {swatches.map((swatch) => (
            <div key={swatch.key} className="flex flex-1 flex-col items-center gap-2">
              <span
                aria-hidden="true"
                className="h-14 w-full border border-hairline"
                style={{ backgroundColor: swatch.value }}
              />
              <span className="font-mono text-mono-sm text-graphite">{swatch.label}</span>
            </div>
          ))}
        </div>

        {/* Sample card that adopts the brand colours */}
        <div
          className="mt-6 border p-5"
          style={{ borderColor: secondary, backgroundColor: "var(--linen-surface, #faf7f2)" }}
        >
          <p className="font-display text-headline-sm" style={{ color: primary }}>
            Your brand, applied
          </p>
          <p className="mt-2 font-body text-body-sm" style={{ color: secondary }}>
            This is how your colours read on a generated card.
          </p>
          <span
            className="mt-4 inline-flex items-center px-4 py-2 font-body text-label-sm uppercase tracking-[0.14em]"
            style={{ backgroundColor: accent, color: "#ffffff" }}
          >
            Sample button
          </span>
        </div>
      </div>
    </div>
  );
}

function ColorField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
        {label}
      </label>
      <div className="flex items-center gap-3">
        <input
          id={id}
          type="color"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-label={`${label} colour`}
          className="h-10 w-12 shrink-0 cursor-pointer border border-hairline bg-transparent p-0"
        />
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-label={`${label} colour hex`}
          spellCheck={false}
          className="w-full border-0 border-b border-t border-hairline bg-transparent px-0 py-2 font-mono text-mono-sm text-ink outline-none transition-colors focus:border-b-2 focus:border-b-signal"
        />
      </div>
    </div>
  );
}
