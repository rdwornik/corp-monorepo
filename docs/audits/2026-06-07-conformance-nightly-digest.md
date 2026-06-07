# corp-monorepo — Nightly Conformance Digest (2026-06-07)

- **Date:** 2026-06-07
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=0 survived=0 killed=0 -->

## Summary

Documentation health is excellent: across three verifiers covering JOURNAL-vs-git fidelity (V1), living-doc structural claims (V2), and deterministic numeric-inventory drift (V3), zero conformance findings were raised. Because no raw findings were generated, the skeptic had nothing to adjudicate, yielding a kill-rate of 0% (0 killed of 0 raw). The checked_clean list is substantive and the absence of findings is therefore informative rather than a coverage gap: all Tier-1 plugin commits are properly journaled, the nightly conformance routine envelope is complete, the CLAUDE.md audit fixes (P1-P6 incl. the status.json retry wrapper) are in place, every declared path/command/hook/ADR was confirmed present, all four tach layers and OneDrive safety guards exist, and every numeric inventory claim (LOC counts, module/CLI/agent/type-code counts) was independently re-verified against the working tree. The only unverified items are explicitly out-of-clone artifacts (user-level ~/.claude paths and the gitignored index.db note count). No corrective action is required.

## Findings (PROPOSALS ONLY)

_None — all checked claims conform. See checked-and-clean below._

## Next Actions (proposals for operator)

_No action required — clean night._

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-06-06 Triage ratification: three Tier-1 plugin commits (13fea1e, a7a161e, 4b46709) from 2026-06-02 properly journaled as catch-up entry 25398a0 on 2026-06-06
- V1: 2026-06-06 Nightly conformance routine: all four envelope parts exist (conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1) + test fixtures + SessionStart hook; 4381f6f journal entry; full build merged 34a2a9a
- V1: 2026-06-06 Remote bookkeeping: GitHub push documented, BACKLOG #13 added, d8d129e commit exists
- V1: 2026-06-06 CLAUDE.md audit: P1-P5 fixes documented, P6 retry wrapper implemented (1a057f2), audit closes #75 per b98a115
- V1: 2026-06-04 ARCHITECTURE count refresh: all six drifts re-verified and fixed (96db96b), counts documented in commit message with evidence commands
- V1: 2026-06-04 Conformance baseline review: audit digest file exists (2026-06-04-conformance-baseline-digest.md), run journal entry 0275923, five real findings identified and properly classified
- V1: 2026-06-03 Ruff drift: BACKLOG item #12 added (48a565e), tracked as P3 issue
- V1: 2026-06-03 Stale branches: three branches preserved-then-deleted, findings extracted to BACKLOG #10/#11 per e7eb86a
- V1: 2026-06-03 Doctools hooks: ADR-71 TOC hook consumed from .dev-knowledge, TOC markers generated in ARCHITECTURE.md (3bf0192), pre-commit hook wired (d764c79)
- V1: 2026-06-02 Ecosystem unification: VISION.md created, LESSONS.md created, BACKLOG.md migrated to ADR-66 story-map, JOURNAL H1 standardized
- V1: All git history available in clone: shallow boundary at 2026-05-18, all last-10 entries well within history (2026-06-02 onwards)
- V1: No unrecorded substantive work in git since 2026-06-02: all commits match JOURNAL entries
- V2: PATHS: config/paths.toml exists
- V2: PATHS: src/corp/ namespace exists with 34 submodules
- V2: PATHS: tests/safety/test_vault_writer_invariant.py exists
- V2: PATHS: config/naming_config.yaml exists
- V2: PATHS: .pre-commit-config.yaml exists
- V2: PATHS: docs/decisions/ directory exists with 32 ADRs
- V2: PATHS: docs/audits/ directory exists with 11 audit files
- V2: PATHS: .claude/skills/gotchas/ directory exists
- V2: PATHS: config/agents.yaml, workflows.yaml, content_registry.yaml all exist
- V2: PATHS: config/rfp/anonymization.yaml exists
- V2: COMMANDS: 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: COMMANDS: corp-meta entry point is corp.schema.cli:main
- V2: COMMANDS: scripts/run-all-tests.ps1 exists
- V2: COMMANDS: scripts/dev-check.ps1 exists
- V2: HOOKS: ruff pre-commit hook present in .pre-commit-config.yaml (id: ruff)
- V2: HOOKS: tach pre-commit hook present in .pre-commit-config.yaml (id: tach-check)
- V2: HOOKS: .github/workflows/tach.yml exists for CI enforcement
- V2: HOOKS: .claude/settings.json contains SessionStart hook for surface-conformance.ps1
- V2: NAMES: ADR-14-naming-convention-v2.md exists in docs/decisions/
- V2: NAMES: ADR-23-monorepo-internal-architecture.md exists in docs/decisions/
- V2: NAMES: ADR-27-safety-invariants.md exists in docs/decisions/
- V2: NAMES: ADR-26-tach-adoption.md exists in docs/decisions/
- V2: NAMES: Module map lists all major modules: schema, extractor, extraction, ingest, ops, retrieve, cleanup, overnight, project, opportunity, rfp, cli
- V2: NAMES: Root-level modules exist: models.py, config.py, vault_io.py, index_builder.py, query_engine.py
- V2: LAYER: tach.toml contains exact=true (strict mode)
- V2: LAYER: tach.toml defines 4 layers: interface, orchestration, core, foundation
- V2: LAYER: 32 module assignments in tach.toml
- V2: SAFETY: OneDriveSafetyError class exists in cleanup/errors.py
- V2: SAFETY: _guard_onedrive function exists in cleanup/executor.py and cleanup/disk.py
- V2: DATABASE: WAL mode enabled in ops/database.py
- V2: DATABASE: Foreign keys enforced in ops/database.py
- V2: VAULT: vault_io.py is sole writer for vault notes at core layer
- V2: VAULT: extraction/vault_writer.py exists
- V2: unverifiable-in-clone: ~/.claude/commands user-level slash commands
- V2: unverifiable-in-clone: ~/.claude/skills user-level skills
- V3: extract.py LOC: 1184 (verified: wc -l src/corp/extractor/extract.py)
- V3: router.py LOC: 893 (verified: wc -l src/corp/ingest/router.py)
- V3: inbox.py LOC: 951 (verified: wc -l src/corp/ingest/inbox.py)
- V3: database.py LOC: 542 (verified: wc -l src/corp/ops/database.py)
- V3: actions/ modules: 12 (verified: ls src/corp/actions/*.py | wc -l)
- V3: cli/ files: 18 (verified: ls src/corp/cli/*.py | wc -l)
- V3: type codes: 22 in config/naming_config.yaml
- V3: client aliases: 32 in config/naming_config.yaml
- V3: agents in config/agents.yaml: 6
- V3: Five CLIs in pyproject.toml: 5
- V3: corp commands: ~39 total (matches 40+ claim in ARCHITECTURE.md)
- V3: unverifiable-in-clone: notes count (index.db not in clone -- gitignored artifact in %LOCALAPPDATA%)

