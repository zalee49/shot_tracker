<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Espresso Tracker Web App

This directory is the production app for Zach's Espresso Shot Tracker. The root `../AGENTS.md`
contains repository-wide guidance; this file adds the web-specific workflow.

## Commands

```bash
npm run dev       # http://localhost:3000
npm test          # Vitest unit tests
npm run lint      # ESLint
npm run build     # production build and type check
```

Use `npm test`, `npm run lint`, and `npm run build` as the default verification path after web app
changes. For UI/runtime changes, also smoke-check `/`, `/history`, and `/insights`.

## Environment and Access

- Copy `.env.example` to `.env.local` and fill in `SUPABASE_URL` and `SUPABASE_KEY`.
- Keep Supabase env vars server-only; do not rename them with `NEXT_PUBLIC_`.
- The app is URL-private/no-login: anyone with the deployed URL can browse, log, and delete shots.
  Do not assume a write gate or auth layer unless one is explicitly implemented.

## Implementation Notes

- `src/lib/supabase.ts` is the server-only PostgREST boundary.
- `src/actions/shots.ts` owns create/delete validation and route revalidation.
- Keep Insights bean-specific unless the user explicitly asks for cross-bean comparison.
