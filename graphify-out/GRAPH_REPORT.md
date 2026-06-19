# Graph Report - shot_tracker  (2026-06-19)

## Corpus Check
- 3 files · ~2,173 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 22 nodes · 25 edges · 4 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ae1065e2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]

## God Nodes (most connected - your core abstractions)
1. `get_headers()` - 4 edges
2. `get_url()` - 4 edges
3. `load_data()` - 3 edges
4. `save_shot()` - 3 edges
5. `delete_shot()` - 3 edges
6. `What this is` - 1 edges
7. `Commands` - 1 edges
8. `Secrets` - 1 edges
9. `Architecture` - 1 edges
10. `Standing rules` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (4 total, 0 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (5): Architecture, Commands, Secrets, Standing rules, What this is

### Community 2 - "Community 2"
Cohesion: 0.60
Nodes (5): delete_shot(), get_headers(), get_url(), load_data(), save_shot()

## Knowledge Gaps
- **5 isolated node(s):** `What this is`, `Commands`, `Secrets`, `Architecture`, `Standing rules`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_headers()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `get_url()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `load_data()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **What connects `What this is`, `Commands`, `Secrets` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._