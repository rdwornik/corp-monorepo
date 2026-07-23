# corp-monorepo — Nightly Conformance Digest (2026-07-23)

- **Date:** 2026-07-23
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=7 survived=7 killed=0 -->

## Summary

Documentation health is moderate: all 7 raw findings survived the adversarial skeptic (0 killed, a 0% kill-rate), meaning every drift signal was independently reproduced and none were false positives. The issues cluster in two areas: one structural living-docs defect (a documented task_manager.py module and wired 'corp task' command that do not exist anywhere in the codebase) and six numeric/count inventory drifts (module counts, self-asserted line budgets, LOC figures, file counts), plus one journal-completeness gap (the ARC-4 leg-1 merge lacks a dedicated JOURNAL entry). The extensive checked-clean list confirms that JOURNAL-vs-git provenance, ADR existence, config inventories, and most LOC/count claims are accurate, so the drift is localized rather than systemic. No high-severity findings surfaced; the profile is 4 medium and 3 low, all cheaply fixable via documentation edits.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- living-docs: ARCHITECTURE.md (89, 212, 228, 341), cli/README.md:25, and cli/__init__.py:11-14 document a task_manager.py module and wired 'corp task add/list/done' command via cli/task.py, but neither file exists and no task command is imported/registered.
- counts: ARCHITECTURE.md calls actions/ '12 modules' (line 86) and repeats '12 domain modules' (line 418), but the package holds only 9 domain-action modules (11 files incl. __init__.py and _helpers.py).
- counts: CLAUDE.md:13 self-asserts 'Single canonical agent-instruction file (<=200 lines)' but the file is 240 lines.
- journal: ARC-4 leg-1 ruff/pytest floor equalization merge (2c48fd5, 2026-07-18) is substantive merged work with no dedicated JOURNAL entry, appearing only incidentally as a worktree base-SHA in the 2026-07-19 module-connection-map entry (JOURNAL.md:19).

### Low

- counts: ARCHITECTURE.md:193 describes cli/ as '18 files' but the package contains 17 .py files.
- counts: ARCHITECTURE.md:179 states database.py is '542 LOC'; the live file is 562 LOC.
- counts: ARCHITECTURE.md describes extract.py as '1184 LOC' (line 116) and echoes '1589->1184 LOC' (line 419); the live file is 1194 LOC.

## Next Actions (proposals for operator)

- Resolve the task_manager/cli/task references: either remove them from ARCHITECTURE.md (89, 212, 228, 341), cli/README.md:25, and the cli/__init__.py:11-14 docstring, or restore the removed modules and wire the command.
- Update the actions/ module count from '12 domain modules' to '9 domain modules' in ARCHITECTURE.md lines 86 and 418.
- Reconcile CLAUDE.md's self-asserted budget: trim to <=200 lines or amend line 13 to match the actual 240-line size.
- Add a dedicated 2026-07-18 JOURNAL entry documenting the ARC-4 leg-1 ruff/pytest floor equalization merge (2c48fd5), per the per-merge anchor convention.
- Correct the low-severity numeric drifts: cli/ '18 files'->'17' (line 193), database.py '542 LOC'->'562' (line 179), and extract.py '1184'->'1194' in both cells (lines 116 and 419), leaving the '1589' pre-refactor figure as-is.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-07-19 'Module connection map' entry: commits 95e1f0c and b066c4a both exist and match the described content
- V1: 2026-07-19 'Night consolidation batch' entry: N2 4749dc9, N3 4bbbf9a, N1 5816b03 all exist with matching subjects
- V1: 2026-07-19 'E5 lane #38: terra GREEN (pass 5)' entry: merge commit 60b7367 exists matching claimed story-return merge
- V1: 2026-07-19 'terra re-review #4' entry: b28db4d exists, touches src/corp/ops/database.py and source_observation_repo.py as claimed
- V1: 2026-07-19 'terra re-review #3' entry: 363bdd4 exists, subject matches
- V1: 2026-07-19 'terra re-review #2' entry: 2c1ab27 exists, subject matches
- V1: 2026-07-19 'terra pre-merge review' entry: a406b4c exists, subject matches
- V1: 2026-07-19 'FR-10 source registry' entry: all 5 step commits exist with matching subjects
- V1: 2026-07-19 'S13 archival manifest EXECUTED' entry: merges 236de12/74ef46c and commit aad2575 all match claimed file-move/delete counts precisely
- V1: 2026-07-19 'S13 archival manifest SIGNED' entry: commit 26876a0 exists and adds the claimed file
- V1: 2026-07-18 'BACKLOG distribution Part 2' entry: merge 770a804 exists matching claim
- V1: All 10 most-recent JOURNAL entries fall within available non-shallow git history (boundary 2026-07-16)
- V2: config/paths.toml exists
- V2: src/corp/ namespace exists as unified package
- V2: tests/safety/test_vault_writer_invariant.py exists
- V2: config/naming_config.yaml exists
- V2: .pre-commit-config.yaml exists
- V2: 5 CLIs corp/corp-meta/cke/cpe/com declared in pyproject.toml [project.scripts]
- V2: scripts/run-all-tests.ps1 exists
- V2: scripts/dev-check.ps1 exists
- V2: repo-level slash command ./.claude/commands/override.md matches CLAUDE.md s7
- V2: all 9 pre-commit hook ids in CLAUDE.md s9 found in .pre-commit-config.yaml
- V2: corp ADR-14, ADR-23, ADR-27 exist under docs/decisions/
- V2: ARCHITECTURE.md Governing ADRs local list all exist under docs/decisions/
- V2: OneDrive guard functions exist as ARCHITECTURE.md claims
- V2: chat.py, sandbox.py, test_pipeline.py exist at src/corp/ root as claimed
- V2: docs/diagrams/ absence and no Mermaid blocks consistent with ARCHITECTURE.md's own notice
- V2: .github/workflows/tach.yml runs 'tach check' consistent with CI claim
- V3: src/corp/ingest/router.py = 893 LOC matches claim
- V3: src/corp/ingest/inbox.py = 951 LOC matches claim
- V3: config/naming_config.yaml type_codes = 22 matches claim
- V3: config/naming_config.yaml client_aliases = 32 matches claim
- V3: config/agents.yaml agents = 6 matches claim
- V3: pyproject.toml [project.scripts] = 5 entries matches claim
- V3: src/corp/ops/database.py instantiates 5 repository classes matching OpsDB-delegates-to-5-repos claim

