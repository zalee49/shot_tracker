import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchShots, removeShot } from "../supabase";

vi.mock("server-only", () => ({}));

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("supabase config errors", () => {
  it("returns the normal outage result when read env vars are missing", async () => {
    vi.stubEnv("SUPABASE_URL", "");
    vi.stubEnv("SUPABASE_KEY", "");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchShots()).resolves.toEqual({
      shots: [],
      error: "Could not load shots from the database.",
      skippedRows: 0,
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns the normal delete error when write env vars are missing", async () => {
    vi.stubEnv("SUPABASE_URL", "");
    vi.stubEnv("SUPABASE_KEY", "");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(removeShot(7)).resolves.toEqual({
      ok: false,
      error: "Could not delete the shot. Check the database connection and permissions.",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
