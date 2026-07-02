# Graph Report - shot_tracker  (2026-07-02)

## Corpus Check
- 3 files · ~4,213 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 41 nodes · 59 edges · 8 communities (6 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d489e61d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]

## God Nodes (most connected - your core abstractions)
1. `bean_key()` - 6 edges
2. `normalize_shot()` - 5 edges
3. `get_headers()` - 4 edges
4. `get_url()` - 4 edges
5. `normalize_text()` - 4 edges
6. `coerce_number()` - 4 edges
7. `load_data()` - 4 edges
8. `delete_shot()` - 4 edges
9. `get_saved_beans()` - 4 edges
10. `normalize_date()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `normalize_shot()` --calls--> `normalize_text()`  [EXTRACTED]
  coffee_app.py → coffee_app.py  _Bridges community 4 → community 5_
- `normalize_shot()` --calls--> `coerce_number()`  [EXTRACTED]
  coffee_app.py → coffee_app.py  _Bridges community 2 → community 5_

## Import Cycles
- None detected.

## Communities (8 total, 2 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (5): Architecture, Commands, Secrets, Standing rules, What this is

### Community 2 - "Community 2"
Cohesion: 0.38
Nodes (7): coerce_number(), delete_shot(), get_headers(), get_url(), load_data(), save_shot(), widget_default()

### Community 4 - "Community 4"
Cohesion: 0.29
Nodes (8): bean_key(), get_previous_shots_by_id(), get_saved_beans(), normalize_text(), Return display bean names mapped to their most recent shot., Map each shot id to its chronologically previous shot for the same bean.      It, saved_bean_name(), shots_for_bean()

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): display_date(), normalize_date(), normalize_shot()

## Knowledge Gaps
- **5 isolated node(s):** `What this is`, `Commands`, `Secrets`, `Architecture`, `Standing rules`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_saved_beans()` connect `Community 4` to `Community 0`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `get_previous_shots_by_id()` connect `Community 4` to `Community 0`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `bean_key()` connect `Community 4` to `Community 0`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **What connects `Return display bean names mapped to their most recent shot.`, `Map each shot id to its chronologically previous shot for the same bean.      It`, `What this is` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._