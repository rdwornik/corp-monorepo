# corp-monorepo — Nightly Conformance Digest (2026-06-06)

- **Date:** 2026-06-06
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=6 survived=2 killed=4 -->

## Summary

Nightly conformance: 6 raw findings, 2 survived the skeptic (67% kill-rate). Both survivors are ARCHITECTURE.md count drift (the repo's dominant class); no behavioral or safety defects. Proposals only.

## Findings (PROPOSALS ONLY)

### High

- ARCHITECTURE.md:244 client aliases (32) -> live value differs; refresh count.

### Med

- ARCHITECTURE.md:240 inbox.py (951 LOC) -> live wc -l differs; refresh count.

### Low

_No low-severity findings._

## Next Actions (proposals for operator)

- Refresh the two drifted ARCHITECTURE.md counts and re-stamp last_reviewed (single doc cleanup).
- Consider the deterministic count-verifier already covers this class; no code change needed.

## Killed Findings

- router.py (893 LOC) drift — _evidence-not-definitive_
- extract.py (1184 LOC) drift — _evidence-not-definitive_
- corp '40+ commands' understated — _true-but-irrelevant_
- actions/ '12 modules' — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: last-10 JOURNAL entries corroborated against git
- V2: 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml
- V3: extract.py=1184 and router.py=893 match the doc
- V3: unverifiable-in-clone: notes count (index.db not in clone)

