# AGENTS.md

Guidance for AI coding tools working in this repository.

## What this is

An espresso shot tracker ("Zach's Espresso Shot Tracker") backed by one Supabase Postgres table
named `shots`, accessed over Supabase's PostgREST HTTP API.

- **`web/`** — the production Next.js app (App Router + TypeScript + Tailwind + shadcn/ui +
  Recharts). This is the primary app going forward; see `web/README.md` for setup, env vars,
  the URL-private/no-login access model, and Vercel deploy notes.
- **`coffee_app.py`** — the original single-file Streamlit app, kept as legacy reference only.

## Commands

Run primary app commands from `web/`:

```bash
npm run dev       # local app at http://localhost:3000
npm test          # Vitest unit tests
npm run lint      # ESLint
npm run build     # production build and type check
```

The legacy Streamlit reference can still be launched manually if its Python dependencies are
installed:

```bash
streamlit run coffee_app.py
```

## Environment

The production web app reads server-only env vars from `web/.env.local`:

```bash
SUPABASE_URL="https://<project>.supabase.co"
SUPABASE_KEY="<supabase anon key>"
```

Use `web/.env.example` as the safe template. Do not add `NEXT_PUBLIC_` to these variables; all
Supabase requests should stay in server components, server actions, or `src/lib/supabase.ts`.

## Architecture

- **Web app** — `web/src/app` contains App Router pages for logging, history, and insights.
  `web/src/components` contains the UI, and `web/src/lib` contains Supabase access, shot
  normalization, coaching, deltas, and insights helpers.
- **Data layer** — `web/src/lib/supabase.ts` is the server-only PostgREST boundary. It normalizes
  database rows with `normalizeShot`, keeps malformed rows visible through skipped-row banners,
  and returns friendly outage errors so writes can be disabled when reads fail.
- **Server actions** — `web/src/actions/shots.ts` validates shot creation/deletion and revalidates
  `/`, `/history`, and `/insights` after successful writes.
- **Access model** — this is a personal URL-private app with no login. Anyone with the deployed URL
  can browse, log, and delete shots, so do not document or assume an auth/write gate unless one is
  explicitly added.
- **Legacy Streamlit** — `coffee_app.py` remains useful for historical behavior comparisons, but new
  fixes should target `web/` unless the user asks otherwise.

## Standing rules

1. **Follow existing project conventions.** Match the surrounding code's style: formatting, naming,
   structure, import ordering, error handling. Consistency with the existing code beats personal
   defaults. Prefer clear, explicit names over clever/condensed code. Do not add dependencies,
   abstractions, or configuration the task did not require.

2. **Be concise, don't over-explain.** Don't explain standard, well-known patterns unless asked.
   Focus commentary on non-obvious parts or real decisions. If a change is effectively identical to
   existing code, say "no changes needed". When unsure, say so rather than projecting false
   confidence.

3. **Ask before assuming.** If intent or requirements are unclear, ask before writing code.
   Implement the simplest thing that could work; don't add unrequested flexibility. Don't modify
   files or functions outside the current task. Never run destructive commands, never commit without
   review, and never delete or overwrite config files (`.streamlit/`, secrets) without explicit
   confirmation. If you notice a security issue, stop and flag it.

4. **Explain code at the requested level** when asked to explain "at level 1/2/3":
   Level 1 = maximum depth, quoting each line and explaining every piece of syntax plus what the
   line accomplishes; never group lines or skip anything. Level 2 = function/block level: what each
   function/block does, its inputs, outputs, and why it exists — no syntax, no line-by-line.
   Level 3 = big picture in plain English: the goal, strategy, and outcome — no functions, no syntax.
