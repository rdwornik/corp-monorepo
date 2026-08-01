# corp-monorepo — Nightly Conformance Digest (2026-08-01)

- **Date:** 2026-08-01
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** native

<!-- counts: raw=10 survived=9 killed=1 -->

## Summary

Documentation health is broadly sound: the two structural living-docs (ARCHITECTURE.md, CLAUDE.md) verify cleanly on the overwhelming majority of structural, configuration, and numeric-inventory claims (50+ checked-clean items across V1/V2/V3, including all 5 CLIs, all 9 pre-commit hooks, ADR presence, module-map existence, and several exact LOC/count matches). The surviving defects cluster into three understood buckets: (1) stale ARCHITECTURE.md codemap content describing a retired task subsystem (task_manager.py, cli/task.py) plus small numeric drift (LOC and module counts) — all known-deferred to the A3 R9 codemap rewrite, but still asserting live subsystems and specific falsifiable numbers that are now wrong; (2) two JOURNAL coverage gaps on the freshest repo state (the 2026-07-29 W1 visibility merge and the ARC-4 leg-1 floor-equalization merge), both remediable by prepend without touching append-only history; (3) one dangling audit citation. The skeptic kill-rate was 1/10 (10%): the sole false positive was the module-connection-map JOURNAL entry, correctly killed because "fixing" a point-in-time append-only entry that was accurate at session wrap would itself violate the ADR-49 / CLAUDE.md §5 append-only critical rule. No high-severity defects; 3 med, 6 low.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- ARCHITECTURE.md:89 (also :212, :228) documents task_manager.py as a live root-level src/corp/ module (add_task/list_tasks/complete_task), but the file was deleted in commit 8ffe8e5 and no longer exists — codemap describes a retired subsystem as live.
- ARCHITECTURE.md:341 routes `corp task add/list/done` to cli/task.py, but neither the file nor the command group exists — the task workflow was retired in Arc-B (8ffe8e5 + d846c0d).
- JOURNAL.md has no entry for the 2026-07-29 chore/vscode-w1-visibility merge (the newest substantive work); the freshest entry is dated 2026-07-19 — coverage gap on the latest repo state.

### Low

- JOURNAL.md has no entry anywhere for the ARC-4 leg-1 ruff/pytest floor-equalization merge (2c48fd5, commits 07578f6/bee236c) — a substantive --no-ff merge touching pyproject.toml with zero journal trace.
- JOURNAL.md:33 states the #38 E5 lane was '11 commits', but git shows 15 on epic/e5-registry before merge 60b7367 — a genuine write-time arithmetic error (correctable only via a note in a new append-only entry).
- ARCHITECTURE.md:454 cites docs/audits/2026-04-21-p1-verification.md, a file that never existed in git history — dangling citation (adjacent 2026-04-21-codex-hotfix-review.md is the likely intended target).
- ARCHITECTURE.md:116 (also :419) states extract.py is 1184 LOC; actual is 1194 — numeric drift in the A3 R9 known-deferred codemap.
- ARCHITECTURE.md:179 states ops/database.py is 542 LOC; actual is 562 (~3.5% drift) — same known-deferred codemap category (line 417's 705 LOC is the intentional pre-split historical figure).
- ARCHITECTURE.md:86 (also :418) says actions/ contains 12 modules; there are 11 Python modules (the 12th file is README.md, not a module) — off-by-one count.

## Next Actions (proposals for operator)

- ARCHITECTURE.md A3 R9 codemap rewrite: remove the task_manager.py codemap row + its two dependency/call-chain references (:89/:212/:228) and drop the `corp task` -> cli/task.py CLI row (:341) — both describe subsystems retired in Arc-B.
- ARCHITECTURE.md A3 R9 codemap rewrite: refresh the drifted numerics — extract.py 1184->1194 (:116/:419), ops/database.py 542->562 (:179), actions/ '12 modules'->11 (:86/:418) — or drop hard LOC/count figures to stop future drift.
- ARCHITECTURE.md:454: repoint the dangling audit citation to the existing 2026-04-21-codex-hotfix-review.md or remove it.
- JOURNAL.md: prepend an ADR-49-shape entry covering the 2026-07-29 W1-visibility + e1 re-date merge (freshest work, currently untracked).
- JOURNAL.md: prepend a short entry recording the ARC-4 leg-1 ruff/pytest floor-equalization merge (pyproject.toml).
- JOURNAL.md: in a future entry, note the corrected #38 E5 count (15 commits: 6 build + 4 terra-fix + 5 terra-anchor) — the source entry at :33 is append-only and must not be edited.

## Killed Findings

- Module-connection-map JOURNAL entry (Result: 'not merged'; Next: 'review/merge the docs branch --no-ff') is contradicted by git, which shows merge 1dfee3e already in main — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: All E5 #38 commit SHAs present in git log — terra pass fixes (a406b4c, 2c1ab27, 363bdd4, b28db4d), build steps (eaafda7, 989811e, d3e8094, cf36bac, 380ebfd), merge 60b7367
- V1: Night-consolidation commits (4749dc9, 4bbbf9a, 5816b03) present in git log
- V1: Module-connection-map audit commits (95e1f0c, b066c4a) present in git log
- V1: S13 merges present in git log — G4 relocate 236de12, G1 kill-html 74ef46c, G2 kill-digests af02a0c (anchor 0c8a32d), signed manifest 59f29d8
- V1: S1 ratification merges present — 10d8620 SIM, f0a0dd8 ADR-37, cf08af4 ADR-38
- V1: E5 #38 source files exist on disk — ops/source_registry.py, source_value.py, source_observation_repo.py, database.py
- V1: E5 #38 test files exist — tests/test_ops/test_source_registry.py, test_source_value.py, test_source_observation_repo.py
- V1: N2 worktree-compat fix verified in tests/integration/test_cross_package.py (pyproject.toml identity check)
- V1: G1 .html kill confirmed — zero .html files remain in docs/audits/
- V1: BACKLOG #69 present; docs/audits/2026-07-19-night-consolidation-decision-plan.md exists; .vscode/extensions.json + settings.json exist (ec276e5)
- V1: Nightly conformance digest commits (abed866, 3da2d8c, fa4583e, 870c593, b76d1d2, 2bb37b0, c954876) are automated bot commits — no operator JOURNAL entry expected
- V1: Module-connection-map branch base 'main@2c48fd5' consistent — ARC-4 merge (23:48) predates the anchor 4e2610a (00:30+1 day)
- V2: config/paths.toml, config/naming_config.yaml, config/agents.yaml, .methodology.yaml, .pre-commit-config.yaml all exist
- V2: src/corp/ namespace exists with all declared sub-packages; template_manager.py present
- V2: tests/safety/test_vault_writer_invariant.py exists (§5 rule 4)
- V2: 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts]
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 exist (§5 rule 10)
- V2: .claude/commands/override.md exists matching §7
- V2: All 9 §9 pre-commit hooks present in .pre-commit-config.yaml (ruff, tach-check, normalize-headers, floor-hash-verify, canonical_freshness, validate-audit-casing, validate-backlog, backlog-id-on-close, block-ff-push)
- V2: ADR-14, ADR-23, ADR-27 exist under docs/decisions/ (§11); ADR-16/22/26/32 exist (ARCHITECTURE Governing ADRs)
- V2: .claude/settings.json SessionStart and Stop hooks match §9
- V2: docs/audits/2026-04-21-codex-hotfix-review.md exists
- V2: extractor/ module map verified — providers/base.py, anthropic_provider.py, gemini_provider.py, frames/sampler.py, slides/renderer.py, pdf_converter.py, scripts/run.py
- V2: cleanup/ modules (scanner, classifier, proposer, executor, disk) exist; safety/onedrive.py exists
- V2: cli/ directory has 18 files matching ARCHITECTURE.md §cli/
- V3: exact-LOC matches — ingest/router.py = 893, ingest/inbox.py = 951
- V3: exact-count matches — naming_config type_codes = 22, client_aliases = 32, agents.yaml agents = 6, pyproject scripts = 5, cli/ files = 18
- V3: OpsDB delegates to exactly 5 repo classes in ops/database.py (Asset, Package, Event, Routing, Suggestion)
- Unverifiable-in-clone (not defects): ~/.claude user-level commands/skills/settings SessionStart; index.db notes count 488 (db not committed)

