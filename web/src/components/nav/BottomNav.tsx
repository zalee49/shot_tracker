"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PencilLine, History, ChartLine } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/", label: "Log Shot", icon: PencilLine },
  { href: "/history", label: "History", icon: History },
  { href: "/insights", label: "Insights", icon: ChartLine },
] as const;

export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card/95 backdrop-blur pb-[env(safe-area-inset-bottom)] md:hidden"
      aria-label="Primary"
    >
      <div className="mx-auto flex max-w-2xl">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-[0.7rem] font-medium transition-colors",
                active ? "text-primary" : "text-muted-foreground",
              )}
            >
              <Icon className="size-5" strokeWidth={active ? 2.4 : 2} />
              {label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
