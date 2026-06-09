# corp-monorepo — Nightly Conformance Digest (2026-06-09)

- **Date:** 2026-06-09
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=3 survived=3 killed=0 -->

## Summary

Documentation health is strong: 42 verifier checks across JOURNAL-vs-git, living-doc structural claims, and deterministic numeric inventory all passed clean, and the skeptic kill-rate was 0% (3 of 3 raw findings survived adversarial review, none reclassified as false positives). The three survivors are all bookkeeping or wording drift rather than structural defects: two journal-hygiene gaps (one medium, one low) and one low-severity wording mismatch between CLAUDE.md and the actual pre-commit ruff configuration. No high-severity issues were found, and every claimed git SHA, branch merge, file path, CLI entry point, and numeric inventory count was confirmed.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- journal: Two manual commits on 2026-06-06 after the last journal write (d0989ee gotchas capture at 13:53; 116feea gh auth gate in surface-conformance.ps1 at 14:08) are unrecorded in any JOURNAL entry.

### Low

- journal: The 2026-06-04 graphify pilot entry sits at JOURNAL.md:459 in the pre-cutover March-era bottom section, invisible to the 'read last 5 entries' session-start protocol.
- living-docs: CLAUDE.md §4 (line 48) and §9 (line 114) describe ruff as 'formatting/linting' pre-commit hook, but .pre-commit-config.yaml runs only the ruff linting hook (ruff-format omitted).

## Next Actions (proposals for operator)

- Append a TODAY-dated catch-up JOURNAL entry recording d0989ee (gotchas.md harness/shell gotchas) and 116feea (gh auth gate in surface-conformance.ps1).
- Move the 2026-06-04 graphify pilot entry from JOURNAL.md:459 up to the top section alongside the other 2026-06-04 entries (lines 45-48) to match the newest-at-top convention.
- Edit CLAUDE.md §4 (line 48) and §9 (line 114) to state ruff runs linting only as a pre-commit hook (ruff-format omitted; run manually via dev-check.ps1).

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: Entry 2026-06-06 (triage catch-up): SHAs 13fea1e, a7a161e, 4b46709 all exist in git history
- V1: Entry 2026-06-06 (triage catch-up): branch chore/triage-2026-06-06 merged --no-ff (d5999cb present)
- V1: Entry 2026-06-06 (nightly conformance): branches feat/nightly-conformance (34a2a9a) and chore/remove-synthetic-proof-digest (97aca40) merged
- V1: Entry 2026-06-06 (nightly conformance): four claimed files exist (conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1)
- V1: Entry 2026-06-06 (nightly conformance): tests/test_nightly_triage_parser.py and tests/fixtures/nightly-triage/* exist
- V1: Entry 2026-06-06 (remote bookkeeping): BACKLOG.md and JOURNAL.md touched by d8d129e
- V1: Entry 2026-06-06 (remote bookkeeping): branch chore/remote-bookkeeping merged (41d5189 present)
- V1: Entry 2026-06-06 (#75 closeout): CLAUDE.md, src/corp/extractor/manifest.py, tests/extractor/test_manifest.py touched by aca2c95
- V1: Entry 2026-06-04 (ARCHITECTURE count refresh): branch docs/architecture-count-refresh merged (7b7e708); ARCHITECTURE.md changed by 96db96b
- V1: Entry 2026-06-04 (conformance baseline): branch docs/conformance-baseline merged (1aa97c4); baseline digest exists on disk
- V1: Entry 2026-06-03 (ruff drift BACKLOG): branch docs/backlog-ruff-drift merged (98dd12a present)
- V1: Entry 2026-06-03 (resolve 3 branches): branch chore/close-stale-branches merged (37abe8d present)
- V1: Entry 2026-06-03 (ADR-71 doctools): branch feat/consume-doctools-hooks merged (99c7925 present)
- V1: Entry 2026-06-02 (ecosystem unification): branch chore/ecosystem-unify merged; LESSONS.md created and exists
- V1: Automated nightly digest commits 552e262 (2026-06-07) and 2f3be4d (2026-06-08) are machine-generated; no journal entry required
- V2: config/paths.toml exists
- V2: src/corp/ directory exists
- V2: tests/safety/test_vault_writer_invariant.py exists
- V2: config/naming_config.yaml exists
- V2: .pre-commit-config.yaml exists
- V2: pyproject.toml [project.scripts] contains all 5 CLIs (corp, corp-meta, cke, cpe, com)
- V2: scripts/run-all-tests.ps1 exists
- V2: scripts/dev-check.ps1 exists
- V2: .claude/commands/ does not exist (consistent with CLAUDE.md §7 'none currently')
- V2: .pre-commit-config.yaml contains tach hook (id: tach-check)
- V2: docs/decisions/ contains ADR-14-naming-convention-v2.md
- V2: docs/decisions/ contains ADR-23-monorepo-internal-architecture.md
- V2: docs/decisions/ contains ADR-27-safety-invariants.md
- V2: unverifiable-in-clone: SessionStart hook runs surface-closures.ps1 from ~/.claude/settings.json
- V2: unverifiable-in-clone: /session-summary and /codex-review user-level commands
- V2: unverifiable-in-clone: gotchas and verify skills at user level
- V3: extract.py LOC = 1184: wc -l src/corp/extractor/extract.py → 1184
- V3: ingest/router.py LOC = 893: wc -l src/corp/ingest/router.py → 893
- V3: ingest/inbox.py LOC = 951: wc -l src/corp/ingest/inbox.py → 951
- V3: ops/database.py LOC = 542: wc -l src/corp/ops/database.py → 542
- V3: actions/ module count = 12: ls src/corp/actions/*.py | wc -l → 12
- V3: cli/ file count = 18: ls src/corp/cli/*.py | wc -l → 18
- V3: type_codes count = 22: python3 yaml count → 22
- V3: client_aliases count = 32: python3 yaml count → 32
- V3: agents count = 6: python3 yaml count → 6
- V3: CLI entry points = 5: grep pyproject.toml → 5 (corp, corp-meta, cke, cpe, com)
- V3: unverifiable-in-clone: notes count (488 notes, live 2026-06-04) — index.db not committed

