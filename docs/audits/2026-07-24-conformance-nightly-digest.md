# corp-monorepo — Nightly Conformance Digest (2026-07-24)

- **Date:** 2026-07-24
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=10 survived=8 killed=2 -->

## Summary

Overall doc health is fair: the core CLAUDE.md/ARCHITECTURE.md scaffolding (config paths, unified namespace, 5 CLIs, pre-commit hooks, ADR citations, several LOC and count annotations) verified clean across ~30 checks, but ARCHITECTURE.md carries one hard structural fabrication (a task_manager.py module and `corp task` CLI documented across four locations that exist nowhere in code) plus a cluster of stale counts and mislabels, and VISION.md points at a non-existent root README.md. Of 10 raw findings, 8 survived the adversarial skeptic and 2 were killed as true-but-irrelevant (out-of-scope bot commits in JOURNAL; a sub-1% extract.py LOC drift within the noise floor), a 20% kill-rate. The dominant theme is drift in ARCHITECTURE.md numeric/label inventory rather than governance or safety-invariant breakage; the JOURNAL is accurate for the sessions it narrates aside from one unrecorded ARC-4 floor-equalization merge that has now persisted across four nightly digests.

## Findings (PROPOSALS ONLY)

### High

- ARCHITECTURE.md documents task_manager.py (add_task/list_tasks/complete_task) as orchestration and a `corp task add/list/done` CLI via cli/task.py at :89/:212/:228/:341 — none exist in code (phantom module + phantom CLI).

### Med

- VISION.md:149 lists README.md as a canonical living doc, but no README.md exists at repo root and no ADR ratifies its removal (dangling reference).
- ARCHITECTURE.md:86,418 calls actions/ 'Domain-split action handlers (12 modules)' but the live dir has 9 *_actions.py domain modules (11 .py total) — wrong in two spots.

### Low

- JOURNAL.md:18-30 last-10 entries omit the ARC-4 leg-1 ruff/pytest floor-equalization merge (2c48fd5, 2026-07-18) that falls chronologically inside the narrated window — unchanged open item since the 07-21/22/23 digests.
- ARCHITECTURE.md:219-220 foundation-layer enumeration omits corp.safety, which tach.toml declares as foundation (lists 4 of 5 modules).
- ARCHITECTURE.md:493 labels ADR-16 '(skill-eval split)' but ADR-16 is 'Evaluation Metrics and Baseline' with no mention of 'skill' — genuine mislabel.
- ARCHITECTURE.md:179 states database.py is 542 LOC; the file is 562 lines (~3.7% understatement, above the noise floor).
- ARCHITECTURE.md:193 says cli/ has 18 files; there are 17 .py files (off-by-one).

## Next Actions (proposals for operator)

- ARCHITECTURE.md (high): remove or correct the task_manager.py module rows and the `corp task add/list/done` CLI entry at :89/:212/:228/:341 (and the cli/__init__ docstring) to match the actual workflow-based task handling.
- VISION.md:149 (med): either create the referenced root README.md or drop the README.md line from the References list.
- ARCHITECTURE.md:86,418 (med): correct the actions/ '12 modules' count to the actual 9 domain modules (or 11 files) in both locations.
- JOURNAL.md (low): prepend an ADR-49-shape entry narrating the ARC-4 leg-1 pyproject ruff/pytest floor-equalization merge (2c48fd5).
- ARCHITECTURE.md:219-220 (low): add corp.safety to the foundation-layer Layer Assignments list.
- ARCHITECTURE.md:493 (low): fix ADR-16's parenthetical from '(skill-eval split)' to 'eval metrics/baseline'.
- ARCHITECTURE.md:179 (low): update the database.py LOC annotation from 542 to 562.
- ARCHITECTURE.md:193 (low): correct the cli/ file count from 18 to 17.

## Killed Findings

- 3 automated nightly conformance-digest commits after 2026-07-19 (abed866, 3da2d8c, fa4583e) are not reflected in any JOURNAL entry. — _true-but-irrelevant_
- ARCHITECTURE.md says extract.py is 1184 LOC; the file is actually 1194 lines. — _true-but-irrelevant_

## Checked-and-clean (so absence is informative)

- JOURNAL 2026-07-19 module connection map entry: audit amended 204/0 via 95e1f0c, §8 probe b066c4a, merged --no-ff as 1dfee3e — matches Did/Result/Changes exactly.
- JOURNAL 2026-07-19 night consolidation N2 fix (test_cke_paths_resolve worktree-compat, 4749dc9) verified.
- JOURNAL 2026-07-19 night consolidation N3 BACKLOG #69 ADR-archival task (4bbbf9a) present in current BACKLOG.md:138.
- JOURNAL 2026-07-19 night consolidation N1 doc (5816b03) and 3-commit merge to main (334da4e) both present in git log.
- JOURNAL 2026-07-19 E5 lane #38 (FR-10 registry + terra passes 1-5 + GREEN merge): all SHAs present in claimed order, culminating in merge 60b7367.
- JOURNAL 2026-07-19 S13 archival manifest SIGNED + EXECUTED: all SHAs present and match G1/G2/G4 groupings.
- JOURNAL: all SHAs in last-10 entries fall within available shallow git history back to f844e14 (2026-07-16).
- config/paths.toml exists (CLAUDE.md §4).
- src/corp/ unified namespace exists (CLAUDE.md §3, ARCHITECTURE.md Purpose).
- tests/safety/test_vault_writer_invariant.py exists (CLAUDE.md §5 rule 4).
- config/naming_config.yaml exists (CLAUDE.md §4).
- .pre-commit-config.yaml exists with ruff + tach-check hooks (CLAUDE.md §4/§9).
- All 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts].
- scripts/run-all-tests.ps1 exists.
- scripts/dev-check.ps1 exists.
- .claude/commands/ contains exactly override.md, matching CLAUDE.md §7.
- docs/decisions/ADR-14, ADR-23, ADR-27 all exist, matching CLAUDE.md §11 citations.
- GEMINI_API_KEY configured in config/extractor/settings.yaml, matching CLAUDE.md §4.
- Pre-commit hooks listed in CLAUDE.md §9 all present in .pre-commit-config.yaml.
- ruff lenient select [E,F,I] in pyproject.toml matches ARCHITECTURE.md:486 (ADR-32).
- corp-meta CLI commands validate/normalize/report exist in src/corp/schema/cli.py.
- docs/diagrams/ does not exist, matching ARCHITECTURE.md:10 header note that it was deleted.
- config/project/, config/opportunity/, config/rfp/, config/extractor/ subdirectories all exist.
- ARCHITECTURE.md ingest/router.py claimed 893 LOC — actual 893.
- ARCHITECTURE.md ingest/inbox.py claimed 951 LOC — actual 951.
- '5 CLIs' — actual 5 entries in pyproject.toml [project.scripts].
- 'OpsDB delegates to 5 repos' — actual 5 *_repo.py files present.
- 'Type codes (22)' from naming_config.yaml — actual 22 keys.
- 'client aliases (32)' from naming_config.yaml — actual 32 keys.

