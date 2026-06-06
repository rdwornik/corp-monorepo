# corp-monorepo — Nightly Conformance Digest (2026-06-06)

- **Date:** 2026-06-06
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=2 survived=1 killed=1 -->

## Summary

Documentation health is strong. Across three verifiers, 51 distinct claims spanning JOURNAL-vs-git reconciliation, living-doc structural assertions (CLAUDE.md, ARCHITECTURE.md), and deterministic numeric-inventory drift were checked and found clean (or correctly flagged unverifiable-in-clone). Only 2 raw findings surfaced; the skeptic killed 1 as a true-but-irrelevant false positive (a 50% kill-rate), leaving a single surviving med-severity gap: the 2026-06-02 Tier-1 lifecycle plugin install (three substantive commits) was never journaled, violating CLAUDE.md §6's 'JOURNAL Changes: is the sole change record' rule. No high-severity drift, no structural mismatches in the canonical docs, and all numeric inventories (LOC, module/CLI/agent counts, ADR presence) reconcile.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- journal: 2026-06-02 Tier-1 lifecycle plugin install (commits 13fea1e, a7a161e, 4b46709 — .claude/settings.json + .gitignore changes) is absent from the last 10 JOURNAL entries, violating CLAUDE.md §6 'Changes: is the sole change record'.

### Low

_No low-severity findings._

## Next Actions (proposals for operator)

- Operator: add a JOURNAL.md entry (ADR-49 shape: Did/Result/Changes/Abandoned/Next) for the 2026-06-02 Tier-1 lifecycle plugin install, recording the .claude/settings.json install/reorder and .gitignore logs/ changes per CLAUDE.md §6.

## Killed Findings

- CLAUDE.md:98 says repo-level slash commands are 'none currently' but the .claude/commands/ directory does not exist at all — _true-but-irrelevant_

## Checked-and-clean (so absence is informative)

- JOURNAL last-10 entries (2026-06-02..06-06) reconcile to git: all cited commits present
- JOURNAL Entry 1 nightly-conformance scaffolding: all files exist; SessionStart hook wired
- JOURNAL Entry 3 (#75): retry wrapper in manifest.py load_status() + transient-failure test confirmed
- Git history bounded (oldest commit 2026-04-15) -- no out-of-scope entries in last-10 window
- CLAUDE.md §3: 5 CLIs (corp, corp-meta, cke, cpe, com) all declared in pyproject.toml [project.scripts]
- CLAUDE.md §3 / ARCHITECTURE.md: src/corp/ namespace and submodules exist
- CLAUDE.md §4/§5: config/paths.toml, config/naming_config.yaml, scripts/run-all-tests.ps1, scripts/dev-check.ps1 all exist
- CLAUDE.md §5: tests/safety/test_vault_writer_invariant.py exists
- CLAUDE.md §9: pre-commit ruff + tach (tach-check) hooks present in .pre-commit-config.yaml
- CLAUDE.md §11: corp ADR-14, ADR-23, ADR-27 files exist in docs/decisions/
- ARCHITECTURE.md: all 3 diagrams exist; CLI reference matches pyproject.toml; all config files exist; governing ADRs (14, 16, 22, 23, 26, 27, 32) all present
- .github/workflows/ present with nightly-conformance-triage.yml and tach.yml
- Numeric inventory drift: extract.py 1184 LOC, router.py 893, inbox.py 951, database.py 542; actions/ 12 modules; cli/ 18 files; naming_config 22 type codes + 32 client aliases; agents.yaml 6 agents; pyproject 5 CLIs; OpsDB delegates to 5 repos -- all reconcile
- Out-of-scope / unverifiable-in-clone (correctly excluded): user-level ~/.claude/commands/ and ~/.claude/skills/, ~/.claude/settings.json SessionStart surface-closures.ps1, ~/.codex/AGENTS.md, and live notes count (488, requires gitignored index.db)
- Killed false positive: CLAUDE.md:98 'none currently' for repo-level slash commands -- accurate, no drift

