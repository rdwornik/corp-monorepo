# ADR-32: Ruff select strictness — keep lenient ruleset as intentional baseline

- **Status:** Accepted
- **Date:** 2026-05-28
- **Related:** Deep audit D1 (`docs/audits/2026-05-20-corp-monorepo-deep.md` §9.D1); BACKLOG "Per-repo deeper cleanup follow-up" (closed by this ADR)
- **Source:** 2026-05-28 ruff hook bump session; Action 7c closure

## Context

corp-monorepo carries two ruff configurations that conflict:

- `ruff.toml` (repo root) — lenient: `select = ["E", "F", "I"]`, ignore E501
- `pyproject.toml [tool.ruff]` — strict: `select = ["E","F","I","W","B","UP"]`, line-length 120, ignore E402

Ruff's config-discovery order gives `ruff.toml` precedence, so the **lenient ruleset
is the active one** in all normal invocations (deep audit finding D1, 2026-05-20-corp-monorepo-deep.md §9.D1).

Prior state (pre-2026-05-28): the pre-commit ruff hook was pinned at v0.4.0 while the venv
had v0.11+ installed. The version mismatch caused the hook to run against the hook-bundled
binary instead of the project venv, silently allowing 89 `I001` (import-sort) violations that
the venv ruff would have flagged. After the hook was bumped to `rev: v0.15.8` the 89 violations
were fixed (`ruff check --fix`) and the repo reached 0 errors under the lenient ruleset.

The universalization mega-session (2026-05-27) deferred the strictness question rather than
resolving it, leaving the ruff-strictness decision open. The open decision was blocking the
ADR-59 visual-pattern retrofit for corp-monorepo and the BACKLOG cleanup entry.

## Decision

**Keep the current lenient ruff select (`["E", "F", "I"]`) as the intentional, accurate
baseline for corp-monorepo.**

Rationale:
1. The repo is **lint-clean** (0 errors) under this config as of 2026-05-28, with 2524+ tests
   passing. Tightening the select would introduce an unknown error count with no triggering
   problem — a "big-bang" optimization that contradicts the "Incremental, never big-bang" VISION
   value.
2. The lenient baseline **is not neglect** — it reflects a deliberate choice (from the original
   `ruff.toml` comment "Start lenient, tighten over time") that has not yet produced a concrete
   problem warranting tightening.
3. Future tightening **remains available** as a focused pass if a concrete lint issue arises
   (e.g., a bug caught by B-series rules, or an operator decision to raise the quality bar).

The `pyproject.toml [tool.ruff]` strict config block is left in place as a preserved intention
marker; it does not affect runtime behavior because `ruff.toml` wins. Consolidating the two
configs into one is a separate chore (D1 cleanup) and is not required to close the strictness
question.

**Baseline for any future tightening:** 0 errors at current lenient select; error count under
strict select is unknown and must be measured before any tightening commit.

## Consequences

### Positive
- Ruff-strictness question is resolved; corp-monorepo ADR-59 visual-pattern retrofit is
  unblocked.
- BACKLOG "Per-repo deeper cleanup" corp-monorepo item (89 pre-existing errors) is closed —
  errors were fixed by the hook-bump session, not deferred.
- Clear documented intent: future sessions will not re-open the strictness question without
  a concrete triggering problem.

### Negative
- The `pyproject.toml [tool.ruff]` strict block remains an inconsistency until D1 is cleaned
  up in a dedicated chore session. Risk: a reader may assume the strict config is active.
  Mitigation: this ADR documents the discovery order explicitly.

## References

- Deep audit D1 (ruff config duplication): `docs/audits/2026-05-20-corp-monorepo-deep.md` §9.D1
- BACKLOG entry (P3, closed): "Per-repo deeper cleanup follow-up (post-retrofit)"
- BACKLOG entry (P2, unblocked): "ADR-59 universal visual pattern — child-repo retrofits §corp-monorepo retrofit"
- `.ruff.toml` (active config)
- `pyproject.toml [tool.ruff]` (inactive strict config, not runtime-effective)
