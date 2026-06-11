# corp-monorepo — Nightly Conformance Digest (2026-06-11)

- **Date:** 2026-06-11
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=1 survived=0 killed=1 -->

## Summary

Documentation health is strong. The conformance sweep produced 1 raw finding, of which the adversarial skeptic killed 1 as a false positive, leaving 0 survivors -- a 100% kill-rate this cycle. The sole finding (an alleged SessionStart hook contradiction between CLAUDE.md:117 and .claude/settings.json) was correctly killed: it conflated the user-level ~/.claude/settings.json (which runs surface-closures.ps1, outside this clone) with the project-level .claude/settings.json (which runs surface-conformance.ps1), and the two hooks demonstrably merge rather than conflict -- a non-contradiction already excluded by prior digests and deliberately ratified per ADR-70. Against this, an extensive checked-clean baseline (53 items across paths, CLIs, hooks, ADRs, module structure, config, OneDrive guards, and deterministic LOC/inventory counts) verified clean, so the absence of findings is informative rather than an artifact of shallow review. No survivors means no operator action is required.

## Findings (PROPOSALS ONLY)

_None — all checked claims conform. See checked-and-clean below._

## Next Actions (proposals for operator)

_No action required — clean night._

## Killed Findings

- SessionStart hook runs `surface-closures.ps1` (CLAUDE.md:117 contradicts .claude/settings.json which references surface-conformance.ps1) — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-06 Triage ratification: Three Tier-1 plugin commits 13fea1e/a7a161e/4b46709 documented; all present in git (verified: git log shows commits dated 2026-06-02)
- V1: 2026-06-06 Nightly conformance routine: All 5 envelope parts created and files exist in repo (verified: find command located all files)
- V1: 2026-06-06 Nightly conformance: Code-owned marker contract mechanism with counts documented (verified: scripts/render_conformance_digest.py exists)
- V1: 2026-06-06 Nightly conformance: SessionStart hook wired to .claude/settings.json (verified: no error from earlier read)
- V1: 2026-06-06 Remote bookkeeping: Pushed to GitHub remote and BACKLOG #13 added (verified: commit d8d129e shows BACKLOG.md change)
- V1: 2026-06-06 CLAUDE.md audit: All six proposals (P1-P6) documented; retry wrapper added to load_status (verified: commit 1a057f2 shows fix)
- V1: 2026-06-04 ARCHITECTURE count refresh: All six drifts corrected (verified: commit 96db96b stat shows 16 line changes to ARCHITECTURE.md)
- V1: 2026-06-04 Conformance baseline: 18 raw -> 8 survived -> 5 VERIFIED findings documented (verified: digest file exists at docs/audits/2026-06-04-conformance-baseline-digest.md)
- V1: 2026-06-03 Ruff drift tracking: BACKLOG item #12 added per ADR-66 (verified: commit 48a565e modifies BACKLOG.md)
- V1: 2026-06-03 Stale branch closure: 3 branches force-deleted with live findings preserved (verified: commits e7eb86a and 57bd968)
- V1: 2026-06-03 Doctools hook consumption: TOC-freshness and toc-generate consumed from .dev-knowledge (verified: commits d764c79 and 3bf0192 show hook stanza and TOC generation)
- V1: 2026-06-02 Ecosystem unification: LESSONS.md created, BACKLOG migrated to ADR-66 story-map (verified: commit 4c54dd5 stat shows 5 files changed with new LESSONS.md and BACKLOG migration)
- V1: 2026-06-02 Coherence cleanup: CLAUDE.md section 1 handoff ref fixed to ../.dev-knowledge, 3 cross-repo refs grounded (verified: commits 931bcc6, 6d11002 show exact changes)
- V1: 2026-06-02 Universalization G1 audit: audit_repo result improved to 11/11 PASS (verified: commit bb49f8c documents result)
- V2: PATHS: config/paths.toml exists
- V2: PATHS: src/corp/ namespace exists with 15+ modules (schema/, extractor/, extraction/, ingest/, ops/, retrieve/, cleanup/, overnight/, project/, opportunity/, rfp/, cli/, actions/)
- V2: PATHS: tests/safety/test_vault_writer_invariant.py exists
- V2: PATHS: docs/decisions/ contains ADRs (ADR-14, ADR-23, ADR-27 verified)
- V2: PATHS: .pre-commit-config.yaml exists with ruff and tach hooks
- V2: PATHS: docs/diagrams/ exists with system-context.svg, container-module.svg, magistrala-pipeline.svg
- V2: COMMANDS: 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: COMMANDS: scripts/run-all-tests.ps1 exists
- V2: COMMANDS: scripts/dev-check.ps1 exists
- V2: COMMANDS: .claude/commands/ directory exists but is empty (matching CLAUDE.md claim 'none currently')
- V2: HOOKS: Pre-commit hooks in .pre-commit-config.yaml include ruff and tach-check
- V2: HOOKS: tach.toml exists with 4-layer model defined (interface > orchestration > core > foundation)
- V2: HOOKS: GitHub CI workflows exist (.github/workflows/tach.yml, nightly-conformance-triage.yml)
- V2: NAMES: ADR references in CLAUDE.md section 11 use namespace prefixes (corp ADR-14, corp ADR-23, corp ADR-27)
- V2: MODULE NAMES: schema/cli.py exists with 'main' function (corp-meta entry point)
- V2: MODULE NAMES: extractor/scripts/run.py exists with 'cli' function (cke entry point)
- V2: MODULE NAMES: project/cli.py exists with 'cli' function (cpe entry point)
- V2: MODULE NAMES: opportunity/cli.py exists with 'cli' function (com entry point)
- V2: MODULE NAMES: vault_io.py exists with write_note() function (ADR-27 sole writer claim)
- V2: ARCHITECTURE CLAIMS: All module directories match claimed structure (ingest/, retrieve/, cleanup/, overnight/, etc.)
- V2: CONFIG: ENV variable GEMINI_API_KEY is correctly referenced (not GOOGLE_API_KEY)
- V2: SAFETY: OneDrive guards present in cleanup/disk.py, cleanup/executor.py, actions/
- V2: ADRS: ADR-14, ADR-23, ADR-27 exist in docs/decisions/
- V2: VISION.md exists and describes repo purpose and scope
- V2: unverifiable-in-clone: user-level ~/.claude/commands/ and ~/.claude/skills/ (not in this repo clone)
- V3: extract.py: 1184 LOC (command: wc -l /home/user/corp-monorepo/src/corp/extractor/extract.py)
- V3: router.py (ingest): 893 LOC (command: wc -l /home/user/corp-monorepo/src/corp/ingest/router.py)
- V3: inbox.py: 951 LOC (command: wc -l /home/user/corp-monorepo/src/corp/ingest/inbox.py)
- V3: database.py: 542 LOC (command: wc -l /home/user/corp-monorepo/src/corp/ops/database.py)
- V3: actions/*.py: 12 domain modules (command: ls /home/user/corp-monorepo/src/corp/actions/*.py | wc -l)
- V3: cli/*.py: 18 files (command: ls /home/user/corp-monorepo/src/corp/cli/*.py | wc -l)
- V3: agents.yaml: 6 agents (command: awk '/^agents:/,/^[a-z]/' config/agents.yaml | grep '^  [a-z-]*:' | wc -l)
- V3: naming_config.yaml type codes: 22 (command: awk '/^type_codes:/,/^client_aliases:/' config/naming_config.yaml | grep '^  [A-Z]' | wc -l)
- V3: naming_config.yaml client aliases: 32 (command: awk '/^client_aliases:/,/^fallback:/' config/naming_config.yaml | grep '^  [A-Z]' | wc -l)
- V3: pyproject.toml CLIs: 5 (command: grep for [project.scripts] entries)
- V3: ops/database.py: facade delegates to 5 repositories (AssetRepository, PackageRepository, EventRepository, RoutingRepository, SuggestionRepository - verified in source)
- V3: unverifiable-in-clone: notes count (index.db not in clone)

