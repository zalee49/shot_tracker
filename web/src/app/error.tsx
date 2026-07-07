"use client";

import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-input bg-card px-4 py-12 text-center">
      <p className="text-sm font-medium">Something went wrong.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Try again — if it keeps happening, check the database connection.
      </p>
      <Button variant="outline" onClick={reset} className="mt-4">
        Try again
      </Button>
    </div>
  );
}
