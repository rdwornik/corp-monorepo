# corp-monorepo — Nightly Conformance Digest (2026-06-14)

- **Date:** 2026-06-14
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=3 survived=3 killed=0 -->

## Summary

Doc health is strong: all structural and numeric-inventory claims verified clean (V2 and V3 verifiers found zero drift across CLI entry points, ADRs, config files, and 12 inventory counts), and most 2026-06-06 JOURNAL entries reconcile against git. Three findings survived, all documentation-currency gaps rather than correctness defects: two med-severity missing JOURNAL entries for substantive 2026-06-06 commits (gotchas capture d0989ee, gh-auth gate 116feea), and one low-severity stale CLAUDE.md §9 wording overstating ruff's pre-commit scope. The skeptic kill-rate was 0% (0 of 3 raw findings killed) — every raw finding was re-confirmed with git timestamps, stat output, and grep misses, indicating the verifiers produced no false positives this run.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- JOURNAL gap: 2026-06-06 commits d0989ee (gotchas harness/shell capture) + merge fc31ab9 modify .claude/skills/gotchas/gotchas.md but no JOURNAL entry covers them; triage entry scopes its Changes to JOURNAL.md only.
- JOURNAL gap: 2026-06-06 commits 116feea (gh-auth gate on surface-conformance.ps1) + merge 0ef1fcd modify the production SessionStart surfacing hook but no JOURNAL entry covers them; 'Nightly conformance routine build' entry predates the enhancement.

### Low

- CLAUDE.md §9 claims ruff pre-commit hook does 'linting and formatting', but ruff-format is commented out in .pre-commit-config.yaml (lines 7-9) for CRLF/LF reasons — only the linter runs in pre-commit.

## Next Actions (proposals for operator)

- Append a 2026-06-06 JOURNAL entry recording the harness/here-string gotcha capture (d0989ee, branch docs/gotchas-2026-06-06), Changes: .claude/skills/gotchas/gotchas.md.
- Append a 2026-06-06 JOURNAL entry recording the gh-auth gate added to surface-conformance.ps1 (116feea, branch chore/gh-auth-check), Changes: scripts/surface-conformance.ps1, .claude/skills/gotchas/gotchas.md.
- Edit CLAUDE.md §9 to read 'ruff — linting only (ruff-format omitted per .pre-commit-config.yaml comment; format via dev-check.ps1)' instead of 'linting and formatting'.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-06-06 JOURNAL 'Triage ratification' — commits 13fea1e, a7a161e, 4b46709 verifiable via git log
- V1: 2026-06-06 JOURNAL 'Nightly conformance routine build' — conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1 commits confirmed present
- V1: 2026-06-06 JOURNAL 'Remote bookkeeping' — commit d8d129e present; Changes (JOURNAL.md, BACKLOG.md) verified
- V1: 2026-06-06 JOURNAL 'Scoped CLAUDE.md conformance deep-audit (#75)' — commits aca2c95, 1a057f2, f5c41e6 all present
- V1: 2026-06-04 JOURNAL 'Refresh drifted ARCHITECTURE.md counts' — commit 96db96b and merge 7b7e708 present
- V1: 2026-06-04 JOURNAL 'Conformance baseline review' — commits ae9210f and 0275923 present
- V1: Nightly digest commits (19efa78, c9fea97, ae3e711, 39c06d7, 2f3be4d, 552e262, 4a54f77) correctly excluded as automated Routine outputs
- V2: config/paths.toml exists
- V2: src/corp/ namespace exists
- V2: tests/safety/test_vault_writer_invariant.py exists
- V2: config/naming_config.yaml exists
- V2: .pre-commit-config.yaml exists with ruff (id: ruff) and tach (id: tach-check) hooks
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 exist
- V2: .claude/commands/ directory absent — matches CLAUDE.md §7 'none currently'
- V2: pyproject.toml [project.scripts] declares all 5 CLIs: corp, corp-meta, cke, cpe, com
- V2: docs/decisions/ADR-14, ADR-23, ADR-27 all exist
- V2: .github/workflows/ contains nightly-conformance-triage.yml and tach.yml
- V2: tach.toml exists with 4-layer model (interface, orchestration, core, foundation)
- V2: All CLI entry points resolve (corp.cli:cli, schema.cli:main, extractor.scripts.run:cli, project.cli:cli, opportunity.cli:cli)
- V2: unverifiable-in-clone: CLAUDE.md §9 SessionStart hook (~/.claude/settings.json outside clone)
- V3: extract.py LOC=1184 (claimed 1184)
- V3: ingest/inbox.py LOC=951 (claimed 951)
- V3: ops/database.py LOC=542 (claimed 542)
- V3: ingest/router.py LOC=893 (claimed 893)
- V3: actions/ modules=12 (claimed 12)
- V3: cli/ files=18 (claimed 18)
- V3: type_codes=22 (claimed 22)
- V3: client_aliases=32 (claimed 32)
- V3: agents=6 (claimed 6)
- V3: CLIs=5 (claimed 5)
- V3: OpsDB 5 repos (AssetRepository, PackageRepository, EventRepository, RoutingRepository, SuggestionRepository)
- V3: unverifiable-in-clone: notes count of 488 (index.db gitignored, not in clone)

