# corp-monorepo — Nightly Conformance Digest (2026-06-19)

- **Date:** 2026-06-19
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=2 survived=1 killed=1 -->

## Summary

Overall documentation health is strong. Across three verifiers spanning JOURNAL-vs-git history, living-doc structural claims, and deterministic numeric-inventory drift, only 2 raw findings surfaced and 42 distinct items were verified clean (commit/file existence, LOC counts, inventory counts, CLI registration, layer model, and ADR presence all conform). The adversarial skeptic killed 1 of 2 findings (50% kill-rate), discarding a documentation-precision nitpick against an explicitly accepted ARCHITECTURE.md note on runtime lazy-import depth that lacked definitive proof of a conformance defect. The single survivor is a med-severity dangling living-doc reference: VISION.md:149 lists a root README.md as a canonical reference, but no such file exists at repo root (the only README is the ADR index at docs/decisions/README.md), and no ADR documents its retirement.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- VISION.md:149 lists root README.md as canonical reference for 'current capability and module index', but README.md is MISSING at repo root (only docs/decisions/README.md exists, a different artifact; no ADR retires it).

### Low

_No low-severity findings._

## Next Actions (proposals for operator)

- Resolve VISION.md:149 dangling README reference: either create a root README.md providing the 'current capability and module index' it promises, or strike the README.md line from the VISION.md References section. Operator decision only — no action taken.

## Killed Findings

- Runtime call chains can reach 9 levels deep via lazy imports (example: cli.misc → chat → workflow_engine → built_in_actions → task_manager → intent_router) — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16 audit/current-state-architecture merge: scripts/current_state_audit.py + _audit_core.py + config/audit.yaml + docs/audits files all present in commit 1913d30
- V1: 2026-06-16 audit: 8 revertable commits from 73631e3..eb7d825 verified in git log
- V1: 2026-06-06 triage ratification: commits 13fea1e, a7a161e, 4b46709 all exist in git log (within history boundary)
- V1: 2026-06-06 triage: chore/triage-2026-06-06 branch merged (d5999cb)
- V1: 2026-06-06 nightly conformance routine files all present (.claude/workflows/conformance-corp.js, scripts/render_conformance_digest.py, .github/workflows/nightly-conformance-triage.yml, tests/test_nightly_triage_parser.py, .claude/settings.json SessionStart hook)
- V1: 2026-06-06 nightly conformance: scripts/surface-conformance.ps1 added
- V1: 2026-06-06 remote bookkeeping: BACKLOG.md #13 sanitize-fixtures-archives item exists
- V1: 2026-06-06 CLAUDE.md audit: commit refreshes CLAUDE.md §6-§9, adds retry wrapper to manifest.py, adds test to test_manifest.py
- V1: 2026-06-04 ARCHITECTURE.md refresh: commit verifies counts (inbox 1161→951, database 705→542, type_codes 19→22, client_aliases 15→32, notes 1972→488, agents 5→6)
- V1: 2026-06-04 conformance baseline: docs/audits/2026-06-04-conformance-baseline-digest.md created
- V1: 2026-06-03 track ruff drift: BACKLOG.md item #12 added, grooming log shows 2026-06-03 entry
- V1: 2026-06-03 resolve branches: BACKLOG.md items #10 and #11 added, branch closure verified
- V1: 2026-06-03 consume hub doc-tooling: .pre-commit-config.yaml TOC hook stanza + ARCHITECTURE.md TOC markers verified in commits
- V1: All major developer work between 2026-06-03 and 2026-06-16 is covered by last 10 JOURNAL entries
- V1: Nightly conformance digests (automated, routine) correctly absent from JOURNAL — established pattern per 2026-06-06 session record
- V2: CLAUDE.md §4 + §9 — ruff + tach pre-commit hooks declared and verified in .pre-commit-config.yaml
- V2: CLAUDE.md §5.1 — tests/safety/test_vault_writer_invariant.py EXISTS
- V2: CLAUDE.md §5 — scripts/run-all-tests.ps1 and scripts/dev-check.ps1 EXIST
- V2: CLAUDE.md §7 — repo-level .claude/commands/ correctly DOES NOT EXIST (matches 'none currently')
- V2: CLAUDE.md §8 — .claude/skills/ EXISTS with gotchas skill directory
- V2: CLAUDE.md §11 — corp ADR-14, ADR-23, ADR-27 all EXIST in docs/decisions/
- V2: ARCHITECTURE.md — all 11 src/corp/ subdirectories EXIST (schema, extractor, extraction, ingest, ops, retrieve, cleanup, overnight, project, opportunity, rfp, cli)
- V2: ARCHITECTURE.md §Configuration — config/paths.toml, agents.yaml, workflows.yaml, content_registry.yaml, naming_config.yaml, rfp/anonymization.yaml all EXIST
- V2: ARCHITECTURE.md §Diagrams — docs/diagrams/system-context.svg, container-module.svg, magistrala-pipeline.svg all EXIST
- V2: ARCHITECTURE.md §Layer Assignments — tach.toml verified with 4-layer model (interface > orchestration > core > foundation)
- V2: 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: ARCHITECTURE.md Codemap — all 10 clickable src/corp/ module links verified present
- V2: CONTRIBUTING.md and VISION.md structural claims internally consistent with repo (except README.md reference)
- V2: .github/workflows/nightly-conformance-triage.yml and tach.yml both EXIST
- V3: extract.py: 1184 LOC (wc -l src/corp/extractor/extract.py = 1184) — matches ARCHITECTURE.md
- V3: ingest/router.py: 893 LOC (wc -l src/corp/ingest/router.py = 893) — matches ARCHITECTURE.md
- V3: ingest/inbox.py: 951 LOC (wc -l src/corp/ingest/inbox.py = 951) — matches ARCHITECTURE.md
- V3: ops/database.py: 542 LOC (wc -l src/corp/ops/database.py = 542) — matches ARCHITECTURE.md
- V3: actions/: 12 files (ls src/corp/actions/*.py | wc -l = 12) — matches ARCHITECTURE.md
- V3: cli/: 18 files (ls src/corp/cli/*.py | wc -l = 18) — matches ARCHITECTURE.md
- V3: naming_config.yaml: type_codes=22, client_aliases=32 — matches ARCHITECTURE.md and CLAUDE.md
- V3: agents.yaml: 6 agents (com, cpe, cke, schema, ai-council, rfp) — matches ARCHITECTURE.md
- V3: pyproject.toml: 5 CLIs — matches ARCHITECTURE.md and CLAUDE.md
- V3: ops/database.py delegates to 5 repository classes (AssetRepo, PackageRepo, EventRepo, RoutingRepo, SuggestionRepo) — matches ARCHITECTURE.md
- V3: corp CLI '40+ commands' — live count via @command decorators shows 47 commands (satisfies 40+)
- V3: unverifiable-in-clone: notes count (488 notes, live 2026-06-04) — index.db is gitignored, not in clone

