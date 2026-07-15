"use client";

import { type BusinessCategory, CATEGORIES, CATEGORY_KEYS } from "@iievi/constants";

interface CategoryModalProps {
  open: boolean;
  onSelect: (key: BusinessCategory) => void;
  onClose: () => void;
}

/** The 16-category picker shown during registration. */
export function CategoryModal({ open, onSelect, onClose }: CategoryModalProps) {
  if (!open) return null;
  return (
    <div
      role="presentation"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ backgroundColor: "rgba(20,17,13,0.55)" }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="category-title"
        onClick={(e) => e.stopPropagation()}
        className="max-h-[80vh] w-full max-w-2xl overflow-auto border border-hairline bg-surface p-8"
      >
        <h2 id="category-title" className="font-display text-headline-md text-ink">
          What kind of business?
        </h2>
        <p className="mt-2 font-body text-body-sm text-graphite">
          Pick the closest match — you can refine it during setup.
        </p>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {CATEGORY_KEYS.map((key) => {
            const category = CATEGORIES[key];
            return (
              <button
                key={key}
                type="button"
                onClick={() => onSelect(key)}
                className="flex flex-col items-start gap-2 border border-hairline p-4 text-left transition-colors hover:bg-ink hover:text-surface"
              >
                <span aria-hidden="true" className="text-2xl">
                  {category.emoji}
                </span>
                <span className="font-body text-body-sm">{category.displayName}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
