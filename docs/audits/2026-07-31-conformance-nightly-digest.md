# corp-monorepo — Nightly Conformance Digest (2026-07-31)

- **Date:** 2026-07-31
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** native

<!-- counts: raw=8 survived=7 killed=1 -->

## Summary

Documentation health is broadly sound: of 8 raw findings, 7 survived the adversarial skeptic (kill-rate 1/8, ~12.5%) and the sole kill was a correctly-rejected false positive (the logs/TOKEN-LOG.md append-only rule protects a gitignored, out-of-clone operational log, so its absence proves no violation). No high-severity issues surfaced. The one medium is a genuine §6 session-end omission — the entire 2026-07-20..07-29 JOURNAL span is unrecorded despite a real 4-file methodology merge on 2026-07-29. The remaining six lows are low-risk drift: one unjournaled ARC-4 sub-merge, one dangling ARCHITECTURE.md audit cross-reference to a file that never existed, and four deterministic numeric-inventory mismatches (two count off-by-ones, a stale removed-CLI row, and two LOC parentheticals). Extensive structural and inventory checks (JOURNAL-vs-git for all 10 entries, all 9 pre-commit hooks, 5 CLIs, ADR files, config/tree presence, and several exact LOC/count matches) came back clean, so the surviving findings are well-scoped rather than symptomatic of widespread rot.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- journal: 2026-07-29 vscode-w1-visibility methodology merge (ec276e5/65a8a35, 4 corp-local files) has no JOURNAL entry — the entire 2026-07-20..07-29 span is unjournaled (newest entry is 2026-07-19)

### Low

- journal: ARC-4 leg-1 ruff/pytest floor merge (2c48fd5, 2026-07-18, pyproject.toml) is absent from JOURNAL.md and not folded into the same-night 'Night consolidation batch' entry (lists only N1/N2/N3)
- living-docs: ARCHITECTURE.md:454 cites docs/audits/2026-04-21-p1-verification.md as documenting Verified P1 findings, but that file never existed in repo history (only 2026-04-21-codex-hotfix-review.md exists)
- counts: ARCHITECTURE.md:193 says cli/ has '18 files' (actual 17) and :341 documents 'corp task' / cli/task.py, a module removed in the #22 task-manager cascade kill
- counts: ARCHITECTURE.md:86 says actions/ has '12 modules'; the package has 11 .py files and no subpackages
- counts: ARCHITECTURE.md:179 annotates database.py as '542 LOC'; actual is 562 (+20 drift)
- counts: ARCHITECTURE.md:116 annotates extract.py as '1184 LOC'; actual is 1194 (+10 drift)

## Next Actions (proposals for operator)

- Prepend a 2026-07-29 JOURNAL entry (Did/Result/Changes/Next) recording the chore/vscode-w1-visibility methodology merge, restoring §6 session-end coverage for the 07-20..07-29 span (proposal for operator; no action taken)
- Record the ARC-4 leg-1 pyproject.toml ruff/pytest floor merge in the 2026-07-18 JOURNAL Changes line (or confirm it was journaled hub-side as a fleet-floor propagation)
- Repoint ARCHITECTURE.md:454 to the extant 2026-04-21-codex-hotfix-review.md, or add the missing p1-verification audit
- Update ARCHITECTURE.md cli/ count 18->17 and drop the stale 'corp task' / cli/task.py CLI Reference row (killed under #22)
- Correct ARCHITECTURE.md:86 actions/ '12 modules' -> 11
- Refresh the LOC parentheticals: database.py 542->562 (:179), extract.py 1184->1194 (:116)

## Killed Findings

- logs/TOKEN-LOG.md append-only rule (CLAUDE.md:79/:188) is contradicted because the file/dir does not exist in the repo — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- JOURNAL vs git: all 10 existing JOURNAL entries verified against git — module connection map (95e1f0c, b066c4a, merge 1dfee3e), night consolidation batch (4749dc9/N2, 4bbbf9a/N3, 5816b03/N1, merge 334da4e), E5 #38 terra GREEN pass 5 (merge 60b7367, anchor db48093), terra re-reviews #4/#3/#2 (b28db4d, 363bdd4, 2c1ab27), terra pre-merge review (a406b4c), FR-10 source registry 5-step (eaafda7, 989811e, d3e8094, cf36bac, 380ebfd), S13 archival G4/G1/G2 (236de12, 74ef46c, aad2575/af02a0c), S13 manifest SIGNED (59f29d8, 26876a0)
- Nightly conformance digest commits (abed866..b76d1d2, #36-#44) and integration merge c954876 correctly identified as automated workflow runs, not expected manual JOURNAL entries
- Structural presence: config/paths.toml, src/corp/ namespace, tests/safety/test_vault_writer_invariant.py, tach.toml, VISION.md, BACKLOG.md, JOURNAL.md, LESSONS.md, .methodology.yaml (root), src/corp/safety/onedrive.py all present
- All 9 named pre-commit hooks present in .pre-commit-config.yaml: ruff, tach-check, normalize-headers, floor-hash-verify, canonical_freshness, validate-audit-casing, validate-backlog, backlog-id-on-close, block-ff-push
- 5 CLIs in pyproject.toml [project.scripts]: corp, corp-meta, cke, cpe, com
- Hook scripts and commands present: scripts/run-all-tests.ps1, scripts/dev-check.ps1, scripts/surface-conformance.ps1, scripts/session_end_backpressure.py, .claude/check_floor_hash.py, .claude/commands/override.md, .claude/skills/gotchas/, .claude/settings.json (SessionStart+Stop matching s9)
- ADR files present: docs/decisions/README.md, ADR-14 (naming-convention-v2), ADR-23 (monorepo-internal-architecture), ADR-27 (safety-invariants); docs/audits/2026-04-21-codex-hotfix-review.md exists
- Config presence: config/naming_config.yaml, config/agents.yaml, config/extractor/, config/rfp/, config/workflows.yaml, config/content_registry.yaml
- Exact numeric matches (no drift): router.py=893 LOC, inbox.py=951 LOC, type_codes=22, client_aliases=32, agents=6 (com, cpe, cke, schema, ai-council, rfp), CLIs=5, OpsDB delegates to 5 repos (Asset/Package/Event/Routing/Suggestion)
- Correctly scoped out as unverifiable-in-clone: user-level ~/.claude/ commands/skills/settings, and notes count (488, index.db gitignored)

