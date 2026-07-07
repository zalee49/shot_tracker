"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { beanKey, type Shot } from "@/lib/shots";
import { useTargetRatio } from "@/lib/useTargetRatio";
import { ShotCard } from "./ShotCard";

const ALL_BEANS = "__all__";
const SEARCH_FIELDS = ["bean_name", "roaster", "origin", "tasting_notes"] as const;

interface HistoryListProps {
  shots: Shot[];
  beanNames: string[];
  previousById: Record<number, Shot | null>;
}

export function HistoryList({ shots, beanNames, previousById }: HistoryListProps) {
  const [search, setSearch] = useState("");
  const [beanFilter, setBeanFilter] = useState(ALL_BEANS);
  const [targetRatio] = useTargetRatio();

  const filteredShots = useMemo(() => {
    let filtered = shots;
    if (beanFilter !== ALL_BEANS) {
      const filterKey = beanKey(beanFilter);
      filtered = filtered.filter((shot) => beanKey(shot.bean_name) === filterKey);
    }
    const query = search.trim().toLowerCase();
    if (query) {
      filtered = filtered.filter((shot) =>
        SEARCH_FIELDS.some((field) => shot[field].toLowerCase().includes(query)),
      );
    }
    return filtered;
  }, [shots, search, beanFilter]);

  return (
    <div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search beans, roasters, origins, or notes"
            className="h-11 bg-card pl-9"
            aria-label="Search history"
          />
        </div>
        <Select value={beanFilter} onValueChange={setBeanFilter}>
          <SelectTrigger
            className="h-11 w-full bg-card sm:w-48"
            aria-label="Filter by bean"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_BEANS}>All beans</SelectItem>
            {beanNames.map((name) => (
              <SelectItem key={name} value={name}>
                {name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <p className="tnum mb-3 mt-2.5 text-xs text-muted-foreground">
        Showing {filteredShots.length} of {shots.length} shots
      </p>

      {filteredShots.length === 0 ? (
        <div className="rounded-xl border border-dashed border-input bg-card px-4 py-10 text-center text-sm text-muted-foreground">
          No shots match those filters.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredShots.map((shot, index) => (
            <ShotCard
              key={shot.id ?? `row-${index}`}
              shot={shot}
              previousShot={shot.id !== null ? previousById[shot.id] ?? null : null}
              targetRatio={targetRatio}
            />
          ))}
        </div>
      )}
    </div>
  );
}
