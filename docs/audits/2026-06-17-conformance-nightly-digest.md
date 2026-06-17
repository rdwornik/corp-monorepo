# corp-monorepo — Nightly Conformance Digest (2026-06-17)

- **Date:** 2026-06-17
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=5 survived=4 killed=1 -->

## Summary

Documentation health is strong. Across three verifiers covering JOURNAL-vs-git reconciliation, living-doc structural claims, and deterministic numeric-inventory drift, five raw findings surfaced and four survived adversarial skepticism (skeptic kill-rate 1/5 = 20%). Every survivor is low severity: three are missing JOURNAL Changes-line attributions for same-day gotchas.md merges (0ef1fcd, de5cb53, fc31ab9 per §6 'sole change record'), and one is a dangling ARCHITECTURE.md reference to a non-existent audit file (2026-04-21-p1-verification.md, whose sibling codex-hotfix-review.md does exist). No high or medium findings exist; no source-of-truth, safety-guard, or numeric-inventory drift was detected. The single killed finding (deferred onedrive.py/test centralization targets) was a false positive correctly explained by ADR-27's documented PR-1/PR-2/PR-3 deferral. The extensive checked-clean list confirms all declared paths, CLIs, hooks, ADRs, and ARCHITECTURE.md LOC/count claims hold, making the absence of findings in those areas informative rather than merely unexamined.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

_No med-severity findings._

### Low

- [journal] Merge 0ef1fcd (chore/gh-auth-check, 2026-06-06) modified surface-conformance.ps1 (+24/-2) and gotchas.md (+4) with no same-day JOURNAL Changes-line attribution.
- [journal] Merge de5cb53 (chore/dev-check-gotcha, 2026-06-03) added +7 lines to gotchas.md (dev-check tree-mutation gotcha) with no Changes-line attribution in any 2026-06-03 entry.
- [journal] Merge fc31ab9 (docs/gotchas-2026-06-06, 2026-06-06) added +17 lines to gotchas.md (here-string + Bash-tool harness gotchas) with no Changes-line attribution in any same-day entry.
- [living-docs] ARCHITECTURE.md lines 547-548 cite docs/audits/2026-04-21-p1-verification.md as present-tense documentation, but the file does not exist (sibling 2026-04-21-codex-hotfix-review.md does).

## Next Actions (proposals for operator)

- Append a catch-up JOURNAL Changes-line note crediting 0ef1fcd (2026-06-06): gh auth gate added to surface-conformance.ps1 + gotchas.md entry — proposal for operator, no action taken.
- Credit de5cb53 (2026-06-03) in a Changes line (gotchas.md dev-check tree-mutation gotcha) on a 2026-06-03 or catch-up entry — proposal for operator, no action taken.
- Credit fc31ab9 (2026-06-06) in a Changes line (gotchas.md here-string + Bash-tool harness gotchas) on a 2026-06-06 or catch-up entry — proposal for operator, no action taken.
- Resolve the dangling ARCHITECTURE.md reference (lines 547-548): either restore/commit docs/audits/2026-04-21-p1-verification.md or correct the pointer to the existing 2026-04-21-codex-hotfix-review.md — proposal for operator, no action taken.
- Optional: consider batching the three gotchas.md attribution gaps into a single catch-up JOURNAL entry to satisfy §6 'sole change record' with minimal churn — proposal for operator, no action taken.

## Killed Findings

- ARCHITECTURE.md §OneDrive guards and ADR-27 cite src/corp/safety/onedrive.py and tests/safety/test_no_unguarded_writes.py as centralization targets; neither exists. — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16 audit session: scripts/current_state_audit.py, scripts/_audit_core.py, config/audit.yaml, all test files exist on disk
- V1: 2026-06-16 audit session: docs/audits/2026-06-16-current-state-architecture-audit.md, inventory JSON, codex review doc all exist
- V1: 2026-06-16 audit session: branch audit/current-state-architecture merged --no-ff via commit 1913d30
- V1: 2026-06-16 audit session: '33 audit safety tests pass' confirmed (25+3+5 in tests/safety/)
- V1: 2026-06-06 Triage ratification: Tier-1 install SHAs 13fea1e, a7a161e, 4b46709 all present in git history
- V1: 2026-06-06 Nightly conformance routine: .claude/workflows/conformance-corp.js, scripts/render_conformance_digest.py, .github/workflows/nightly-conformance-triage.yml, scripts/surface-conformance.ps1, tests/test_nightly_triage_parser.py all exist
- V1: 2026-06-06 Nightly conformance routine: branch feat/nightly-conformance merged --no-ff confirmed
- V1: 2026-06-06 Scoped CLAUDE.md deep-audit: load_status() retry wrapper confirmed in src/corp/extractor/manifest.py
- V1: 2026-06-06 Scoped CLAUDE.md deep-audit: transient-failure retry test confirmed in tests/extractor/test_manifest.py
- V1: 2026-06-06 Remote bookkeeping: BACKLOG.md item #13 confirmed at line 62
- V1: 2026-06-04 ARCHITECTURE.md count refresh: commit 96db96b dated 2026-06-04 with correct message confirmed
- V1: 2026-06-04 Conformance baseline review: docs/audits/2026-06-04-conformance-baseline-digest.md exists
- V1: 2026-06-03 Track ruff drift: merged via 98dd12a confirmed
- V1: 2026-06-03 Resolve 3 unmerged branches: merged via 37abe8d, stale branches absent
- V1: 2026-06-03 ADR-71 pilot: .pre-commit-config.yaml has ../.dev-knowledge stanza with toc-freshness + toc-generate hooks
- V1: 2026-06-02 Ecosystem unification: LESSONS.md new (+17 lines), all 5 files (ARCHITECTURE, BACKLOG, CONTRIBUTING, JOURNAL, LESSONS) modified confirmed
- V1: Automated nightly digest commits (06-07 through 06-16) not in JOURNAL by design — spec-orchestration automated runs, not human sessions
- V2: PATHS: config/paths.toml exists
- V2: PATHS: src/corp/ namespace exists
- V2: PATHS: tests/safety/test_vault_writer_invariant.py exists
- V2: PATHS: config/naming_config.yaml exists
- V2: PATHS: .pre-commit-config.yaml exists
- V2: PATHS: scripts/run-all-tests.ps1 exists
- V2: PATHS: scripts/dev-check.ps1 exists
- V2: PATHS: tach.toml exists
- V2: PATHS: docs/diagrams/system-context.svg, magistrala-pipeline.svg, container-module.svg all exist
- V2: PATHS: config/agents.yaml, workflows.yaml, content_registry.yaml, extractor/, project/default.yaml, opportunity/default.yaml, rfp/anonymization.yaml, rfp/product_profiles/ all exist
- V2: PATHS: All 13 sub-module dirs (schema, extractor, extraction, ingest, ops, retrieve, cleanup, overnight, project, opportunity, rfp, cli, actions) exist under src/corp/
- V2: PATHS: extractor/scripts/run.py (cke CLI entry point) exists
- V2: COMMANDS: All 5 CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- V2: COMMANDS: .claude/commands/ is empty, consistent with CLAUDE.md §7 'none currently'
- V2: HOOKS: ruff hook (id: ruff) present in .pre-commit-config.yaml
- V2: HOOKS: tach hook (id: tach-check, entry: tach check) present in .pre-commit-config.yaml
- V2: HOOKS/CI: tach.yml workflow exists and runs 'tach check'
- V2: HOOKS/CI: nightly-conformance-triage.yml CI workflow exists
- V2: NAMES: ADR-14, ADR-23, ADR-27, ADR-26, ADR-32, ADR-16, ADR-22 all exist under docs/decisions/
- V2: unverifiable-in-clone: user-level ~/.claude/commands/, ~/.claude/skills/, ~/.claude/settings.json (not in repo clone)
- V2: unverifiable-in-clone: ../.dev-knowledge/docs/handoffs/ and ../.dev-knowledge/docs/decisions/ (outside clone)
- V3: extract.py LOC = 1184 matches ARCHITECTURE.md claim: wc -l src/corp/extractor/extract.py → 1184
- V3: inbox.py LOC = 951 matches ARCHITECTURE.md claim: wc -l src/corp/ingest/inbox.py → 951
- V3: database.py LOC = 542 matches ARCHITECTURE.md claim: wc -l src/corp/ops/database.py → 542
- V3: router.py LOC = 893 matches ARCHITECTURE.md claim: wc -l src/corp/ingest/router.py → 893
- V3: actions modules = 12 matches ARCHITECTURE.md claim: ls src/corp/actions/*.py | wc -l → 12
- V3: cli files = 18 matches ARCHITECTURE.md claim: ls src/corp/cli/*.py | wc -l → 18
- V3: naming_config.yaml type_codes = 22 matches ARCHITECTURE.md claim
- V3: naming_config.yaml client_aliases = 32 matches ARCHITECTURE.md claim
- V3: config/agents.yaml agent count = 6 matches ARCHITECTURE.md claim
- V3: pyproject.toml CLI scripts = 5 matches ARCHITECTURE.md/CLAUDE.md claim (corp, corp-meta, cke, cpe, com)
- V3: OpsDB delegates to 5 repos (Asset, Package, Event, Routing, Suggestion) matches ARCHITECTURE.md claim
- V3: corp CLI 40+ commands: actual count ≥47, claim is stated lower bound, not exact
- V3: unverifiable-in-clone: notes count (488 notes, live 2026-06-04) — index.db is gitignored and not in clone

