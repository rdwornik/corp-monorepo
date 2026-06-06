# corp-monorepo — Nightly Conformance Digest (2026-06-06)

- **Date:** 2026-06-06
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=5 survived=0 killed=5 -->

## Summary

Nightly conformance: 5 raw findings, 0 survived the skeptic (100% kill-rate). All living-doc counts and structural claims conform to live repo state. Clean night.

## Findings (PROPOSALS ONLY)

_None — all checked claims conform. See checked-and-clean below._

## Next Actions (proposals for operator)

_No action required — clean night._

## Killed Findings

- extract.py LOC drift — _evidence-not-definitive_
- router.py LOC drift — _evidence-not-definitive_
- actions/ module count — _documented-decision_
- corp '40+ commands' — _true-but-irrelevant_
- [#5] JLR open — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: last-10 JOURNAL entries corroborated against git
- V2: 5 CLIs declared; ruff + tach in .pre-commit-config.yaml; ADR-14/23/27 exist
- V3: extract.py=1184, router.py=893, inbox.py=951, database.py=542 all match
- V3: unverifiable-in-clone: notes count (index.db not in clone)

