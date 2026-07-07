import { InsightsView } from "@/components/insights/InsightsView";
import { EmptyState, StatusBanners } from "@/components/StatusBanners";
import { savedBeans } from "@/lib/shots";
import { fetchShots } from "@/lib/supabase";

export default async function InsightsPage() {
  const { shots, error, skippedRows } = await fetchShots();
  const beanNames = Array.from(savedBeans(shots).keys());

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-xl font-semibold tracking-tight">Insights</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          See how each bean responds as you dial it in.
        </p>
      </div>
      <StatusBanners error={error} skippedRows={skippedRows} />
      {error ? (
        <EmptyState>Insights are unavailable until the database reconnects.</EmptyState>
      ) : beanNames.length === 0 ? (
        <EmptyState>Trends will appear once you have shots to compare.</EmptyState>
      ) : (
        <InsightsView shots={shots} beanNames={beanNames} />
      )}
    </div>
  );
}
