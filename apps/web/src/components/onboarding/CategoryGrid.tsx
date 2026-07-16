"use client";

import { CATEGORIES, CATEGORY_KEYS } from "@iievi/constants";

/** The category grid shown at the category_select stage; a click sends the choice. */
export function CategoryGrid({
  onSelect,
  disabled = false,
}: {
  onSelect: (displayName: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {CATEGORY_KEYS.map((key) => {
        const category = CATEGORIES[key];
        return (
          <button
            key={key}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(category.displayName)}
            className="flex items-start gap-3 border border-hairline p-3 text-left transition-colors hover:border-ink hover:bg-neutral disabled:opacity-50"
          >
            <span aria-hidden="true" className="text-xl leading-none">
              {category.emoji}
            </span>
            <span className="min-w-0">
              <span className="block font-body text-body-sm text-ink">{category.displayName}</span>
              <span className="mt-0.5 block font-body text-mono-sm text-stone">
                {category.description}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
