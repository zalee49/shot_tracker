import { LogShotForm } from "@/components/log/LogShotForm";
import { StatusBanners } from "@/components/StatusBanners";
import { savedBeans } from "@/lib/shots";
import { fetchShots } from "@/lib/supabase";

export default async function LogShotPage() {
  const { shots, error, skippedRows } = await fetchShots();
  const beans = Array.from(savedBeans(shots), ([name, shot]) => ({ name, shot }));
  const lastShot = shots[0] ?? null;

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-xl font-semibold tracking-tight">Log a new shot</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Capture the recipe, then add what you tasted.
        </p>
      </div>
      <StatusBanners error={error} skippedRows={skippedRows} />
      <LogShotForm beans={beans} lastShot={lastShot} disabled={error !== null} />
    </div>
  );
}
