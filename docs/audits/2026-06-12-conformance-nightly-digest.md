# corp-monorepo — Nightly Conformance Digest (2026-06-12)

- **Date:** 2026-06-12
- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)
- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)
- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72).
- **Execution path:** spec-orchestration

<!-- counts: raw=4 survived=3 killed=1 -->

## Summary

Documentation health is strong overall: 35 verifier checks passed clean across JOURNAL/git corroboration, living-doc structural claims, and deterministic numeric-inventory drift, with every spot-checked LOC count, module count, config tally, and CLI inventory matching ARCHITECTURE.md exactly. Of 4 raw findings, 3 survived adversarial skeptic review and 1 was killed (25% kill rate) — the killed item misread a documented forward-reference (planned corp/safety/onedrive.py, explicitly deferred to a three-PR plan in ADR-27) as an existing-state contradiction. Survivors are a genuine JOURNAL omission of 2026-06-06 merged work, a dangling present-tense reference to a nonexistent p1-verification audit file cited in two living docs, and an unsupported '40+ commands' header over a 28-row table. No high-severity issues; all survivors are deterministic and in-clone verifiable.

## Findings (PROPOSALS ONLY)

### High

_No high-severity findings._

### Med

- JOURNAL.md omits the 2026-06-06 13:53-14:08 merged work (gotchas update + gh-auth-gate feature, commits fc31ab9/0ef1fcd/116feea) despite the repo's sole-change-record contract (CLAUDE.md §6).
- ARCHITECTURE.md:548 and ADR-27:179 reference docs/audits/2026-04-21-p1-verification.md as present-tense existing evidence, but the file does not exist (companion 2026-04-21-codex-hotfix-review.md does).

### Low

- ARCHITECTURE.md:407 'corp (main CLI — 40+ commands)' header overstates the table, which lists 28 rows (~37-39 even with multi-verb commands expanded).

## Next Actions (proposals for operator)

- Append a JOURNAL.md entry recording the docs/gotchas-2026-06-06 sections and the surface-conformance.ps1 gh auth gate (commit 116feea) per CLAUDE.md §6 'Changes: is the sole change record'.
- Resolve the dangling p1-verification reference: either create docs/audits/2026-04-21-p1-verification.md or correct ARCHITECTURE.md:548 and ADR-27:179 to point at the existing 2026-04-21-codex-hotfix-review.md.
- Adjust ARCHITECTURE.md:407 header to match the actual inventory (e.g. '~28 commands' for table rows, or state the expanded subcommand count explicitly) so the '40+' claim is supported.

## Killed Findings

- corp/safety/onedrive.py exists as centralized OneDrive guard implementation per ADR-27 (file does not exist -> contradiction) — _documented-decision_

## Checked-and-clean (so absence is informative)

- V1: 2026-06-06 Triage ratification JOURNAL entry corroborated (commits d5999cb/25398a0 match)
- V1: 2026-06-06 Nightly conformance routine JOURNAL entry corroborated (commit 34a2a9a + artifacts all exist)
- V1: 2026-06-06 Remote bookkeeping JOURNAL entry corroborated (commits 41d5189/d8d129e match, BACKLOG #13 added)
- V1: 2026-06-06 CLAUDE.md #75 deep-audit JOURNAL entry corroborated (commits aca2c95/b98a115, retry wrapper in manifest.py confirmed)
- V1: 2026-06-04 ARCHITECTURE.md count refresh JOURNAL entry corroborated (commit 96db96b, all 6 count drifts fixed)
- V1: 2026-06-04 Conformance baseline JOURNAL entry corroborated (commit 1aa97c4, digest file exists)
- V1: 2026-06-03 Track ruff drift JOURNAL entry corroborated (commit 48a565e, BACKLOG #12 added)
- V1: JOURNAL entries 8-10 (2026-06-02/03) predate visible git history boundary — out-of-scope per shallow-history guard
- V1: Nightly digest commits (c9fea97 through 4a54f77) are automated routine outputs — no JOURNAL entry expected
- V2: 5 CLIs in pyproject.toml [project.scripts] (corp, corp-meta, cke, cpe, com) — verified
- V2: scripts/run-all-tests.ps1 and scripts/dev-check.ps1 exist — verified
- V2: .pre-commit-config.yaml contains ruff hook and tach-check hook — verified
- V2: tests/safety/test_vault_writer_invariant.py exists — verified
- V2: config/paths.toml and config/naming_config.yaml exist — verified
- V2: .claude/commands/ absent — consistent with CLAUDE.md §7 'none currently'
- V2: docs/decisions/ADR-14, ADR-23, ADR-27 all exist — verified
- V2: docs/diagrams/system-context.svg, container-module.svg, magistrala-pipeline.svg all exist
- V2: tach.toml exists at repo root
- V2: src/corp/ unified namespace with all 12 subpackages present
- V2: docs/audits/2026-04-21-codex-hotfix-review.md exists (companion to the missing p1-verification)
- V2: OneDrive safety guards currently distributed as documented — inline-guard state is intentional per ADR-27
- V2: unverifiable-in-clone: ~/.claude/commands user-level slash commands (not in this clone)
- V2: unverifiable-in-clone: ~/.claude/skills user-level skills (not in this clone)
- V3: wc -l src/corp/extractor/extract.py = 1184 (ARCHITECTURE.md claims 1184 LOC) — MATCH
- V3: wc -l src/corp/ingest/inbox.py = 951 (ARCHITECTURE.md claims 951 LOC) — MATCH
- V3: wc -l src/corp/ops/database.py = 542 (ARCHITECTURE.md claims 542 LOC) — MATCH
- V3: wc -l src/corp/ingest/router.py = 893 (ARCHITECTURE.md claims 893 LOC) — MATCH
- V3: ls src/corp/actions/*.py | wc -l = 12 (ARCHITECTURE.md claims 12 modules) — MATCH
- V3: ls src/corp/cli/*.py | wc -l = 18 (ARCHITECTURE.md claims 18 files) — MATCH
- V3: config/naming_config.yaml type_codes = 22 (ARCHITECTURE.md claims 22) — MATCH
- V3: config/naming_config.yaml client_aliases = 32 (ARCHITECTURE.md claims 32) — MATCH
- V3: config/agents.yaml has 6 agents (ARCHITECTURE.md claims 6) — MATCH
- V3: pyproject.toml [project.scripts] has 5 CLIs (ARCHITECTURE.md claims 5) — MATCH
- V3: ops/database.py OpsDB delegates to 5 repos (AssetRepo, PackageRepo, EventRepo, RoutingRepo, SuggestionRepo) — MATCH
- V3: unverifiable-in-clone: notes count (488, live 2026-06-04) — index.db not committed to repo

