import Link from "next/link";
import { BeanMark } from "./BeanMark";
import { NavLinks } from "./NavLinks";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-2xl items-center gap-3 px-4">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="grid size-8 place-items-center rounded-lg bg-accent text-primary">
            <BeanMark className="size-5" />
          </span>
          <span className="text-[0.95rem] font-semibold tracking-tight">
            Zach&apos;s Espresso Tracker
          </span>
        </Link>
        <div className="ml-auto flex items-center gap-1">
          <NavLinks />
        </div>
      </div>
    </header>
  );
}
