# Lessons Learned — corp-monorepo

<!-- scope: hybrid -->

> **Format:** `### YYYY-MM-DD | source | lesson | category | [scope: X] | action taken`
> New entries go at the top of the Entries section. Never edit old entries. Never delete (ADR-29).
> Cross-ecosystem lessons live in `../.dev-knowledge/LESSONS.md`; this file is corp-monorepo-local.
> Last updated: 2026-07-13

---

### 2026-05-28 | ruff hook-version mismatch | A pinned pre-commit ruff binary can disagree with the venv ruff and manufacture phantom violations | tooling | [scope: dev] | bumped the pre-commit ruff to v0.15.8; 89 I001 import-sort violations cleared; lenient select `["E","F","I"]` kept as the intentional baseline (recorded in ADR-32)

The pre-commit `ruff` hook was pinned at v0.4.0 while the project venv ran ruff v0.11+. The two versions sorted imports differently, so `tach`/CI showed 89 `I001` violations that did not reproduce under the venv binary — phantom failures that cost a debugging cycle. Forward rule: pin the pre-commit hook ruff and the venv ruff to the same major/minor, or the lint signal is not trustworthy. When a lint error will not reproduce locally, check the hook-pinned tool version against the venv version BEFORE chasing the code.

### 2026-05-28 | VISION-vs-code drift | An aspirational VISION principle that the code never realized produces false conformance assessments | methodology | [scope: hybrid] | deep-read all 4 routing modules, confirmed genuinely distinct per-domain routing (no cross-imports/shared dispatch), amended VISION §Values to "Deterministic per-domain routing" (Path B; deep-audit D2 closed, commit `0a9410c`)

VISION §Values declared "one routing authority / single source of truth" but routing is deterministically distributed across `extraction/routing.py`, `ingest/router.py`, `overnight/classifier.py`, `retrieve/engine.py` — disjoint inputs, no shared mutable state. The principle was Council-origin aspiration that the implementation never adopted. Forward rule: when an audit flags a VISION-vs-file-state mismatch, first establish which is ground truth (the working code or the stated principle); correcting documentation drift (Path B) is not an architectural decision and needs no Council — only a genuine consolidation (Path A) does.
