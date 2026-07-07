import { CloudOff, TriangleAlert } from "lucide-react";

export function StatusBanners({
  error,
  skippedRows,
}: {
  error: string | null;
  skippedRows: number;
}) {
  if (error) {
    return (
      <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-destructive/25 bg-destructive/5 px-3.5 py-3 text-sm text-destructive">
        <CloudOff className="mt-0.5 size-4 shrink-0" />
        <span>{error} Logging and deletion are disabled until it reconnects.</span>
      </div>
    );
  }
  if (skippedRows > 0) {
    return (
      <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-warning/25 bg-warning-soft px-3.5 py-3 text-sm text-warning">
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
        <span>
          Skipped {skippedRows} unreadable database row{skippedRows === 1 ? "" : "s"}.
        </span>
      </div>
    );
  }
  return null;
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-input bg-card px-4 py-12 text-center text-sm text-muted-foreground">
      {children}
    </div>
  );
}
