import { afterEach, describe, expect, it, vi } from "vitest";
import { createShot, deleteShot, type ShotInput } from "../shots";
import { insertShot, removeShot } from "@/lib/supabase";

vi.mock("@/lib/supabase", () => ({
  insertShot: vi.fn(),
  removeShot: vi.fn(),
}));

const validShot: ShotInput = {
  date: "2026-07-07",
  bean_name: "Kenya AA",
  roaster: "Test Roaster",
  origin: "Kenya",
  roast_level: "Light",
  process_method: "Washed",
  roast_date: "2026-07-01",
  dose: 18,
  yield: 36,
  brew_time: 28,
  grind_size: "11",
  grind_direction: ["Same"],
  temperature: 93,
  rating: 6,
  tasting_notes: "",
};

afterEach(() => {
  vi.clearAllMocks();
});

describe("createShot validation", () => {
  it("rejects zero recipe numbers before inserting", async () => {
    await expect(createShot({ ...validShot, yield: 0 })).resolves.toEqual({
      ok: false,
      error: "Some fields are invalid. Check the form and try again.",
    });
    await expect(createShot({ ...validShot, brew_time: 0 })).resolves.toEqual({
      ok: false,
      error: "Some fields are invalid. Check the form and try again.",
    });
    expect(insertShot).not.toHaveBeenCalled();
  });
});

describe("deleteShot validation", () => {
  it("passes database delete failures through", async () => {
    vi.mocked(removeShot).mockResolvedValue({
      ok: false,
      error: "Could not delete the shot. Check the database connection and permissions.",
    });

    await expect(deleteShot(7)).resolves.toEqual({
      ok: false,
      error: "Could not delete the shot. Check the database connection and permissions.",
    });
  });
});
