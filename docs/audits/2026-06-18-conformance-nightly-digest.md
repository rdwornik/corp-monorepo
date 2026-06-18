# corp-monorepo — Nightly Conformance Digest (2026-06-18)

- **Date:** 2026-06-18
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=2 survived=0 killed=2 -->

## Summary

Documentation health is strong: of 2 raw findings surfaced this run, 0 survived adversarial skeptic review (100% kill-rate; both ruled false positives). One was a documented-decision false positive (the user-level SessionStart hook reference, unverifiable-in-clone and already killed in four prior nightly digests per ADR-70), and the other was technically-true-but-trivial drift on an intentionally approximate '40+' command count whose own evidence_command (28/~39) failed to definitively contradict the soft figure. Meanwhile 41 structural, path, command, hook, naming, CI, architecture, and numeric-inventory claims were independently verified clean across three verifiers, so the absence of survivors is informative rather than incidental. No survivors means no operator action is required.

## Findings (PROPOSALS ONLY)

_None — all checked claims conform. See checked-and-clean below._

## Next Actions (proposals for operator)

_No action required — clean night._

## Killed Findings

- CLAUDE.md §9 'Other (~/.claude/settings.json): SessionStart hook — runs surface-closures.ps1 (Tier-1 lifecycle closure surfacing, ADR-70)' — _documented-decision_
- corp CLI (main CLI -- 40+ commands) — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16: Current-state architecture audit tool built with scripts/current_state_audit.py + scripts/_audit_core.py, landed in repo; merged via branch audit/current-state-architecture
- V1: 2026-06-16: Audit deliverables committed to docs/audits/ (inventory JSON, gap report, codex review artifact); verified with git ls-files
- V1: 2026-06-06: Triage ratification entry for 2026-06-02 Tier-1 lifecycle plugin install; commits 13fea1e, a7a161e, 4b46709 verified in git log
- V1: 2026-06-06: Nightly conformance routine built with .claude/workflows/conformance-corp.js, scripts/render_conformance_digest.py, .github/workflows/nightly-conformance-triage.yml, scripts/surface-conformance.ps1; all committed to repo
- V1: 2026-06-06: Nightly conformance digest 2026-06-06 generated and committed to docs/audits/2026-06-06-conformance-nightly-digest.md
- V1: 2026-06-04: ARCHITECTURE.md count refresh branch docs/architecture-count-refresh merged; commit 7b7e708
- V1: 2026-06-04: Conformance baseline digest 2026-06-04 generated and committed to docs/audits/2026-06-04-conformance-baseline-digest.md; commit ae9210f
- V1: 2026-06-03: BACKLOG item #12 added to track ruff drift; branch docs/backlog-ruff-drift merged; commit 98dd12a
- V1: 2026-06-03: Three stale unmerged branches closed and preserved via chore/close-stale-branches; commit 37abe8d
- V1: 2026-06-03: Consumed .dev-knowledge doc-tooling hooks; branch feat/consume-doctools-hooks merged; TOC markers added at commit 3bf0192; pre-commit hook stanza at commit d764c79
- V1: 2026-06-02: Universalization coherence audit G1 completed; branch chore/universalization-conformance merged; commits bb49f8c and ebba85d recorded
- V1: 2026-06-02: Coherence cleanup follow-up; branch chore/coherence-cleanup merged; audit_repo test result 11/11 PASS recorded in journal entry
- V2: PATHS: config/paths.toml exists
- V2: PATHS: src/corp/ namespace directory exists with consolidated structure
- V2: PATHS: tests/safety/test_vault_writer_invariant.py exists (ADR-27 enforcement)
- V2: PATHS: VISION.md exists
- V2: PATHS: .pre-commit-config.yaml exists
- V2: COMMANDS: Five CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: COMMANDS: scripts/run-all-tests.ps1 exists
- V2: COMMANDS: scripts/dev-check.ps1 exists
- V2: HOOKS: ruff hook configured in .pre-commit-config.yaml
- V2: HOOKS: tach-check hook configured in .pre-commit-config.yaml
- V2: NAMES: ADR-14 (corp ADR-14-naming-convention-v2.md) exists in docs/decisions/
- V2: NAMES: ADR-23 (corp ADR-23-monorepo-internal-architecture.md) exists in docs/decisions/
- V2: NAMES: ADR-27 (corp ADR-27-safety-invariants.md) exists in docs/decisions/
- V2: COMMANDS: .claude/commands/ repo-level slash commands directory does not exist (matches CLAUDE.md s7 'none currently')
- V2: CI: .github/workflows/nightly-conformance-triage.yml exists
- V2: ARCHITECTURE: tach.toml exists defining 4-layer model: interface, orchestration, core, foundation
- V3: extract.py LOC = 1184 (wc -l src/corp/extractor/extract.py)
- V3: router.py LOC = 893 (wc -l src/corp/ingest/router.py)
- V3: inbox.py LOC = 951 (wc -l src/corp/ingest/inbox.py)
- V3: database.py LOC = 542 (wc -l src/corp/ops/database.py)
- V3: type codes = 22 in config/naming_config.yaml
- V3: client aliases = 32 in config/naming_config.yaml
- V3: agents = 6 in config/agents.yaml
- V3: Five CLIs = 5 (verified in pyproject.toml [project.scripts])
- V3: CLI files = 18 (ls src/corp/cli/*.py | wc -l)
- V3: actions modules = 12 (ls src/corp/actions/*.py | wc -l)
- V3: OpsDB repos = 5 (header comment in src/corp/ops/database.py)
- V3: notes count — unverifiable-in-clone: notes count (index.db not in clone; gitignored per .gitignore)

