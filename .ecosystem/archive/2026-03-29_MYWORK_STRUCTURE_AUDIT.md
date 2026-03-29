# MyWork Structure Audit — 2026-03-29

**Scope:** `C:\Users\1028120\Documents\MyWork` — read-only scan
**Cross-referenced against:** `folder_names.py` (ALL_MYWORK_FOLDERS), `90_System/routing_map.yaml`, `config/naming_config.yaml` (v2 naming convention)

---

## Top-Level Structure

| Folder | Files | SizeMB | Canonical? | Router Knows? | Notes |
|--------|------:|-------:|:----------:|:-------------:|-------|
| `.claude` | 2 | 0 | ❌ EXTRA | ❌ | Agent config rules — not ingestible content |
| `00_Inbox` | 35* | 22 | ✅ | ✅ | Files are metadata (3 files at root + _Unmatched = 0) |
| `10_Projects` | 595 | 5,922 | ✅ | ✅ | Primary content store |
| `20_Workflows` | 58 | 516 | ❌ EXTRA | ❌ MISMATCH | Router map says `20_Extra_Initiatives`; code says no `20_*` at all |
| `30_Reference` | 22 | 169 | ❌ EXTRA | ❌ MISMATCH | Router/code expect `30_Templates`; actual is `30_Reference` |
| `40_Media` | 0 | 0 | ❌ EXTRA | ❌ | Empty (3 empty subdirs: Demos, Meetings, Training) |
| `70_Admin` | 17 | 0.8 | ✅ | ❌ not mapped | HR/benefits docs |
| `80_Compliance` | 23 | 11.5 | ❌ EXTRA | ❌ MISMATCH | Code/router expect `80_Archive`; actual is `80_Compliance` |
| `90_System` | 48 | 9.6 | ✅ | ✅ (routing_map.yaml lives here) | |

**Canonical folders MISSING from MyWork:**

| Expected Folder | Status | Where did it go? |
|-----------------|--------|------------------|
| `30_Templates` | MISSING | Content is in `30_Reference` — different name/scope |
| `50_RFP` | MISSING | No equivalent folder exists |
| `60_Source_Library` | MISSING | No equivalent folder exists |
| `80_Archive` | MISSING | `80_Compliance` occupies the `80_*` slot but is a different concept |

**Critical misalignment:** `folder_names.py`, `routing_map.yaml`, and actual MyWork are **three different realities**. The router cannot route to `30_Templates`, `50_RFP`, or `60_Source_Library` because they don't exist. This directly explains the 53% MISC rate — the pipeline has nowhere valid to send non-project content.

---

## 00_Inbox Status

**Effectively empty** — no user content waiting.

| Item | Type | Notes |
|------|------|-------|
| `_triage_log.jsonl` | Pipeline metadata | Created 2026-03-11 |
| `_triage_schema.yaml` | Pipeline metadata | Created 2026-03-11 |
| `folder_manifest.yaml` | Pipeline metadata | Created 2026-03-11 |
| `_Unmatched/` | Subdir | 0 files |
| `_Staging/` | — | DOES NOT EXIST |

**Finding:** Inbox root has 3 infrastructure files (skipped by router per `SCAN_SKIP_DIRS`). Clean. No backlog. `_Staging` was never created — router would fail if it tried to write to it.

---

## 10_Projects Inventory

**25 projects total.** 1 is empty (Penguin_Random_House_WMS_TMS — 0 files).

### By Activity

| Status | Threshold | Count | Projects |
|--------|-----------|------:|---------|
| **Active** | Modified ≤30 days (after 2026-02-27) | 9 | JLR, SGDBF, LabelVie, Lenzing, Veronesi, Wurth, Clicks, Michelin, Redcare |
| **Moderate** | 30–90 days (2025-12-30 to 2026-02-27) | 7 | CCI, Rossmann, QDF, Deichmann, Ahold, PepsiCo, IFM |
| **Stale** | >90 days (before 2025-12-30) | 8 | Orbico, Systembolaget, Stellantis, Alfa_Laval, Safilo, Zabka, Almarai, NEOM |
| **Empty** | 0 files | 1 | Penguin_Random_House_WMS_TMS |

### Notable by Size

| Project | Files | SizeMB | Notes |
|---------|------:|-------:|-------|
| Clicks_Retail | 462 | 3,394 | **77% of all project files** — massive outlier |
| Michelin_Planning | 15 | 792 | High density |
| Wurth_Retail | 17 | 1,058 | Large files |
| Veronesi_Planning | 8 | 178 | Large files |
| JLR TMS/WMS/OMS | 11 | 171 | Most recently active |

### Project Naming Convention

All 25 project folders follow `{Client}_{Product}` convention (e.g., `Jaguar_Land_Rover_TMS_WMS_OMS`, `Clicks_Retail`). Consistent with `routing_map.yaml` spec.

**Clients NOT in `naming_config.yaml` client aliases:**

| Project Folder | Client | In aliases? |
|----------------|--------|:-----------:|
| `Veronesi_Planning` | Veronesi | ❌ |
| `Wurth_Retail` | Wurth | ❌ |
| `Redcare_Planning` | Redcare | ❌ |
| `CCI_Planning` | CCI | ❌ |
| `QDF_CatMan` | QDF | ❌ |
| `Deichmann_Network` | Deichmann | ❌ |
| `IFM_Planning` | IFM | ❌ |
| `Orbico_Planning` | Orbico | ❌ |
| `Systembolaget_Planning` | Systembolaget | ❌ |
| `Stellantis_Mopar_E2E` | Stellantis | ❌ |
| `Zabka_Retail` | Zabka | ❌ |
| `Almarai_Planning` | Almarai | ❌ |
| `NEOM_WMS` | NEOM | ❌ |
| `Penguin_Random_House_WMS_TMS` | Penguin | ❌ |
| `Alfa_Laval_Planning` | Alfa Laval | ❌ |
| `Safilo_Planning` | Safilo | ❌ |

**9 of 25 projects have client aliases defined; 16 do not.** This forces classifier to fall back to `UNK` for those clients — contributing to MISC classification rate.

### File Naming Compliance (v2 pattern: `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.ext`)

**0 of 100 sampled files are v2-compliant.** Zero.

Common actual patterns observed:
- `Clicks_Workshop.pptx` — no date, no type code
- `BlueYonder-Clicks-PPT-V1.pptx` — vendor naming, no convention
- `Ahold Delhaize Tech Workshop 28012026.pdf` — date at end, DD/MM/YYYY
- `PSEstimator_T&M_2025 OP-0247496.xlsx` — tool exports, internal naming
- `ORIGINAL LOCALCOPYAnnex A CCI...` — raw client documents, unchanged

**Finding:** Projects contain unmolested source documents — never renamed by the pipeline. Either the renamer has not been run, or naming is left as-is intentionally. This is correct behavior for raw project archives; renaming would be destructive.

---

## 90_System Contents

| Path | Classification | Recommendation |
|------|---------------|----------------|
| `config.json` | **CONFIG** | Keep — pipeline config |
| `content_registry.yaml` | **CONFIG** | Keep — core registry |
| `routing_map.yaml` | **CONFIG** | Keep — but update to match actual folder names |
| `solution_matrix.json` | **CONFIG** | Keep — product reference |
| `Platform_Usage_by_Product.xlsx` | **CONFIG** | Keep — reference data |
| `Project_Codes.xlsm` | **CONFIG** | Keep — source for project IDs |
| `.audit/` | **LOG/CACHE** | 14 files, 5.3MB total — historical audit artifacts |
| `.audit/preflight_manifest.json` | **CACHE** | 3,672 KB — regenerable |
| `.audit/full_scan.json` | **CACHE** | 2,274 KB — regenerable |
| `.audit/archive_scan.json` | **CACHE** | 931 KB — regenerable |
| `.audit/cleanup_20260322.md` | **LOG** | Historical — archive or delete |
| `.audit/migration_*.md` | **LOG** | Historical — archive or delete |
| `.logs/cleanup_log.jsonl` | **LOG** | 2,113 KB — operational history |
| `.logs/moves.yaml` | **LOG** | 25 KB — move history |
| `.logs/.corp/` | **LOG** | 9 overnight run logs — historical |
| `.scripts/` | **CONFIG/SCRIPTS** | 3 PS1 scripts — keep |
| `_corp_prep/` | **CACHE** | 2 prep files from 2026-03-26 — regenerable |

**Cacheable/deletable (after confirmation):** ~7MB in `.audit/` large JSON + `.logs/` accumulated logs + `_corp_prep/` = ~9MB recoverable.

---

## Other Folders

### 20_Workflows (58 files, 516 MB)
**Purpose:** Sales/pre-sales presentation templates and master decks.
**Subdirs:** `00_Master_Deck`, `PreSales`, `Sales`, `Services`
**Status:** Active content. Conceptually this is "working templates" or "role-based templates." The routing_map.yaml references this slot as `20_Extra_Initiatives` (internal non-client projects) — completely different semantic.
**Problem:** Name, meaning, and router expectation are all misaligned.

### 30_Reference (22 files, 169 MB)
**Purpose:** Evergreen reference material by topic.
**Subdirs:** `Architecture` (2), `Brand_Marketing` (3), `Competitive` (5), `Data_Requirements` (1), `Product` (10), `Training` (1)
**Status:** Active reference library. Maps to `60_Source_Library` semantically — but uses the `30_*` slot that the router expects for Templates.
**Problem:** This folder serves the role of both `30_Templates` and `60_Source_Library`.

### 40_Media (0 files, 0 MB)
**Purpose:** Unknown — 3 empty subdirs (Demos, Meetings, Training).
**Status:** Dead placeholder. Not in canonical spec.
**Recommendation:** Remove after Rob confirms nothing planned for it.

### 70_Admin (17 files, 0.8 MB)
**Purpose:** HR/admin documents (Benefits, Corporate_Goals_2026).
**Status:** Present in canonical spec, not in routing_map.yaml. Low-value for pipeline.
**Note:** Root also has `.agentignore` (0 bytes) — tells pipeline to skip this folder.

### 80_Compliance (23 files, 11.5 MB)
**Purpose:** Security/compliance certificates and policies.
**Subdirs:** `Certificates`, `Policies`, `Security_Questionnaires`
**Status:** Active. Occupies the `80_*` slot but not the canonical `80_Archive`. Archive behavior (for completed projects) has no actual destination folder.

### .claude (2 files, 0 MB)
**Contents:** `code-standards.md`, `mywork-rules.md`
**Status:** Agent instruction files. Invisible to pipeline. Fine where it is but not a canonical MyWork folder.

---

## File Type Distribution (All of MyWork)

| Rank | Extension | Count | Notes |
|-----:|-----------|------:|-------|
| 1 | `.pdf` | 141 | Client docs, certs |
| 2 | `.pptx` | 140 | Presentations (core content) |
| 3 | `.xlsx` | 122 | Spreadsheets |
| 4 | `.docx` | 85 | Word docs |
| 5 | `.jpg` | 68 | Images |
| 6 | `.csv` | 53 | Data files |
| 7 | `.md` | 35 | Pipeline-generated notes |
| 8 | `.gitkeep` | 26 | Empty folder markers |
| 9 | `.json` | 20 | Pipeline metadata |
| 10 | `.jpeg` | 14 | Images |
| 11 | `.png` | 14 | Images |
| 12 | `.gz` | 11 | Compressed files |
| 13 | `.jsonl` | 11 | Pipeline logs |
| 14 | `.xlsm` | 11 | Macro spreadsheets |
| 15 | `.7z` | 10 | Archives |
| — | `.mp4` | 2 | Video (in empty 40_Media?) |

**26 `.gitkeep` files** = structural scaffolding for empty folders (Orbico, Penguin, etc.). Pipeline should skip these.

---

## Routing Coverage

**Router (`router.py`) routes to destinations read from `content_registry.yaml` (not `routing_map.yaml` directly). The `routing_map.yaml` defines vault targets — different concern.**

| MyWork Folder | Router/Code Aware? | routing_map.yaml entry | Verdict |
|---------------|:-----------------:|------------------------|---------|
| `00_Inbox` | ✅ (source) | ✅ | OK |
| `10_Projects` | ✅ (destination) | ✅ | OK |
| `20_Workflows` | ❌ | `20_Extra_Initiatives` (mismatch) | **GAP** |
| `30_Reference` | ❌ | `30_Templates` (mismatch) | **GAP** |
| `40_Media` | ❌ | not present | **UNKNOWN** |
| `70_Admin` | ❌ | not present | Not ingestible |
| `80_Compliance` | ❌ | `80_Archive` (mismatch) | **GAP** |
| `90_System` | skipped | ✅ (triage_required=false implied) | OK |

**Three folder mismatches between routing_map.yaml and actual MyWork.** Content in `20_Workflows`, `30_Reference`, `80_Compliance` cannot be routed — the router doesn't know these folder names exist.

**Three canonical destinations with no actual folders:** `30_Templates`, `50_RFP`, `60_Source_Library`. Pipeline has vault targets defined for them but files can never arrive there.

---

## Near-Duplicates in 10_Projects

Top duplicates found — all within Clicks_Retail which contains subfolders with copied/versioned files:

| Count | Filename | Locations |
|------:|----------|-----------|
| 2 | `PSEstimator_T&M_2025 OP-0247496.xlsx` | Services \| PSE All… |
| 2 | `Clicks_Services_Summary_v2.0.xlsx` | Services \| Services |
| 2 | `Clicks_Services_Summary_v1.0.xlsx` | Services \| Services |
| 2 | `Blue_Yonder_ISO27001.pdf` | 2020 \| 2021 (in 80_Compliance subfolders — expected) |
| 2 | `Blue_Yonder_ISO20000.pdf` | 2020 \| 2021 (in 80_Compliance) |

**Pattern:** Duplicates are mostly within Clicks_Retail (space-vs-underscore pairs of the same file) and year-dated compliance certs. Not a structural problem — but the space/underscore pairs suggest manual copy without cleanup.

---

## Recommendations

### P0 — Fix the configuration mismatch (blocks pipeline correctness)

1. **Reconcile routing_map.yaml vs actual folders.** Three options per mismatched slot — pick one:
   - Rename actual folder to match config (destructive, needs Rob approval)
   - Update config to match actual folder name
   - Create the expected folder and migrate content

   Affected slots:
   - `20_Workflows` ↔ `20_Extra_Initiatives` (routing_map.yaml) — neither in folder_names.py
   - `30_Reference` ↔ `30_Templates` — present in folder_names.py as `TEMPLATES`
   - `80_Compliance` ↔ `80_Archive` — present in folder_names.py as `ARCHIVE`

2. **Update folder_names.py** to include `20_Workflows` and `80_Compliance` if those are the canonical names going forward. Currently `20_Workflows` has no constant defined anywhere.

3. **Create `50_RFP` and `60_Source_Library`** — or remove their entries from routing_map.yaml and folder_names.py. These folders are defined everywhere but don't exist.

### P1 — Missing client aliases (raises MISC rate)

4. **Add 16 missing clients to `naming_config.yaml`.** Active projects (JLR, Clicks, Michelin, Wurth, SGDBF) include 5 clients with aliases + 4 without (Veronesi, Wurth, Redcare, CCI). Classifier falls back to `UNK` for unmapped clients, inflating MISC rate.

### P2 — Structural cleanup (low risk)

5. **40_Media** — 0 files, empty scaffolding. Remove or populate. Confirm with Rob before deleting.

6. **90_System/.audit/ large JSONs** — `preflight_manifest.json` (3.6MB), `full_scan.json` (2.3MB), `archive_scan.json` (0.9MB) are regenerable caches. Safe to archive/delete after confirmation.

7. **Clicks_Retail cleanup** — 462 files (77% of all project files). Space/underscore duplicate pairs exist. Consider dedup pass when processing this project.

8. **Penguin_Random_House_WMS_TMS** — 0 files. Either stub (waiting for content) or dead. Confirm with Rob.

### P3 — No-action items

- File naming non-compliance (0%) is expected — raw client documents should NOT be renamed by the pipeline
- `_OLD_FILES.txt` markers in CCI/Rossmann — intentional cleanup markers, leave
- `.gitkeep` files — infrastructure, pipeline skips these correctly

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total files | ~799 |
| Total size | ~6.6 GB |
| Canonical folders present | 4 / 8 (50%) |
| Missing canonical folders | 4 (30_Templates, 50_RFP, 60_Source_Library, 80_Archive) |
| Extra non-canonical folders | 5 (.claude, 20_Workflows, 30_Reference, 40_Media, 80_Compliance) |
| Router-aware folders | 2 of 9 actual folders (22%) |
| Project naming v2 compliance | **0%** |
| Active projects (≤30 days) | 9 / 25 |
| Stale projects (>90 days) | 8 / 25 |
| Missing client aliases | 16 / 25 clients |
