# corp-monorepo — Nightly Conformance Digest (2026-06-16)

- **Date:** 2026-06-16
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=2 survived=1 killed=1 -->

## Summary

Documentation conformance is strong: of 2 raw findings, only 1 survived adversarial skepticism (50% skeptic kill-rate). The single survivor is a low-severity dangling living-doc pointer in VISION.md, where the References section still cites README.md as a live capability index despite its deliberate deletion under ADR-38 A5 (commit 6a1ba20). The killed finding (unjournaled nightly digest commits) was a true-but-irrelevant false positive: those commits are machine-generated output of an already-journaled, self-merging nightly conformance routine documented in the 2026-06-06 entry. Across 80+ verifier checks spanning JOURNAL-vs-git reconciliation, living-doc structural claims, and deterministic numeric-inventory drift, no other drift was found, indicating the corp-monorepo living docs (CLAUDE.md, ARCHITECTURE.md, VISION.md, CONTRIBUTING.md, pyproject.toml, JOURNAL.md) are well-aligned with the codebase.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

_No med-severity findings._

### Low

- VISION.md:149 References section lists README.md as 'current capability and module index', but README.md was deliberately deleted per ADR-38 A5 (commit 6a1ba20) — a dangling living-doc pointer to a removed file.

## Next Actions (proposals for operator)

- Remove the README.md line from VISION.md:149 References (or repoint it to ARCHITECTURE.md/CLAUDE.md), since README was intentionally deleted per ADR-38 A5 — operator decision, no action taken.

## Killed Findings

- Nightly conformance digest commits 2026-06-07 through 2026-06-15 are merged work not mentioned in last 10 JOURNAL entries — _documented-decision_

## Checked-and-clean (so absence is informative)

- JOURNAL 2026-06-06 Triage ratification: SHAs 13fea1e, a7a161e, 4b46709 present with correct dates/descriptions
- JOURNAL 2026-06-06 Nightly conformance routine: all four envelope files exist; merge commit 34a2a9a confirmed
- JOURNAL 2026-06-06 Remote bookkeeping: commit d8d129e confirmed with BACKLOG #13 addition
- JOURNAL 2026-06-06 CLAUDE.md audit: commits aca2c95, 1a057f2, b98a115 all present and verified
- JOURNAL 2026-06-04 ARCHITECTURE count refresh: merge commit 7b7e708 confirmed
- JOURNAL 2026-06-04 Conformance baseline: merge commit 1aa97c4 confirmed; baseline digest file exists
- JOURNAL 2026-06-03 Ruff drift: merge commit 98dd12a confirmed
- JOURNAL 2026-06-03 Stale branches: merge commit 37abe8d confirmed
- JOURNAL 2026-06-03 Doctools hooks: merge commit 99c7925 confirmed; TOC hooks wired
- JOURNAL 2026-06-02 Ecosystem unification: merge commit f1cb75b confirmed
- Git history boundary: earliest commit 2026-05-18; all JOURNAL entries from 2026-06-02 within available history
- CLAUDE.md §2 repo identity: corp-monorepo name and status active confirmed
- CLAUDE.md §3: ARCHITECTURE.md exists and is authoritative
- CLAUDE.md §4 naming: ADR-14 exists at docs/decisions/ADR-14-naming-convention-v2.md
- CLAUDE.md §4 testing: ./scripts/run-all-tests.ps1 exists
- CLAUDE.md §4 linting: .pre-commit-config.yaml exists with ruff and tach hooks
- CLAUDE.md §4 config: config/paths.toml exists
- CLAUDE.md §5 rule 1: tests/safety/test_vault_writer_invariant.py exists
- CLAUDE.md §5 rule 2: CKE module at src/corp/extractor/ exists
- CLAUDE.md §5 rule 5: ./scripts/run-all-tests.ps1 and ./scripts/dev-check.ps1 both exist
- CLAUDE.md §7: repo-level ./.claude/commands/ correctly absent (documented 'none currently')
- CLAUDE.md §8: repo-level skill ./.claude/skills/gotchas/ exists with SKILL.md and gotchas.md
- CLAUDE.md §9: .pre-commit-config.yaml contains ruff and tach hooks as documented
- CLAUDE.md §11: corp ADR-14, ADR-23, ADR-27 all exist in docs/decisions/
- ARCHITECTURE.md Module Map: all named root-level modules exist (models.py, config.py, vault_io.py, etc.)
- ARCHITECTURE.md schema/: models.py, overlays.py, config.py, pipeline_config.py, folder_names.py exist in src/corp/schema/
- ARCHITECTURE.md packages: extractor/, extraction/, ingest/, ops/, retrieve/, cleanup/, overnight/, project/, opportunity/, rfp/ all exist
- ARCHITECTURE.md cli/: package exists with 18 files as documented
- ARCHITECTURE.md 4-layer model: interface > orchestration > core > foundation defined in tach.toml layers
- ARCHITECTURE.md layer assignments: cli=interface, ingest=orchestration, extractor/ops/retrieve/etc=core, schema/extraction=foundation verified in tach.toml
- ARCHITECTURE.md tach.toml: exists with forbid_circular_dependencies=true
- ARCHITECTURE.md Configuration: paths.toml, agents.yaml, workflows.yaml, content_registry.yaml, naming_config.yaml all exist
- ARCHITECTURE.md Configuration: config/extractor/*.yaml exist (anonymize, categories, filters, processing, settings)
- ARCHITECTURE.md Configuration: config/project/default.yaml, clients.yaml; config/opportunity/default.yaml; config/rfp/anonymization.yaml and product_profiles/ all exist
- ARCHITECTURE.md OneDrive safety guards: cleanup/disk.py, cleanup/executor.py, cleanup/errors.py, actions/_helpers.py exist with guard references
- ARCHITECTURE.md OneDrive safety guards: docs/audits/ exists with 2026-04-21 audit references
- ARCHITECTURE.md Diagrams: docs/diagrams/ contains system-context.svg, magistrala-pipeline.svg, container-module.svg/.mermaid, magistrala-pipeline.mermaid
- ARCHITECTURE.md ADRs: docs/decisions/README.md exists; ADR-26 (Tach) and ADR-27 (safety invariants) exist
- CONTRIBUTING.md: exists with branch naming, commit style, Tach rules; ./scripts/dev-check.ps1 and tach.toml referenced and exist
- VISION.md: exists with Vision, Scope, Values, Relationships, Lifecycle sections; tier classification retired 2026-05-23 per ADR-33/40
- pyproject.toml: all 5 CLIs declared in [project.scripts] — corp, corp-meta, cke, cpe, com with correct entry points
- JOURNAL.md: exists with correct ADR-49 entry shape (Did/Result/Changes/Abandoned/Next)
- BACKLOG.md: exists as documented reference in VISION.md References section
- Numeric inventory: extractor/extract.py 1184 LOC; ingest/router.py 893 LOC; ingest/inbox.py 951 LOC; ops/database.py 542 LOC — all match documented values
- Numeric inventory: naming_config.yaml has 22 type codes and 32 client aliases
- Numeric inventory: 5 CLIs in pyproject.toml; 6 agents in config/agents.yaml; 5 OpsDB repos; 12 action modules; 18 CLI files; 28 corp CLI commands in ARCHITECTURE table

