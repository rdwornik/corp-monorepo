# ADR-38: Deletion-manifest doctrine

- **Status:** Accepted
- **Date:** 2026-07-18
- **Decision tier:** Senior review 2026-07-17 item 1 (source AMD-1 + AMD-2, Arc-B plan Addendum B); operator-ratified 2026-07-18
- **Related:** ADR-37 (the `projects.facts_count` column whose 29-site enumeration is amendment A's precedent); ADR-27 (safety invariants)
- **Supersedes:** `docs/templates/deletion-manifest-template.md` — removed with this ADR. The methodology home for a decision is an ADR, not a template scaffold; future deletion manifests cite this ADR for doctrine.
- **First signed instance (worked example):** `docs/audits/2026-07-17-deletion-manifest-arc-b.md`

## Context

A deletion manifest is an operator-signable **contract**; execution is a **separate, operator-signed arc** (zero deletions in the session that produces the manifest — no `src/`, `tests/`, or `main` change). Manifest instances are **immutable audits** (CLAUDE.md §5 rule 3): never edit a signed manifest in place.

The binding doctrine below was previously homed in a template scaffold under `docs/templates/`. That is not the methodology home for a decision — an ADR is. This ADR relocates the **normative doctrine**; the template's per-manifest structural scaffolding is intentionally **not** carried forward (manifest authors follow this doctrine plus the first signed instance as the worked example).

## Decision

**Standard method — three evidence legs per KILL/GATED row**, each re-derived *fresh* against a named HEAD sha (never quoted from an audit):

1. whole-repo **caller re-grep** (source + tests), verbatim in a per-batch fence;
2. **data-binding cross-check** — a zero-caller module with a live data-READ binding is **not** zero-use;
3. **docs/ + config reference grep**.

A row missing any leg is stamped **UNVERIFIED** and cannot be signed.

**Ruling legend:** `PROPOSED-KILL` (re-grep supports deletion, awaiting signature) · `PROPOSED-GATED` (blocked until the operator's explicit confirmation — his word is the evidence) · `PROPOSED-KEEP` (re-grep contradicts deletion, exclusion) · `DEFER` (visibility-only, **not** signable as KILL).

**Amendment A — column-granularity enumeration before a column KILL.** A removal that drops a *column* (or a model field) requires a verbatim consumer enumeration at **column granularity** — every `path:line` that reads / writes / orders / aggregates the column — recorded *before* the row may be ruled KILL. A module-granularity caller grep is insufficient for column removals. *Precedent:* AMD-1 enumerated the `projects.facts_count` consumer sites (witnessed count **29** — 26 `src/` + 3 `tests/`; the audit's "31" summary label was an over-count corrected under ADR-37), and only the column-level pass surfaced that the column is a **live vault-sourced scalar** (populated at `index_builder.py:389/:414` from note frontmatter), *independent* of the dead facts loader — so a module-level grep would have mis-ruled it KILL. Re-confirmed by the 2026-07-18 process audit (F7).

**Amendment B — runtime-claim kills default to PROPOSED-GATED.** When a row's deletion evidence is a **runtime claim** ("this lane never fires", "0 rows ever") rather than a **caller grep** — i.e. the target is still reachable in the import graph — the row defaults to **PROPOSED-GATED**, never PROPOSED-KILL. Its exact dead boundary must be witnessed at execution, and it requires the operator's explicit word. *Precedent:* Arc-B Batch 3 (`ingest/router.py` inbox-lane internals) — `_run_extraction` / `_run_package_extraction` are **live in the import graph** (`router.py:295/:596`); "dead" rested on a runtime write-never-completed claim, so the batch is boundary-gated, never a blanket `router.py` delete.

## Consequences

- The deletion-manifest doctrine has a proper methodology home (this ADR); the `docs/templates/` scaffold is removed and **not recreated** anywhere. Future manifests cite ADR-38 for doctrine.
- The lesson side is separately recorded in `LESSONS.md` (2026-07-18 manifest-doctrine entry, amendments A/B); this ADR is the doctrine side.
- Execution discipline for any manifest: one commit per batch (independently revertable) · `./scripts/run-all-tests.ps1` after each · GATED rows fire only on the operator's recorded word.
