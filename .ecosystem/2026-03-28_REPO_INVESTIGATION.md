# Repo Investigation — Full Audit Before Cleanup

**Date:** 2026-03-28
**Branch:** `investigate/repo-audit-2026-03-28`
**Status:** Complete

---

## Question 1: What Do the 3 Ingest Commands Do?

### `corp ingest` (cli.py:2302) — Batch Non-Interactive

Processes files from `00_Inbox` to their vault destinations via the content registry.

| Aspect | Detail |
|--------|--------|
| **Handler** | `corp_by_os.ingest.router` → `ingest_all()`, `ingest_file()`, `ingest_folder()` |
| **Input** | Optional PATH (file or dir), otherwise scans entire `00_Inbox` |
| **Pipeline** | detect metadata → match via ContentRegistry → route (quarantine if no match, stage if low confidence, route if high) → record in ops.db → move file → optionally extract via CKE |
| **Output: matched files** | `mywork_root/{destination_path}/` |
| **Output: low-confidence** | `mywork_root/{destination}/_Staging/` |
| **Output: unmatched** | `mywork_root/00_Inbox/_Unmatched/` |
| **Output: vault notes** | `vault/01_Knowledge/` (flat, per Council #7) |
| **Flags** | `--dry-run`, `--no-extract` |
| **Extraction** | Via `_run_extraction()` → `cke_client.extract_sync()` → `move_to_vault()` |

### `corp ingest-inbox` (cli.py:2484) — Interactive One-at-a-Time

The "Magistrala" (Distribution Bus). Processes files from `00_Inbox` with Rich UI: classify, confirm destination, rename, move, then trigger CKE extraction.

| Aspect | Detail |
|--------|--------|
| **Handler** | `corp_by_os.ingest.inbox` → `process_file()` |
| **Input** | `--path` (specific file) or scans `00_Inbox` |
| **Pipeline per file** | dedup check (SHA256 via FileRegistry) → near-dup check (MinHash) → classify → propose rename → Rich panel → interactive accept/edit/skip → move → register → log event → extract |
| **Output: files** | `mywork_root/{destination}/{renamed_file}` |
| **Output: vault notes** | `vault/01_Knowledge/` |
| **Output: events** | `ops.db` `ingest_events` table |
| **Flags** | `--dry-run`, `--auto` (≥0.90 confidence), `--undo N`, `--full`, `--skip-extract`, `--list`, `--list-all`, `--destination` |
| **Undo** | Moves file back to `00_Inbox`, optionally removes vault package + rebuilds index |
| **Modules** | `ingest.classifier`, `ingest.renamer`, `ingest.router`, `ops.file_registry`, `overnight.cke_client` |

### `corp ingest-extractions` (cli.py:3300) — Vault Note Ingestion from CKE Output

Ingests pre-existing CKE extraction output into the Obsidian vault. This is the "last mile" — it does not extract, it imports.

| Aspect | Detail |
|--------|--------|
| **Handler** | `corp_by_os.ingest.extractions` → `ingest_extractions()` |
| **Input** | `CKE_OUTPUT_PATH` (required, directory) |
| **Pipeline** | Walk CKE output_v2 structure → read `_meta.yaml` → find `.md` in `extract/` → validate frontmatter → quality gate (≥25 by default) → check trust_level=verified protection → set trust_level=extracted → write to vault |
| **Output: accepted** | `vault/01_Knowledge/{note_name}.md` |
| **Output: quarantined** | `vault/_quarantine/{note_name}.md` |
| **Output: covers** | `vault/_assets/{package_name}_cover.png` |
| **Flags** | `--dry-run`, `--force` (overwrite verified), `--quality-threshold N`, `--rebuild-index` |
| **Used by** | `rebuild_complete.py` script (Council #20 vault rebuild) |

### How They Relate

```
corp ingest / ingest-inbox          corp overnight
  │ (routes + extracts in one step)    │ (batch extracts to staging)
  │                                     │
  └─► _run_extraction()                 └─► move_to_vault()
        │                                     │
        └─► cke_client.extract_sync()         │
              │                               │
              └─► vault/01_Knowledge/  ◄──────┘

corp ingest-extractions
  │ (imports pre-existing CKE output)
  └─► reads extract/ dirs → vault/01_Knowledge/
```

`ingest` and `ingest-inbox` do the full pipeline (route + extract + vault write).
`ingest-extractions` only does the vault write from existing CKE output.
`overnight` does batch extraction then vault write via `move_to_vault()`.

---

## Question 2: What Is golden_set/?

**Location:** `packages/corp-knowledge-extractor/_outputs/_outputs/golden_set/`
**Size:** ~103 MB

**Answer: It is a human-verified evaluation reference set used for quality gate calibration and extraction benchmarking.**

### Contents

- `golden_set/` — 12 CKE extraction packages (each with `extract/`, `index.md`, `source/` subdirs)
- `golden_set_review/` — review subdirectory
- 10 standalone `golden_set_review*.md` files — human review notes per golden extraction

### 12 Golden Packages

Demo2Win Exercise Packet, BY Platform Architecture, Blue Yonder Platform Training, Warehouse Management Architecture, Cognitive Demand Planning Help, Deep Meta Learning, Enterprise Data Orchestration Pitch Deck, Horizon Web, MaaS HighLevel Overview, Platform and Cognitive High Level Architecture (+ 2 more).

### Evidence

1. **README.md** (`_outputs/_outputs/README.md`) explicitly states:
   > `golden_set/ (formerly output/golden_set/)` — Use for: eval_extraction.py benchmarking, quality gate calibration
2. **`scripts/eval.py:162`** loads `tag_golden_set.json` from fixtures for eval scoring
3. **`scripts/extract_training_data.py:102`** has `gen_tag_golden_set()` generating tag golden set from extraction notes
4. **`tests/test_tag_golden_set.py`** validates golden set JSON integrity
5. **Ecosystem docs** reference "79/100 golden set average" as quality score; Council Decision #16 discusses Tag Jaccard scoring against it

**Verdict:** Keep. This is the eval reference set. Not training data. Required for `eval_extraction.py` benchmarking.

---

## Question 3: Root Cause of Nested `_outputs/_outputs/`

### How CKE Constructs Output Paths

| Command | Output path source | Default | Code location |
|---------|-------------------|---------|---------------|
| `cke process` | `--output` CLI flag | `"output"` (relative) | `run.py:282` |
| `cke process-manifest` | `manifest.output_dir` from JSON | varies | `manifest.py:69`, `batch.py:69` |
| `cke reextract` | `package_path.parent` | sibling of source | `reextract.py:94` |
| `build_rebuild_batch.py` | hardcoded | `.ecosystem/rebuild_staging/...` | `build_rebuild_batch.py:43` |
| `build_pilot_batch.py` | hardcoded | `.ecosystem/rebuild_staging/...` | `build_pilot_batch.py:19` |

### Root Cause: Manual Consolidation Error (Not a Code Bug)

The nesting is **not caused by a bug in the CKE pipeline**. Evidence:

1. The outer `_outputs/` has `{README.md, inventory.md, _outputs/, jlr_pilot/, jlr_staged/}`
2. The inner `_outputs/_outputs/` has `{README.md, inventory.md, golden_set/, misc/, test/, v2/, v3/}`
3. Both `README.md` files are **content-identical** (only line-ending diffs from `.gitattributes`)
4. `jlr_pilot/` and `jlr_staged/` are only in the outer dir (newer additions, not duplicated)

**What happened:** The CKE originally had separate output directories (`output/`, `output_v2/`, `output_v3/`, `output_test/`). These were consolidated into a single `_outputs/` directory. During consolidation, the entire `_outputs/` directory was copied/moved **into itself** as a subdirectory, creating the nesting. The README confirms the renaming: "v2/ (formerly output_v2/)", "golden_set/ (formerly output/golden_set/)".

**Fix:** Flatten — move contents of `_outputs/_outputs/` up one level into `_outputs/`, then delete the empty nested dir. The `jlr_pilot/` and `jlr_staged/` dirs already at the correct level don't conflict.

---

## Question 4: What's in misc/ (2.7 GB)?

**Location:** `packages/corp-knowledge-extractor/_outputs/_outputs/misc/`

### Contents: 2 Subdirectories

**1. `01_Product_Docs/` — Ad-hoc Video Extraction Run (Abandoned)**
- `source/video/` — 5 MP4 video files (meeting recordings: ARB Planning Architecture Review, MDAP as a Service, Gabriel Rey CB-Interop, LifeScience session, Platform Edited)
- `temp_frames/` — **1,535 PNG files** across 5 subdirectories (one per video)
- No `extract/` directory — extraction was never completed
- **This is the bulk of the 2.7 GB**

**2. `Cognitive_Friday/` — Completed Ad-hoc Extraction**
- `source/video/`, `source/docs/`, `source/frames/`, `source/slides/` — source material
- `extract/` — 8 extracted markdown files (extraction completed)
- `temp_frames/` — empty (cleaned up after extraction)
- `index.md` — 3.2 KB index

### What Are temp_frames/?

Temporary video frame sampling artifacts from CKE Tier 3 (MULTIMODAL) extraction. OpenCV samples frames at fixed intervals, dumps as `sample_NNNN.png`, then Gemini AI selects unique slides. Selected frames go to `source/frames/` or `source/slides/`, `temp_frames/` should be deleted after.

**Code locations creating temp_frames:**
- `run.py:424` — `temp_dir = output_p / package_name / "temp_frames" / f.name`
- `batch.py:211` — `temp_dir = pkg_dir / "temp_frames" / source_file.name`
- `batch_api.py:492` — `temp_dir = pkg_dir / "temp_frames" / source_file.name`

### No Code References "misc" as Output

No code writes to a "misc" output directory. This was created manually or by a one-off CLI invocation.

**Verdict:** `01_Product_Docs/` is orphaned processing waste — 1,535 temp PNGs from an abandoned extraction run. Safe to delete entirely. `Cognitive_Friday/` has completed extractions; check if already ingested to vault before deleting.

---

## Question 5: Where Does `corp overnight` Write Output?

### Command Definition (cli.py:1340)

| Option | Default | Purpose |
|--------|---------|---------|
| `--scope` | `all-non-project` | Target: `source-library`, `rfp`, `templates`, `full-reshape`, or all |
| `--budget` | 1.0 | Max USD spend |
| `--dry-run` | false | Preflight only |
| `--batch` | false | Use Gemini Batch API (50% cheaper) |
| `--auto-threshold` | 0.90 | Auto-approve confidence |
| `--reset` | false | Clear pending files from state DB |

### Scopes → MyWork Folders

```python
OVERNIGHT_SCOPES = {
    "all-non-project": ["30_Templates", "50_RFP", "60_Source_Library"],
    "source-library": ["60_Source_Library"],
    "rfp": ["50_RFP"],
    "templates": ["30_Templates"],
    "full-reshape": [],  # uses CKE scan
}
```

### All Output Paths

| What | Where |
|------|-------|
| **CKE extraction staging** | `%LOCALAPPDATA%/corp-by-os/staging/{folder_name}/` |
| **Vault notes (after extraction)** | `vault/{route.vault_target}/` (typically `01_Knowledge/`) |
| **State tracking DB** | `%LOCALAPPDATA%/corp-by-os/overnight_state.db` |
| **Monitor heartbeat** | `mywork_root/90_System/.corp/overnight_status.json` |
| **Event log** | `mywork_root/90_System/.corp/overnight_log_{run_id}.jsonl` |
| **Morning report** | `mywork_root/90_System/.corp/overnight_report_{run_id}.md` |
| **Freshness report** | `mywork_root/90_System/freshness_report.json` |
| **Reshape plan** | `%LOCALAPPDATA%/corp-by-os/` (full-reshape scope only) |

### CKE Invocation

Overnight invokes CKE **via Python import** (not subprocess) through `corp_by_os.overnight.cke_client`:
- `extract_batch(manifest_path)` → CKE `BatchJobRunner` (Gemini Batch API)
- `extract_sync(manifest_path)` → CKE `BatchProcessor` (synchronous)
- `scan_local(path)` → CKE `scan_path` (Tier 1, full-reshape only)

The output path passed to CKE is determined by the manifest's `output_dir` field, set to the staging directory.

### overnight_state.db Schema

3 tables: `runs` (run_id, scope, budget, status, timestamps, cost), `files` (path, hash, status, batch_id, tier, retry_count, cost), `batches` (batch_id, run_id, status, file_count).

**Key finding:** Overnight does NOT write to CKE `_outputs/`. It writes to `%LOCALAPPDATA%/corp-by-os/staging/`, then moves to vault. The `_outputs/` data predates the overnight pipeline.

---

## Question 6: Is rebuild_staging Safe to Delete?

**Location:** `.ecosystem/rebuild_staging/` — 2.0 GB, 2,037 files, 279 extract dirs

### Structure

```
.ecosystem/rebuild_staging/
  source_library/
    rebuild/          — 255 package dirs + status.json
    rebuild_pilot/    — 25 package dirs
```

### Code References (4 scripts only, all in `scripts/`)

| Script | Role |
|--------|------|
| `build_rebuild_batch.py` | Builds CKE manifest, sets output_dir to rebuild_staging |
| `build_pilot_batch.py` | Builds pilot manifest (25 files) |
| `rebuild_complete.py` | Polls status.json, runs `corp ingest-extractions` on staging dir |
| `rebuild_finalize.py` | Reads status.json for counts, writes report |

**Zero references in any package source code.** Only one-off scripts.

### Completion Evidence

1. `status.json` exists (2,910 bytes) — confirms rebuild completed
2. `rebuild_complete.py` ran `corp ingest-extractions` which copied accepted notes into vault
3. Archived report at `.ecosystem/archive/2026-03-27_VAULT_REBUILD_REPORT.md`
4. Manifests archived in `.ecosystem/archive/`
5. JOURNAL.md entry records the rebuild

### Verdict: SAFE TO DELETE

- Rebuild is complete and ingested
- No production code references it
- Data is redundant (notes now in vault `01_Knowledge/`)
- Audit trail preserved in `.ecosystem/archive/`
- 2.0 GB of pure intermediate artifacts

The 4 scripts in `scripts/` (`build_rebuild_batch.py`, `build_pilot_batch.py`, `rebuild_complete.py`, `rebuild_finalize.py`) are also single-use and could be archived.

---

## V2/V3/Vault Cross-Reference Manifest

### Version Definitions

- **v2:** CKE v0.4.0 — no tags, no provenance metadata
- **v3:** CKE v0.5.0 — tags + provenance (Batch B, aborted — valid extractions but no user context)

### Category Inventory

| Version | Categories |
|---------|-----------|
| **v2** | `projects/` (19 pkgs), `rfp/` (1 pkg), `source_library/` (3 pkgs), `templates/` (1 pkg) |
| **v3** | `projects/` (5 pkgs), `source_library/` (2 pkgs) |

### Overlap Analysis: 6 Packages Need Best-Version Audit

| Package | Category | v2 Notes | v3 Notes | v2 extract/ | v3 extract/ | Recommendation |
|---------|----------|----------|----------|-------------|-------------|----------------|
| Lenzing_Planning | projects | 11 | 166 | YES | YES | v3 (much deeper extraction) |
| Michelin_Planning | projects | 23 | 0 | YES | NO | v2 (v3 empty) |
| PepsiCo_Planning | projects | 12 | 4 | YES | YES | v2 (v3 incomplete) |
| SGDBF_Retail | projects | 18 | 0 | YES | NO | v2 (v3 empty) |
| 01_Product_Docs | source_library | 45 | 43 | YES | YES | **Needs per-note comparison** |
| 02_Training_Enablement | source_library | 231 | 0 | YES | NO | v2 (v3 empty) |

### v2-Only Packages (18) — No Dedup Needed

| Package | Category | Notes |
|---------|----------|-------|
| Ahold_Delhaize_CatMan | projects | 4 |
| Alfa_Laval_Planning | projects | 6 |
| Almarai_Planning | projects | 3 |
| CCI_Planning | projects | 5 |
| IFM_Planning | projects | 5 |
| LabelVie_TMS | projects | 6 |
| NEOM_WMS | projects | 10 |
| Orbico_Planning | projects | 3 |
| QDF_CatMan | projects | 5 |
| Redcare_Planning | projects | 4 |
| Rossmann_Migration | projects | 8 |
| Stellantis_Mopar_E2E | projects | 5 |
| Veronesi_Planning | projects | 8 |
| Wurth_Retail | projects | 13 |
| Zabka_Retail | projects | 4 |
| 50_RFP | rfp | 46 |
| 03_Competitive | source_library | 6 |
| 30_Templates | templates | 74 |

### v3-Only Packages (1)

| Package | Category | Notes | extract/ |
|---------|----------|-------|----------|
| Jaguar_Land_Rover_TMS_WMS_OMS | projects | 9 | NO (incomplete) |

### Summary Counts

| Bucket | Packages | Notes |
|--------|----------|-------|
| v2-only | 18 | 212 |
| v3-only | 1 | 9 (no extract) |
| Both (need audit) | 6 | v2: 340, v3: 213 |
| **v2 total** | 24 | 555 |
| **v3 total** | 7 | 222 |

### Dedup Verdict

Of the 6 overlapping packages:
- **4 are trivial** — v3 is empty/no-extract, keep v2 (Michelin, PepsiCo, SGDBF, Training)
- **1 clear winner** — Lenzing: v3 has 166 notes vs v2's 11, keep v3
- **1 needs per-note comparison** — 01_Product_Docs: v2 has 45, v3 has 43, both extracted

**Only `01_Product_Docs` requires a true best-version audit.** The rest can be resolved by note count and extraction completeness alone.

### Gap Analysis

The vault rebuild (Council #20) re-extracted 257 notes through the current pipeline, producing the notes now in `vault/01_Knowledge/`. The `_outputs/` v2/v3 data represents **earlier extractions** that may or may not overlap with the vault rebuild. The v2/v3 data is historical — the vault rebuild is the authoritative current state.

---

## Recommended Actions

### Immediate (Safe)

1. **Delete `misc/01_Product_Docs/temp_frames/`** — 1,535 orphaned PNGs, ~2.5 GB
2. **Delete `rebuild_staging/`** — 2.0 GB, rebuild complete and ingested
3. **Flatten `_outputs/_outputs/`** — move contents up one level, delete nested dir

### After Review

4. **Resolve v2/v3 overlap** — keep v2 for 4 trivial cases, v3 for Lenzing, compare 01_Product_Docs per-note
5. **Delete losing versions** after dedup
6. **Archive or delete `misc/Cognitive_Friday/`** — check if already in vault first

### Decision Needed

7. **Entire `_outputs/` directory** — after dedup, decide: keep golden_set locally, archive the rest to external storage, or delete if all notes are in vault
