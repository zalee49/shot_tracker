"use client";

import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { brewRatio, formatRatio, ratioFlag } from "@/lib/coaching";
import { metricDeltas } from "@/lib/deltas";
import { displayDate, scoreText } from "@/lib/format";
import type { Shot } from "@/lib/shots";
import { cn } from "@/lib/utils";
import { DeleteShotDialog } from "./DeleteShotDialog";

interface ShotCardProps {
  shot: Shot;
  previousShot: Shot | null;
  targetRatio: number;
}

export function ShotCard({ shot, previousShot, targetRatio }: ShotCardProps) {
  const beanName = shot.bean_name || "Unknown bean";
  const ratio = brewRatio(shot.yield, shot.dose);
  const flag = ratioFlag(shot.yield, shot.dose, targetRatio);
  const deltas = metricDeltas(shot, previousShot);

  const shortFlag =
    flag === null ? "—" : flag.status === "on-target" ? "On target" : flag.status === "over" ? "Over" : "Under";
  const pillClass =
    flag === null
      ? "bg-muted text-muted-foreground"
      : flag.status === "on-target"
        ? "bg-success-soft text-success"
        : "bg-warning-soft text-warning";

  const detailRows: [string, string][] = [
    ["Grind size", shot.grind_size || "—"],
    ["Adjustments", shot.grind_direction || "—"],
    ["Temperature", shot.temperature !== null ? `${shot.temperature}°C` : "—"],
    [
      "Coffee",
      [shot.roast_level, shot.process_method].filter(Boolean).join(" · ") || "—",
    ],
    ["Tasting notes", shot.tasting_notes || "—"],
    ["Roaster", shot.roaster || "—"],
    ["Origin", shot.origin || "—"],
    ["Roast date", shot.roast_date ? displayDate(shot.roast_date) : "—"],
  ];

  return (
    <article className="overflow-hidden rounded-xl border border-border bg-card shadow-xs">
      <div className="p-4 pb-3">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
          <h3 className="min-w-0 break-words text-[0.925rem] font-semibold">{beanName}</h3>
          <span className="shrink-0 text-xs text-muted-foreground">
            {displayDate(shot.date)}
          </span>
        </div>
        <div className="grid grid-cols-4 divide-x divide-border rounded-lg border border-border bg-muted/40">
          {deltas.map((metric) => (
            <div key={metric.label} className="min-w-0 px-2.5 py-2.5 sm:px-3">
              <p className="text-[0.62rem] font-semibold uppercase tracking-wide text-muted-foreground">
                {metric.label}
              </p>
              <p className="tnum mt-0.5 truncate text-[1.05rem] font-bold leading-snug">
                {metric.value}
              </p>
              <p
                className={cn(
                  "tnum mt-0.5 truncate text-[0.7rem]",
                  metric.direction === "none" ? "text-muted-foreground" : "text-foreground/70",
                )}
              >
                {metric.change}
              </p>
            </div>
          ))}
        </div>
      </div>

      <Collapsible>
        <CollapsibleTrigger className="group flex w-full items-center justify-center gap-1 border-t border-border py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground">
          Details
          <ChevronDown className="size-3.5 transition-transform group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="border-t border-border p-4">
            <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1.5">
              <span
                className={cn(
                  "inline-flex min-h-6 items-center rounded-full px-2.5 text-xs font-semibold",
                  pillClass,
                )}
              >
                {shortFlag}
              </span>
              <span className="tnum text-sm font-semibold">{formatRatio(ratio)}</span>
              <span className="text-sm text-muted-foreground">{scoreText(shot.rating)}</span>
            </div>
            <dl className="grid grid-cols-[7.5rem_1fr] gap-x-4 gap-y-2 text-sm">
              {detailRows.map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="min-w-0 break-words">{value}</dd>
                </div>
              ))}
            </dl>
            {shot.id !== null && (
              <div className="mt-4 border-t border-border pt-3">
                <DeleteShotDialog
                  shotId={shot.id}
                  beanName={beanName}
                  dateLabel={displayDate(shot.date)}
                />
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </article>
  );
}
