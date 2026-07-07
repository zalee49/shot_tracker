# Espresso Tracker (web)

Production web app for Zach's espresso shot tracker — Next.js App Router +
TypeScript + Tailwind + shadcn/ui + Recharts, backed by the same Supabase
`shots` table as the original Streamlit app (`../coffee_app.py`).

## Run locally

```bash
npm install
cp .env.example .env.local   # fill in the values
npm run dev                  # http://localhost:3000
```

Other scripts: `npm run build`, `npm run lint`, `npm test` (Vitest unit tests
for the ported ratio/delta/grind/normalization logic).

## Environment variables

| Var | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL (server-side only) |
| `SUPABASE_KEY` | Supabase anon key — never exposed to the browser |

Neither uses the `NEXT_PUBLIC_` prefix, so Next.js keeps them out of client
bundles. All Supabase requests happen in server components and server actions
(`src/lib/supabase.ts` is marked `server-only`).

## Access model

This is a personal, single-user tracker with no login: anyone with the URL
can browse, log, and delete shots. Don't share the link anywhere you wouldn't
want random writes to your data.

## Deploying to Vercel

1. Import the repo, set **Root Directory** to `web`.
2. Add the two environment variables above.
3. Deploy — no other configuration needed.
