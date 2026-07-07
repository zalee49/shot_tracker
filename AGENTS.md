# AGENTS.md

Guidance for AI coding tools (Claude Code, Gemini, Cline, etc.) working in this repository.

## What this is

An espresso shot tracker ("Zach's Espresso Shot Tracker") with two apps sharing one Supabase
Postgres table named `shots`, accessed over Supabase's PostgREST HTTP API:

- **`web/`** — the production Next.js app (App Router + TypeScript + Tailwind + shadcn/ui +
  Recharts). This is the primary app going forward; see `web/README.md` for setup, env vars,
  the read-public/write-gated access model, and Vercel deploy notes.
- **`coffee_app.py`** — the original single-file Streamlit app, kept as-is for reference.
  The sections below describe it.

## Commands

```bash
streamlit run coffee_app.py          # run the app locally (opens on http://localhost:8501)
```

There is no `requirements.txt`, test suite, build step, or linter configured. Dependencies are
`streamlit`, `pandas`, and `requests` — install them manually if the environment is fresh.

## Secrets

The app reads credentials via `st.secrets` (Streamlit). To run locally, create
`.streamlit/secrets.toml` (gitignored, not in the repo) with:

```toml
SUPABASE_URL = "https://<project>.supabase.co"
SUPABASE_KEY = "<supabase api key>"
```

`get_headers()` sends `SUPABASE_KEY` as both the `apikey` and `Bearer` token on every request.

## Architecture

The whole app is `coffee_app.py`, structured as: helper functions at the top, then a single
top-to-bottom Streamlit script body (Header → Settings → Log form → Shot History → Trends) that
re-executes on every interaction.

- **Data layer** — `load_data`, `save_shot`, `delete_shot` are thin `requests` calls against
  `{SUPABASE_URL}/rest/v1/shots`. PostgREST query syntax is used directly in the URL
  (e.g. `?order=id.desc`, `?id=eq.{shot_id}`). There is no ORM or schema definition in the repo;
  the `shots` table is defined in Supabase. The implicit row shape is whatever `save_shot` sends:
  `date, bean_name, roaster, origin, roast_level, process_method, roast_date, dose, yield,
  brew_time, grind_size, grind_direction, temperature, rating, tasting_notes` (plus `id`).

- **Bean reuse** — `get_saved_beans` derives a deduplicated bean list from existing shots (most
  recent wins per `bean_name`), powering the "Select Bean" dropdown and "Quick Log Mode" so you
  can re-log a shot for a known bean without re-entering bean metadata.

- **Brew-ratio coaching** — `ratio_flag` compares `yield / dose` against the user's target ratio
  (session-state `target_ratio`, default 2.0) and returns on-target / over / under guidance.
  This is the app's core domain logic and is reused in both the log-confirmation message and each
  history entry.

- **State & refresh** — no caching; `load_data()` runs on every rerun. After a save or delete the
  code calls `st.rerun()` to refetch. Settings persist only within the session via
  `st.session_state`.

- **Theming** — coffee-colored palette in `.streamlit/config.toml`; the header logo is inline SVG
  rendered with `unsafe_allow_html=True`.

## Standing rules

1. **Follow existing project conventions.** Match the surrounding code's style: formatting, naming,
   structure, import ordering, error handling. Consistency with the existing code beats personal
   defaults. Prefer clear, explicit names over clever/condensed code. Do not add dependencies,
   abstractions, or configuration the task did not require. Note this codebase's conventions:
   plain top-to-bottom Streamlit script, small module-level helper functions, no classes, and
   trailing-underscore for the `yield_` reserved word.

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
