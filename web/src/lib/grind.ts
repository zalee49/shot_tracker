import { normalizeText } from "./shots";

export function parseGrindSize(value: unknown): number | null {
  const text = normalizeText(value);
  if (!text) return null;
  const match = text.match(/-?(?:\d+\.\d+|\.\d+|\d+)/);
  if (!match) return null;
  return parseFloat(match[0]);
}
