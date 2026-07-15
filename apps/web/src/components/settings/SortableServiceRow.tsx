"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ServiceItem } from "@iievi/types";
import { motion } from "framer-motion";
import { GripVertical, Trash2 } from "lucide-react";

import { LINEN_EASE } from "@/lib/animations";

/** ₹ from paise, thousands-grouped for Indian display. */
function rupees(paise: number): string {
  return (paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

interface SortableServiceRowProps {
  /** Stable id for dnd-kit (the item's original index, as a string). */
  id: string;
  service: ServiceItem;
  onDelete: () => void;
  deleting: boolean;
}

export function SortableServiceRow({ id, service, onDelete, deleting }: SortableServiceRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id,
  });

  const priceLabel =
    service.price_min_paise === service.price_max_paise
      ? `₹${rupees(service.price_min_paise)}`
      : `₹${rupees(service.price_min_paise)}–₹${rupees(service.price_max_paise)}`;

  return (
    <motion.li
      layout
      transition={{ duration: 0.25, ease: LINEN_EASE }}
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        ...(transition ? { transition } : {}),
      }}
      className={`flex items-center gap-3 border border-hairline bg-surface px-4 py-3 ${
        isDragging ? "relative z-10 opacity-90" : ""
      }`}
    >
      <button
        type="button"
        aria-label={`Reorder ${service.name}`}
        className="shrink-0 cursor-grab touch-none text-stone transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal active:cursor-grabbing"
        {...attributes}
        {...listeners}
      >
        <GripVertical aria-hidden="true" size={18} strokeWidth={1.5} />
      </button>

      <div className="min-w-0 flex-1">
        <p className="truncate font-body text-body-md text-ink">{service.name}</p>
        <p className="font-mono text-mono-sm text-graphite">
          {priceLabel}
          {service.unit ? <span className="text-stone"> / {service.unit}</span> : null}
        </p>
      </div>

      <button
        type="button"
        onClick={onDelete}
        disabled={deleting}
        aria-label={`Delete ${service.name}`}
        className="shrink-0 text-stone transition-colors hover:text-signal focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal disabled:opacity-50"
      >
        <Trash2 aria-hidden="true" size={16} strokeWidth={1.5} />
      </button>
    </motion.li>
  );
}
