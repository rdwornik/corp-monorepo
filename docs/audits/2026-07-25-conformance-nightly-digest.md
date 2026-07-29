# corp-monorepo — Nightly Conformance Digest (2026-07-25)

- **Date:** 2026-07-25
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** native

<!-- counts: raw=7 survived=6 killed=1 -->

## Summary

Documentation health is broadly sound: 78 verifier checks came back clean (all declared paths, hooks, CLIs, ADR files, and most numeric inventory claims match the tree), and only 7 raw findings surfaced across three domains. Of those, the adversarial skeptic killed 1 false positive (a point-in-time JOURNAL entry that a later operator-gated merge moved past — normal append-only behavior, not drift), a 14% kill-rate, leaving 6 survivors. The survivors are dominated by low-severity numeric drift in ARCHITECTURE.md (four LOC/module-count skews plus a phantom cli/task.py reference), one low-severity missing JOURNAL entry for the ARC-4 leg-1 merge, and a single medium-severity dangling living-doc citation to an audit file (2026-04-21-p1-verification.md) that was never tracked in git. No high-severity findings. The drift is recent and mechanical (E5/#38 and terra work grew several modules), so remediation is low-risk doc-sync plus one reference reconciliation.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- ARCHITECTURE.md:454 and docs/audits/2026-04-21-codex-hotfix-review.md:9 both cite docs/audits/2026-04-21-p1-verification.md as the P1 verification source, but that file was never tracked (git diff-filter=A empty on all branches, not gitignored) — a real dangling living-doc reference.

### Low

- JOURNAL.md has no session entry for the ARC-4 leg-1 ruff/pytest floor-equalization merge (2c48fd5, feat/arc4-leg1-ruff-equalization, 2026-07-18), confirmed an ancestor of HEAD.
- ARCHITECTURE.md:179 states database.py is 542 LOC; actual is 562 (+20, recent E5 #38 'gated' column).
- ARCHITECTURE.md:193 states cli/ contains 18 files; actual is 17, and the referenced cli/task.py (ARCHITECTURE.md:341 'corp task') does not exist on disk.
- ARCHITECTURE.md:86 (and RESOLVED row :418) states actions/ contains 12 modules; actual is 11 .py files (9 domain modules).
- ARCHITECTURE.md:116 states extract.py is 1184 LOC; actual is 1194 (+10).

## Next Actions (proposals for operator)

- Reconcile the dangling P1 citation (med): either restore/commit docs/audits/2026-04-21-p1-verification.md, or amend ARCHITECTURE.md:454 and docs/audits/2026-04-21-codex-hotfix-review.md:9 to point at the audit that actually holds the P1 findings.
- Sync ARCHITECTURE.md numeric inventory in one doc-edit pass: database.py 542->562 (:179), extract.py 1184->1194 (:116), cli/ 18->17 (:193), actions/ 12->11 (:86 and :418).
- Remove or correct the phantom 'corp task | cli/task.py' CLI-reference row (ARCHITECTURE.md:341) since cli/task.py does not exist.
- Prepend a catch-up JOURNAL entry for the ARC-4 leg-1 ruff/pytest equalization merge (2c48fd5), or confirm in-record that it is a hub-orchestrated fleet floor change exempt from the corp session log.

## Killed Findings

- Module-connection-map branch was 'not merged' at session close (entry 1 Result line) is now a stale/contradicted permanent record — _true-but-irrelevant_

## Checked-and-clean (so absence is informative)

- V1: JOURNAL entries 1-10 all cross-checked against git — every cited commit/merge SHA (95e1f0c, b066c4a, 4749dc9, 4bbbf9a, 5816b03, 334da4e, 60b7367, b28db4d, 363bdd4, 2c1ab27, a406b4c, eaafda7, 989811e, d3e8094, cf36bac, 380ebfd, 236de12, 74ef46c, af02a0c, 59f29d8) present
- V1: Entry 2 N2 fix: test_cross_package.py uses pyproject identity check (name = "corp") not REPO_ROOT.name basename (line 37)
- V1: Entry 9 S13 docs/audits count arithmetic 82->55 verified via git ls-tree at the cited commits
- V1: BACKLOG #69 (ADR-archival task) present in BACKLOG.md line 138
- V1: Nightly conformance digest commits (abed866, 3da2d8c, fa4583e, 870c593) correctly classified as automated/spec-orchestration — not expected to carry JOURNAL entries
- V2: All declared paths present — config/paths.toml, src/corp/ namespace, tests/safety/test_vault_writer_invariant.py, .pre-commit-config.yaml, scripts/run-all-tests.ps1, scripts/dev-check.ps1, docs/decisions/ + README.md, .claude/commands/override.md, .claude/settings.json, .methodology.yaml, tach.toml, config/naming_config.yaml
- V2: docs/handoffs/ correctly absent (matches CLAUDE.md s1 ADR-36 read-only claim)
- V2: OneDrive guard sites present — src/corp/safety/onedrive.py, cleanup/disk.py, cleanup/executor.py, cleanup/errors.py re-exports, actions/_helpers.py guards
- V2: All 5 CLI entry points (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts] and their handler modules exist on disk
- V2: All 9 declared pre-commit hooks present (ruff, tach-check, normalize-headers, floor-hash-verify, canonical_freshness, validate-audit-casing, validate-backlog, backlog-id-on-close, block-ff-push)
- V2: ADR files present — ADR-14, ADR-23, ADR-27 under docs/decisions/
- V2: unverifiable-in-clone (correctly not flagged): ~/.claude/ user-level commands and gotchas skill
- V3: router.py=893 LOC matches doc (ARCHITECTURE.md:165)
- V3: inbox.py=951 LOC matches doc (ARCHITECTURE.md:166)
- V3: naming_config.yaml type_codes=22 and client_aliases=32 match doc (ARCHITECTURE.md:171,299)
- V3: agents.yaml agent count=6 matches doc (ARCHITECTURE.md:296)
- V3: pyproject.toml CLIs=5 matches doc (ARCHITECTURE.md:17, CLAUDE.md s3)
- V3: OpsDB delegates to exactly 5 repository classes, matches doc (ARCHITECTURE.md:392)
- V3: unverifiable-in-clone (correctly not flagged): 488 notes count — index.db is an uncommitted runtime artifact

