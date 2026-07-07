"use client";

import { CircleCheck, CircleAlert, CircleDashed } from "lucide-react";
import { brewRatio, formatRatio, ratioFlag } from "@/lib/coaching";
import { cn } from "@/lib/utils";

interface RatioCoachProps {
  dose: number | null;
  yieldG: number | null;
  targetRatio: number;
}

export function RatioCoach({ dose, yieldG, targetRatio }: RatioCoachProps) {
  const ratio = brewRatio(yieldG, dose);
  const flag = ratioFlag(yieldG, dose, targetRatio);

  if (ratio === null || flag === null) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2.5 text-sm text-muted-foreground">
        <CircleDashed className="size-4 shrink-0" />
        Enter a dose and yield to see your brew ratio.
      </div>
    );
  }

  const onTarget = flag.status === "on-target";
  const Icon = onTarget ? CircleCheck : CircleAlert;
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm",
        onTarget
          ? "border-success/25 bg-success-soft text-success"
          : "border-warning/25 bg-warning-soft text-warning",
      )}
    >
      <Icon className="size-4 shrink-0" />
      <span className="tnum font-semibold">{formatRatio(ratio)}</span>
      <span className="min-w-0">{flag.message}</span>
    </div>
  );
}
