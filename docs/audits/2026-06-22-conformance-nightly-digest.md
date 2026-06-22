# corp-monorepo — Nightly Conformance Digest (2026-06-22)

- **Date:** 2026-06-22
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=3 survived=1 killed=2 -->

## Summary

Documentation conformance for corp-monorepo is strong. Of 3 raw findings surfaced by the verifiers, the adversarial skeptic killed 2 as false positives (a 67% kill rate), leaving 1 genuine survivor — a low-severity JOURNAL omission where a doc-only gotchas.md commit (9477a1d, merge de5cb53) that did land on main is not recorded in any JOURNAL Changes: line, in violation of the ADR-49/ADR-30 sole-change-log contract. Both kills shared the same defect: the claimed branches (fc31ab9, 0ef1fcd) were never merged to main and are only branch-local on the working branch, so absence from JOURNAL is expected and not a conformance breach. The checked-clean set is broad and confirms living-doc structural claims (paths, CLIs, hooks, ADRs), numeric inventory (LOC counts, file/module counts, agent and alias tallies), and JOURNAL-vs-git history across the audited date range all hold; remaining gaps are explicitly unverifiable-in-clone (GitHub API state, user-level ~/.claude/ config, index.db). Overall doc health is healthy with a single low-severity bookkeeping fix outstanding.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

_No med-severity findings._

### Low

- JOURNAL omission: merged-to-main commit 9477a1d (dev-check tree-mutation gotcha, merge de5cb53) is absent from any JOURNAL Changes: line — confirmed ancestor of main, touches only gotchas.md, ADR-49/ADR-30 require it (JOURNAL.md:65).

## Next Actions (proposals for operator)

- Operator proposal: append `.claude/skills/gotchas/gotchas.md (dev-check tree-mutation gotcha)` to the Changes: line of the 2026-06-03 ruff-drift JOURNAL entry (JOURNAL.md:65), OR add a one-line JOURNAL entry covering merge de5cb53, to close the ADR-49/ADR-30 change-log gap for commit 9477a1d.

## Killed Findings

- 2026-06-06 docs/gotchas-2026-06-06 branch (commit d0989ee, merge fc31ab9) merged to main but has no JOURNAL entry — _evidence-not-definitive_
- 2026-06-06 chore/gh-auth-check branch (commit 116feea, merge 0ef1fcd) merged to main but has no JOURNAL entry — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16 entry: scripts/current_state_audit.py exists on disk — git show 1913d30 + ls confirm
- V1: 2026-06-16 entry: scripts/_audit_core.py exists on disk — ls confirm
- V1: 2026-06-16 entry: config/audit.yaml exists — ls confirm
- V1: 2026-06-16 entry: docs/audits/2026-06-16-current-state-architecture-audit.md and .json both exist
- V1: 2026-06-16 entry: merged as audit/current-state-architecture via merge 1913d30; 10 constituent commits present (73631e3 through c43b85f)
- V1: 2026-06-06 triage entry: three cited commits (13fea1e, a7a161e, 4b46709) all present in git log
- V1: 2026-06-06 nightly conformance entry: branch feat/nightly-conformance merged via 34a2a9a; four constituent commits present (294c417, d7e8031, f39b511, 0febe06)
- V1: 2026-06-06 nightly conformance entry: conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1 all present
- V1: 2026-06-06 nightly conformance entry: tests/test_nightly_triage_parser.py and tests/fixtures/nightly-triage/ present
- V1: 2026-06-06 CLAUDE.md conformance audit entry: manifest.py retry wrapper implemented — commit 1a057f2 present
- V1: 2026-06-04 ARCHITECTURE.md count refresh entry: commit 96db96b present; 2026-06-04-conformance-baseline-digest.md exists
- V1: 2026-06-03 ruff-drift entry: BACKLOG #12 verified — commit 48a565e present
- V1: 2026-06-03 stale-branches entry: commits e7eb86a, 57bd968 present; merge 37abe8d confirmed
- V1: 2026-06-03 doctools-hooks entry: commits d764c79, 3bf0192, 8b80a34 present; merge 99c7925 confirmed
- V1: Nightly conformance digests 2026-06-07 through 2026-06-21 (15 commits) present as automated squash-merges — not required to be journaled by design
- V1: unverifiable-in-clone: GitHub issue #4 closed-state and comment body (requires GitHub API)
- V1: unverifiable-in-clone: GitHub issue #2 deleted-state (requires GitHub API)
- V1: unverifiable-in-clone: ~/.claude/ user-level settings and skills (outside repo)
- V2: PATHS: src/corp/ namespace exists (src/corp/__init__.py present)
- V2: PATHS: config/paths.toml exists
- V2: PATHS: config/naming_config.yaml exists
- V2: PATHS: .pre-commit-config.yaml exists at repo root
- V2: PATHS: tests/safety/test_vault_writer_invariant.py exists
- V2: PATHS: scripts/run-all-tests.ps1 exists
- V2: PATHS: scripts/dev-check.ps1 exists
- V2: PATHS: src/corp/actions/ directory exists with all named domain modules
- V2: PATHS: src/corp/actions/_helpers.py exists
- V2: PATHS: src/corp/vault_io.py exists
- V2: PATHS: src/corp/audit.py exists
- V2: PATHS: src/corp/integrity.py exists
- V2: PATHS: tach.toml exists
- V2: PATHS: config/agents.yaml exists
- V2: PATHS: config/workflows.yaml exists
- V2: PATHS: config/opportunity/default.yaml exists
- V2: PATHS: docs/decisions/README.md exists
- V2: PATHS: .claude/skills/gotchas/ exists
- V2: PATHS: .github/workflows/tach.yml exists
- V2: PATHS: .github/workflows/nightly-conformance-triage.yml exists
- V2: PATHS: scripts/normalize_headers.py exists
- V2: PATHS: scripts/render_conformance_digest.py exists
- V2: PATHS: src/corp subdirectories all present: schema/, extraction/, extractor/, ingest/, ops/, retrieve/, project/, opportunity/, rfp/, cli/, actions/, cleanup/
- V2: PATHS: No AGENTS.md at repo root — consistent with CLAUDE.md claim
- V2: COMMANDS: All 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: COMMANDS: .claude/commands/ does not exist — consistent with CLAUDE.md §7 'none currently'
- V2: HOOKS: ruff hook present in .pre-commit-config.yaml
- V2: HOOKS: tach hook (id: tach-check, entry: tach check) present in .pre-commit-config.yaml
- V2: NAMES: corp ADR-14 exists: docs/decisions/ADR-14-naming-convention-v2.md
- V2: NAMES: corp ADR-23 exists: docs/decisions/ADR-23-monorepo-internal-architecture.md
- V2: NAMES: corp ADR-27 exists: docs/decisions/ADR-27-safety-invariants.md
- V2: NAMES: corp ADR-16, ADR-22, ADR-26, ADR-32 all exist in docs/decisions/
- V2: unverifiable-in-clone: CLAUDE.md §7 user-level ~/.claude/commands/ (not in this clone)
- V2: unverifiable-in-clone: CLAUDE.md §8 user-level ~/.claude/skills/gotchas/ (not in this clone)
- V2: unverifiable-in-clone: CLAUDE.md §9 ~/.claude/settings.json SessionStart hook (not in this clone)
- V2: unverifiable-in-clone: ARCHITECTURE.md corp/safety/onedrive.py — explicitly described as planned future artifact
- V3: extract.py 1184 LOC: wc -l src/corp/extractor/extract.py → 1184
- V3: ingest/router.py 893 LOC: wc -l src/corp/ingest/router.py → 893
- V3: ingest/inbox.py 951 LOC: wc -l src/corp/ingest/inbox.py → 951
- V3: ops/database.py 542 LOC: wc -l src/corp/ops/database.py → 542
- V3: cli/ 18 files: ls src/corp/cli/*.py | wc -l → 18
- V3: actions/ 12 modules: ls src/corp/actions/*.py | wc -l → 12
- V3: agents.yaml 6 agents: grep confirmed → 6
- V3: naming_config.yaml 22 type codes: awk type_codes section → 22
- V3: naming_config.yaml 32 client aliases: awk client_aliases section → 32
- V3: 5 CLIs in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com → 5
- V3: OpsDB delegates to 5 repos: AssetRepo/PackageRepo/EventRepo/RoutingRepo/SuggestionRepo → 5 confirmed
- V3: unverifiable-in-clone: notes count (index.db not in clone)

