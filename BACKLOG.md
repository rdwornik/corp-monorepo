# corp-monorepo BACKLOG

Cross-session pending items for `corp-monorepo`. Schema per ADR-41
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
