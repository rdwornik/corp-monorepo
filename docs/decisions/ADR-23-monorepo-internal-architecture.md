---
# ADR-23: Monorepo Internal Architecture Refactoring

**Date:** 2026-03-28
**Status:** Accepted
**Council debate:** `.ecosystem/council_transcripts/DECISION_23_monorepo_internal_architecture.md`
**Panelists:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)

## Context

Package architecture audit (`.ecosystem/archive/2026-03-28_PACKAGE_ARCHITECTURE_AUDIT.md`)
revealed that the 6-package monorepo structure is sound — 5 of 6 packages have clean
subprocess boundaries. The navigability problem is internal to corp-by-os: `cli.py` monolith
(3,573 lines, 71 commands), one boundary violation (`overnight/cke_client.py` directly imports
CKE with 10 import sites), unnecessary nesting (`doctor/`, `freshness/` at 2 files each;
`extraction/non_project/` at depth 6), duplicated utility (`parse_llm_json` exists in both
`corp-os-meta` and CKE with diverged implementations), and dead code (4 confirmed unused files
in `corp-rfp-agent`).

## Decisions

**Q1: Boundary Violation (`cke_client.py`) — Eliminate via subprocess**
Refactor `overnight/cke_client.py` to use subprocess calls matching the established ecosystem
pattern (`corp-project-extractor`'s `cke_invoker.py`). Measure call volume first; if >100
calls/run, implement batched invocation to limit subprocess overhead.

**Q2: CLI Monolith (`cli.py`, 3,573 lines) — Split into Click command groups**
Create `cli/` directory with domain modules (`ingest.py`, `retrieve.py`, `analytics.py`,
`overnight.py`, etc.) and `_common.py` for shared helpers/state. Thin root `cli.py` registers
all groups. All 71 commands remain accessible as `corp <command>` — zero user-facing changes.

**Q3: Unnecessary Nesting — Flatten `doctor/`, `freshness/`, `extraction/non_project/`**
Merge `doctor/` (2 files) and `freshness/` (2 files) into root-level modules. Flatten
`extraction/non_project/` (3 files) into `extraction/`. Reduces max depth from 6 to 4.
`extraction/` parent (8 files) remains intact.

**Q4: Duplication — Centralize `parse_llm_json` in `corp-os-meta`; do not rename dataclasses**
Delete CKE's local `parse_llm_json`. Port CKE's extra error handling and `normalize_string_list`
into `corp-os-meta/utils.py`. CKE imports from `corp-os-meta` (dependency already declared).
Do NOT undertake a repo-wide dataclass renaming campaign — the 10 collisions are harmless at
runtime. Rename individual dataclasses only when specific collisions cause proven, repeated
confusion.

**Q5: Dead Code — Delete 4 confirmed dead files in `corp-rfp-agent`**
Remove `clean_kb.py`, `scan_kb.py`, `kb_to_markdown.py`, `_paths.py`. Verify absence of
references outside documentation first. Git history preserves them.

## Implementation Order

| Phase | Scope | Gate |
|-------|-------|------|
| **Phase 0** | Prerequisites: measure CKE call volume, audit `cli.py` shared state, snapshot all 71 CLI help outputs, verify dead code | None |
| **Phase 1** | CLI split (Q2): `cli/` directory, domain modules, `_common.py`, smoke test | Phase 0 shared-state audit |
| **Phase 2** | Subprocess boundary (Q1): subprocess wrapper, integration tests, CI lint rule | Phase 0 call volume measurement |
| **Phase 3** | Flatten nesting (Q3): `doctor/`, `freshness/`, `extraction/non_project/` | Phase 1 complete |
| **Phase 4** | Centralize utils + delete dead code (Q4 + Q5) | Phase 3 complete |

## Alternatives Rejected

- **Formalize CKE as optional dependency (Q1 Option A):** One exception becomes precedent; the
  rest of the ecosystem uses subprocess. A formalized exception is a permanent maintenance burden
  vs. a one-time migration cost.
- **Split corp-by-os into domain packages (Q2 Option B):** Packaging/release/import churn
  disproportionate to the actual audit findings. Internal Click modularization achieves 80% of
  the benefit at 10% of the cost.
- **Rename all 10 colliding dataclasses (Q4 Option C):** Runtime-harmless collisions don't
  justify broad cross-cutting changes. Address only when specific confusion is repeatedly
  demonstrated.

## Revisit Signals

- Overnight batch runtime increases >10% after subprocess migration → implement batched
  invocation or worker pool pattern
- CLI startup exceeds 500ms after modularization → introduce lazy loading for command groups
- Specific dataclass collisions cause repeated, demonstrable bugs → rename those instances
- corp-by-os exceeds 20k lines after all phases → re-evaluate package-level extraction
