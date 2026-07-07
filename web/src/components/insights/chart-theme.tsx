"use client";

import { formatChartDate } from "@/lib/insights";

export const AXIS_TICK = {
  fill: "var(--muted-foreground)",
  fontSize: 11,
} as const;

export const GRID_PROPS = {
  stroke: "var(--border)",
  strokeDasharray: "0",
  vertical: false,
} as const;

export function timeAxisProps() {
  return {
    dataKey: "dateMs",
    type: "number" as const,
    scale: "time" as const,
    domain: ["dataMin", "dataMax"] as [string, string],
    tickFormatter: formatChartDate,
    tick: AXIS_TICK,
    tickLine: false,
    axisLine: false,
    tickMargin: 8,
    minTickGap: 32,
  };
}

interface TooltipRow {
  label: string;
  value: string;
  color?: string;
}

export function ChartTooltipCard({
  title,
  rows,
}: {
  title: string;
  rows: TooltipRow[];
}) {
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-semibold text-popover-foreground">{title}</p>
      {rows.map((row) => (
        <div key={row.label} className="flex items-center gap-1.5 py-0.5">
          {row.color && (
            <span
              className="size-2 shrink-0 rounded-full"
              style={{ background: row.color }}
            />
          )}
          <span className="text-muted-foreground">{row.label}</span>
          <span className="tnum ml-auto pl-3 font-medium text-popover-foreground">
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export function ChartCard({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-card p-4 shadow-xs">
      <h2 className="text-sm font-semibold">{title}</h2>
      <p className="mb-3 mt-0.5 text-xs text-muted-foreground">{caption}</p>
      {children}
    </section>
  );
}
