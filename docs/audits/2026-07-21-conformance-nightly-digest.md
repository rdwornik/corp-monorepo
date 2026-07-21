# corp-monorepo — Nightly Conformance Digest (2026-07-21)

- **Date:** 2026-07-21
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=8 survived=8 killed=0 -->

## Summary

Overall documentation health is solid but showing measurable post-review drift. Of 8 raw findings, all 8 survived adversarial skepticism and 0 were killed as false positives — a 0% skeptic kill-rate, indicating the verifiers produced clean, well-evidenced signal with no noise this pass. The single high-severity issue and two of the low-severity count issues all trace to one root cause: the signed Arc-B Batch-4 deletion of cli/task.py (commit 8ffe8e5, 2026-07-17), which postdates ARCHITECTURE.md's last_reviewed stamp of 2026-07-12 — the doc was correct when reviewed and has drifted since. The remaining findings are a genuine journal gap (an entire ARC-4 merge, including a --no-verify gate bypass, went unlogged), two never-existent dangling references (root README.md, a mis-cited audit file), a repeated wrong module count (12 vs 9), and routine LOC drift on two files edited after the review stamp. The extensive checked-clean set — every 2026-07-19 JOURNAL entry, the full living-doc structural inventory, and most numeric figures — confirms the drift is localized rather than systemic.

## Findings (PROPOSALS ONLY)

### High

- ARCHITECTURE.md:341 — CLI Reference table lists `corp task add/list/done` (handled by `cli/task.py`), but that file was deleted in commit 8ffe8e5 and no task command group is registered; row is stale.

### Med

- JOURNAL.md — ARC-4 leg 1 (universal ruff/pytest floor equalization, merge 2c48fd5, incl. a self-declared --no-verify freshness-gate bypass) is entirely absent from the session log.
- ARCHITECTURE.md:86 (restated at :418) — `actions/` claimed as "12 modules"; actual is 9 domain modules (11 total .py files), wrong figure repeated twice.
- VISION.md:149 — References section cites a repo-root README.md that has never existed (zero git history).

### Low

- ARCHITECTURE.md:454 — OneDrive safety-guards section cites docs/audits/2026-04-21-p1-verification.md, which does not exist; the real file is 2026-04-21-codex-hotfix-review.md.
- ARCHITECTURE.md:179 — database.py OpsDB LOC listed as 542; actual is 562 (modified post-review by 380ebfd, b28db4d).
- ARCHITECTURE.md:193 — cli/ file count listed as 18; actual is 17 after the cli/task.py deletion (8ffe8e5).
- ARCHITECTURE.md:116 — extract.py LOC listed as 1184; actual is 1194 (modified post-review by 7d9cfb2, 40d8fec).

## Next Actions (proposals for operator)

- Re-stamp and reconcile ARCHITECTURE.md against 8ffe8e5: remove/annotate the corp task add/list/done CLI Reference row (:341), correct the cli/ file count 18→17 (:193), then refresh last_reviewed so future drift is measured from a clean baseline.
- Backfill the JOURNAL.md gap: prepend a retroactive ARC-4 leg-1 entry (07578f6, bee236c, merge 2c48fd5) in the ADR-49 Did/Result/Changes/Abandoned/Next shape, explicitly recording the deliberate --no-verify bypass of canonical_freshness.
- Fix the module count in both places: update ARCHITECTURE.md :86 and :418 from '12 modules' to 9 domain action modules (11 total .py incl. __init__.py and _helpers.py).
- Resolve the two dangling references: remove the README.md bullet from VISION.md :149 (or create the root README if intended); repoint ARCHITECTURE.md :454 to docs/audits/2026-04-21-codex-hotfix-review.md.
- Refresh the three post-review LOC figures: database.py 542→562 (:179), extract.py 1184→1194 (:116) — bundle with proposal 1's re-stamp so the numeric inventory matches HEAD.

## Killed Findings

_No findings killed this run._

## Checked-and-clean (so absence is informative)

- V1: All 10 most-recent JOURNAL.md entries (2026-07-19 module-connection-map through S13-manifest-SIGNED) corroborated against git history — commits, merges, and cited files all exist as described.
- V2: 5 CLIs (corp, corp-meta, cke, cpe, com) declared in pyproject.toml [project.scripts], matching CLAUDE.md §2/§3 and ARCHITECTURE.md.
- V2: src/corp/ unified namespace and all named submodules present.
- V2: tests/safety/test_vault_writer_invariant.py present (CLAUDE.md §5 rule 4).
- V2: All cited config/ paths present (paths.toml, agents.yaml, workflows.yaml, content_registry.yaml, naming_config.yaml, etc.).
- V2: .pre-commit-config.yaml roster exactly matches CLAUDE.md §9; .claude/settings.json hooks match §9 'Other'; enabledPlugins includes tier1-lifecycle@dev-knowledge-methodology.
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 present; .claude/commands/ contains exactly override.md (§7).
- V2: ADRs present — corp ADR-14/23/27; local ADR-16/22/26/32/38; docs/decisions/README.md.
- V2: tach.toml, src/corp/safety/onedrive.py, src/corp/cleanup/errors.py, docs/audits/2026-04-21-codex-hotfix-review.md, docs/archive/2026-04-15-tach-baseline-violations.md all present.
- V2: cli/*.py handlers exist for every CLI Reference row except cli/task.py (see HIGH finding); docs/diagrams/ correctly absent per header note.
- V2: unverifiable-in-clone — user-level slash commands, skills, ~/.claude/settings.json hooks, .dev-knowledge hub paths, routing_map.yaml (external MyWork-root runtime config).
- V3: ingest/router.py 893 LOC; ingest/inbox.py 951 LOC; 6 agents; naming_config 22 type codes / 32 client aliases; CLAUDE.md 5 CLIs; OpsDB delegates to 5 repos; historical/struck RESOLVED-row numbers correctly excluded — all match live values.

