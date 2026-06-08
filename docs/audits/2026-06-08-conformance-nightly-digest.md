# corp-monorepo — Nightly Conformance Digest (2026-06-08)

- **Date:** 2026-06-08
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=3 survived=2 killed=1 -->

## Summary

Documentation health is strong. Of 3 raw findings across the JOURNAL-vs-git, living-doc structural, and numeric-inventory verifiers, only 2 survived the skeptic, both low-severity JOURNAL omissions on the active branch (claude/great-mayer-Au5Av) where committed gotchas.md and surface-conformance.ps1 changes lack the CLAUDE.md s6-mandated Changes: record — neither merged to main yet. The skeptic killed 1 of 3 (a 33% kill-rate): the CLAUDE.md s98 'none currently' repo-level commands claim, which a missing .claude/commands/ directory satisfies as well as an empty one. No high- or medium-severity issues exist, and an extensive checked-clean sweep confirms all structural claims (5 CLIs, ADR files, config files, pre-commit hooks, diagrams, src layout), numeric inventories (LOC counts, module/CLI/alias/type-code tallies), and recent JOURNAL entries verify against git.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

_No med-severity findings._

### Low

- JOURNAL.md has no Changes: entry for commits d0989ee/fc31ab9 adding the 'Shell & Claude Code harness' section to .claude/skills/gotchas/gotchas.md:322-335 on branch claude/great-mayer-Au5Av.
- JOURNAL.md has no Changes: entry for commits 116feea/0ef1fcd adding the gh-auth gate to scripts/surface-conformance.ps1:24-55 plus a gotchas.md:318-319 pointer on the active branch.

## Next Actions (proposals for operator)

- Append a JOURNAL entry (ADR-49 shape) recording the gotchas.md 'Shell & Claude Code harness' section (commits d0989ee/fc31ab9) under Changes: before merging claude/great-mayer-Au5Av to main.
- Append a JOURNAL entry (ADR-49 shape) recording the surface-conformance.ps1 gh-auth gate plus gotchas.md pointer (commits 116feea/0ef1fcd) under Changes: before merging the branch to main.
- Optionally consolidate both omissions into a single catch-up JOURNAL entry covering all four 2026-06-06 branch commits.

## Killed Findings

- CLAUDE.md:98 'Repo-level (./.claude/commands/): none currently' — the .claude/commands/ directory does not exist at all. — _true-but-irrelevant_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-06 Triage ratification commits 13fea1e, a7a161e, 4b46709 verified in git with correct dates and file changes
- V1: 2026-06-06 Triage ratification Changes line ('JOURNAL.md only', d5999cb +7) verified correct
- V1: 2026-06-06 Nightly conformance routine artifacts all exist on disk (conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1, test_nightly_triage_parser.py, fixtures dir with 4 files)
- V1: 2026-06-06 Nightly conformance merge commit 34a2a9a and cleanup merge 97aca40 confirmed in git
- V1: 2026-06-06 Remote bookkeeping commit d8d129e (BACKLOG #13 sensitivity sweep) confirmed
- V1: 2026-06-06 CLAUDE.md #75 closeout merge aca2c95 and load_status retry test (test_manifest.py:170) confirmed
- V1: 2026-06-04 ARCHITECTURE.md count refresh commits 96db96b and 7d43bd4 confirmed; last_reviewed re-stamped
- V1: 2026-06-04 Conformance baseline commit ae9210f (baseline digest, 100 lines) confirmed
- V1: 2026-06-03 ruff drift BACKLOG commit 48a565e and unmerged-branches commit e7eb86a confirmed
- V1: 2026-06-03 Hub doc-tooling merge 99c7925 and .pre-commit-config.yaml dev-knowledge/toc refs confirmed
- V1: 2026-06-02 Ecosystem unification merge f1cb75b and LESSONS.md root file confirmed
- V1: 2026-06-06 and 2026-06-07 automated nightly digests correctly handled per workflow contract (no operator journal entry required)
- V2: CLAUDE.md s4 config files (paths.toml, naming_config.yaml, .pre-commit-config.yaml) all present
- V2: CLAUDE.md s9 pre-commit hooks ruff and tach declared in .pre-commit-config.yaml
- V2: CLAUDE.md s3/s11 all 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts]
- V2: CLAUDE.md s5 safety/test files present (test_vault_writer_invariant.py, run-all-tests.ps1, dev-check.ps1)
- V2: CLAUDE.md s11 corp ADR-14, ADR-23, ADR-27 files present in docs/decisions/
- V2: ARCHITECTURE.md src/corp/ namespace, tach.toml, and all 5 CLI entry points resolve to existing modules
- V2: ARCHITECTURE.md diagrams (system-context.svg, container-module.svg, magistrala-pipeline.svg) present
- V2: ARCHITECTURE.md cli/ package contains 18 files; .github/workflows/ has CI workflows
- V2: CLAUDE.md s8 .claude/skills/gotchas repo-level skill present
- V2: unverifiable-in-clone: ~/.claude/settings.json SessionStart hook (ADR-70) — user-level path outside clone
- V2: unverifiable-in-clone: ~/.claude/commands/ user-level slash commands — user-level path outside clone
- V2: unverifiable-in-clone: ~/.claude/skills/ user-level gotchas skill — user-level path outside clone
- V3: LOC counts verified — extract.py 1184, ingest/router.py 893, ingest/inbox.py 951, ops/database.py 542
- V3: module/file tallies verified — actions/ 12 modules, cli/ 18 files
- V3: inventory counts verified — 22 type codes, 32 client aliases, 6 agents in agents.yaml, 5 CLIs in pyproject.toml
- V3: OpsDB delegates to 5 repos (Asset, Package, Event, Routing, Suggestion) confirmed
- V3: unverifiable-in-clone: notes count (488, live 2026-06-04) — index.db gitignored

