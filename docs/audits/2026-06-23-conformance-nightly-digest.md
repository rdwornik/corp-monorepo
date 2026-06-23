# corp-monorepo — Nightly Conformance Digest (2026-06-23)

- **Date:** 2026-06-23
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=4 survived=3 killed=1 -->

## Summary

Overall documentation health is strong: the deterministic numeric-inventory layer (V3) and structural living-doc claims (V2) verify cleanly with no drift, and the bulk of JOURNAL-vs-git history (V1) reconciles across the 2026-06-03 through 2026-06-16 sessions. Of 4 raw findings, 3 survived adversarial skeptic review and 1 was killed as a false positive (25% kill rate) — the killed item being the corp/safety/onedrive.py reference, which ARCHITECTURE.md and ADR-27 explicitly document as phased future work rather than a defect. The 3 survivors are all journal/living-doc bookkeeping gaps: one high-severity missing JOURNAL entry for the 2026-06-21/22 foundation-review session (the sole change record per CLAUDE.md §6), plus two low-severity items (an unrecorded 2026-06-06 gh-auth gate addition and a dangling ARCHITECTURE.md:548 reference to a never-committed p1-verification.md). No structural, dependency-layer, or numeric-count violations were found.

## Findings (PROPOSALS ONLY)

### High

- Foundation-extension verification pass (commits b13c163, 941e60a, 2026-06-22, adding docs/audits/2026-06-21-foundation-review.md) has no corresponding JOURNAL.md entry — violates CLAUDE.md §6 sole-change-record rule.

### Med

_No med-severity findings._

### Low

- 2026-06-06 gh-auth gate added to surface-conformance.ps1 (commits 0ef1fcd, 116feea) is not recorded in any JOURNAL entry.
- ARCHITECTURE.md:548 references docs/audits/2026-04-21-p1-verification.md, a dangling pointer to a file that does not exist and was never committed.

## Next Actions (proposals for operator)

- Append a JOURNAL.md entry in ADR-49 shape for the 2026-06-21/22 foundation-review session, recording docs/audits/2026-06-21-foundation-review.md as a Changes item (addresses the high-severity gap).
- Add a Changes line (or short entry) noting the leading gh-auth gate added to surface-conformance.ps1 on 2026-06-06.
- Resolve the ARCHITECTURE.md:548 dangling reference — either restore docs/audits/2026-04-21-p1-verification.md or repoint the line at the existing 2026-04-21-codex-hotfix-review.md.

## Killed Findings

- ADR-27 centralization design references corp/safety/onedrive.py (implying path exists or will exist under src/corp/safety/) — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-16 entry — scripts/current_state_audit.py, scripts/_audit_core.py, config/audit.yaml all exist on disk and in commit 73631e3
- V1: 2026-06-16 entry — current-state-architecture-audit .md/.json and codex-current-state-audit-tool.md all exist on disk
- V1: 2026-06-16 entry — tests/safety/test_audit_readonly_invariant.py and test_audit_core.py both exist
- V1: 2026-06-16 entry — merge via branch audit/current-state-architecture confirmed in merge commit 1913d30
- V1: 2026-06-06 (Nightly conformance) — conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1 all exist
- V1: 2026-06-06 (Nightly conformance) — tests/test_nightly_triage_parser.py and tests/fixtures/nightly-triage/* exist
- V1: 2026-06-06 (Scoped CLAUDE.md audit) — load_status retry wrapper present in src/corp/extractor/manifest.py (lines 81-89); retry test at tests/extractor/test_manifest.py lines 171-200
- V1: 2026-06-06 (Scoped CLAUDE.md audit) — CLAUDE.md §9 shows surface-closures.ps1; no /boot or /evolve references remain
- V1: 2026-06-06 (Triage ratification) — commits 13fea1e, a7a161e, 4b46709 present with matching subjects
- V1: 2026-06-06 (Remote bookkeeping) — BACKLOG.md #13 'Sanitize fixtures and archives' present with 2026-06-06 grooming-log timestamp
- V1: 2026-06-04 (ARCHITECTURE.md count refresh) — 2026-06-04-conformance-baseline-digest.md exists; merge commit 7b7e708 present
- V1: 2026-06-04 (graphify pilot) — 2026-06-04-graphify-pilot.md created in commit 9f7533e; graphify branch confirmed deleted
- V1: 2026-06-03 (Resolve 3 unmerged branches) — commit e7eb86a present; BACKLOG #10 and #11 confirmed
- V1: 2026-06-03 (Consume hub doc-tooling hooks) — commits 3bf0192 and d764c79 present
- V1: 2026-06-03 (Track ruff drift) — BACKLOG #12 present with 2026-06-03 grooming-log timestamp
- V2: CLAUDE.md:49 — config/paths.toml exists
- V2: CLAUDE.md:38 — src/corp/ namespace exists
- V2: CLAUDE.md:58 — tests/safety/test_vault_writer_invariant.py exists
- V2: CLAUDE.md:48/113 — .pre-commit-config.yaml exists with both ruff and tach hooks
- V2: CLAUDE.md:47 — scripts/run-all-tests.ps1 exists
- V2: CLAUDE.md:62 — scripts/dev-check.ps1 exists
- V2: CLAUDE.md:40 — all 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts]
- V2: CLAUDE.md:98 — repo-level .claude/commands/ absent, consistent with 'none currently'
- V2: CLAUDE.md:108 — .claude/skills/gotchas repo-level skill dir exists
- V2: CLAUDE.md:133 — docs/decisions/ADR-14-naming-convention-v2.md exists
- V2: CLAUDE.md:134 — docs/decisions/ADR-23-monorepo-internal-architecture.md exists
- V2: CLAUDE.md:135 — docs/decisions/ADR-27-safety-invariants.md exists
- V2: CLAUDE.md:130 — docs/decisions/README.md exists
- V2: ARCHITECTURE.md:59 — docs/diagrams/system-context.svg exists
- V2: ARCHITECTURE.md:326 — docs/diagrams/container-module.svg exists
- V2: ARCHITECTURE.md:476 — docs/diagrams/magistrala-pipeline.svg exists
- V2: ARCHITECTURE.md:271 — tach.toml exists
- V2: ARCHITECTURE.md:387 — config/agents.yaml exists
- V2: ARCHITECTURE.md:389 — config/workflows.yaml exists
- V2: ARCHITECTURE.md:390 — config/content_registry.yaml exists
- V2: ARCHITECTURE.md:391 — config/naming_config.yaml exists
- V2: ARCHITECTURE.md:392 — config/extractor/ directory exists
- V2: ARCHITECTURE.md:393 — config/project/default.yaml exists
- V2: ARCHITECTURE.md:394 — config/opportunity/default.yaml exists
- V2: ARCHITECTURE.md:395 — config/rfp/anonymization.yaml exists
- V2: ARCHITECTURE.md:396 — config/rfp/product_profiles/ directory exists
- V2: ARCHITECTURE.md:544 — corp.cleanup.errors module exists with OneDriveSafetyError
- V2: ARCHITECTURE.md:550 — docs/audits/2026-04-21-codex-hotfix-review.md exists
- V2: ARCHITECTURE.md:577 — scripts/dev-check.ps1 exists
- V2: ARCHITECTURE.md — src/corp/ schema/, extractor/, extraction/, ingest/, ops/, cli/, retrieve/, cleanup/, overnight/, project/, opportunity/, rfp/ all exist
- V2: ARCHITECTURE.md:587 — docs/decisions/ADR-16, ADR-22, ADR-26, ADR-32 all exist
- V2: ARCHITECTURE.md:13/15 — CI workflow .github/workflows/tach.yml exists and runs tach check on PR/push to main
- V2: unverifiable-in-clone — CLAUDE.md §7 user-level ~/.claude/commands/ (not in this clone)
- V2: unverifiable-in-clone — CLAUDE.md §8 user-level ~/.claude/skills/gotchas/ (not in this clone)
- V2: unverifiable-in-clone — CLAUDE.md §9 ~/.claude/settings.json SessionStart hook (not in this clone)
- V2: unverifiable-in-clone — ARCHITECTURE.md corp/safety/onedrive.py described as planned future artifact (killed by skeptic as documented-decision ADR-27)
- V3: extract.py 1184 LOC (ARCHITECTURE.md:190) confirmed
- V3: ingest/router.py 893 LOC (ARCHITECTURE.md:239) confirmed
- V3: ingest/inbox.py 951 LOC (ARCHITECTURE.md:240) confirmed
- V3: ops/database.py 542 LOC (ARCHITECTURE.md:253) confirmed
- V3: actions/ 12 modules (ARCHITECTURE.md:160) confirmed
- V3: cli/ 18 files (ARCHITECTURE.md:267) confirmed
- V3: 22 type codes (ARCHITECTURE.md:391) confirmed
- V3: 32 client aliases (ARCHITECTURE.md:391) confirmed
- V3: 6 agents (ARCHITECTURE.md:388) confirmed
- V3: 5 CLIs in pyproject.toml (ARCHITECTURE.md:56) confirmed
- V3: OpsDB delegates to 5 repos (ARCHITECTURE.md:486) confirmed
- V3: unverifiable-in-clone — notes count (index.db not in clone)

