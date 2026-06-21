# corp-monorepo — Nightly Conformance Digest (2026-06-21)

- **Date:** 2026-06-21
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=5 survived=4 killed=1 -->

## Summary

Documentation health is strong overall: of 5 raw findings, 4 survived adversarial skepticism and 1 was killed as a false positive (skeptic kill-rate 20%, or 1/5). No high-severity findings exist; the survivors are 3 medium/low JOURNAL conformance gaps and 1 low living-doc inaccuracy. The journal findings cluster on a single recurring pattern — gotcha-capture and follow-up commits on 2026-06-03 and 2026-06-06 that were never recorded in any Changes: line, violating ADR-49's 'sole change record' rule and CLAUDE.md section 6. The one living-docs finding is a cosmetic doc-vs-config contradiction about ruff-format in pre-commit. Extensive verification came back clean: all 2026-06-16 audit-tool artifacts, the nightly-conformance build files, every claimed file path and CLI declaration, both pre-commit hooks, the ADR-14/23/27 files, and all numeric inventory claims in ARCHITECTURE.md (LOC counts, module/CLI/agent counts) matched. The killed finding (graphify-pilot entry placement) was correctly discarded because the entry obeyed the literally written 'Append-only' instruction and no newest-at-top ordering rule is documented anywhere.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- 2026-06-06 docs(gotchas) commit d0989ee (here-string + Bash-tool harness gotchas, branch docs/gotchas-2026-06-06, merge fc31ab9) has no JOURNAL entry and appears in no Changes: line.
- 2026-06-06 feat(surface) commit 116feea (gh auth gate in surface-conformance.ps1, branch chore/gh-auth-check, merge 0ef1fcd) has no JOURNAL entry and appears in no Changes: line.

### Low

- 2026-06-03 docs(gotchas) commit 9477a1d (dev-check.ps1 tree-mutation gotcha, branch chore/dev-check-gotcha, merge de5cb53) unjournaled; ruff-drift entry Changes: (JOURNAL line 65) omits gotchas.md.
- CLAUDE.md section 4 (line 48) and section 9 (line 114) imply ruff-format runs in pre-commit, but .pre-commit-config.yaml explicitly omits ruff-format (only lint/--fix ruff hook runs).

## Next Actions (proposals for operator)

- Add a 2026-06-06 JOURNAL entry for gotchas.md harness/shell capture (commit d0989ee, branch docs/gotchas-2026-06-06) with its Changes: line.
- Add a 2026-06-06 JOURNAL entry for the gh-auth gate edit to surface-conformance.ps1 (commit 116feea, branch chore/gh-auth-check) with its Changes: line.
- Append gotchas.md (branch chore/dev-check-gotcha, commit 9477a1d) to the Changes: line of the 2026-06-03 ruff-drift entry, or add a dedicated entry.
- Reword CLAUDE.md section 4/section 9 to clarify ruff runs lint/--fix only in pre-commit; ruff-format runs via dev-check.ps1.

## Killed Findings

- 2026-06-04 graphify pilot JOURNAL entry (commit df22f8f) was appended to the bottom (line 466) instead of prepended at top with the other 2026-06-04 entries, making it invisible to the 'read last 5 entries from top' protocol. — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: All 2026-06-16 audit-tool artifacts present and verified.
- V1: 2026-06-06 triage-ratification SHAs 13fea1e / a7a161e / 4b46709 all present.
- V1: 2026-06-06 nightly-conformance build files all present (conformance-corp.js, render_conformance_digest.py, nightly-conformance-triage.yml, surface-conformance.ps1, test_nightly_triage_parser.py).
- V1: manifest.py retry wrapper and test_manifest.py retry test verified.
- V1: 2026-06-04 ARCHITECTURE.md count refresh and conformance-baseline-digest verified.
- V1: 2026-06-03 BACKLOG items #10/#11/#12, ADR-71 TOC hook stanza verified.
- V1: Nightly conformance digests 2026-06-07 through 2026-06-20 (13) all present — no JOURNAL entry required by design.
- V2: All claimed paths present (src/corp/, config/paths.toml, config/naming_config.yaml, test_vault_writer_invariant.py, .pre-commit-config.yaml, run-all-tests.ps1, dev-check.ps1).
- V2: All 5 CLIs declared in pyproject.toml; .claude/commands/ absent per CLAUDE.md §7.
- V2: tach-check and ruff hooks both present in .pre-commit-config.yaml.
- V2: corp ADR-14/23/27 files present; 4-layer dependency model in tach.toml.
- V3: All ARCHITECTURE.md numeric claims match live repo: extract.py=1184, router.py=893, inbox.py=951, database.py=542, actions=12, cli=18, type_codes=22, client_aliases=32, CLIs=5, OpsDB repos=5, agents=6.
- Unverifiable-in-clone: GitHub issue state, user-level ~/.claude/, index.db notes count.
- Killed false positive: graphify-pilot entry bottom-placement obeyed CLAUDE.md 'Append-only'; no ordering rule documented.

