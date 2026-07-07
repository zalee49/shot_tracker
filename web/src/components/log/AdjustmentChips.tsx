"use client";

import { ADJUSTMENT_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface AdjustmentChipsProps {
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function AdjustmentChips({ selected, onChange }: AdjustmentChipsProps) {
  function toggle(option: string) {
    if (selected.includes(option)) {
      onChange(selected.filter((item) => item !== option));
    } else {
      onChange([...selected, option]);
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label="Adjustments vs last shot">
      {ADJUSTMENT_OPTIONS.map((option) => {
        const active = selected.includes(option);
        return (
          <button
            key={option}
            type="button"
            onClick={() => toggle(option)}
            aria-pressed={active}
            className={cn(
              "min-h-9 rounded-full border px-3 text-[0.8rem] font-medium transition-colors",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-input bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground",
            )}
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}
