import { brewRatio } from "./coaching";
import { parseGrindSize } from "./grind";
import { beanKey, normalizeText, type Shot } from "./shots";

export const SERIES_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
  "var(--chart-7)",
  "var(--chart-8)",
] as const;

export function dateMs(date: string | null): number | null {
  if (!date) return null;
  const [year, month, day] = date.split("-").map(Number);
  return new Date(year, month - 1, day).getTime();
}

export interface ScorePoint {
  dateMs: number;
  bean: string;
  rating: number;
}

/** Rated shots per bean, oldest-first, for the all-beans score chart. */
export function scoreSeriesByBean(shots: Shot[]): Map<string, ScorePoint[]> {
  const displayNameByKey = new Map<string, string>();
  for (const shot of shots) {
    const name = normalizeText(shot.bean_name);
    const key = beanKey(name);
    if (key && !displayNameByKey.has(key)) displayNameByKey.set(key, name);
  }

  const seriesByKey = new Map<string, ScorePoint[]>();
  for (const shot of [...shots].reverse()) {
    const ms = dateMs(shot.date);
    const key = beanKey(shot.bean_name);
    const bean = displayNameByKey.get(key);
    if (ms === null || shot.rating === null || !bean) continue;
    const points = seriesByKey.get(key) ?? [];
    points.push({ dateMs: ms, bean, rating: shot.rating });
    seriesByKey.set(key, points);
  }

  const series = new Map<string, ScorePoint[]>();
  for (const [key, points] of seriesByKey) {
    const bean = displayNameByKey.get(key);
    if (bean) series.set(bean, points);
  }
  return series;
}

export interface TrendPoint {
  dateMs: number;
  bean: string;
  value: number;
  rolling?: number;
}

function withRolling(points: TrendPoint[]): TrendPoint[] {
  return points.map((point, index) => {
    const window = points.slice(Math.max(0, index - 2), index + 1);
    const rolling = window.reduce((sum, p) => sum + p.value, 0) / window.length;
    return { ...point, rolling };
  });
}

/** Oldest-first trend points for one metric of one bean's shots. */
export function beanTrend(
  beanShots: Shot[],
  metric: "ratio" | "brew_time" | "rating" | "grind",
  rolling = false,
): TrendPoint[] {
  const points: TrendPoint[] = [];
  for (const shot of [...beanShots].reverse()) {
    const ms = dateMs(shot.date);
    if (ms === null) continue;
    let value: number | null;
    switch (metric) {
      case "ratio":
        value = brewRatio(shot.yield, shot.dose);
        break;
      case "brew_time":
        value = shot.brew_time;
        break;
      case "rating":
        value = shot.rating;
        break;
      case "grind":
        value = parseGrindSize(shot.grind_size);
        break;
    }
    if (value === null) continue;
    points.push({ dateMs: ms, bean: shot.bean_name, value });
  }
  return rolling && points.length >= 3 ? withRolling(points) : points;
}

export interface ScatterPoint {
  dateMs: number;
  ratio: number;
  rating: number;
}

/** One point per shot that has both a brew ratio and a score. */
export function ratioScorePoints(beanShots: Shot[]): ScatterPoint[] {
  const points: ScatterPoint[] = [];
  for (const shot of beanShots) {
    const ms = dateMs(shot.date);
    const ratio = brewRatio(shot.yield, shot.dose);
    if (ms === null || ratio === null || shot.rating === null) continue;
    points.push({ dateMs: ms, ratio, rating: shot.rating });
  }
  return points;
}

export interface BeanStats {
  shotCount: number;
  avgRating: string;
  avgRatio: string;
}

export function beanStats(beanShots: Shot[]): BeanStats {
  const ratings = beanShots
    .map((shot) => shot.rating)
    .filter((rating): rating is number => rating !== null && rating !== 0);
  const ratios = beanShots
    .map((shot) => brewRatio(shot.yield, shot.dose))
    .filter((ratio): ratio is number => ratio !== null);
  return {
    shotCount: beanShots.length,
    avgRating: ratings.length
      ? `${(ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1)} / 10`
      : "—",
    avgRatio: ratios.length
      ? `${(ratios.reduce((a, b) => a + b, 0) / ratios.length).toFixed(2)}:1`
      : "—",
  };
}

export function formatChartDate(ms: number): string {
  const date = new Date(ms);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
