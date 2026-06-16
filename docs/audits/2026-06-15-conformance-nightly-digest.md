# corp-monorepo — Nightly Conformance Digest (2026-06-15)

- **Date:** 2026-06-15
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=8 survived=6 killed=2 -->

## Summary

Documentation health is solid: 8 raw findings, 6 survived adversarial skepticism (25% kill-rate). The killed items were a non-violation (JOURNAL append ordering is unconstrained by CLAUDE.md §6) and a non-definitive count dispute (actions/ is 12 incl. __init__, already adjudicated). Survivors split into two clusters: JOURNAL.md completeness/format gaps (three undocumented merge sessions on 2026-06-03 and 2026-06-06, plus one pre-cutover entry missing ADR-49 fields) and living-doc accuracy drift (dev-check.ps1 step description, the ruff-format pre-commit overstatement, and a dangling audit-file reference). No high-severity issues; survivors are 3 medium and 3 low. Extensive structural, path, CLI, hook, and numeric-inventory checks all came back clean, so the issues are narrow documentation-conformance gaps rather than systemic decay.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- JOURNAL.md omits the 2026-06-03 chore/dev-check-gotcha session (merge de5cb53, +7 to gotchas.md) — grep returns 0 mentions across June 3 entries.
- JOURNAL.md omits two 2026-06-06 sessions: chore/gh-auth-check (merge 0ef1fcd, gh auth gate) and docs/gotchas-2026-06-06 (merge fc31ab9, +17 to gotchas.md) — grep returns 0.
- ARCHITECTURE.md:577 describes dev-check.ps1 as pytest + pre-commit run --all-files + tach check, but the script runs ruff format/lint --fix, run-all-tests.ps1, and integration tests — no pre-commit or tach calls.

### Low

- JOURNAL.md:45-46 2026-06-04 entry uses pre-cutover combined Did/Result: bullet, missing mandatory ADR-49 Changes/Abandoned/Next fields.
- CLAUDE.md:114 §9 lists ruff — linting and formatting as a pre-commit hook, but .pre-commit-config.yaml omits ruff-format (CRLF/LF conflict); only linting is hooked.
- ARCHITECTURE.md:548 cites docs/audits/2026-04-21-p1-verification.md as existing, but the file is absent (only codex-hotfix-review.md exists).

## Next Actions (proposals for operator)

- Add a JOURNAL.md catch-up entry for the 2026-06-03 chore/dev-check-gotcha session (+7 lines to .claude/skills/gotchas/gotchas.md).
- Add JOURNAL.md catch-up entries for the two 2026-06-06 sessions (gh auth gate in surface-conformance.ps1; harness/shell gotchas capture).
- Update ARCHITECTURE.md:577 to describe dev-check.ps1 real steps (ruff format, ruff check --fix, run-all-tests.ps1, integration pytest).
- Flag JOURNAL.md:45-46 as a known pre-cutover format deviation; enforce ADR-49 Did/Result/Changes/Abandoned/Next shape going forward (backfill forbidden).
- Change CLAUDE.md §9 hook bullet to: ruff — linting (formatting omitted from pre-commit; run via dev-check.ps1).
- Fix dangling reference at ARCHITECTURE.md:548 — point to 2026-04-21-codex-hotfix-review.md or remove citation.

## Killed Findings

- The 2026-06-04 graphify pilot JOURNAL entry (line 459) was appended to the file bottom rather than near the other June 4 entries, creating out-of-order date sequencing. — _style_
- actions/ package has 11 domain modules, not the 12 claimed at ARCHITECTURE.md:160 and :513. — _evidence-not-definitive_

## Checked-and-clean (so absence is informative)

- JOURNAL vs git: all major sessions (2026-06-02 through 2026-06-06) corroborated by git — coherence cleanup, ecosystem unification, ruff drift, stale branches, ADR-71 hooks, ARCHITECTURE.md count refresh, conformance baseline, CLAUDE.md audit (#75), triage ratification all confirmed
- JOURNAL vs git: nightly digests 2026-06-07 through 2026-06-14 are automated 0-survivor outputs; no manual entries required
- Unverifiable-in-clone (not flagged): ADR-72, secrets CLEAN sweep, runtime test-suite counts
- PATHS: all key paths verified present — config/paths.toml, src/corp/ namespace and subpackages, safety test invariant, scripts, naming_config.yaml, tach.toml, docs/decisions, VISION.md, JOURNAL.md, all diagrams, all action/extractor subdirs
- COMMANDS: all 5 CLIs declared in pyproject.toml with resolving entry points
- HOOKS/CI: ruff and tach-check hooks in .pre-commit-config.yaml; tach.yml CI workflow; 4-layer tach.toml confirmed
- NAMES: corp ADR-14, ADR-23, ADR-27 in docs/decisions/; repo-level commands/ absent as documented
- Unverifiable-in-clone: user-level ~/.claude, ~/.codex, ../.dev-knowledge paths
- NUMERIC: extract.py=1184, router.py=893, inbox.py=951, database.py=542 LOC all match ARCHITECTURE.md
- NUMERIC: cli/ files=18, type_codes=22, client_aliases=32, agents=6, CLIs=5, OpsDB repos=5 all match
- Unverifiable-in-clone: notes count (index.db absent)

