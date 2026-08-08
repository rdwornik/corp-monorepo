# corp-monorepo — Nightly Conformance Digest (2026-08-08)

- **Date:** 2026-08-08
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** native

<!-- counts: raw=10 survived=9 killed=1 -->

## Summary

Documentation health for corp-monorepo is broadly sound structurally but shows a cluster of factual drift concentrated in ARCHITECTURE.md, plus minor JOURNAL staleness. The strongest signals are two dangling phantom-module references (task_manager.py across three ARCHITECTURE.md sites, and a corp task CLI row pointing at a nonexistent cli/task.py) that tie together into one coherent missing-module story. The remaining survivors are deterministic numeric drift (two LOC annotations off by +10/+20, two directory counts off by one) and JOURNAL coverage gaps (an untracked ARC-4 leg-1 merge and a ~10-day staleness window through 2026-07-29). All V2/V3 structural and inventory verifiers that could be checked in-clone passed — config files, hooks, CLIs, ADRs, tach layers, and provider modules all confirmed present. The adversarial skeptic killed 1 of 10 raw findings (10% kill-rate): a JOURNAL 'commit-and-STOP, not merged' entry that only looked contradictory but is the documented operator-gated-merge workflow firing as designed, and which append-only ADR-49 forbids retro-editing. Net: 9 survivors, none high-severity, most low-urgency drift on a single living doc.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- ARCHITECTURE.md:89,212,228 — task_manager.py is cited in the Module Map, orchestration layer assignments, and runtime call chain, but no such module exists in src/corp/, the codebase, or tach.toml.
- ARCHITECTURE.md:341 — CLI Reference lists 'corp task add/list/done -> cli/task.py' but src/corp/cli/task.py does not exist (17 cli files, none named task.py).

### Low

- ARCHITECTURE.md:454 — dangling reference to docs/audits/2026-04-21-p1-verification.md; only 2026-04-21-codex-hotfix-review.md exists for that date.
- ARCHITECTURE.md:116 — extract.py annotated (1184 LOC); actual is 1194 (+10 drift).
- ARCHITECTURE.md:179 — database.py annotated (542 LOC); actual is 562 (+20 drift).
- ARCHITECTURE.md:86 — actions/ stated as 12 modules; actual is 11 .py files.
- ARCHITECTURE.md:193 — cli/ stated as 18 files; actual is 17 .py files.
- JOURNAL.md — ARC-4 leg-1 ruff/pytest floor equalization merge (2c48fd5, 2026-07-18) has no JOURNAL entry.
- JOURNAL.md:18 — newest entry dated 2026-07-19; main carries merges through 2026-07-29 (vscode W1 visibility, 65a8a35) with no covering entry.

## Next Actions (proposals for operator)

- ARCHITECTURE.md: remove or correct the three phantom task_manager.py references (Module Map line 89, layer assignments line 212, call chain line 228) and the corp task / cli/task.py CLI Reference row (line 341) — likely a single coordinated edit since the phantom cli/task.py also drives the cli/ count being off.
- ARCHITECTURE.md: fix the dangling docs/audits/2026-04-21-p1-verification.md reference (line 454).
- ARCHITECTURE.md: refresh the deterministic inventory annotations — extract.py 1184->1194 (line 116), database.py 542->562 (line 179), actions/ 12->11 (line 86), cli/ 18->17 (line 193).
- JOURNAL.md: add an entry covering the ARC-4 leg-1 ruff/pytest floor equalization merge (2c48fd5, 2026-07-18), or confirm it was journaled at the hub if fleet-parity-driven.
- JOURNAL.md: prepend an entry covering post-07-19 work through 2026-07-29 (vscode W1 visibility / .methodology.yaml re-date, 65a8a35) to close the staleness window.

## Killed Findings

- JOURNAL 2026-07-19 module-connection-map entry says the branch was 'commit-and-STOP, not merged (operator gates the merge)' but git shows it merged (1dfee3e) the same day; status never updated. — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: All 10 surveyed JOURNAL entries' cited commits/merges exist in git (95e1f0c, b066c4a, 4e2610a, 4749dc9, 4bbbf9a, 5816b03, 334da4e, 60b7367, b28db4d, 363bdd4, 2c1ab27, a406b4c, and Entry 8/9/10 step+merge hashes).
- V1: JOURNAL ordering is correctly newest-first across all surveyed 2026-07-18..2026-07-19 entries.
- V1: Nightly conformance digests (abed866..cbc8c58, 2026-07-21..2026-08-01) are automated commits — no JOURNAL coverage expected.
- V2: config/paths.toml, config/naming_config.yaml, and .methodology.yaml (repo root) all exist as documented.
- V2: src/corp/ unified namespace, tach.toml, and corp.project_resolver core layer assignment all match ARCHITECTURE.md.
- V2: tests/safety/test_vault_writer_invariant.py exists (CLAUDE.md §5 rule 4).
- V2: .pre-commit-config.yaml exists with all 9 listed hooks (ruff, tach-check, normalize-headers, floor-hash-verify, canonical_freshness, validate-audit-casing, validate-backlog, backlog-id-on-close, block-ff-push).
- V2: 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts].
- V2: scripts/run-all-tests.ps1, scripts/dev-check.ps1, scripts/surface-conformance.ps1, scripts/session_end_backpressure.py all exist.
- V2: .claude/commands/override.md and .claude/skills/gotchas/ exist.
- V2: ADR-14, ADR-23, ADR-27, and docs/decisions/README.md all exist (CLAUDE.md §11).
- V2: .claude/settings.json project-level hooks match CLAUDE.md §9 (surface-conformance, check_floor_hash --require-present, pre_commit install, session_end_backpressure Stop).
- V2: src/corp/safety/onedrive.py and docs/audits/2026-04-21-codex-hotfix-review.md exist.
- V2: extractor/providers/{base,anthropic_provider}.py, extractor/frames/sampler.py, extractor/slides/renderer.py exist.
- V2: No local docs/handoffs/ directory, matching the ADR-36 read-only contract.
- V2: unverifiable-in-clone (not counted as findings): logs/TOKEN-LOG.md (logs/ gitignored), ~/.claude/ user-level commands and skills.
- V3: router.py (893) and inbox.py (951) LOC annotations match actual.
- V3: naming_config.yaml 22 type_codes and 32 client_aliases match; agents.yaml 6 agents match.
- V3: OpsDB delegates to 5 repository classes (Asset, Package, Event, Routing, Suggestion) as documented.
- V3: unverifiable-in-clone (not counted): notes count (index.db gitignored).

