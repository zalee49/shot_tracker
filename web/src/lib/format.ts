import { normalizeDate } from "./shots";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function displayDate(value: unknown): string {
  const normalized = normalizeDate(value);
  if (!normalized) return "Unknown date";
  const [year, month, day] = normalized.split("-").map(Number);
  return `${MONTHS[month - 1]} ${day}, ${year}`;
}

export function scoreText(rating: number | null): string {
  if (!rating) return "Not scored";
  return `${Math.trunc(rating)}/10`;
}
