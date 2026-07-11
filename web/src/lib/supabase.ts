import "server-only";
import { normalizeShot, type Shot } from "./shots";

function getConfig() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_URL and SUPABASE_KEY must be set");
  }
  return { url, key };
}

function getHeaders(key: string): HeadersInit {
  return {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
  };
}

function shotsUrl(base: string, query = ""): string {
  return `${base}/rest/v1/shots${query}`;
}

export interface ShotsResult {
  shots: Shot[];
  error: string | null;
  skippedRows: number;
}

export async function fetchShots(): Promise<ShotsResult> {
  let data: unknown;
  try {
    const { url, key } = getConfig();
    const response = await fetch(shotsUrl(url, "?order=id.desc"), {
      headers: getHeaders(key),
      signal: AbortSignal.timeout(15000),
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
  } catch {
    return { shots: [], error: "Could not load shots from the database.", skippedRows: 0 };
  }

  if (!Array.isArray(data)) {
    return { shots: [], error: "The database returned an unexpected response.", skippedRows: 0 };
  }

  const shots: Shot[] = [];
  let skippedRows = 0;
  for (const row of data) {
    if (row === null || typeof row !== "object" || Array.isArray(row)) {
      skippedRows += 1;
      continue;
    }
    const shot = normalizeShot(row);
    if (shot === null) {
      skippedRows += 1;
    } else {
      shots.push(shot);
    }
  }
  return { shots, error: null, skippedRows };
}

export type NewShotRow = Omit<Shot, "id">;

export async function insertShot(row: NewShotRow): Promise<void> {
  const { url, key } = getConfig();
  const response = await fetch(shotsUrl(url), {
    method: "POST",
    headers: { ...getHeaders(key), Prefer: "return=minimal" },
    body: JSON.stringify(row),
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    let detail = "Check the Supabase connection and table permissions.";
    try {
      const payload = await response.json();
      detail = payload.message || payload.hint || detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }
}

export async function removeShot(shotId: number): Promise<{ ok: boolean; error?: string }> {
  let deletedRows: unknown;
  try {
    const { url, key } = getConfig();
    const response = await fetch(
      shotsUrl(url, `?id=eq.${shotId}&select=id`),
      {
        method: "DELETE",
        headers: { ...getHeaders(key), Prefer: "return=representation" },
        signal: AbortSignal.timeout(15000),
      },
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    deletedRows = await response.json();
  } catch {
    return {
      ok: false,
      error: "Could not delete the shot. Check the database connection and permissions.",
    };
  }

  if (
    !Array.isArray(deletedRows) ||
    deletedRows.length !== 1 ||
    typeof deletedRows[0] !== "object" ||
    deletedRows[0] === null ||
    (deletedRows[0] as { id?: unknown }).id !== shotId
  ) {
    return {
      ok: false,
      error: "The database did not confirm that exactly one shot was deleted.",
    };
  }
  return { ok: true };
}
