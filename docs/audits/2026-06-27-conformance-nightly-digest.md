# corp-monorepo — Nightly Conformance Digest (2026-06-27)

- **Date:** 2026-06-27
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=2 survived=2 killed=0 -->

## Summary

Doc health is strong: of 2 raw findings, both survived adversarial skeptic review (0 killed), giving a 0% kill-rate this run — no false positives were generated, and the surviving findings are genuine, low-blast-radius drift rather than systemic rot. The 44-item checked-clean list confirms the bulk of structural, numeric, and lifecycle claims across CLAUDE.md, ARCHITECTURE.md, ADRs, pyproject.toml, and recent branch merges hold on disk. The two survivors are a missing JOURNAL entry for the 2026-06-22 foundation-extension verification pass (med) and a stale audit-doc citation referenced by two living docs but absent on disk (low). Both are already partially on the team's radar and require only routine documentation maintenance, no code or architecture changes.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- journal: 2026-06-22 foundation-extension verification pass (commits 941e60a/b13c163, 218-line audit doc) merged to main with no JOURNAL.md entry — newest entry is 2026-06-16.

### Low

- living-docs: ARCHITECTURE.md:548 and ADR-27:179 cite docs/audits/2026-04-21-p1-verification.md, which does not exist on disk (flagged unresolved at JOURNAL:136).

## Next Actions (proposals for operator)

- Append an ADR-49-shaped JOURNAL.md entry for the 2026-06-22 foundation-extension verification pass (commits 941e60a/b13c163, docs/audits/2026-06-21-foundation-review.md).
- Resolve JOURNAL:136 open question: either recreate docs/audits/2026-04-21-p1-verification.md or correct the two citations (ARCHITECTURE.md:548, ADR-27:179) to point at the existing 2026-04-21-codex-hotfix-review.md.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16: scripts/current_state_audit.py, scripts/_audit_core.py, config/audit.yaml all exist on disk (git merge 1913d30 verified)
- V1: 2026-06-16: docs/audits/2026-06-16-current-state-architecture-audit.md and -inventory.json exist
- V1: 2026-06-16: tests/safety/test_audit_readonly_invariant.py and test_audit_core.py exist
- V1: 2026-06-16: Branch audit/current-state-architecture merged to main via merge commit 1913d30
- V1: 2026-06-06: conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1 all exist
- V1: 2026-06-06: Tier-1 install commits 13fea1e, a7a161e, 4b46709 verified in git
- V1: 2026-06-06: load_status() retry wrapper exists in manifest.py
- V1: 2026-06-04: graphify-pilot.md exists; graphify pilot branch deleted
- V1: 2026-06-04: conformance-baseline-digest.md exists
- V1: 2026-06-03: BACKLOG items #10 and #11 present
- V1: 2026-06-03: ARCHITECTURE.md TOC markers at lines 12/47
- V1: 2026-06-03: Stale branches deleted as claimed
- V2: config/paths.toml exists
- V2: src/corp/ unified namespace exists
- V2: tests/safety/test_vault_writer_invariant.py exists
- V2: config/naming_config.yaml exists
- V2: .pre-commit-config.yaml exists with ruff and tach hooks
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 exist
- V2: 5 CLIs declared in pyproject.toml [project.scripts]
- V2: docs/decisions/ADR-14, ADR-23, ADR-27, README.md exist
- V2: .claude/commands/ absent — consistent with 'none currently'
- V2: tach.toml and .github/workflows/tach.yml exist
- V2: unverifiable-in-clone: user-level ~/.claude/ paths
- V2: unverifiable-in-clone: .dev-knowledge ecosystem ADRs
- V3: extract.py 1184 LOC matches doc
- V3: ingest/router.py 893 LOC matches doc
- V3: ingest/inbox.py 951 LOC matches doc
- V3: ops/database.py 542 LOC matches doc
- V3: actions/ 12 modules matches doc
- V3: cli/ 18 files matches doc
- V3: 5 CLIs in pyproject.toml matches doc
- V3: 22 type codes in naming_config.yaml matches doc
- V3: 32 client aliases in naming_config.yaml matches doc
- V3: 6 agents in agents.yaml matches doc
- V3: OpsDB delegates to 5 repositories matches doc
- V3: unverifiable-in-clone: notes count (index.db not in clone)

