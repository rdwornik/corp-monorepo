# corp-monorepo — Nightly Conformance Digest (2026-07-22)

- **Date:** 2026-07-22
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=8 survived=8 killed=0 -->

## Summary

Documentation health for corp-monorepo is mixed: all 8 findings raised across the three verifiers survived the adversarial skeptic stage, yielding a 0% kill-rate (0 of 8 killed as false positives) — meaning every flagged discrepancy was definitively re-verified against git and the filesystem. The root cause is concentrated: a cluster of stale ARCHITECTURE.md claims (last_reviewed 2026-07-12) that predate a wave of 2026-07-17 changes, including the task_manager.py deletion cascade (8ffe8e5), the corp.safety package creation, and the OneDrive-guard centralization (3bc561e/b56a851/4c0aa91), plus several numeric-inventory drifts. One high-severity item (phantom task_manager.py / cli/task.py / `corp task` references), four med items, and three low LOC/count drifts. The journal also carries a persisting med gap: the ARC-4 leg-1 floor-equalization merge (2c48fd5) has no JOURNAL entry. Extensive checked-clean coverage across JOURNAL-vs-git, config/structural claims, and numeric inventories confirms the rest of the docs are accurate, so these survivors are localized drift rather than systemic decay. A 0% skeptic kill-rate here indicates high-signal verifiers rather than lax skepticism, since every finding is backed by a reproducible evidence_command.

## Findings (PROPOSALS ONLY)

### High

- ARCHITECTURE.md (67, 89, 212, 228, 341): five stale references to task_manager.py / cli/task.py / `corp task` CLI persist though commit 8ffe8e5 deleted the module cascade 2026-07-17, five days after the doc's 2026-07-12 last_reviewed.

### Med

- JOURNAL.md: ARC-4 leg-1 universal ruff/pytest floor equalization (07578f6, bee236c, merge 2c48fd5) was merged to main with no JOURNAL entry — only an incidental worktree base-SHA mention at line 19; persisting gap since yesterday's digest.
- ARCHITECTURE.md (219-220, 183-193): corp.safety (tach.toml layer=foundation utility=true, imported by 8 modules, created 2026-07-17) is absent from both the foundation Layer Assignments list and the Module Map Other-Modules table.
- ARCHITECTURE.md (435-458): OneDrive safety-guard section still labels centralization onto corp.safety.onedrive.guard_path as 'future work' though commits 3bc561e/b56a851/4c0aa91 landed 2026-07-17 and all four guard sites now delegate to it.
- ARCHITECTURE.md (86, RESOLVED row 418): actions/ count stated as 12 modules but there are 11 .py files / 9 *_actions.py domain modules — neither reading is 12, off by 3, echoed at line 418.

### Low

- ARCHITECTURE.md:116: extract.py stated at 1184 LOC but wc -l re-confirms 1194 (10-line drift); the line-419 echo is a historical refactor-result and is not itself stale.
- ARCHITECTURE.md:179: database.py stated at 542 LOC but wc -l re-confirms 562 (20-line drift).
- ARCHITECTURE.md:193: cli/ stated at 18 files but ls re-confirms 17 — same root cause as the task_manager finding (cli/task.py deletion 8ffe8e5 dropped the count after the 2026-07-12 stamp).

## Next Actions (proposals for operator)

- Propose removing the five stale task_manager.py / cli/task.py / `corp task` references at ARCHITECTURE.md 67, 89, 212, 228, 341 and restamping last_reviewed, per the 8ffe8e5 deletion cascade (2026-07-17).
- Propose prepending a retroactive ARC-4 leg-1 JOURNAL entry (07578f6, bee236c, merge 2c48fd5) in Did/Result/Changes/Next shape.
- Propose adding the corp.safety foundation package (utility=true) to the foundation Layer Assignments list (219-220) and the Module Map Other-Modules table (183-193).
- Propose rewriting the OneDrive safety-guards section (435-458) to state centralization onto corp.safety.onedrive.guard_path has landed (PR-1/2/3 done), replacing the 'future work' language.
- Propose correcting the actions/ count at line 86 (and RESOLVED row 418) from 12 to the actual figure (11 .py files / 9 domain-suffixed modules).
- Propose updating extract.py at line 116 from 1184 to 1194 LOC.
- Propose updating database.py at line 179 from 542 to 562 LOC.
- Propose updating the cli/ file count at line 193 from 18 to 17.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: 2026-07-19 entry: N1 module-connection-map amendment commits 95e1f0c and b066c4a both exist and match the described §5 in-file amendment mechanism
- V1: 2026-07-19 entry: night-consolidation batch N1/N2/N3 commits 5816b03, 4749dc9, 4bbbf9a all exist, merged via 334da4e, matching claims
- V1: 2026-07-19 entry: BACKLOG #69 (ADR-archival task) added by 4bbbf9a matches claimed wording/refs
- V1: 2026-07-19 E5 #38 terra GREEN (pass 5) merge commit 60b7367 exists and matches
- V1: 2026-07-19 E5 #38 terra pass-4 commit b28db4d (gated column) matches
- V1: 2026-07-19 E5 #38 terra pass-3 commit 363bdd4 (exclude-hard-gate + dims-key-allowlist) matches
- V1: 2026-07-19 E5 #38 terra pass-2 commit 2c1ab27 (forward-slash path normalization) matches
- V1: 2026-07-19 E5 #38 terra pre-merge review commit a406b4c (root-key/type-validation hardening) matches
- V1: 2026-07-19 E5 #38 FR-10 registry: all 5 step commits exist on epic/e5-registry matching claimed breakdown
- V1: 2026-07-19 S13 execution: G4 merge 236de12 relocates exactly 8 old audits + inventory.json into docs/archive/, matching claim
- V1: 2026-07-19 S13 execution: G1 merge 74ef46c deletes exactly the 8 named .html render-twins, matching claim
- V1: 2026-07-19 S13 execution: G2 commit aad2575 deletes exactly 19 conformance digest files, matching claim
- V1: 2026-07-19 S13 SIGNED entry: merge chain and #66/#68 close, #67 retained all match
- V1: All 20 SHAs cited across the last-10 JOURNAL entries exist in git history, well within the non-shallow clone boundary (168 commits, oldest 983cf4a)
- V2: Five CLIs declared in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com — all present and match CLAUDE.md/ARCHITECTURE.md
- V2: config/paths.toml, naming_config.yaml, agents.yaml, workflows.yaml, content_registry.yaml, extractor/*.yaml, project/default.yaml, opportunity/default.yaml, rfp/anonymization.yaml, rfp/product_profiles/ all exist as claimed
- V2: tests/safety/test_vault_writer_invariant.py exists (CLAUDE.md §5 rule 4)
- V2: .pre-commit-config.yaml lists exactly the hooks claimed in CLAUDE.md §9: ruff, tach-check, normalize-headers, floor-hash-verify, canonical_freshness, validate-audit-casing, validate-backlog, backlog-id-on-close, block-ff-push
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 exist
- V2: scripts/surface-conformance.ps1, scripts/session_end_backpressure.py, .claude/check_floor_hash.py exist and .claude/settings.json wires them as claimed
- V2: .claude/CLAUDE-FLOOR.md and its .sha256 sidecar exist
- V2: .claude/skills/gotchas/ exists with SKILL.md
- V2: .claude/commands/ contains exactly one file, override.md, matching CLAUDE.md §7's sole repo-level claim
- V2: corp ADR-14, ADR-23, ADR-27 all exist under docs/decisions/ with matching filenames
- V2: src/corp/ namespace and codemap submodules (cli, ingest, extractor, retrieve, project, opportunity, rfp, ops, schema, extraction) all exist
- V2: .github/workflows/tach.yml exists and runs `tach check`, matching CI claims
- V2: docs/decisions/ADR-26-tach-adoption.md exists, matching CONTRIBUTING.md's reference
- V2: unverifiable-in-clone: CLAUDE.md §7 user-level commands /session-summary, /codex-review
- V2: unverifiable-in-clone: CLAUDE.md §7 plugin commands /review-closures, /ship
- V2: unverifiable-in-clone: CLAUDE.md §8 user-level skill gotchas and built-in/plugin skill 'verify'
- V3: src/corp/ingest/router.py = 893 LOC matches ARCHITECTURE.md claim
- V3: src/corp/ingest/inbox.py = 951 LOC matches ARCHITECTURE.md claim
- V3: config/naming_config.yaml has 22 type_codes entries, matches ARCHITECTURE.md '22 type codes'
- V3: config/naming_config.yaml has 32 client_aliases entries, matches ARCHITECTURE.md '32 client aliases'
- V3: config/agents.yaml has 6 top-level agents, matches ARCHITECTURE.md '6 agents'
- V3: pyproject.toml [project.scripts] lists exactly 5 CLIs, matches ARCHITECTURE.md/CLAUDE.md
- V3: src/corp/ops/database.py instantiates exactly 5 repo classes, matches ARCHITECTURE.md 'OpsDB delegates to 5 repos'
- V3: corp CLI has 43 leaf Click commands, consistent with ARCHITECTURE.md 'corp (main CLI -- 40+ commands)'
- V3: unverifiable-in-clone: notes count (488 notes) requires index.db, not committed to the repo

