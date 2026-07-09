/**
 * Linen Pill primitive (outline variant), ported from
 * apps/marketing/src/components/linen/Pill.tsx. Pills are the only rounded
 * element in the design system.
 */
export function StatusPill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-hairline bg-transparent px-3 py-1.5 font-body text-label-sm uppercase tracking-label text-ink">
      {label}
    </span>
  );
}
