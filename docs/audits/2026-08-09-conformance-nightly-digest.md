# corp-monorepo — Nightly Conformance Digest (2026-08-09)

- **Date:** 2026-08-09
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=11 survived=10 killed=1 -->

## Summary

Documentation health is good in structure and poor in currency. Every structural existence claim that could be checked held — 39 clean checks across JOURNAL-vs-git provenance, living-doc file/table claims, and deterministic numeric inventories, including exact LOC and config-count matches and a byte-consistent CONTRIBUTING/pre-commit hook table. All ten survivors are drift, not error-in-design, and eight of them trace to just two root causes: the [#22] task-manager KILL cascade of 2026-07-17 (which ARCHITECTURE.md, last committed 2026-07-16, cannot yet reflect — the phantom task_manager.py, the phantom cli/task.py plus its stale cli/__init__.py docstring, and both module-count annotations) and ordinary post-doc LOC churn. The remaining two are a stale JOURNAL (21 days, two unrecorded operator merges plus the ARC-4 leg-1 merge) and a References line pointing at a README that never existed. The one genuinely load-bearing risk is ARCHITECTURE.md:483, which tells the operator that dev-check.ps1 runs tach and pre-commit when it does not — CLAUDE.md §5 rule 10 routes pre-PR confidence through that false claim. The skeptic killed 1 of 11 raw findings (9% kill rate), a low rate consistent with verifiers that carried concrete evidence commands; the single kill was a template-guideline line-count objection against a divergence the repo already documents and justifies in-file, i.e. correctly rejected as a waiver matter rather than a defect.

## Findings (PROPOSALS ONLY)

### High

- [living-docs] ARCHITECTURE.md:89 (also :212, :228) still documents task_manager.py ("Task CRUD via Obsidian vault notes", add_task/list_tasks/complete_task) — module deleted by 8ffe8e5 [#22]; doc last committed eb6d5fc predates the KILL. evidence: find src/corp -iname 'task*'; grep -rln "add_task|list_tasks|complete_task" src/corp --include=*.py

### Med

- [living-docs] ARCHITECTURE.md:341 and src/corp/cli/__init__.py:11-14 advertise `corp task add/list/done` handled by `cli/task.py` — no such file or registered command group (same [#22] cascade). evidence: find src/corp/cli -iname 'task*'; grep -n "task" src/corp/cli/__init__.py
- [living-docs] ARCHITECTURE.md:483 claims `scripts/dev-check.ps1` is the pre-PR gate running pytest + pre-commit + tach check — the script runs only ruff format, ruff check --fix, run-all-tests.ps1, pytest tests/integration/; no tach, no pre-commit. evidence: cat scripts/dev-check.ps1; grep -n 'tach|pre-commit' scripts/dev-check.ps1 scripts/run-all-tests.ps1
- [journal] JOURNAL.md newest entry is 2026-07-19 (21 days stale) while two genuine operator --no-ff session merges went unrecorded: 65a8a35 (2026-07-29, chore/vscode-w1-visibility) and 37b8aa1 (2026-08-08, worktree-lane-a-283-dedup). evidence: grep -m1 '^### ' JOURNAL.md && git log --oneline --since=2026-07-20 --until=2026-08-09

### Low

- [journal] Merged ARC-4 leg-1 ruff/pytest floor equalization (2c48fd5, feat/arc4-leg1-ruff-equalization, pyproject.toml +14/-2) has no JOURNAL entry by topic or branch name. evidence: git show 2c48fd5 --stat && grep -n 'ARC-4|arc4|ruff-equalization' JOURNAL.md
- [living-docs] VISION.md:149 lists `README.md` as a canonical reference doc — the file does not exist on disk and never existed in git history. evidence: test -f README.md || echo MISSING
- [counts] ARCHITECTURE.md:116 says extract.py is 1184 LOC — actual 1194 (changed 40d8fec, post-doc). evidence: wc -l src/corp/extractor/extract.py
- [counts] ARCHITECTURE.md:179 says database.py (OpsDB) is 542 LOC — actual 562 (changed b28db4d, post-doc). evidence: wc -l src/corp/ops/database.py
- [counts] ARCHITECTURE.md:86 says actions/ has 12 modules — actual 11 (task_actions.py killed in [#22]). evidence: ls src/corp/actions/*.py | wc -l
- [counts] ARCHITECTURE.md:193 says cli/ has 18 files — actual 17 (cli/task.py killed in [#22]). evidence: ls src/corp/cli/*.py | wc -l

## Next Actions (proposals for operator)

- Single ARCHITECTURE.md refresh commit closing the [#22] cascade: drop the three task_manager references (:89, :212, :228), drop the `corp task add/list/done` row (:341), and correct the two counts (:86 12→11 modules, :193 18→17 files).
- Same-branch code edit: strip the four stale `corp task*` / `corp tasks` usage lines from src/corp/cli/__init__.py:11-14.
- Decide the dev-check.ps1 discrepancy in the direction you want it to be true: either correct ARCHITECTURE.md:483 to the script's actual four stages, or add the pre-commit and tach legs to the script so the §5 rule-10 promise holds.
- Prepend JOURNAL entries (ADR-49 shape, newest-first) for the 2026-07-29 chore/vscode-w1-visibility merge (65a8a35), the 2026-08-08 worktree-lane-a-283-dedup merge (37b8aa1), and the ARC-4 leg-1 ruff-equalization merge (2c48fd5).
- Refresh the two LOC annotations (extract.py 1184→1194, database.py 542→562) in the same doc commit as item 1.
- Drop the README.md line from VISION.md:149, or create the capability/module index it promises.
- Optional hygiene: record the CLAUDE.md length overrun as an explicit waiver in .methodology.yaml so the killed finding stops resurfacing each nightly run.

## Killed Findings

- CLAUDE.md is a 'Single canonical agent-instruction file (≤200 lines)' but is 240 lines — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- V1: 2026-07-19 Night consolidation batch N1 — docs/audits/2026-07-19-night-consolidation-decision-plan.md exists on disk.
- V1: 2026-07-19 Night consolidation batch N2 — test_cke_paths_resolve worktree-compat fix confirmed in 4749dc9.
- V1: 2026-07-19 Night consolidation batch N3 — BACKLOG #69 ADR-archival task present at BACKLOG.md:138.
- V1: 2026-07-19 Module connection map Wave-3/Wave-4 amendments — confirmed via 95e1f0c and b066c4a.
- V1: 2026-07-19 S13 archival manifest SIGNED — file exists on disk.
- V1: 2026-07-19 S13 archival manifest EXECUTED G1 — 8 .html render-twins KILLed, confirmed via 74ef46c.
- V1: 2026-07-19 S13 archival manifest EXECUTED G2 — 19 conformance digests KILLed, confirmed via aad2575.
- V1: 2026-07-19 E5 lane #38 FR-10 source registry — source_registry.py, source_value.py, source_observation_repo.py all exist and match git log.
- V1: 2026-07-19 E5 lane #38 terra re-review — pass2/3/4 fix commits present with matching subjects.
- V1: 2026-07-19 E5 lane #38 merge to main — confirmed via 60b7367.
- V2: config/paths.toml, config/naming_config.yaml, tach.toml, .methodology.yaml, .claude/CLAUDE-FLOOR.md.sha256 all exist.
- V2: src/corp/ unified namespace exists; tests/safety/test_vault_writer_invariant.py exists.
- V2: .pre-commit-config.yaml hook set exactly matches CLAUDE.md §9 roster.
- V2: scripts/run-all-tests.ps1 exists and runs pytest tests/ -x --tb=short as claimed; scripts/dev-check.ps1 exists (contents flagged above).
- V2: 5 CLIs declared in pyproject.toml [project.scripts], matching CLAUDE.md and ARCHITECTURE.md.
- V2: docs/decisions/ADR-14, ADR-23, ADR-27 and docs/decisions/README.md exist.
- V2: repo-level slash commands match CLAUDE.md §7 (only /override); repo skills contain only gotchas/, matching §8.
- V2: all ARCHITECTURE.md Module Map root modules exist except task_manager.py (flagged); all CLI Reference files exist except cli/task.py (flagged).
- V2: secondary CLI entry points (schema/cli.py, extractor/scripts/run.py, project/cli.py, opportunity/cli.py) all exist.
- V2: all top-level package dirs in the ARCHITECTURE.md codemap exist; all config/ files in the Configuration Architecture table exist.
- V2: CONTRIBUTING.md's Validators hook table is byte-consistent with .pre-commit-config.yaml.
- V3: ingest/router.py 893 LOC; ingest/inbox.py 951 LOC — exact match.
- V3: config/agents.yaml 6 agents; naming_config.yaml 22 type codes and 32 client aliases — exact match.
- V3: 5 CLIs in pyproject.toml [project.scripts]; OpsDB facade delegates to 5 repos; CLAUDE.md §5 has 12 numbered critical rules — exact match.

