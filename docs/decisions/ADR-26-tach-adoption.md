# ADR-26: Tach Import Boundary Enforcement

**Date:** 2026-04-15
**Status:** Accepted
**Debate:** Council #26

## Decision

Adopt Tach for static import boundary enforcement across the `src/corp/` namespace.
Enforce via pre-commit hook and GitHub Actions CI. Distributed ownership of `tach.toml`
with lightweight review — any developer may update `tach.toml` when adding a legitimate
new dependency, but must do so deliberately (see Cultural Rules).

## Context

The repo uses a 4-layer static architecture documented in `ARCHITECTURE.md`.
Until now, import direction was enforced solely by a manual checklist item in `AGENTS.md`
(Codex code review). Codex found 3 upward dependency violations in a single module during
a routine diff review, proving that manual enforcement is insufficient at this repo's
current size (12 modules, 2,495 tests, 34 tach-tracked modules).

Codex audit findings that triggered this ADR:
- `src/corp/ingest/router.py:18` imports `corp.ops.database` (core → orchestration, upward)
- `src/corp/ingest/router.py:653` imports `corp.overnight.cke_client` (core → orchestration, upward)
- `src/corp/ingest/router.py:743` imports `corp.overnight.cke_client` (core → orchestration, upward)

These are legitimate dependencies (ingest drives overnight extraction), but they reveal that
`corp.ingest` belongs in the "orchestration" layer, not "core" — a classification error in
earlier architecture documentation.

## Architecture: 4-Layer Model

```
interface > orchestration > core > foundation
```

A module at layer N may import from layers N and below. Never from N+1 or higher.

Layer assignments (defined in `tach.toml`):

foundation — no corp.* imports or only same-package/utility imports:
  corp.schema (utility), corp.models, corp.routing_types (utility), corp.extraction

core — imports from foundation only:
  corp.extractor, corp.config, corp.vault_io, corp.intent_router, corp.llm_router,
  corp.audit, corp.integrity, corp.freshness_scanner, corp.retrieve, corp.cleanup,
  corp.project, corp.opportunity, corp.rfp, corp.ops, corp.overnight,
  corp.project_resolver (reclassified in Phase 2 — see Phase 2 Resolution section below)

orchestration — imports from core and foundation:
  corp.ingest, corp.index_builder, corp.task_manager,
  corp.template_manager, corp.workflow_engine, corp.actions, corp.built_in_actions,
  corp.query_engine (reclassified in Phase 2 — see Phase 2 Resolution section below)

interface — imports from any lower layer:
  corp.sandbox, corp.chat, corp.test_pipeline, corp.cli

### corp.ingest classification: orchestration

`corp.ingest` is classified as "orchestration" (not "core") because:

1. `ingest/router.py` directly imports `corp.ops.database` (orchestration-level OpsDB facade)
2. `ingest/router.py` directly imports `corp.overnight.cke_client` for extraction triggering
3. `ingest/inbox.py` drives the full pipeline at L3 runtime depth

The ingest package is a pipeline orchestrator, not a pure routing primitive. If a future
refactor extracts routing primitives (renamer, classifier) into a separate package with no
ops/overnight dependencies, those primitives could be reclassified as core submodules.

### Utility modules

`corp.schema` and `corp.routing_types` are marked `utility = true`. Utility modules are
exempt from layer ordering — they may be imported by any layer. Both are cross-cutting
constants/dataclasses with no meaningful dependency risk.

## Enforcement

pre-commit: `tach check` runs as a local hook on `src/corp/**/*.py` changes.
CI: `.github/workflows/tach.yml` runs `tach check` on every PR and main push.

`tach sync` is NOT wired into pre-commit or CI. See Cultural Rules.

## Cultural Rules

**tach sync is a manual, deliberate step — not an auto-fix.**

When adding a new import between modules:
1. Run `tach sync --add` manually.
2. Inspect the diff: does the new dependency make architectural sense?
3. Commit `tach.toml` alongside the code change in the same commit.

Never run `tach sync` to make a failing check pass without reviewing what changed.
The diff is the design review. See CONTRIBUTING.md for the full workflow.

## Exclusions

`tests/` is excluded from `source_roots`. Tests legitimately cross-import layers
(e2e tests import from cli/, ingest/, ops/, retrieve/ simultaneously). Tach checking
tests produces false positives with no architectural signal.

## Scope: What Tach Does NOT Own

Tach checks import direction only. It does not replace:
- Ruff (style, formatting, lint)
- Pytest (correctness)
- Codex (security, API contract, error handling, SQL injection checks)

## Alternatives Considered

**Manual AGENTS.md checklist only** — proven insufficient. 3 violations found in single review.
**Pylint import rules** — no layer concept, only explicit allow/deny lists. High maintenance.
**Import Linter** — similar capability but less ergonomic config; no pre-commit integration.

## Deferred

Step 12 (separate PR): Update AGENTS.md and ARCHITECTURE.md to use the 4-layer taxonomy
(foundation/core/orchestration/interface) consistently, replacing the existing 7-layer
static/runtime model description. The two models coexist during Phase 1.

## Phase 2 Resolution (2026-04-15)

After Phase 1 merge, CI surfaced 6 baseline violations from initial layer classification.
Root cause: classification was based on runtime call-chain depth, not actual static import surface.

Reclassifications:
- corp.project_resolver: orchestration → core
  Justification: imported by L1 modules (intent_router, llm_router). Must sit at or below their layer.
- corp.query_engine: interface → orchestration
  Justification: imported by orchestration-layer actions. Cannot be in interface layer.
  Also depends on corp.index_builder (orchestration), confirming correct placement.

Result: tach check clean. CI unblocked. Zero Python source changes.

Lesson: Initial Tach classification should use tach sync --add output (actual import graph)
as ground truth, not architectural intent. Architectural intent maps to layer order;
classification of individual modules maps to actual imports.
