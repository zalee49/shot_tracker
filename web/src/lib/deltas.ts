import type { Shot } from "./shots";

/** Format a number without a trailing .0 (18.0 → "18", 18.5 → "18.5"). */
export function fmtNumber(value: number): string {
  return String(value);
}

export interface MetricDelta {
  label: string;
  value: string;
  change: string;
  direction: "up" | "down" | "none";
}

const METRICS: { label: string; field: "dose" | "yield" | "brew_time" | "rating"; unit: string }[] = [
  { label: "Dose In", field: "dose", unit: "g" },
  { label: "Dose Out", field: "yield", unit: "g" },
  { label: "Time", field: "brew_time", unit: "s" },
  { label: "Score", field: "rating", unit: "" },
];

export function metricDeltas(shot: Shot, previousShot: Shot | null): MetricDelta[] {
  return METRICS.map(({ label, field, unit }) => {
    const value = shot[field];
    let display: string;
    if (value === null) {
      display = "—";
    } else if (field === "rating") {
      display = `${fmtNumber(value)}/10`;
    } else {
      display = `${fmtNumber(value)}${unit}`;
    }

    let change: string;
    let direction: MetricDelta["direction"] = "none";
    if (previousShot === null) {
      change = "First shot";
    } else {
      const previousValue = previousShot[field];
      if (value === null || previousValue === null) {
        change = "No comparison";
      } else {
        const difference = Math.round((value - previousValue) * 100) / 100;
        if (difference === 0) {
          change = "No change";
        } else {
          direction = difference > 0 ? "up" : "down";
          const sign = difference > 0 ? "+" : "−";
          change = `${sign}${fmtNumber(Math.abs(difference))}${unit}`;
        }
      }
    }
    return { label, value: display, change, direction };
  });
}
