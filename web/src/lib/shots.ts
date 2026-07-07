import { z } from "zod";

export interface Shot {
  id: number | null;
  date: string | null;
  bean_name: string;
  roaster: string;
  origin: string;
  roast_level: string;
  process_method: string;
  roast_date: string | null;
  dose: number | null;
  yield: number | null;
  brew_time: number | null;
  grind_size: string;
  grind_direction: string;
  temperature: number | null;
  rating: number | null;
  tasting_notes: string;
}

export function normalizeText(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).split(/\s+/).filter(Boolean).join(" ");
}

export function beanKey(value: unknown): string {
  return normalizeText(value).toLowerCase();
}

export function coerceNumber(
  value: unknown,
  options: { minimum?: number; maximum?: number; integer?: boolean } = {},
): number | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "boolean") return null;
  const number = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(number)) return null;
  if (options.minimum !== undefined && number < options.minimum) return null;
  if (options.maximum !== undefined && number > options.maximum) return null;
  if (options.integer) {
    if (!Number.isInteger(number)) return null;
    return number;
  }
  return number;
}

export function normalizeDate(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return null;
  const text = String(value);
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  const [, year, month, day] = match;
  const parsed = new Date(Number(year), Number(month) - 1, Number(day));
  if (
    parsed.getFullYear() !== Number(year) ||
    parsed.getMonth() !== Number(month) - 1 ||
    parsed.getDate() !== Number(day)
  ) {
    return null;
  }
  return `${year}-${month}-${day}`;
}

const rawShotSchema = z.looseObject({});

export function normalizeShot(row: unknown): Shot | null {
  const parsed = rawShotSchema.safeParse(row);
  if (!parsed.success) return null;
  const record = parsed.data as Record<string, unknown>;
  return {
    id: coerceNumber(record.id, { minimum: 0, integer: true }),
    date: normalizeDate(record.date),
    bean_name: normalizeText(record.bean_name),
    roaster: normalizeText(record.roaster),
    origin: normalizeText(record.origin),
    roast_level: normalizeText(record.roast_level),
    process_method: normalizeText(record.process_method),
    roast_date: normalizeDate(record.roast_date),
    dose: coerceNumber(record.dose, { minimum: 0 }),
    yield: coerceNumber(record.yield, { minimum: 0 }),
    brew_time: coerceNumber(record.brew_time, { minimum: 0, integer: true }),
    grind_size: normalizeText(record.grind_size),
    grind_direction: normalizeText(record.grind_direction),
    temperature: coerceNumber(record.temperature),
    rating: coerceNumber(record.rating, { minimum: 1, maximum: 10, integer: true }),
    tasting_notes: normalizeText(record.tasting_notes),
  };
}

/** Display bean names mapped to their most recent shot (shots must be newest-first). */
export function savedBeans(shots: Shot[]): Map<string, Shot> {
  const seen = new Set<string>();
  const beans = new Map<string, Shot>();
  for (const shot of shots) {
    const name = normalizeText(shot.bean_name);
    const key = beanKey(name);
    if (key && !seen.has(key)) {
      seen.add(key);
      beans.set(name, shot);
    }
  }
  return beans;
}

export function savedBeanName(beanNames: Iterable<string>, value: unknown): string | null {
  const targetKey = beanKey(value);
  if (!targetKey) return null;
  for (const name of beanNames) {
    if (beanKey(name) === targetKey) return name;
  }
  return null;
}

export function shotsForBean(shots: Shot[], beanName: string): Shot[] {
  const targetKey = beanKey(beanName);
  if (!targetKey) return [];
  return shots.filter((shot) => beanKey(shot.bean_name) === targetKey);
}

/**
 * Map each shot id to its chronologically previous shot for the same bean.
 * Shots must be newest-first; iterates oldest-to-newest so the stored
 * "latest" for a bean is the immediate predecessor.
 */
export function previousShotsById(shots: Shot[]): Map<number, Shot | null> {
  const previous = new Map<number, Shot | null>();
  const latestByBean = new Map<string, Shot>();
  for (const shot of [...shots].reverse()) {
    const key = beanKey(shot.bean_name);
    if (shot.id !== null) {
      previous.set(shot.id, latestByBean.get(key) ?? null);
    }
    if (key) latestByBean.set(key, shot);
  }
  return previous;
}
