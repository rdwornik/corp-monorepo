# corp-monorepo BACKLOG

Cross-session pending items for `corp-monorepo`. Schema per ADR-41 as relaxed by ADR-47
(`.dev-knowledge/docs/decisions/ADR-41-cross-session-backlog-architecture.md`):
`[P{N}]` priority, `[open|superseded]` status, dated entries.

Seeded 2026-05-18 from `docs/HANDOFF.md` §"Open Decisions" + §"Pending
Fixes" (file retired same day; snapshot preserved in git history at
commit prior to retirement).

---

## Open Decisions

### [P1] [open] Ontology Q4 — canonical product map
- **What:** Define the canonical product map that resolves the
  semantic product-grouping queries (Q4, Q5, Q7, Q8 in the SQL
  analytics benchmark). Unblocks the 4 remaining benchmark queries
  that today require the ontology layer.
- **Why:** 6/10 benchmark queries answer via SQL; the other 4 stall
  on the missing canonical map. The ontology decision gates the
  remaining analytics coverage.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 5)
- **Status:** open

### [P2] [open] RFP Federation (ADR-22) implementation
- **What:** Implement `corp rfp-index` plus the `rfp_entries` FTS5
  table in `index.db` and the grouped output for `corp retrieve`
  with `--source all` default, per ADR-22.
- **Why:** ADR-22 ratified; not yet built. Without it, the RFP KB
  (1,325 entries) and the vault (~488 notes) stay on separate
  retrieval paths.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 6)
- **Status:** open

### [P2] [open] MyWork bulk rename to naming v2
- **What:** Bulk-rename ~585 MyWork files to the naming v2 convention
  `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` (ADR-14). Sandbox
  rename pipeline tested; not yet applied. `corp folder-review`
  currently produces 0 renames (stable state).
- **Why:** Adoption of the v2 convention across MyWork is incomplete
  (10 v2 / 585 pre-v2 at last count). Bulk rename is the deferred
  cutover.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 7)
- **Status:** open

### [P2] [open] 30-day skill eval checkpoint
- **What:** Run the 30-day skill eval checkpoint against the locked
  stratified 80/20 split (ADR-16). Baseline 2026-03-26; checkpoint
  due 2026-04-25 — **past due** at rehoming time.
- **Why:** ADR-16 mandates the 30-day checkpoint. Skipping it leaves
  classifier/tag/product/people drift undetected against the locked
  baseline.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 10; original due date 2026-04-25)
- **Status:** open

### [P3] [open] Local AI exploration (Ollama)
- **What:** Explore Ollama for an offline / private extraction tier.
- **Why:** Adds a tier that does not depend on Gemini / external
  inference for sensitive or offline-only material.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 8)
- **Status:** open

### [P3] [open] Outlook automation
- **What:** Email ingestion pipeline from Outlook.
- **Why:** Brings inbox content into the ingest pipeline without
  manual file routing.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Open
  Decisions" item 9)
- **Status:** open

### [P3] [closed] Ruff select strictness decision (Action 7c)
- **What:** Decide whether to keep the lenient ruff select (`["E","F","I"]` in `ruff.toml`)
  or tighten it. Corp-monorepo had 89 pre-existing `I001` import-sort violations under the
  hook-pinned v0.4.0 binary vs venv v0.11+ mismatch. Hook bumped to v0.15.8 on 2026-05-28;
  89 violations fixed; repo is now 0-error under lenient select.
- **Why:** The universalization mega-session deferred the strictness decision as ambiguous.
  Resolving it unblocked the ADR-59 visual-pattern retrofit.
- **Added:** 2026-05-28 by claude (closing Action 7c from the mega-session deferred list)
- **Status:** closed 2026-05-28 — Decision: keep lenient select as intentional baseline.
  Documented in ADR-32. Baseline: 0 errors at current select; strict-select error count
  unknown (measure before any future tightening). D1 cleanup (ruff.toml vs pyproject.toml
  duplication) remains a separate future chore.

### [P2] [closed 2026-05-28] VISION §Values routing — resolved via Path B (Action 6)

**Closed 2026-05-28:** Path B executed. Deep-read of all 4 routing modules
(`extraction/routing.py`, `ingest/router.py`, `overnight/classifier.py`,
`retrieve/engine.py`) confirmed genuinely distinct per-domain concerns:
no cross-imports, no shared dispatch table, disjoint inputs/outputs, and
different confidence semantics. The shared word is "routing"; the concepts
are not. VISION.md §Values amended to "Deterministic per-domain routing"
with an inline provenance note preserving the Council-origin original.
Deep-audit finding D2 (HIGH) closed. Commit: `0a9410c`.
Branch: `docs/action6-vision-routing-2026-05-28` (awaiting operator merge).

---

### [P2] [closed 2026-05-28] VISION §Values routing — original entry (preserved for history)
- **What:** VISION.md §Values (line 73) declares "One routing authority. Routing configuration
  has a single source of truth, not per-module copies." File-state contradicts this: routing
  logic is distributed across 4+ modules (`src/corp/extraction/routing.py`,
  `src/corp/ingest/router.py`, `src/corp/overnight/classifier.py`,
  `src/corp/retrieve/engine.py`) and no central `routing_map.yaml` exists.
  Deep audit finding D2 (2026-05-20-corp-monorepo-deep.md §9.D2) classified this as HIGH.
  Resolution requires one of two paths — see Investigation below.
- **Why:** A VISION principle that the file-state does not realize misleads future sessions
  and produces incorrect conformance assessments. Either the code or the VISION must converge.
- **Added:** 2026-05-28 by claude (surfaced from mega-session as CM-CF4 / Action 6,
  Council-gated label)
- **Status:** open — investigated 2026-05-28; see findings below. Awaiting operator routing
  decision (Path A vs Path B).

  **2026-05-28 investigation findings:**

  *Scope (plain terms):* VISION.md §Values line 73-74 declares a principle (one routing
  authority) that doesn't match how the codebase actually works. The code has deterministic,
  per-aspect routing — not a violation of good architecture, just a mismatch between what
  VISION says and what the code does.

  *Two resolution paths:*
  - **Path A — Consolidate routing into a single canonical module/config.** Create
    `routing_map.yaml` or a top-level `corp.router` module that all 4 routing callsites
    delegate to. Architectural change. Touches `src/corp/extraction/routing.py`,
    `src/corp/ingest/router.py`, `src/corp/overnight/classifier.py`,
    `src/corp/retrieve/engine.py`, plus any config YAMLs (content_registry.yaml,
    agents.yaml, workflows.yaml). Requires ADR. Genuinely architectural — the original
    VISION routing language came from an AI Council debate; changing the implementation to
    match would be a material code refactor. **Council-worthy.**
  - **Path B — Amend VISION.md §Values to reflect actual file-state.** Replace the
    aspirational "single source of truth" language with accurate language, e.g., "routing
    rules are deterministic and per-aspect; each domain owns its own routing logic with no
    shared mutable state." Small documentation change. Touches only `VISION.md`. The deep
    audit (D2) itself suggests this path. **Not Council-worthy** — it's correcting
    documentation drift, not making an architectural decision. The architectural decision
    (distributed routing) was already made in practice.

  *Recommendation:* **Path B, implemented as a focused session.** The current distributed
  routing works and has no reported bugs. The VISION language is aspirational drift from the
  original Council debate, not a binding constraint. Correcting VISION to match reality is a
  documentation fix, not a new architectural decision. If Rob disagrees and wants to actually
  consolidate routing, convene Council (Path A). If Path B, no Council needed — one session,
  one VISION.md edit, one ADR amendment noting the correction.

  *Files Path B would touch:* `VISION.md` (lines 73-74 §Values), optionally
  `docs/decisions/ADR-23-monorepo-internal-architecture.md` (cross-ref note).

  *Dependencies / unknowns:* None for Path B. Path A depends on understanding which of the
  4 routing modules has the canonical routing table (content_registry.yaml appears to be it
  for file-pattern routing, but classification logic in overnight/classifier.py and
  retrieve/engine.py is code-embedded).

---

## Pending Fixes

### [P1] [open] MinHash dedup not wired into ingest
- **What:** `check_near_duplicate()` exists in `src/corp/ingest/dedup.py`
  (MinHash 128-perm, word 3-grams, `content_signatures` table in
  `ops.db`) but is not called from `src/corp/ingest/inbox.py`
  `process_file()` after `light_scan()`. Fail-open is intended;
  fail-absent is the current state.
- **Why:** Near-duplicate detection at ingest time is the stated
  guard against re-ingestion. Without the wiring, the table is
  populated but never consulted.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Pending
  Fixes" item 1)
- **Status:** open

### [P2] [open] Cognitive Friday YAML — unquoted hyphen truncates `session_id`
- **What:** Two Cognitive Friday notes carry
  `session_id: "cognitive-friday-season-2` — the unquoted hyphen in
  the value truncates the string on parse. The notes skip on ingest.
- **Why:** Skipped notes silently drop content. Either quote the
  value at source or normalize on ingest.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Pending
  Fixes" item 2)
- **Status:** open

### [P3] [open] Two low-quality JLR notes need re-extraction
- **What:** Two JLR notes score 28–29 against the quality threshold
  (25). Above the soft-fail line but below the comfort band.
  Re-extract with a deeper prompt.
- **Why:** Soft-failed notes ingest with warnings; the deeper prompt
  gives them a clean pass.
- **Added:** 2026-05-18 by rob (rehomed from `docs/HANDOFF.md` §"Pending
  Fixes" item 3)
- **Status:** open
