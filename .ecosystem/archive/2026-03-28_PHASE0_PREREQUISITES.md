# Phase 0 Prerequisites Report — ADR-23 Implementation
**Date:** 2026-03-28
**Branch:** `chore/council23-phase0-prerequisites`
**ADR:** `decisions/ADR-23-monorepo-internal-architecture.md`
**Status:** All Phase 0 gates satisfied

---

## Summary

All four Phase 0 prerequisite measurements are complete. No blockers found.
Implementation phases (Phase 1–4) can proceed in order per ADR-23.

---

## Gate 1 — CKE Call Volume (Q1 gate)

**Question:** How many times does a typical `corp overnight` run invoke CKE? If >100, implement batched invocation.

**Method:** Traced `cli.py:1340` (`overnight` command) → loop over `OVERNIGHT_SCOPES[scope]` at `cli.py:1331` → one `extract_batch()` or `extract_sync()` call per folder.

**Finding:**
- Default scope (`all-non-project`) = `["30_Templates", "50_RFP", "60_Source_Library"]` → **3 CKE calls per run**
- All other scopes: `source-library` (1 folder), `rfp` (1 folder), `templates` (1 folder), `full-reshape` (0 folders)
- Maximum realistic call count: 3 (default) or 6 if running multiple scopes sequentially

**Decision:** Well below the 100-call threshold. **Simple subprocess wrapper is sufficient — no batching or worker pool needed.**

**Phase 2 gate: OPEN.** No call volume concerns.

---

## Gate 2 — CLI Shared State Audit (Q2 gate)

**Question:** What module-level state must be extracted to `cli/_common.py` before splitting cli.py?

**Full audit:** `.ecosystem/archive/2026-03-28_CLI_SHARED_STATE_AUDIT.md`

**Module-level constants:**
| Name | Line | Value |
|------|------|-------|
| `CHECK` | 63 | `"Y"` — Windows console safe checkmark |
| `DASH` | 64 | `"-"` — ASCII dash separator |
| `EXTRACT_EXTENSIONS` | 1205 | set of file extensions |
| `OVERNIGHT_SCOPES` | 1331 | dict: scope → folder list |

**Module-level objects:**
| Name | Line | Type |
|------|------|------|
| `console` | 66 | `rich.console.Console` (shared by all commands) |
| `logger` | 67 | `logging.Logger` |

**Root CLI group:** Lines 70–82. Injects `PipelineConfig.production()` into `ctx.obj["config"]` — all commands depend on this. Must live in root `cli/root.py` or `cli/__init__.py`.

**Private helpers (9 functions):**
- `_show_workflow_list` (582), `_show_workflow_panel` (601) → move to `cli/workflow.py`
- `_run_folder_extraction` (1400), `_update_folder_file_statuses` (1586), `_run_full_reshape` (1615), `_run_freshness_phase` (1760), `_write_reshape_plan` (1822), `_execute_reshape_actions` (1889) → move to `cli/overnight.py`
- `_count_signatures` (2690) → move to `cli/analytics.py`

**Click group inventory:**
- 7 named groups: `project`, `vault`, `task`, `index`, `analytics`, `template`, `rfp`
- 25 direct `@cli.command()` entries
- **Total: 71 CLI entry points**

**Proposed split (14 modules):** `_common.py`, `project.py`, `vault.py`, `task.py`, `index.py`, `analytics.py`, `template.py`, `rfp.py`, `ingest.py`, `overnight.py`, `workflow.py`, `query.py`, `maintenance.py`, `misc.py`

**Phase 1 gate: OPEN.** Shared state fully inventoried. Split plan documented.

---

## Gate 3 — CLI Help Snapshot (Phase 1 regression gate)

**Question:** Capture all 71 CLI help outputs as regression baseline.

**Location:** `eval/cli_snapshot_2026-03-28/` — **55 files**

File count breakdown:
- 1 top-level (`corp_help.txt`)
- 7 group-level (`project_help.txt`, `vault_help.txt`, etc.)
- 17 subcommand-level (all groups' subcommands)
- 25 direct commands + 5 misc
- All captured on 2026-03-28 from corp v0.3.0

**Phase 1 regression gate: OPEN.** Snapshot complete. Use `diff eval/cli_snapshot_2026-03-28/ eval/cli_snapshot_<post-phase1>/` to detect user-visible changes.

---

## Gate 4 — Dead Code Verification (Q5 gate)

**Question:** Verify 4 files in corp-rfp-agent have no live references outside documentation.

**Full audit:** `.ecosystem/archive/2026-03-28_DEAD_CODE_VERIFICATION.md`

| File | Live Python imports | Other live references | Verdict |
|------|--------------------|-----------------------|---------|
| `clean_kb.py` | None | None (docs only) | Delete |
| `scan_kb.py` | None | None (docs only) | Delete |
| `kb_to_markdown.py` | None | `tests/test_cli_smoke.py:13` (script invocation) | Delete + update test |
| `_paths.py` | None | None | Delete |

**Flag:** Deleting `kb_to_markdown.py` requires simultaneously removing its entry from `tests/test_cli_smoke.py`.

**Phase 4 gate: OPEN.** All 4 files confirmed dead. Deletion checklist in verification doc.

---

## Artifacts produced

| Artifact | Location |
|----------|----------|
| Council #23 transcript | `.ecosystem/council_transcripts/DECISION_23_monorepo_internal_architecture.md` |
| ADR-23 | `decisions/ADR-23-monorepo-internal-architecture.md` |
| CKE call volume measurement | This report (Gate 1) + `cli.py:1331-1545` trace |
| Shared state audit | `.ecosystem/archive/2026-03-28_CLI_SHARED_STATE_AUDIT.md` |
| CLI help snapshot | `eval/cli_snapshot_2026-03-28/` (55 files) |
| Dead code verification | `.ecosystem/archive/2026-03-28_DEAD_CODE_VERIFICATION.md` |

---

## Implementation readiness

| Phase | Scope | Gate | Status |
|-------|-------|------|--------|
| Phase 1 | CLI split (Q2) | Shared-state audit | **READY** |
| Phase 2 | Subprocess boundary (Q1) | Call volume measurement | **READY** |
| Phase 3 | Flatten nesting (Q3) | Phase 1 complete | Waiting on Phase 1 |
| Phase 4 | Centralize utils + dead code (Q4+Q5) | Phase 3 complete | Waiting on Phase 3 |

---

## No blockers found

All measurements align with the Council's projected scope:
- Q1: Simple subprocess wrapper, no batching
- Q2: 14-module split plan, no circular dependency risks
- Q3: doctor (2 files), freshness (2 files), extraction/non_project (3 files) — all small
- Q4: parse_llm_json centralization (confirmed single implementation in corp-os-meta)
- Q5: 4 dead files, coordinated test update for kb_to_markdown
