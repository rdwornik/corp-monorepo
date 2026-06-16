# corp-monorepo — Nightly Conformance Digest (2026-06-10)

- **Date:** 2026-06-10
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=4 survived=3 killed=1 -->

## Summary

Documentation health is strong: of 4 raw findings surfaced across the three verifiers, 3 survived the adversarial skeptic and 1 was killed as a false positive (25% kill-rate). All three survivors are low-severity living-doc drift issues — a dangling cross-reference to a never-committed audit file, a stale module count (12 vs. actual 10 domain handlers), and a deleted README.md still listed as live in VISION.md. No high or medium findings exist. The JOURNAL-vs-git verifier (V1) found all 10 recent entries fully corroborated by git history, the structural living-doc verifier (V2) confirmed CLAUDE.md and ARCHITECTURE.md claims hold, and the numeric-inventory verifier (V3) found deterministic counts (LOC, type codes, aliases, CLIs, agents, repositories) all accurate. The killed finding concerned a user-level SessionStart hook that is unverifiable within this clone and was correctly not treated as an in-clone conformance defect.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

_No med-severity findings._

### Low

- Dangling reference: docs/audits/2026-04-21-p1-verification.md cited as verification evidence in 3 places (ARCHITECTURE.md:548, ADR-27:179, codex-hotfix-review.md:9) but the file never existed in git history.
- Count drift: ARCHITECTURE.md:160 and :512 say actions/ split into '12 domain modules' but only 10 domain handlers exist (__init__.py and _helpers.py are infrastructure, not handlers).
- Stale reference: VISION.md:149 lists README.md as a live capability/module index, but README.md was deliberately deleted in commit 6a1ba20.

## Next Actions (proposals for operator)

- Resolve the dangling 2026-04-21-p1-verification.md reference: either create/restore the file or repoint ARCHITECTURE.md:548, ADR-27:179, and codex-hotfix-review.md:9 to the existing 2026-04-21-codex-hotfix-review.md.
- Correct the module count at ARCHITECTURE.md:160 and :512 from '12 domain modules' to '10 domain modules' (or clarify as '10 domain handlers + __init__ registry shim + _helpers').
- Remove the stale 'README.md — current capability and module index' bullet from VISION.md:149, or repoint it to ARCHITECTURE.md.

## Killed Findings

- SessionStart hook runs ./scripts/surface-closures.ps1 — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- JOURNAL.md (V1): all 10 recent entries (2026-06-02 through 2026-06-06) corroborated by git history, including commits 13fea1e/a7a161e/4b46709, issue #4 closure (merge d5999cb), sensitivity sweep (d8d129e), CLAUDE.md §6-§9 update (f5c41e6), branch deletion (e7eb86a), and ecosystem unification artifacts.
- Nightly conformance pipeline (V1): all five required files created; digests for 2026-06-06 through 2026-06-09 present in docs/audits/; code-owned count marker format verified.
- Retry wrapper (V1): confirmed present in src/corp/extractor/manifest.py for concurrent status reads.
- CLAUDE.md structural claims (V2): 5 CLIs in [project.scripts]; 4-layer dependency model enforced via tach.toml; vault_io.write_note() sole-writer invariant with test_vault_writer_invariant.py; run-all-tests.ps1 and dev-check.ps1 exist; no repo-level .claude/commands/; ruff and tach in .pre-commit-config.yaml.
- ARCHITECTURE.md structural claims (V2): 5 CLIs match pyproject.toml; 4-layer tach model verified; OneDrive safety guards present at cleanup/disk.py, cleanup/executor.py, actions/_helpers.py, project/renderer.py; 31 local ADRs in docs/decisions/; config/paths.toml, naming_config.yaml, tach.toml present; docs/diagrams/ contains the three expected SVGs.
- Numeric inventory (V3): extract.py 1184 LOC, ingest/router.py 893 LOC, ingest/inbox.py 951 LOC, ops/database.py 542 LOC; 22 type codes; 32 client aliases; 6 agents; 18 CLI files; 5 CLIs in [project.scripts]; 5 OpsDB repositories — all match.
- Excluded as unverifiable-in-clone (not failures): user-level ~/.claude/commands and ~/.claude/skills items; notes count (index.db absent from clone).

