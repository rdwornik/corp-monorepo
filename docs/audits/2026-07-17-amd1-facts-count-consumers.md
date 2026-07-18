# AMD-1 evidence — `facts_count` consumer enumeration (2026-07-17)

> Evidence backing **PROPOSED amendment AMD-1** (plan Addendum B): the deferred removal of the
> `projects.facts_count` column + the `facts_count` model field. AMD-1 is gated on (a) verbatim
> consumer enumeration — **this document** — and (b) operator sign-off. Non-gating for Arc-B.
> **Source:** Codex **luna** (`gpt-5.6-luna`, `-s read-only`), independent read-only fan-out, 2026-07-17.
> Corroborates the executor's Batch-2 re-grep (~15 live sites); luna's count is broader because it
> also enumerates the `index_builder.py` DDL/population/bookkeeping sites.

## Enumeration — 31 consumer sites (verbatim `path:line`)

**(a) column DDL + population — `src/corp/index_builder.py`**
```
index_builder.py:38   facts_count INTEGER DEFAULT 0,          # projects table column DDL
index_builder.py:163  facts_count = 0                          # rebuild local accumulator (now always 0)
index_builder.py:204  (str(facts_count),),                     # total_facts meta write (=0)
index_builder.py:220  facts_count,                             # IndexStats log arg
index_builder.py:228  facts_indexed=facts_count,               # IndexStats.facts_indexed (=0)
index_builder.py:306  "facts_count": 0,                        # info dict default
index_builder.py:333  "facts_count": 0,                        # info dict default
index_builder.py:389  info["facts_count"] = data.get("facts_count", 0)   # VAULT-DATA population
index_builder.py:400  region, industry, files_processed, facts_count,    # _insert_project INSERT cols
index_builder.py:414  info.get("facts_count", 0),              # _insert_project INSERT value (vault-sourced)
```

**(b) `src/corp/query_engine.py`**
```
query_engine.py:75   " topics, facts_count FROM projects WHERE 1=1"        # search_projects SELECT
query_engine.py:87   sql += " ORDER BY facts_count DESC, client ASC"       # search_projects ordering
query_engine.py:113  facts_count=row[5] or 0,                              # ProjectResult output
query_engine.py:179  "SELECT AVG(facts_count) FROM projects WHERE facts_count > 0"   # get_analytics avg
```

**(c) `src/corp/models.py` fields**
```
models.py:81   facts_count: int = 0    # ProjectInfo
models.py:100  facts_count: int = 0    # (project summary)
models.py:253  facts_count: int = 0    # ProjectResult
```

**(d) `src/corp/actions/`**
```
actions/brief_actions.py:66       f"**Facts Extracted:** {info.facts_count}",
actions/monitoring_actions.py:59  if info.facts_count == 0:
actions/monitoring_actions.py:64  "issue": "No extraction (facts_count = 0)",
actions/vault_actions.py:51       "facts_count": 0,
```

**(e) `src/corp/cli/`**
```
cli/project.py:47  str(p.facts_count) if p.facts_count else DASH,
cli/project.py:82  table.add_row("Facts", str(info.facts_count))
cli/query.py:76    str(r.facts_count),
```

**(f) `src/corp/vault_io.py`**
```
vault_io.py:252  facts_count=data.get("facts_count", 0),   # reads from vault-note data
vault_io.py:354  summary.facts_count = info.facts_count
```

**(g) `tests/`**
```
tests/conftest.py:43           "facts_count": 992,
tests/test_vault_io.py:250     assert info.facts_count == 992
tests/test_index_builder.py:132  "SELECT facts_count FROM projects WHERE project_id = ?",
```

**Total: 31 consumer sites.**

<!-- AMENDMENT 2026-07-18 (ADR-37, in-file marker per CLAUDE.md §5 rule 3 — original preserved): the "31" summary label over-counts this document's own verbatim enumeration, which lists **29** sites; live re-witness (26 src + 3 tests) and an independent sol recount both confirm **29**. The 29 are textual references (DDL, model declarations, defaults, bookkeeping, a message literal, fixtures), not all read-consumers. Corrected count: **29**. -->


## Disposition notes for the operator (AMD-1 sign-off)

- **Population is vault-data-sourced, loader-independent.** `index_builder.py:389/:414` populate
  `projects.facts_count` from vault-note data via `_insert_project`; the (now-removed) facts loader's
  UPDATE never fired (n≡0 per ground-truth §6 D-1). So the column is a live metadata scalar, not a
  facts-search derivative — which is why Batch 2 (Option A) KEPT it.
- **Conflicting prior data point:** `docs/audits/2026-07-05-deep-extraction.md:221` states
  "Drop/ignore: … `projects.facts_count` … all zero today; no data loss." Whether the column
  carries non-zero data in the live vault (post-`corp index rebuild` it showed **0 facts** indexed,
  but `facts_count` is sourced from note frontmatter, not the facts table) is the key question for
  AMD-1 disposition — the operator rules at sign-off.
- **Removal blast radius if signed:** ~15 non-test live sites (the (b)–(f) groups) require rewiring —
  a behaviour change to `corp projects` (ordering + output), `get_analytics`, briefs, monitoring, and
  the CLIs. That is a separate scoped change with its own commit, NOT Arc-B.

---
*Curated 2026-07-17 · Codex luna read-only enumeration · evidence for AMD-1 (plan Addendum B). The
signed Arc-B manifest is untouched; AMD-1 remains PROPOSED pending operator sign-off.*
