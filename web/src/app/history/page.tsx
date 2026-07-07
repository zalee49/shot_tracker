import { HistoryList } from "@/components/history/HistoryList";
import { EmptyState, StatusBanners } from "@/components/StatusBanners";
import { previousShotsById, savedBeans, type Shot } from "@/lib/shots";
import { fetchShots } from "@/lib/supabase";

export default async function HistoryPage() {
  const { shots, error, skippedRows } = await fetchShots();
  const beanNames = Array.from(savedBeans(shots).keys());
  const previousById: Record<number, Shot | null> = {};
  for (const [id, previous] of previousShotsById(shots)) {
    previousById[id] = previous;
  }

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-xl font-semibold tracking-tight">Shot history</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Review recipes and compare adjustments shot by shot.
        </p>
      </div>
      <StatusBanners error={error} skippedRows={skippedRows} />
      {error ? (
        <EmptyState>Shot history is unavailable until the database reconnects.</EmptyState>
      ) : shots.length === 0 ? (
        <EmptyState>Your first shot will appear here after you log it.</EmptyState>
      ) : (
        <HistoryList shots={shots} beanNames={beanNames} previousById={previousById} />
      )}
    </div>
  );
}
