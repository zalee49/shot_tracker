export function brewRatio(yieldG: number | null, dose: number | null): number | null {
  if (yieldG === null || dose === null || dose <= 0) return null;
  return yieldG / dose;
}

export type RatioStatus = "on-target" | "over" | "under";

export interface RatioFlag {
  status: RatioStatus;
  message: string;
}

export function ratioFlag(
  yieldG: number | null,
  dose: number | null,
  target: number,
): RatioFlag | null {
  const ratio = brewRatio(yieldG, dose);
  if (ratio === null) return null;
  const diff = ratio - target;
  if (Math.abs(diff) <= 0.05) {
    return { status: "on-target", message: "On target" };
  }
  if (diff > 0) {
    return {
      status: "over",
      message: `Over by ${diff.toFixed(2)} — try less yield or more dose`,
    };
  }
  return {
    status: "under",
    message: `Under by ${Math.abs(diff).toFixed(2)} — try more yield or less dose`,
  };
}

export function formatRatio(ratio: number | null): string {
  return ratio === null ? "—" : `${ratio.toFixed(2)}:1`;
}
