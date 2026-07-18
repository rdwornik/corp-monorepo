# ADR-37: Metadata canonical layer + facts-pipeline disposition

- **Status:** Accepted
- **Date:** 2026-07-18
- **Decision tier:** Senior-architect ruling 2026-07-18 (Session-1 A1-4), sol-adjudicated; operator-ratified
- **Related:** ADR-27 (safety invariants — vault `.md` notes are the writeable knowledge substrate; the index is a cache); Arc-B Batch 2 (the facts-pipeline kill this ADR affirms)
- **Evidence base:** Session-1 Arc-1 evidence pack (witnessed live 2026-07-18); `docs/audits/2026-07-16-architecture-ground-truth.md` §6 D-1; `docs/audits/2026-07-17-amd1-facts-count-consumers.md`; `docs/audits/2026-07-18-process-audit.md` F7/F14
- **Adjudication:** `gpt-5.6-sol` independent read-only derivation (no decision overturned; scope-precision + implementation constraints folded)

## Context

Two long-open questions on the knowledge core, re-witnessed against **live** state (not inherited):

1. **Canonical layer.** Note frontmatter and the `index.db` `notes` table both hold metadata. Frontmatter is the richer, authoritative layer (`key_facts` populated as YAML block-lists in 392/488 indexed notes; `quality` 486/488; `extraction_cost_usd` 159/488). `index.db` is a **lossy, derived** projection rebuilt drop/recreate from source files; it does **not** project `key_facts` or the cost fields. Which layer is canonical had never been ruled.

2. **Facts pipeline (F7).** Arc-B Batch 2 already removed the `facts`/`facts_fts` tables, DDL, triggers, and the `_load_and_insert_facts` loader; `search_facts()` survives only as a `notes_fts` shim. `projects.facts_count` remains, **0 across all 29 projects**, referenced at 29 code sites. The historical "0 rows ever" was loader **starvation** (loader read a `facts.yaml` path nothing produced), not absent data — `key_facts` is in fact the densest field in the vault.

## Decision

**(i) Canonical layer = frontmatter.** Note frontmatter is the source of truth for knowledge metadata. `index.db` is a **derived, disposable** projection (drop/recreate at rebuild). **No dual-write, ever** — every DB value is derived at rebuild from a source file (note `.md` frontmatter for note rows; vault/OneDrive `project-info.yaml` for project rows), with the sole exception of `meta` bookkeeping, which the rebuild preserves. A DB field not derived from a source file is not a source of truth.

**(ii) F7 = stay-dead pipeline + one projection leg.** The Batch-2 kill stands — no `facts`/`facts_fts`, no loader, no facts FTS; `search_facts()` stays the `notes_fts` shim. Add **exactly one** projection leg at index rebuild: `projects.facts_count := Σ over the project's notes of len(key_facts-from-frontmatter)`. This makes the 29 existing sites truthful (not uniformly zero), with no new tables or query surface. **Implementation constraints (sol-adjudicated, binding on the implementer):**
- **Post-scan aggregation/UPDATE**, not the current pre-scan `facts_count` insert point (which reads `project-info.yaml`): the leg runs after notes are scanned and UPDATEs the project row.
- **Guard `key_facts`** (schema `list[str] | None`, consumed as raw YAML without validation): missing/`None` → 0; a non-list value → rejected/0, **never** passed raw to `len()`.
- **Honor project association, package-note exclusion** (`index.md`/`synthesis.md`, per F8), and **source-hash dedup** — else blank-project notes, package notes, or duplicates distort the count.

**(iii) Re-open trigger (quantified).** `key_facts` becomes a retrieval surface (its own FTS/searchable projection) **only** on witnessed **post-F6** evidence that body-FTS grounding is insufficient in real RFP use — i.e. after F6 (note-body FTS) ships, a witnessed real-RFP query that fails to ground on body-FTS but would have grounded on a `key_facts` index. Until then: **parked**. No speculative revival.

## Consequences

- Canonical layer settled (frontmatter); no dual-write ambiguity. `facts_count` stops lying (29 sites truthful) at minimal surface. F7 revival gated on real evidence, not a stale "pipeline exists" premise.
- **Cost:** one summation leg in the rebuild path (must be covered by a rebuild test asserting `facts_count == Σ len(key_facts)` for a fixture project); one behavior change — `corp projects` ordering / analytics now sort on a non-zero `facts_count`.
- **Non-goals:** does not revive facts search, add DB write paths, or change the vault-writer invariant (ADR-27).

## Folded label correction (witnessed 2026-07-18)

The `facts_count` consumer count is **29** (witnessed live: 26 `src/` + 3 `tests/`; independently recounted by sol), not 31. The "31" in `docs/audits/2026-07-17-amd1-facts-count-consumers.md` (summary label) and `docs/audits/2026-07-18-process-audit.md` (F14) over-counts their own verbatim enumerations, which list 29. Those immutable audits carry an in-file amendment marker recording this correction (this commit); their original text is preserved per CLAUDE.md §5 rule 3. The 29 are *textual references* (DDL, model declarations, defaults, bookkeeping, a message literal, fixtures), not all read-consumers.
