# Lessons Learned — corp-monorepo

<!-- scope: hybrid -->

> **Format:** `### YYYY-MM-DD | source | lesson | category | [scope: X] | action taken`
> New entries go at the top of the Entries section. Never edit old entries. Never delete (ADR-29).
> Cross-ecosystem lessons live in `../.dev-knowledge/LESSONS.md`; this file is corp-monorepo-local.
> Last updated: 2026-07-13

---

### 2026-07-18 | manifest doctrine (senior review 2026-07-17 item 1; AMD-1 + Arc-B Batch 3) | Deletion-manifest rulings must gate two failure modes — column removals need consumer enumeration at COLUMN granularity before KILL, and kills whose only evidence is a runtime claim (not a caller grep) default to PROPOSED-GATED | methodology | [scope: hybrid] | codified in `docs/templates/deletion-manifest-template.md` (amendments A/B); JOURNAL noted

A deletion manifest that rules a *column* KILL off a module-level caller grep can mis-fire. AMD-1's column-granularity enumeration of `projects.facts_count` (31 sites) surfaced that the column is a **live vault-sourced scalar** populated from note frontmatter (`index_builder.py:389/:414`), independent of the dead facts loader — a module-level grep would have called it dead. Separately, a "dead lane" whose evidence is a **runtime claim** rather than a zero-caller grep (Arc-B Batch 3: `ingest/router.py` internals are live in the import graph, `router.py:295/:596`) must be **PROPOSED-GATED**, not KILL — the boundary is witnessed at execution on the operator's word. Forward rule: for a column/field removal, enumerate consumers at **column** granularity first; for a runtime-claim kill, **default the ruling to GATED**. Both are now in the deletion-manifest template doctrine (amendments A/B). The 2026-07-18 process audit independently re-confirmed the facts_count case (F7).

### 2026-05-28 | ruff hook-version mismatch | A pinned pre-commit ruff binary can disagree with the venv ruff and manufacture phantom violations | tooling | [scope: dev] | bumped the pre-commit ruff to v0.15.8; 89 I001 import-sort violations cleared; lenient select `["E","F","I"]` kept as the intentional baseline (recorded in ADR-32)

The pre-commit `ruff` hook was pinned at v0.4.0 while the project venv ran ruff v0.11+. The two versions sorted imports differently, so `tach`/CI showed 89 `I001` violations that did not reproduce under the venv binary — phantom failures that cost a debugging cycle. Forward rule: pin the pre-commit hook ruff and the venv ruff to the same major/minor, or the lint signal is not trustworthy. When a lint error will not reproduce locally, check the hook-pinned tool version against the venv version BEFORE chasing the code.

### 2026-05-28 | VISION-vs-code drift | An aspirational VISION principle that the code never realized produces false conformance assessments | methodology | [scope: hybrid] | deep-read all 4 routing modules, confirmed genuinely distinct per-domain routing (no cross-imports/shared dispatch), amended VISION §Values to "Deterministic per-domain routing" (Path B; deep-audit D2 closed, commit `0a9410c`)

VISION §Values declared "one routing authority / single source of truth" but routing is deterministically distributed across `extraction/routing.py`, `ingest/router.py`, `overnight/classifier.py`, `retrieve/engine.py` — disjoint inputs, no shared mutable state. The principle was Council-origin aspiration that the implementation never adopted. Forward rule: when an audit flags a VISION-vs-file-state mismatch, first establish which is ground truth (the working code or the stated principle); correcting documentation drift (Path B) is not an architectural decision and needs no Council — only a genuine consolidation (Path A) does.
