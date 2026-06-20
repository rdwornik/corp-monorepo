# corp-monorepo — Nightly Conformance Digest (2026-06-20)

- **Date:** 2026-06-20
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=5 survived=5 killed=0 -->

## Summary

Overall documentation health is good with no high-severity conformance breaks: all 5 raw findings survived adversarial review (0 killed, a 0% skeptic kill-rate), indicating the verifiers produced clean, well-evidenced signals rather than noise. The single material issue is one medium-severity inaccuracy in ARCHITECTURE.md:577, which inverts what dev-check.ps1 actually runs and could mislead an operator into believing tach layer enforcement runs in the pre-PR gate when it does not. The remaining 4 findings are low severity: one cosmetic CLAUDE.md ruff-format pre-commit description drift (no behavioral risk), and three JOURNAL.md s6 change-record gaps (two un-journaled 2026-06-06 doc/script-only branches plus one 2026-06-04 entry mis-ordered at file bottom). A broad checked-clean sweep (paths, CLI declarations, hooks/CI, ADR files, numeric inventory of LOC and config counts, and 10 JOURNAL-vs-git entries) all conform, so the absence of findings there is informative: structural and numeric conformance is intact and the defects are confined to doc-prose drift and journal hygiene.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- ARCHITECTURE.md:577 inverts dev-check.ps1: claims it runs pytest + pre-commit run --all-files + tach check, but it actually runs ruff format + ruff check --fix + run-all-tests.ps1 + integration pytest (no pre-commit/tach), misleadingly implying tach enforcement in the pre-PR gate.

### Low

- CLAUDE.md:48 and :114 describe the ruff pre-commit hook as covering formatting, but ruff-format is explicitly omitted from .pre-commit-config.yaml (formatting runs only via dev-check.ps1).
- JOURNAL.md: chore/gh-auth-check branch (gh auth gate in surface-conformance.ps1 + gotchas.md, merge 0ef1fcd/116feea, 2026-06-06) is unrecorded in any Changes section (s6 gap).
- JOURNAL.md: docs/gotchas-2026-06-06 branch (two harness gotchas in gotchas.md, merge fc31ab9/d0989ee, 2026-06-06) is unrecorded in any Changes section (s6 gap).
- JOURNAL.md: the 2026-06-04 'graphify pilot REJECTED' entry (df22f8f) was bottom-appended below the 2026-05-18 entry, breaking newest-first order and the s6 'last 5 entries' read.

## Next Actions (proposals for operator)

- Reword ARCHITECTURE.md:577 to state dev-check.ps1 runs ruff format + ruff check --fix + run-all-tests.ps1 + integration pytest (NOT pre-commit/tach, which are the separate pre-commit gate).
- Change CLAUDE.md s4/s9 'ruff (formatting/linting)' to 'ruff (linting only; ruff-format omitted from pre-commit — runs via dev-check.ps1)'.
- Append a catch-up JOURNAL entry covering 116feea (surface-conformance.ps1 gh auth gate + gotchas.md) per CLAUDE.md s6.
- Append a catch-up JOURNAL entry covering d0989ee (gotchas.md 'Shell & Claude Code harness' section) per CLAUDE.md s6.
- Move the 2026-06-04 graphify entry into the top newest-first section (between the 2026-06-04 count-refresh and 2026-06-03 entries), leaving a redaction-safe note rather than silently editing history.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16 entry — scripts/current_state_audit.py and scripts/_audit_core.py exist on disk (git show 1913d30 + ls confirm).
- V1: 2026-06-16 entry — config/audit.yaml, tests/safety/test_audit_readonly_invariant.py, tests/safety/test_audit_core.py exist.
- V1: 2026-06-16 entry — docs/audits/2026-06-16-current-state-architecture-audit.md and .json exist.
- V1: 2026-06-16 entry — merged as audit/current-state-architecture branch via 8 commits through 1913d30 (git log confirms).
- V1: 2026-06-06 triage entry — three cited commits (13fea1e, a7a161e, 4b46709) exist and match described changes.
- V1: 2026-06-06 nightly conformance entry — conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1 all exist.
- V1: 2026-06-06 nightly conformance entry — tests/test_nightly_triage_parser.py and tests/fixtures/nightly-triage/ created (merge 34a2a9a).
- V1: 2026-06-06 remote bookkeeping entry — BACKLOG.md #13 sanitize-fixtures-archives item present (line 62).
- V1: 2026-06-06 CLAUDE.md audit entry — load_status() in src/corp/extractor/manifest.py has 3-attempt JSONDecodeError retry (lines 81-89).
- V1: 2026-06-06 CLAUDE.md audit entry — manifest.py retry wrapper matches 'P6(a)' claim (for attempt in range(3) with JSONDecodeError catch).
- V1: 2026-06-04 ARCHITECTURE.md count refresh entry — commit 96db96b exists; ARCHITECTURE.md and JOURNAL.md changed.
- V1: 2026-06-04 conformance baseline entry — docs/audits/2026-06-04-conformance-baseline-digest.md exists (commit ae9210f).
- V1: 2026-06-03 ruff drift BACKLOG entry — commit 48a565e exists; BACKLOG.md #12 ruff drift item present.
- V1: 2026-06-03 stale branches entry — commit e7eb86a exists; BACKLOG.md #10 path-traversal and #11 dead-code entries present (lines 60, 63).
- V1: 2026-06-03 ADR-71 pilot entry — .pre-commit-config.yaml TOC hook stanza (d764c79); ARCHITECTURE.md TOC:START/TOC:END markers present (lines 12, 47).
- V1: 2026-06-17 to 2026-06-19 commits are automated nightly digests only — correctly omitted from JOURNAL.
- V1: History boundary — oldest git commit is 2026-05-18; all 10 JOURNAL entries fall on/after this date, none out-of-scope.
- V2: PATHS — config/paths.toml exists (CLAUDE.md:49, ARCHITECTURE.md:387).
- V2: PATHS — src/corp/ unified namespace exists with all 12 subdirectories (schema, extractor, extraction, ingest, ops, retrieve, cleanup, overnight, project, opportunity, rfp, cli).
- V2: PATHS — tests/safety/test_vault_writer_invariant.py exists (CLAUDE.md:58).
- V2: PATHS — .pre-commit-config.yaml exists (CLAUDE.md:113).
- V2: PATHS — scripts/run-all-tests.ps1 exists (CLAUDE.md:47, ARCHITECTURE.md:579).
- V2: PATHS — scripts/dev-check.ps1 exists (CLAUDE.md:62, ARCHITECTURE.md:577).
- V2: PATHS — tach.toml exists (ARCHITECTURE.md:293).
- V2: PATHS — docs/decisions/README.md exists (CLAUDE.md:130).
- V2: PATHS — config/naming_config.yaml exists (ARCHITECTURE.md:391).
- V2: PATHS — config/agents.yaml exists (ARCHITECTURE.md:388).
- V2: PATHS — config/workflows.yaml exists (ARCHITECTURE.md:389).
- V2: PATHS — config/content_registry.yaml exists (ARCHITECTURE.md:390).
- V2: PATHS — config/project/default.yaml exists (ARCHITECTURE.md:393).
- V2: PATHS — config/opportunity/default.yaml exists (ARCHITECTURE.md:394).
- V2: PATHS — config/rfp/anonymization.yaml exists (ARCHITECTURE.md:395).
- V2: PATHS — config/rfp/product_profiles/ exists (ARCHITECTURE.md:396).
- V2: PATHS — config/extractor/*.yaml directory exists with yaml files (ARCHITECTURE.md:392).
- V2: PATHS — src/corp/vault_io.py exists (ARCHITECTURE.md:152).
- V2: PATHS — src/corp/extractor/scripts/run.py exists, CKE CLI entry point (ARCHITECTURE.md:222).
- V2: PATHS — src/corp/actions/_helpers.py exists (ARCHITECTURE.md:544).
- V2: PATHS — src/corp/cleanup/disk.py exists (ARCHITECTURE.md:542).
- V2: PATHS — src/corp/cleanup/executor.py exists (ARCHITECTURE.md:543).
- V2: PATHS — .claude/skills/gotchas/ exists (CLAUDE.md:108-109).
- V2: COMMANDS — 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com (CLAUDE.md:40).
- V2: COMMANDS — repo-level .claude/commands/ absent, consistent with CLAUDE.md s7 'none currently'.
- V2: COMMANDS — scripts/run-all-tests.ps1 runs pytest tests/ -x --tb=short (ARCHITECTURE.md:579).
- V2: HOOKS/CI — .pre-commit-config.yaml has ruff hook (id: ruff) for linting (CLAUDE.md:114, ARCHITECTURE.md:580).
- V2: HOOKS/CI — .pre-commit-config.yaml has tach-check hook (CLAUDE.md:115, ARCHITECTURE.md:293).
- V2: HOOKS/CI — .github/workflows/tach.yml exists (ARCHITECTURE.md:578).
- V2: HOOKS/CI — .github/workflows/nightly-conformance-triage.yml exists.
- V2: NAMES — ADR-14 (naming-convention-v2) exists (CLAUDE.md:133).
- V2: NAMES — ADR-23 (monorepo-internal-architecture) exists (CLAUDE.md:134).
- V2: NAMES — ADR-27 (safety-invariants) exists (CLAUDE.md:135).
- V2: NAMES — ADR-16, ADR-22, ADR-26, ADR-32 all exist under docs/decisions/ (ARCHITECTURE.md:587).
- V2: NAMES — 4-layer dependency model interface > orchestration > core > foundation declared in tach.toml (CLAUDE.md:39, ARCHITECTURE.md:271).
- V3: extract.py 1184 LOC — MATCH (ARCHITECTURE.md:190).
- V3: ingest/router.py 893 LOC — MATCH (ARCHITECTURE.md:239).
- V3: ingest/inbox.py 951 LOC — MATCH (ARCHITECTURE.md:240).
- V3: ops/database.py 542 LOC — MATCH (ARCHITECTURE.md:253).
- V3: actions/ 12 modules — MATCH (ARCHITECTURE.md:160).
- V3: cli/ 18 files — MATCH (ARCHITECTURE.md:267).
- V3: agents.yaml 6 agents — MATCH (ARCHITECTURE.md:388).
- V3: naming_config.yaml 22 type codes — MATCH (ARCHITECTURE.md:244,391).
- V3: naming_config.yaml 32 client aliases — MATCH (ARCHITECTURE.md:244,391).
- V3: 5 CLIs in pyproject.toml — MATCH: corp, corp-meta, cke, cpe, com (ARCHITECTURE.md:56).
- V3: OpsDB delegates to 5 repos — MATCH: Asset/Package/Event/Routing/Suggestion repositories (ARCHITECTURE.md:486).
- V3: unverifiable-in-clone — notes count (index.db absent from clone); ARCHITECTURE.md:367 claims 488 notes live 2026-06-04.

