"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { insertShot, removeShot } from "@/lib/supabase";
import { normalizeDate, normalizeText } from "@/lib/shots";
import {
  ADJUSTMENT_OPTIONS,
  PROCESS_METHODS,
  ROAST_LEVELS,
} from "@/lib/constants";

const dateInputSchema = z.string().refine((value) => normalizeDate(value) === value);

const shotInputSchema = z.object({
  date: dateInputSchema,
  bean_name: z.string().transform(normalizeText),
  roaster: z.string(),
  origin: z.string(),
  roast_level: z.enum(ROAST_LEVELS),
  process_method: z.enum(PROCESS_METHODS),
  roast_date: dateInputSchema,
  dose: z.number().min(0).max(30),
  yield: z.number().min(0).max(100),
  brew_time: z.number().int().min(0).max(120),
  grind_size: z.string(),
  grind_direction: z.array(z.enum(ADJUSTMENT_OPTIONS)),
  temperature: z.number().min(80).max(100),
  rating: z.number().int().min(1).max(10),
  tasting_notes: z.string(),
});

export type ShotInput = z.infer<typeof shotInputSchema>;

export interface ActionResult {
  ok: boolean;
  error?: string;
}

export async function createShot(input: ShotInput): Promise<ActionResult> {
  const parsed = shotInputSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Some fields are invalid. Check the form and try again." };
  }
  const shot = parsed.data;
  if (!shot.bean_name) {
    return { ok: false, error: "Add a bean name before logging this shot." };
  }
  if (shot.dose <= 0) {
    return { ok: false, error: "Dose must be greater than zero." };
  }

  try {
    await insertShot({
      date: shot.date,
      bean_name: shot.bean_name,
      roaster: shot.roaster,
      origin: shot.origin,
      roast_level: shot.roast_level,
      process_method: shot.process_method,
      roast_date: shot.roast_date,
      dose: shot.dose,
      yield: shot.yield,
      brew_time: shot.brew_time,
      grind_size: shot.grind_size,
      grind_direction: shot.grind_direction.join(", "),
      temperature: shot.temperature,
      rating: shot.rating,
      tasting_notes: shot.tasting_notes,
    });
  } catch (error) {
    const detail =
      error instanceof Error && error.message
        ? error.message
        : "Check the Supabase connection and table permissions.";
    return { ok: false, error: `Could not log the shot. ${detail}` };
  }

  revalidatePath("/");
  revalidatePath("/history");
  revalidatePath("/insights");
  return { ok: true };
}

export async function deleteShot(shotId: number): Promise<ActionResult> {
  if (!Number.isInteger(shotId) || shotId < 0) {
    return { ok: false, error: "Could not delete this shot because its ID is invalid." };
  }

  const result = await removeShot(shotId);
  if (!result.ok) {
    return { ok: false, error: result.error };
  }

  revalidatePath("/");
  revalidatePath("/history");
  revalidatePath("/insights");
  return { ok: true };
}
