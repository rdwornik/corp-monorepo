# Functional Audit — Telemetry Base (Phase 1)

**Date:** 2026-07-05
**Branch:** `docs/2026-07-05-functional-audit`
**HEAD at audit start:** `fb9b2dd` (after `git pull --ff-only` from `b13c163`; the 2 pulled commits are nightly conformance digests only)
**Method:** read-only. All SQLite access via `sqlite3.connect("file:...?mode=ro", uri=True)`. No OneDrive path touched or traversed. No production pipeline executed.

This document is evidence only — interpretation happens in the scenario/inventory/synthesis deliverables.

---

## 1. Database telemetry

DB files live at `%LOCALAPPDATA%\corp-by-os\` (confirmed against `config/paths.toml` `[paths.databases]`).

### 1.1 File-level

| DB | Size | File mtime (last data write) |
|----|------|------------------------------|
| `ops.db` | 1,368,064 B | **2026-03-28 17:21** |
| `index.db` | 1,228,800 B | **2026-03-28 15:57** (`index.db-shm` touched 2026-06-04 — read via WAL during the ARCHITECTURE count-refresh session; `-wal` is 0 B) |
| `overnight_state.db` | 299,008 B | **2026-03-13 23:28** |

Also present in the same dir: `reshape_plan.md` (554 KB, 2026-03-13), `usage.json` (`{"date": "2026-03-09", "calls": 1}`), `staging/`, `overnight_staging/` (see §2.3).

### 1.2 ops.db

| Table | Rows | Timestamp range |
|-------|------|-----------------|
| `assets` | 33 | mtime 2026-03-04 .. 2026-03-23 |
| `packages` | 4 | created 2026-03-14 .. 2026-03-15 |
| `ingest_events` | 2,726 | **2026-03-14 .. 2026-03-27** |
| `files` (file_registry) | 11 | first_seen 2026-03-23 .. 2026-03-24 |
| `extractions` | **0** | — |
| `routing_feedback` | **0** | — |
| `registry_suggestions` | **0** | — |
| `content_signatures` | **0** | — |

`ingest_events` by month × action × method — **every row is 2026-03**; ingest was last used for real on **2026-03-27T12:23**:

| Month | Action | Method | Count |
|-------|--------|--------|-------|
| 2026-03 | ingested | ingest-extractions | 2,673 |
| 2026-03 | routed | rule | 15 |
| 2026-03 | ingest_inbox_route | rule | 14 |
| 2026-03 | routed | client | 6 |
| 2026-03 | ingest_inbox_route | client | 6 |
| 2026-03 | extracted | ? | 4 |
| 2026-03 | routed | series | 3 |
| 2026-03 | ingest_inbox_route | manual | 2 |
| 2026-03 | routed | manual | 2 |
| 2026-03 | quarantined | none | 1 |

Reading: 98% of all ingest events are the 2026-03-26/27 bulk `ingest-extractions` runs (v2/v3/JLR, per JOURNAL §3.2 below). Interactive inbox routing was used ~22 times, ever. Assets: 28 `routed`, 5 `quarantined`.

`extractions` (per-model extraction history, writer `ops/file_registry`) has **never received a row**. The learning/dedup surfaces (`routing_feedback`, `registry_suggestions`, `content_signatures`) have **never received a row** — despite `content_signatures` having been implemented with 24 tests on 2026-03-27 (JOURNAL) and `routing_feedback` being built 2026-03-25.

### 1.3 index.db

| Table | Rows | Timestamps |
|-------|------|-----------|
| `notes` | 488 | extracted_at max **2026-03-27T12:21** |
| `notes_fts` | 488 | — |
| `facts` | **0** | — |
| `facts_fts` | **0** | — |
| `projects` | 25 | updated_at all 2026-03-28T15:57 |
| `meta` | 5 | `last_rebuild = 2026-03-28T15:57:36`, `total_notes=488`, `total_facts=0`, `rebuild_duration_seconds=8.05` |

`rfp_visible`: 182 notes visible, 306 not.

**Notes by client (top + anomalies):** `''` (empty) 258 · Lenzing 124 · Michelin 11 · Heineken 11 · Stellantis 5 · PepsiCo 5 · Rolls-Royce 4 · Martin Brower 4 · LabelVie 4 · Avon 4 · JLR 3 · … long tail of 1–3s.
**Encoding-corruption duplicates present:** `Würth` (2) vs `WÃ¼rth` (1); `Żabka` (1) vs `Å»abka` (1); `Coca-Cola İçecek` needed UTF-8 console to print. Same client, distinct rows → client-scoped queries split across variants.

**Notes by doc_type:** document 213 · presentation 130 · spreadsheet 58 · unknown 35 · training 23 · questionnaire 5 · documentation 5 · demo 5 · note 4 · meeting 3 · training_session 2 · plus 4 singletons incl. the malformed literal `meeting|presentation|rfp|documentation` (1).

### 1.4 Empirical coverage map v0 (product term × doc_type, from `notes.products`)

403/488 notes carry a non-empty `products` field. Term frequency (top families) and doc_type spread:

| Product family (term) | Notes | document | presentation | spreadsheet | training | Verdict vs THIN(<20) |
|---|---|---|---|---|---|---|
| blue yonder platform | 231 | 118 | 81 | 8 | 20 | RICH |
| blue yonder demand planning | 185 | 95 | 57 | 19 | 9 | RICH |
| azure | 127 | 34 | 65 | — | 18 | RICH |
| blue yonder supply planning | 101 | 49 | 25 | 19 | 4 | RICH |
| blue yonder wms | 66 | 53 | 9 | 2 | — | RICH (but presentation-thin) |
| blue yonder tms | 54 | 45 | 5 | 2 | — | RICH (but presentation-thin) |
| blue yonder control tower | 43 | 22 | 10 | 9 | 1 | RICH |
| snowflake | 32 | — | 24 | — | 5 | RICH |
| blue yonder workforce management | 12 | 7 | 2 | 2 | — | **THIN** |
| blue yonder network design | 10 | 7 | — | 3 | — | **THIN** |
| blue yonder oms | 9 | 8 | — | 1 | — | **THIN** |
| blue yonder commerce | 4 | — | — | — | — | **THIN** |
| category management (catman) | 0 | — | — | — | — | **ABSENT** |

Long tail of near-duplicate uncanonicalized product terms exists (`demand planning`, `demand planning module`, `platform demand planning`, `idsp (integrated demand`, `supply & inventory planning)` — the last two are one term split on an embedded comma), i.e. the `products` field is not normalized to a canonical family list.

### 1.5 overnight_state.db

| Metric | Value |
|--------|-------|
| Runs | 9, all **2026-03-12 .. 2026-03-13** |
| Run outcomes | 3 `completed`, 2 `dry_run`, **4 stuck `running`** (started 2026-03-13, `completed_at IS NULL`) |
| Files | 601 rows, all `status=done`, `tier=pending`, processed 2026-03-13 |
| Batches | 0 rows (Batch API path never used) |
| Total actual_cost | **$0.24** across all runs (largest completed run: 270 files, $0.243) |

---

## 2. Filesystem telemetry (local paths only)

### 2.1 MyWork canonical zones (`C:/Users/1028120/Documents/MyWork`, per `paths.toml`)

| Zone | Files | Size (MB) | Newest mtime | Newest file |
|------|-------|-----------|--------------|-------------|
| `10_Projects` | 620 | 6,555 | **2026-07-03** | `Unilever_AnR/Unilever_VMI_Platform_Story.pptx` |
| `30_Reference` | 1,356 | 3,796 | **2026-07-05** | `Training/2026_Platform_Training_Warsaw/WORKSPACE_MASTER_REFERENCE.md` |
| `00_Inbox` | 75 | 232 | **2026-04-10** | `raw/rfp/docs/...Rolls Royce APS RFP...docx` |
| `20_Workflows` | 30 | 228 | 2026-05-05 | `Technical_Presentations/~$Slides_for_Integration.pptx` (Office lock file) |
| `15_Extra_Inititives` | 63 | 89 | 2026-05-15 | `MBO/MBO_Databricks_BY_Integration_Options.pptx` |
| `80_Compliance` | 29 | 14 | 2026-04-24 | `Certificates/Current/Security Incident Response Policy.pdf` |
| `70_Admin` | 17 | 1 | 2026-03-26 | `Corporate_Goals_2026/MBO_2026_H1_Robert.xlsx` |
| `90_Archive` | **0** | 0 | — | (empty) |
| `.corp` | 46 | 10 | 2026-03-30 | `routing_map.yaml` |
| `.claude` | 2 | 0 | 2026-03-22 | rules |

Notes: `15_Extra_Inititives` (sic — misspelled) is not one of the 7 Council-#24 canonical folders in `folder_names.py`. `90_Archive` has never received a file. `Project_Codes.xlsm` resolves via env `PROJECT_CODES_EXCEL` to `MyWork/30_Reference/Project_Codes.xlsm` (local, not OneDrive).

### 2.2 Obsidian vault (`C:/Users/1028120/Documents/ObsidianVault`)

| Zone | Files | Newest mtime |
|------|-------|--------------|
| `01_Knowledge` | 814 | **2026-03-27** |
| `02_Navigate` | 18 | 2026-03-27 |
| `_quarantine` | 23 | 2026-03-27 |
| `_assets` | 11 | 2026-03-27 |
| `99_System` | 5 | 2026-03-26 |
| `00_Home` | 1 | 2026-03-23 |

- Total `.md` on disk: **850**. Indexed `notes` rows: **488** (index built 2026-03-28 after source_hash dedup; JOURNAL 2026-03-26 records 583 found → 493 unique at that point).
- **There is no `02_sources/` zone on disk.** The vault writer invariant (CLAUDE.md §5, ADR-27) names `02_sources/`; physical zones are `00_Home/01_Knowledge/02_Navigate/99_System`. Same finding as the 2026-06-16 audit ("declared immutable 02_sources zone has no physical folder").
- The vault is a **git repo with no remote** (`git remote -v` empty); last commit 2026-03-26. History exists on this laptop only.

### 2.3 Extraction/staging/output footprint (disposable-artifact analysis)

| Location | Files | Size | Newest |
|----------|-------|------|--------|
| repo `data/_outputs/` total | 2,925 | **18.4 GB** | 2026-03-26 |
| — `v2/` | 1,560 | 11.3 GB | 2026-03-22 |
| — `v3/` | 1,184 | 6.9 GB | 2026-03-26 |
| — `golden_set/` | 115 | 107 MB | 2026-03-20 |
| — `test/`, `jlr_pilot/`, `jlr_staged/` | 66 | ~14 MB | 2026-03-26 |
| `%LOCALAPPDATA%/corp-by-os/staging/` | 2 + two empty zone dirs (`50_RFP`, `60_Source_Library`) | ~0 | 2026-03-23 |
| `%LOCALAPPDATA%/corp-by-os/overnight_staging/20260312_192817/` | 1 (`manifest.json`) | ~0 | 2026-03-12 (leaked run dir) |

### 2.4 RFP KB (`C:/Users/1028120/Documents/corp_data/rfp_kb`)

1,329 files total, **every family's newest mtime is 2026-03-15** — the KB has not been touched since.

| Family | Files | | Family | Files |
|--------|-------|-|--------|-------|
| planning | **894** | | wms | 34 |
| `_staging` | 174 | | catman, catman_assortment, catman_space | 0 |
| logistics | 121 | | commerce, commerce_orders | 0 |
| network | 63 | | control_tower, planning_ibp, planning_pps | 0 |
| aiml | 43 | | retail_ar, retail_demand_edge, retail_mfp, scp, scp_sequencing | 0 |

12 of 17 product-family directories are **empty**. Planning is 67% of all populated content.

---

## 3. Git + JOURNAL archaeology

### 3.1 Last commit touching each `src/corp/` package (dormancy signal)

| Package | Last commit | | Package | Last commit |
|---------|-------------|-|---------|-------------|
| `ingest/` | 2026-03-30 | | `actions/` | 2026-04-21 (safety hotfix) |
| `ops/` | 2026-03-30 | | `cleanup/` | 2026-04-21 (safety hotfix) |
| `overnight/` | 2026-03-30 | | `project/` | 2026-04-21 (safety hotfix) |
| `retrieve/` | 2026-03-30 | | `schema/` | 2026-05-28 |
| `rfp/` | **2026-03-30** | | `extractor/` | 2026-06-06 (retry wrapper only) |
| `cli/` | 2026-04-15 (Tach) | | `opportunity/` | 2026-04-15 (Tach) |
| `extraction/` | 2026-04-15 (Tach) | | root modules | mostly 2026-03-29/30; `vault_io.py`/`models.py` 2026-05-18 (invariant test) |

All post-March commits to functional code are safety hotfixes, Tach refactors, or governance conformance — no feature or process work since **2026-03-30**.

### 3.2 JOURNAL evidence of processes being USED (not built)

| Date | Evidence (quoted/paraphrased from JOURNAL) | Process |
|------|-------------------------------------------|---------|
| 2026-03-12/13 | 9 overnight runs, 601 files processed, $0.24 (overnight_state.db) | W2 extract |
| 2026-03-26 | "Ran JLR pilot ingest … Live ingest succeeded. Index rebuilt. `corp retrieve "JLR TMS"` returns 3/3" | W2 + retrieval |
| 2026-03-26 | "Ran v3 bulk ingest: 203 notes ingested … `corp retrieve "demand planning"` → 30 results" | W2 |
| 2026-03-26 | "v2 bulk ingest (387 notes ingested … 493 unique notes indexed)" | W2 |
| 2026-03-26 | "JLR real usage test (useful output)" | D2 ad-hoc Q&A |
| 2026-03-27 | "Re-extracted 216 vault notes via CKE batch … quality-threshold 25, index rebuilt" (Council #20 vault rebuild) | W2 |
| 2026-03-28 | "Council #22 RFP federation debate" → ADR-22 written; **"Next: Implement ADR-22"** | D3 (intent only) |
| 2026-04-10 | (filesystem, not JOURNAL) newest 00_Inbox file: Rolls-Royce APS RFP response docx | W1 capture (last inflow) |
| 2026-05-18 → 2026-07-05 | Every JOURNAL entry is governance/conformance/audit — **zero process-use entries** | — |

**Never mentioned as used anywhere in JOURNAL:** `corp rfp answer` on a real RFP, `com new/list/show/prep-deck` (opportunity lifecycle), deck generation, Win/Loss archiving, publish-to-team, any backup process.

---

*End of Phase 1 telemetry. No writes performed outside this file.*
