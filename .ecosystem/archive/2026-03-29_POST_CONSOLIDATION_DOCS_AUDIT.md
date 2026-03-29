# Post-Consolidation Documentation Audit — 2026-03-29

## Summary

- **Files audited:** 47 (root docs, config, scripts, decisions, gotchas, archive, workspace)
- **Critical stale references found:** 34 (scattered across 12 files)
- **Missing documentation:** 2 key docs (CONTRIBUTING.md, CHANGELOG.md) + 13 module READMEs
- **Discrepancies:** Count mismatches in MASTER_HANDOFF.md and decisions/README.md
- **Status:** Post-consolidation (6 packages → `src/corp/`, completed 2026-03-29, 2,404 tests passing)

---

## Root Docs

| File | Status | Issues |
|------|--------|--------|
| `CLAUDE.md` | **MOSTLY CURRENT** | Shows 7 of 13 src/corp/ subdirs; missing `cli/`, `ops/`, `overnight/`, etc. Not critical but incomplete. |
| `README.md` | **CRITICAL STALE** | Lines 5–35: Old `packages/` table, 6 separate `pip install -e packages/...` commands, stale test count (2,153 → actual 2,404). Should describe unified `pip install -e .` and single src/corp/ namespace. |
| `JOURNAL.md` | **CURRENT** | Last 5 entries accurately describe 2026-03-29 consolidation. 2,404 tests, no stale refs. |
| `pyproject.toml` | **CURRENT** | Single unified root pyproject, all 5 CLI entry points defined, `where = ["src"]` discovery. No stale refs. |
| `.gitignore` | **MINOR STALE** | Line 34: `packages/corp-knowledge-extractor/_outputs/` — dead code, packages/ dir no longer exists. Benign but stale. |
| `.env.example` | **STALE** | Line 9: `CKE_PATH=./packages/corp-knowledge-extractor` — old path. Should be `./src/corp/extractor` or removed (CKE on PATH after `pip install -e .`). |

---

## MASTER_HANDOFF.md

**Status:** MOSTLY CURRENT with count errors

| Issue | Location | Severity |
|-------|----------|----------|
| "All 22 Council Decisions" header | Line 164 | HIGH — table lists 23 entries |
| "37 gotchas" | Line 446 | HIGH — actual count is 41 |
| ADR count "23" in stats table | Line 25 | OK — already correct |

---

## Config Files

| File | Status | Issues |
|------|--------|--------|
| `config/paths.toml` | **CURRENT** | Forward slashes, `%LOCALAPPDATA%/corp-by-os/`, no packages/ refs |
| `config/agents.yaml` | **CURRENT** (likely) | Not read; file exists |
| `config/workflows.yaml` | **CURRENT** (likely) | Not read; file exists |

---

## Scripts

| Script | Status | Issues |
|--------|--------|--------|
| `run-all-tests.ps1` | **CRITICAL STALE** | Lines 10–17: Hardcoded loop over `packages/corp-os-meta`, `packages/corp-knowledge-extractor`, etc. — all non-existent. Script is **broken**. Fix: replace with single `pytest tests/ -x --tb=short`. |
| `dev-check.ps1` | **STALE** | Lines 10, 14: `ruff format "$root/packages/"` and `ruff check "$root/packages/" --fix` — finds no files. Linting silently skipped. Fix: change to `$root/src/`. |
| `update_handoff.py` | **CURRENT** | No hardcoded paths; all derived via `Path(__file__).parent.parent`. |
| Other scripts (29) | **CURRENT** | Spot-check: no `packages/` refs found in py/ps1 scripts outside of above. |

---

## Gotchas (gotchas.md)

**Status:** STALE verify paths

- **Total gotchas:** 41 (not 37 as stated in MASTER_HANDOFF.md)
- **Stale verify paths:** 21 occurrences

Examples:
```
Line 14:  verify: Grep("get_client_variants", path="packages/corp-by-os/src/")
Line 72:  verify: Grep("_check_dedup", path="packages/corp-by-os/src/corp_by_os/ingest/inbox.py")
Line 79:  verify: Grep("destination", path="packages/corp-by-os/src/corp_by_os/ingest/inbox.py")
```

**Path replacements needed (21 occurrences total):**
- `packages/corp-by-os/src/` → `src/corp/`
- `packages/corp-knowledge-extractor/` → `src/corp/extractor/`
- `packages/corp-os-meta/` → `src/corp/schema/`
- `packages/corp-project-extractor/` → `src/corp/project/`
- `packages/corp-rfp-agent/` → `src/corp/rfp/`
- `packages/corp-opportunity-manager/` → `src/corp/opportunity/`

Non-executable (verify comments only), so not runtime-breaking. But confusing for anyone using them as guidance.

---

## Decisions/ADRs

**Count:** 23 ADR files (ADR-01 through ADR-23) + decisions/README.md = 24 files total.

| Issue | Location | Severity |
|-------|----------|----------|
| Stale path in ADR text | `ADR-14`, line 14: `` `packages/corp-by-os/config/naming_config.yaml` `` → should be `` `config/naming_config.yaml` `` | HIGH |
| Count in decisions/README.md | Line 30: header says "22" but table lists 23 entries | MEDIUM |

ADRs are historical — the stale path in ADR-14 is the only content error worth noting.

---

## Workspace File (corp-monorepo.code-workspace)

**Status:** CURRENT
- Untracked in git (`??` in status) — by design
- References `./src` in Python path config
- All launch configs reference `corp.cli` module (unified namespace)
- No stale `packages/` references

---

## Archive (.ecosystem/archive/)

**Status:** COMPLETE (22 files, all properly dated)
- All follow `YYYY-MM-DD_TYPE_description.md` naming convention
- Latest: `2026-03-29_FLATTEN_BLAST_RADIUS.md` — justifies consolidation
- No actionable items left; archive is well-organized

**Candidate for archiving (currently in docs/):**
- `docs/2026-03-24_PHASE1_REPORT.md` — stale paths throughout
- `docs/2026-03-24_PHASE2_REPORT.md` — stale paths throughout
- `docs/2026-03-25_PHASE3_REPORT.md` — stale paths throughout

These are historical phase reports; should move to `.ecosystem/archive/`.

---

## Missing Documentation

| Doc | Should Exist? | Status | Impact |
|-----|---------------|--------|--------|
| `CONTRIBUTING.md` | **YES** | MISSING | Onboarding friction; no guidance on PR process, branch naming, commit style |
| `CHANGELOG.md` | **YES** | MISSING | Version history undocumented; consolidation milestone not recorded |
| `tasks/` directory | NO | — | Current pattern: JOURNAL.md is the task tracker |
| `BACKLOG.md` | NO | — | Open decisions tracked in decisions/; no separate backlog needed |
| Module READMEs (`src/corp/*/README.md`) | **YES** | 0 of 13 exist | Developer friction: no per-module orientation docs |

---

## Stale References: Summary Table

| Severity | Location | Ref Type | Count | Fix Effort |
|----------|----------|----------|-------|------------|
| CRITICAL | `run-all-tests.ps1`, `dev-check.ps1` | `packages/` path | 4 | 5 min |
| HIGH | `README.md` lines 5–35 | Old structure doc | 1 block | 20 min |
| HIGH | `gotchas.md` verify lines | `packages/` path | 21 | 10 min (bulk replace) |
| HIGH | `ADR-14` line 14 | `packages/` path | 1 | 2 min |
| HIGH | `MASTER_HANDOFF.md` counts | 22→23, 37→41 | 2 | 2 min |
| MEDIUM | `decisions/README.md` count | "22" header | 1 | 1 min |
| MEDIUM | `.env.example` line 9 | `packages/` path | 1 | 2 min |
| MEDIUM | `.gitignore` line 34 | Dead pattern | 1 | 1 min |
| MEDIUM | `docs/*.md` (3 files) | Historic, stale paths | 3 files | 5 min (archive) |

**Total: 34 stale references across 12 files**

---

## Recommended Actions (priority order)

### TIER 1 — CRITICAL (Breaks core workflows)

1. **Fix `run-all-tests.ps1`**
   Replace the `$packages = @(...)` loop with: `pytest tests/ -x --tb=short`

2. **Fix `dev-check.ps1`**
   - Line 10: `ruff format "$root/packages/"` → `ruff format "$root/src/"`
   - Line 14: `ruff check "$root/packages/" --fix` → `ruff check "$root/src/" --fix"`

3. **Rewrite README.md**
   Replace old "Packages" table and 6-install instructions with:
   - Single `pip install -e .` install
   - src/corp/ module map
   - Current test count (2,404) and CLI entry points

### TIER 2 — HIGH (Causes confusion)

4. **Update MASTER_HANDOFF.md**
   - Line 164: "All 22 Council Decisions" → "All 23 Council Decisions"
   - Line 446: "37 gotchas" → "41 gotchas"

5. **Bulk-replace gotchas.md verify paths** (21 occurrences)
   All `packages/X/src/` → equivalent `src/corp/` paths

6. **Fix ADR-14 line 14**
   `` `packages/corp-by-os/config/naming_config.yaml` `` → `` `config/naming_config.yaml` ``

7. **Fix decisions/README.md**
   Update count header from "22" to "23"

### TIER 3 — MEDIUM (Onboarding friction)

8. Fix `.env.example` line 9: update or comment out stale `CKE_PATH`
9. Remove dead `.gitignore` line 34 (`packages/corp-knowledge-extractor/_outputs/`)
10. Move `docs/2026-03-24_PHASE*.md` to `.ecosystem/archive/`
11. Create `CONTRIBUTING.md` (PR process, branch naming, testing)
12. Create `CHANGELOG.md` (start with 2026-03-29 consolidation milestone)

### TIER 4 — LOW (Completeness)

13. Add module-level `README.md` to each of 13 `src/corp/*/` subdirectories
14. Update `CLAUDE.md` Architecture section to list all 13 src/corp/ subdirs
15. Add inline comment to pyproject.toml noting consolidation date

---

## Conclusion

The monorepo consolidation is **architecturally complete** (2,404 tests passing, all CLIs working, single pyproject.toml). However, **documentation hygiene is degraded**: 34 stale references remain across 12 files.

Most critical: `run-all-tests.ps1` and `dev-check.ps1` are **silently broken** — they reference `packages/` paths that no longer exist, so any developer relying on them gets no test coverage or linting.

**Estimated effort to resolve TIER 1–2:** 40 minutes (mostly bulk find/replace)
**Estimated effort including TIER 3:** 2 hours
