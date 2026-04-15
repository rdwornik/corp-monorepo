# Tach Baseline Violations — 2026-04-15

Captured on first `tach check` run after Phase 1 bootstrap.
Status: DEFERRED — document only, no fixes in this session.
To fix: create a separate branch per violation group (see Fix Directions below).

---

## Violation Count: 6 (3 unique dependency pairs)

---

## Violation Group 1: intent_router (core) → project_resolver (orchestration)

Upward dependency: core cannot import from orchestration.

Files:
  src/corp/intent_router.py:301 — corp.project_resolver.list_all_project_ids
  src/corp/intent_router.py:355 — corp.project_resolver.list_all_project_ids
  src/corp/intent_router.py:355 — corp.project_resolver.resolve_project

Root cause: intent_router uses project names/IDs to route intent ("show project X"),
which requires knowing what projects exist. It calls project_resolver for the list
and fuzzy resolution.

Fix direction (Phase 2):
Option A — Move project_resolver to core. It has no interface-level deps. This is the
  cleanest fix. Risk: confirms project_resolver is a shared primitive, not an orchestration detail.
Option B — Add a thin project-listing abstraction in core (e.g. a protocol or callback)
  that intent_router calls, with project_resolver providing the implementation at orchestration level.
Option C — Move intent_router to orchestration. It currently routes commands that need
  project awareness; reclassification may be architecturally honest.

---

## Violation Group 2: llm_router (core) → project_resolver (orchestration)

Upward dependency: core cannot import from orchestration.

Files:
  src/corp/llm_router.py:131 — corp.project_resolver.list_all_project_ids

Root cause: llm_router builds a prompt context that includes a project list for the
Gemini intent classification fallback. Same root cause as intent_router above.

Fix direction (Phase 2):
Same options as Group 1. If project_resolver moves to core (Option A), both groups
are resolved with one change.

---

## Violation Group 3: actions (orchestration) → query_engine (interface)

Upward dependency: orchestration cannot import from interface.

Files:
  src/corp/actions/analytics_actions.py:18 — corp.query_engine.get_analytics
  src/corp/actions/knowledge_actions.py:16 — corp.query_engine.search_facts

Root cause: actions/ handles domain-specific chat responses. analytics_actions and
knowledge_actions need to query the FTS5 index to fulfill their action contracts.
They import from query_engine (interface) to do so.

Fix direction (Phase 2):
Option A — Move query_engine to orchestration. query_engine is read-only (no writes,
  no side effects); the "interface" classification was based on its runtime depth,
  not its import surface. Reclassifying as orchestration breaks no invariants.
Option B — Extract a query protocol/ABC into orchestration that query_engine implements,
  and have actions depend on the protocol. Heavier engineering for marginal benefit.

Option A is preferred — query_engine has no interface-level imports, it just reads
from index.db. Moving it to orchestration resolves this violation and is accurate.

---

## Summary Table

Pair | Direction | Files | Preferred Fix
corp.intent_router → corp.project_resolver | core→orchestration | intent_router.py:301,355 | Move project_resolver to core
corp.llm_router → corp.project_resolver | core→orchestration | llm_router.py:131 | (same as above)
corp.actions → corp.query_engine | orchestration→interface | analytics_actions.py:18, knowledge_actions.py:16 | Move query_engine to orchestration

---

## Phase 2 Recommendation

Two targeted reclassifications resolve all 6 violations:
1. Move corp.project_resolver: orchestration → core (fixes Groups 1 and 2)
2. Move corp.query_engine: interface → orchestration (fixes Group 3)

Both are reclassifications in tach.toml only — no Python source changes required.
Verify with `tach check` after each change.
