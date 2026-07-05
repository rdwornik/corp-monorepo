# Deep Audit B — Magistrala / Capture (Wave 2)

**Date:** 2026-07-05 · **Branch:** `docs/deep-magistrala` · **Baseline:** Phase-1 functional audit (`docs/audits/2026-07-05-functional-*.md`, merged at `2753601`)
**Method:** read-only — static code trace, `mode=ro` SQLite, metadata-only inbox scan, dry replication of registry matching (no pipeline execution, no moves, no config edits). No OneDrive path touched.

**One-line verdict:** The capture machinery is DORMANT-but-sound; what is actually BROKEN is its *map* — the live `content_registry.yaml` (2026-03-23) routes into a folder tree that Council #24 (2026-03-29) abolished, both lanes silently `mkdir` whatever the registry names, every identity/learning surface was wired 1–3 days *after* the last real run, and MinHash dedup cannot run at all because `datasketch` was never installed. A restart without the F0 config-truth pass would quarantine 61% of the backlog and re-create the pre-#24 folder structure.

Status vocabulary: ALIVE / DORMANT / EXISTS-UNTESTED / BROKEN / PHANTOM / MISSING.

---

## Step 1 — Two-lane trace

Both lanes share: `ContentRegistry` matching (`src/corp/ops/registry.py`), `OpsDB` recording (`src/corp/ops/database.py`), CKE handoff via `_run_extraction` (`src/corp/ingest/router.py:720-810`), vault target hardcoded `01_Knowledge`, and **no index rebuild** (manual `corp index rebuild` after).

### Lane A — batch `corp ingest` (`cli/ingest.py:14` → `ingest/router.py`)

| Stage | Function | Behaviour | Evidence |
|---|---|---|---|
| detect | `scan_inbox` | Loose files + depth-1 folders-as-packages; skips `_Staging`/`_Unmatched`/infra names/`.tmp` | `router.py:101-152` |
| match (file) | `registry.match_file(filename, ext, folder_context)` | series 0.95 → client 0.80 → first-matching rule 0.85 (0.90/0.75 with folder_hint) → fallback | `router.py:195`; `registry.py:71-103` |
| match (folder) | `registry.match_folder(folder.name)` | **Folder NAME only** — series/client patterns; contents never inspected | `router.py:404-432`; `registry.py:105-120` |
| route | threshold from registry fallback (0.75) | ≥0.75 routed; <0.75 staged to `{dest}/_Staging`; unmatched quarantined to `00_Inbox/_Unmatched` | `router.py:204-221` |
| record | `upsert_asset` **before** move; `update_asset_status` (logs `ingest_events` row) after | Record-before-move honoured for files; folder packages get `create_package` before move | `router.py:228-246,273-285` |
| move | `shutil.move`, collision `_1` counter, **`mkdir(parents=True)` creates any destination** | original filename kept — **no rename** | `router.py:249-264` |
| extract | routed **and staged** files/packages → CKE sync subprocess → `move_to_vault(staging, vault, "01_Knowledge")` | gated on `is_available()` (cke on PATH); `--no-extract` opt-out | `router.py:292-312,711-717` |
| post-verbs | `corp finalize [--approve-all]` (staged → parent), `corp classify` (LLM on `_Unmatched`, Gemini, budget-capped) | quarantine loop exists but is EXISTS-UNTESTED | `cli/ingest.py:310-447` |

Notes: SHA-256 `compute_file_hash` runs on every file (`router.py:202`) but the hash is **only** stored as `source_hash_at_extraction` — never checked against anything (no dedup use). Dual config in one command: paths from legacy `get_config()`, ops.db from `PipelineConfig` (`cli/ingest.py:40-42`).

### Lane B — interactive `corp ingest-inbox` (`cli/ingest.py:193` → `ingest/inbox.py`)

| Stage | Function | Behaviour | Evidence |
|---|---|---|---|
| detect | `_scan_inbox_files` | **Files only — directories skipped entirely** ("folders handled by `corp ingest`") | `inbox_ops.py:26-43` |
| dedup 0 | `_check_dedup` (FileRegistry SHA-256) BEFORE classify/move | known+extracted → skip/re-extract prompt; known+routed → skip/extract prompt; `--auto` skips silently | `inbox.py:200-273,734-737` |
| dedup 0.5 | `_check_near_dup` (MinHash via `light_scan` content) | fails open; **import-dead in production** (see Step 4) | `inbox.py:560-614,739-741` |
| classify | `classify()` → `registry.match_file(filename, ext)` — **no folder_context** | folder_hint confidence modulation unreachable in this lane | `classifier.py:63-111` |
| rename | `propose_name` — ADR-14 `{YYYY-MM}_{TYPE}_{CLIENT}_{Desc}` | compliant names pass through; user [e]dit | `renamer.py:111-180`; `inbox.py:749` |
| route | prompt loop [a/e/d/c/s/q]; `--auto` accepts conf ≥0.90 or `--destination`; low-conf/unmatched need human | **no staging, no quarantine** — a skipped file just stays in Inbox | `inbox.py:754-853` |
| record | `_move_file` **then** `_register_file` (FileRegistry) + `_log_ingest_event` (asset upsert + `ingest_inbox_route` event) + `_log_routing_feedback` | record-**after**-move (reverse of batch); event is undo-capable (`--undo N [--full]`) | `inbox.py:656-713`; `inbox_ops.py:70-139` |
| extract | `_trigger_extraction` → same `_run_extraction`; then `FileRegistry.record_extraction` | `--skip-extract` opt-out | `inbox.py:275-345` |

### Parity table

| Capability | Batch `corp ingest` | Interactive `ingest-inbox` | Parity gap (batch = intended standard, "mechanism, not memory") |
|---|---|---|---|
| ADR-14 rename | **NO** — original names kept (`router.py:253,264`) | YES (`inbox.py:749`) | Batch needs `propose_name` inserted between match and move; renamer is UI-free and importable as-is |
| Content-hash dedup (FileRegistry) | **NO** — hash computed then discarded (`router.py:202`) | YES, pre-move (`inbox.py:734`) | Seam exists: hash already in hand at `router.py:202`; add `get_by_hash` check + `register_file` after move |
| MinHash near-dup | NO (no `light_scan` call anywhere in router) | Wired but BROKEN (datasketch absent) | Both lanes effectively 0; fix dependency first |
| Quarantine unmatched | YES → `_Unmatched` + `corp classify` LLM loop | NO — skip leaves file in Inbox | Interactive relies on human as the quarantine |
| Staging (<0.75) | YES → `{dest}/_Staging` + `corp finalize` | NO — human confirms instead | equivalent-by-design |
| Record-before-move | YES (`router.py:228` comment states intent) | **NO** — registers after move | If parity pass touches inbox lane, move `upsert_asset` pre-move |
| Confidence handling | 0.75 route / stage / quarantine; no human | 0.90 auto-accept (`--auto`), 0.75 needs_human prompt | Two different thresholds for "trust the match" — restart should pick one |
| Folder packages | YES — matched by folder NAME only | NO — dirs invisible | **Neither lane can classify the current backlog per-file** (see Step 3) |
| routing_feedback log | **NO** | YES (`_log_routing_feedback`) | Batch routes learn nothing |
| Undo | NO (events reversible flag set, no CLI verb) | YES (`--undo N [--full]`) | 12 of 22 real interactive events were reverted — undo is load-bearing |
| Extraction of staged files | YES — extracts even <0.75 staged files | n/a | Questionable default: low-confidence files get extracted before human review |

**Third lane (out of scope but load-bearing):** `corp ingest-extractions` (CKE output → vault, `ingest/extractions.py`) is the lane that actually moved the 2,673 March notes; it bypasses registry, rename, dedup and FileRegistry entirely (`ingest_events.action='ingested'`, 2,673 rows, 2026-03-22..27).

---

## Step 2 — Config-truth pass

### 2a. `MyWork/.corp/routing_map.yaml` — PHANTOM targets, but NOT caller-less (Phase-1 finding 10 amended)

Phase 1 recorded "reader has no runtime caller." **Correction:** `resolve_route` (`extraction/routing.py:45`) has two registered CLI consumers, and three more systems require the file to exist:

| Consumer | What it does with it | What breaks if the file is removed |
|---|---|---|
| `corp extract <folder>` (`cli/extract.py:47-66,131`) | `move_to_vault(out_dir, vault, route.vault_target)` | hard exit(1) "routing_map.yaml not found" |
| `corp overnight run` (`cli/overnight.py:167-181,250`) | same per-folder | preflight fails: "routing_map.yaml not found" (`overnight/preflight.py:55-65`) |
| `corp overnight reshape` (`cli/overnight.py:379-386`) | reads key `"folders"` — **a key the v2.0 file doesn't have** (falls back to `{}`) | nothing (already shape-mismatched → classifier gets empty map) |
| `corp doctor` (`cli/system.py:76`; `integrity.py:85-108`) | existence + parse check | reports error issue |

**Phantom-target list** (no `{project_id}` substitution exists anywhere — `move_to_vault` does `vault_root / vault_target; mkdir(parents=True)` (`vault_writer.py:70-71`), so running `corp extract` today would create these as *literal* directory names in the vault):

- `02_sources/{project_id}` (from `10_Projects`)
- `04_evergreen/_generated/template` (from `20_Workflows`)
- `04_evergreen/_generated/evergreen` (from `30_Reference` and `80_Compliance`)
- skeleton `01_projects/{project_id}`

None exist in the vault; the live writer used by both ingest lanes hardcodes `01_Knowledge` (`router.py:714,794`). The file was *updated for Council #24 names on 2026-03-30* (header cites Council #24) while keeping pre-rebuild vault targets — actively maintained, functionally wrong. Status: **BROKEN config, ALIVE-wired on two DORMANT verbs** (`corp extract`, `corp overnight`) — more dangerous than dead: the two commands most likely to be reached for during a restart would split the vault.

### 2b. `MyWork/.corp/content_registry.yaml` (v3.0, 2026-03-23) — live vs phantom

**Dead config surface:** the matcher reads only `series`, `client_patterns`, `destination_rules`, `fallback` (`registry.py:81-103`). The entire `destinations:` block (lines 13–332, ~55% of the file), `routing:` block, `media_collocated`, `versioning/superseded_destination`, `fallback.review_destination`, and `fallback.llm_escalation_threshold` have **zero code consumers** (repo-wide grep = 0). They are PHANTOM: authoritative-looking, parsed, never read.

**Priority inversion:** the file's own `routing.priority` declares `series > destination_rules > client_patterns`; the code implements `series > client_patterns > destination_rules` (`registry.py:81-94`). Observable effect on the backlog: `Blue Yonder Response to Alfa Laval RFP...docx` → client match `10_Projects/Alfa_Laval_Planning` (0.80) instead of the RFP-responses rule (0.85). Config intent and code behaviour disagree; nobody can have noticed because the config's declared order is itself unread config.

**Zone existence (disk sweep, 2026-07-05):**

| Match surface | Destinations | Exist on disk | Phantom (MISS) |
|---|---|---|---|
| series (4) | `30_Reference/Training/{Cognitive_Friday,Lighthouse,Milan,Demo2Win}` | **0/4** | all 4 |
| destination_rules (16) | various | **2/16** (`80_Compliance/Certificates/Current`, `80_Compliance/Policies`) | all `20_Workflows/*` (5), all `30_Reference/Product/*` (3 rules), `Brand_Marketing`, `Data_Analytics`, `Competitive`, `40_Media/Meetings` |
| client_patterns (22) | `10_Projects/{project}` | **17/22** | `Greencore_Planning`, `Merz_Planning`, `PureHealth_Planning`, `Rolls_Royce_Planning`, `Almajdouie_WMS` |
| fallback | `00_Inbox/_Unmatched` | 1/1 | — (`_Review` exists on disk but is consumed by nothing) |

The registry (2026-03-23) describes the **pre-Council-#24 tree**; the restructure (2026-03-29) merged `30_Reference` subdirs and flattened `20_Workflows` to `{Demo_Scripts, Master_Deck, Technical_Presentations, Workshop_Kits}`, and the registry was never rewritten. Because both lanes `mkdir(parents=True)` on move, this is not a crash risk — it is a **silent structure-drift risk**: the first restart run would re-create `20_Workflows/PreSales/...`, `30_Reference/Product/...`, `40_Media/...` against the standing Council decision.

**Which rules would fire on the real backlog:** see Step 3 — 28/72 files match; the only rules that fire are `RFP responses / executive summaries`, `WMS product documentation` (a misfire on client requirement sheets), `Product documentation (generic)`; plus 9 client-pattern hits. No series fires. 44/72 (61%) fall to fallback.

### 2c. `.corp` live copies vs repo `config/` — which copy is consumed

| File | Repo `config/` | `MyWork/.corp` | Runtime consumer reads | Verdict |
|---|---|---|---|---|
| `content_registry.yaml` | v1.0 — pre-#24 zones (`60_Source_Library`, `50_RFP`) | v3.0 (2026-03-23) | **`.corp` copy** (`registry.py:22-26`: `mywork_root/.corp/content_registry.yaml`) | repo copy is a 2-generations-stale seed; **`corp doctor` validates the repo copy, not the live one** (`cli/system.py:75`) — doctor green ≠ live registry sane |
| `naming_config.yaml` | v2 (22 codes / 32 aliases) | absent | **repo copy** (`schema/naming_config.py:18`: `repo/config/naming_config.yaml`) | single-copy, but the *other* half of capture config lives in `.corp` — split-brain by file |
| `routing_map.yaml` | absent | v2.0 (2026-03-30) | `.corp` copy (`cli/extract.py:56` etc.) | see 2a |
| `paths.toml` | present | absent | repo copy (`corp.config`) | fine |
| `config.json` | — | 392 B, 2026-03-10 | **nothing** (grep = 0) | fossil: pre-v2 zone map (`30_Templates`, `90_System`, `FILL_IN` placeholders) — 3 generations old, PHANTOM |
| `solution_matrix.json` | — | 10 KB, 2026-02-19 | **nothing** (grep = 0) | orphan; meanwhile `rfp_excel_agent.py:103` wants `config/rfp/platform_matrix.json`, which is MISSING — the data likely exists here under the old name |

**Single-source answer:** runtime truth for capture is `MyWork/.corp/content_registry.yaml` + repo `config/naming_config.yaml` + `MyWork/.corp/routing_map.yaml` (extract/overnight only). Everything else in `.corp` is dead, and both repo↔.corp "mirror" pairs are fictions (different generations or one-sided).

### 2d. `naming_config.yaml` vs ADR-14 — drift CONFIRMED, worse than counts

- ADR-14 body (2026-03-25): "**19 type codes** (RFP, **DECK, CERT, QA, PROP**, etc.) and **15 client aliases**".
- Live YAML: **22 type codes**, **32 alias groups**. Confirms the foundation brief's 22/32.
- The ADR's example codes `DECK`, `CERT`, `QA`, `PROP` **do not exist** in the live vocabulary (nearest: `PRES`, `SEC`, `VA`, `SOW`) — the ADR body documents neither the ratified set nor the current one. ADR-14 does say the YAML is authoritative ("update it, not code"), so this is doc drift, not config drift — but it is the file CLAUDE.md cites as the naming authority.
- **Functional gap found while testing:** type code `RFP` has `doc_type: rfp_response` and **no `filename_hint`** — a file literally named `...RFP...` renames to `MISC` unless CKE has already classified it (rename happens *before* extraction, so at rename time doc_type is unknown). All 7 backlog RFP responses dry-rename to `2025-xx_MISC_...`. Same gap visible in history: `files` table rows from March are `2026-03_MISC_GEN_JAGUAR_JLR_VA_Questionnaire...`.
- **Cross-config client drift:** `content_registry` client_patterns know Rolls-Royce, Pure Health, Merz, Almajdouie, Greencore→ projects; `naming_config` aliases lack Rolls-Royce/Pure Health/Merz/Almajdouie (auto-generates `ROLLS`, `PUREH`, `MERZP` 5-char codes at rename time, `naming_config.py:118+`). Two vocabularies, independently curated, already disagreeing.

---

## Step 3 — Inbox backlog triage (metadata-only, zero moves)

**Shape:** 75 items = 3 pipeline-infra files (skipped by both scanners) + **2 folder packages**: `raw/` (41 files — 7 RFP-response .docx + 34 RFP/questionnaire .xlsx) and `Training Guides Feb 2026/` (31 files). Newest content file 2026-04-10 (Rolls-Royce APS response); `raw/` dir touched 2026-06-01.

**Lane reality check (dry-run of actual behaviour today):**
- `corp ingest-inbox` (interactive): sees **0 files** — it skips directories, and every content file is inside one of the two folders.
- `corp ingest` (batch): matches the two folders **by name only**: `raw` → no match → whole 41-file package quarantined to `_Unmatched`; `Training Guides Feb 2026` → no match → same. **100% quarantine as-is.**
- Per-file matching (dry replication of `match_file` over all 72 content files, live registry): 28 matched / 44 (61%) → `_Unmatched`. Of the 28, only the 2 `80_Compliance` rules would route into zones that exist; every other match lands in a phantom zone (created on the fly) or a `10_Projects` folder (5 of which don't exist yet).

**Character of the backlog:** this is not inbox flotsam. `raw/rfp/{docs,excel}` is a deliberately curated RFP corpus — exactly the "past-answer style corpus / RFP KB seed" the Phase-1 open question #2 asks about — and the training folder is the Platform Training (Feb 2026) kit that W3 says never enters the system. **Neither belongs to the W1 routing problem the registry was written for; treating them as seeds for R1/W3 is more honest than "routing a backlog."**

### Triage table (operator approval sheet)

Predicted destination = per-file dry match against live registry (method/conf); Age = file mtime. Q? = would quarantine under current registry.

| # | Item (files) | Predicted destination (dry) | Conf | Q? | Age | RFP-rel | Still relevant — gut call | Proposed disposition (for approval) |
|---|---|---|---|---|---|---|---|---|
| 1 | `raw/rfp/docs/` Rolls-Royce APS response (1) | `10_Projects/Rolls_Royce_Planning` (client; **folder doesn't exist**) | 0.80 | no | 2026-04-10 | **R1 pilot seed** | YES — the designated pilot | Hold for R1 style-store/KB decision; do NOT capture-route or auto-extract |
| 2 | `raw/rfp/docs/` Alfa Laval, CCI, Greencore, Pure Health responses (4) | `10_Projects/{client}` (2 folders phantom) | 0.80 | no | 2025-03..2026-01 | YES | YES — submitted-response style corpus | Same as #1 — R1 seed set, single decision |
| 3 | `raw/rfp/docs/` ASOS response + anonymized "(Company Name)" template (2) | `20_Workflows/PreSales/RFP` (phantom zone) | 0.85 | no | 2025-06..08 | YES | YES (template esp. — anonymization reference) | Same as #1 |
| 4 | `raw/rfp/excel/` BRC SIOP set (4) | `_Unmatched` (3) / COMM codes | 0 | YES | 2026-01..02 | YES | **Possibly ACTIVE deal** (revised 2026-02-12) | Operator: active or settled? If active → `10_Projects` by hand, no extraction (standing gotcha: active RFPs don't get extracted) |
| 5 | `raw/rfp/excel/` LabelVie Q&A (1) | `_Unmatched` | 0 | YES | 2026-02-21 | YES | Possibly active (Feb 2026) | Same question as #4 |
| 6 | `raw/rfp/excel/` 3.x requirement set — MBE64/Foundational/AI/Data (10) | `_Unmatched` | 0 | YES | 2025-06..08 | YES | Likely one 2025 RFP's attachment pack (dates cluster w/ Rolls-Royce APS) | R1 KB seed if identified; else archive |
| 7 | `raw/rfp/excel/` RSCT WMS/FMS requirement sheets (4) | 2 → `30_Reference/Product/WMS` (**misroute**: client reqs ≠ product docs; phantom zone), 2 → `_Unmatched` | 0.85/0 | half | 2025-01..2026-03 | YES | Unknown client (RSCT) — identify | R1 KB seed; fix registry before any routing (evidence of rule misfire) |
| 8 | `raw/rfp/excel/` client-matched: Annex CCI, Lenzing forecasts, Merz, NEOM, Systembolaget, Merck×2, ifm, ewave/pricing set, misc IT questionnaires (15) | 4 → `10_Projects/{client}`, 11 → `_Unmatched` | 0.80/0 | most | 2025-05..2026-02 | YES | Mixed — mostly settled 2025 deals | R1 KB seed batch; do not route through W1 |
| 9 | `Training Guides Feb 2026/` hands-on PDFs 00–14 (15) | `30_Reference/Product/Platform` (**wrong** — training, not product docs; phantom zone) | 0.85 | no | 2026-03-24 | no | YES — W3's freshest Platform material | Route to `30_Reference/Training/Platform_Feb2026` (new registry series) + extract — the cleanest W1 restart candidate |
| 10 | `Training Guides Feb 2026/Files for Participants/` exercise payloads (13: xml/json/csv/xsd/trig) | `_Unmatched` | 0 | YES | 2026-03-24 | no | NO — sandbox exercise data | Keep with kit or archive; never extract |
| 11 | `Credentials.xlsx`, `Participants.xlsx`, `Feedback.xlsx` (3) | `_Unmatched` | 0 | YES | 2026-03-24 | no | **Credentials + PII — must not enter KB** | Exclude from any extraction; operator decides delete/keep-local |
| 12 | Infra: `_triage_log.jsonl`, `_triage_schema.yaml`, `folder_manifest.yaml` (3) | skipped by scanners | — | — | 2026-03-11 | no | dead March-era triage experiment | F0 cleanup decision |

**Triage bottom line:** only row 9 (15 training PDFs) is a genuine W1 capture-restart candidate. Rows 1–8 (41 files, all RFP) should bypass W1 and feed the R1 KB/style-store decision — routing them through a filename-matcher would scatter a curated corpus across project folders and `_Unmatched`. Rows 10–11 must be excluded from extraction regardless.

---

## Step 4 — Dedup and identity surfaces

**The single fact that explains all four zero-row tables:** every identity/learning surface was wired *after* the last real use of the lane it instruments.

| Surface (table) | Writer | Wired into lane | Wiring date (git) | Last real lane use | Rows ever |
|---|---|---|---|---|---|
| `routing_feedback` | `_log_routing_feedback` → `RoutingRepository` | interactive only | **2026-03-25** (`bc18ace`) | interactive: **2026-03-24** 20:27 (22 events, 03-23/24) | 0 |
| `content_signatures` | `dedup.store_signature` (on every `check_near_duplicate` call) | interactive only | **2026-03-27** (`d5f434d`) | 2026-03-24 | 0 |
| `extractions` | `FileRegistry.record_extraction` | interactive only (`_trigger_extraction`) | 2026-03-25 (`4e091fa` era) | last inline extraction events 2026-03-23 | 0 |
| `files` | `_register_file` | interactive only | 2026-03-23-ish | 2026-03-24 | 11 (all 03-23/24) |
| `registry_suggestions` | `SuggestionRepository` | no ingest-lane writer (scan tooling only) | — | never | 0 |

Batch lane (`corp ingest`) writes **none** of these — its last real use was 2026-03-14/15 (4 `routed` + 1 `quarantined` events, all into the now-deleted `60_Source_Library` tree). The 2,673-note bulk of March went through `ingest-extractions`, which bypasses them all. So: **unwired-in-the-lane-that-ran, wired-in-the-lane-that-stopped.** Not one of these surfaces has ever been exercised by production traffic.

**MinHash is additionally BROKEN, silently:** `datasketch` is an optional extra (`pyproject.toml:41`, `dedup = ["datasketch>=1.6"]`) and **is not installed** in the production venv (verified: `importlib.find_spec('datasketch') → None` in `Dev/corp-monorepo/.venv`). `check_near_duplicate` catches `ImportError` and returns `[]` at DEBUG level (`dedup.py:284-286`) — the near-dup check is a no-op that reports nothing. Even the interactive lane, run today, would store zero signatures. (Standard install per repo docs is `pip install -e ".[dev,llm]"` — the `dedup` extra was never part of it.)

**Exact seams for parity (batch lane):**
1. Content-hash check: `router.py:202` already computes the SHA-256 — insert `FileRegistry.get_by_hash` there (before Step 3 route), auto-skip like `_check_dedup(auto=True)`; add `register_file` after the move (mirror `inbox.py:734-737` / `inbox_ops.py:163-175`).
2. Near-dup: batch never extracts text — needs a `light_scan` call (interactive does it at `inbox.py:579`) before route; costs one file-parse per file.
3. Extraction history: `_run_extraction` returns `(vault_note, cost)` in both lanes — `record_extraction` is only called from the interactive wrapper (`inbox.py:318-329`); moving that block *into* `_run_extraction` would give both lanes extraction identity for free.
4. Rename: `propose_name(file_path, classify(...))` is UI-free; callable from `ingest_file` between match and move.

---

## Step 5 — Restart-readiness checklist (design input, NOT a runbook — nothing here was executed)

Ordered; each item: why / evidence / risk if skipped.

**Preconditions (F0 config-truth, before any file moves):**

1. **Rewrite `content_registry.yaml` to the Council-#24 tree** (new v4: destinations = zones that exist; add a Training/Platform series for row-9; delete or consciously re-create `PreSales`-style subzones; fix the RSCT-type misfire by tightening the WMS rule or adding a requirements-sheet rule). *Why:* both lanes `mkdir` whatever the registry says; running with v3.0 re-creates the abolished tree. *Evidence:* Step 2b sweep (6/42 live destinations). *Risk:* silent structure drift, 61% quarantine.
2. **Decide the registry priority order** (declared `rules>clients` vs coded `clients>rules`) and make config+code agree. *Evidence:* `registry.py:81-94` vs `routing:` block. *Risk:* client RFP files keep outranking content rules unpredictably.
3. **Decide routing_map.yaml's fate** — rewrite `vault_target`s to `01_Knowledge` (or per-scope subfolders that exist) or park `corp extract`/`corp overnight` behind a guard. Deleting it outright breaks `corp extract`, overnight preflight and doctor (Step 2a). *Risk:* first use of either dormant verb splits the vault with literal `02_sources/{project_id}` dirs.
4. **`pip install -e ".[dedup]"`** (or fold `datasketch` into base deps). *Evidence:* Step 4. *Risk:* near-dup stays a silent no-op; `content_signatures` stays at 0 while looking "enabled".
5. **naming_config touch-ups:** add `filename_hint` for `RFP`; add Rolls-Royce/Pure Health/Merz/Almajdouie aliases (sync with registry client_patterns). *Evidence:* Step 2d; all 7 RFP responses would rename `MISC`. *Risk:* MISC-rate warning fires on day one; ADR-14 body update is optional doc hygiene.
6. **Fix `corp doctor` to validate the live registry copy** (`cli/system.py:75` points at repo v1.0). *Risk:* the health check stays green while live config rots — the exact failure mode this audit found.
7. **Lane choice (operator):** batch is the intended standard, but as-is it can only quarantine the two backlog folders whole. Realistic options: (a) parity-harden batch first (Step 4 seams), (b) run the backlog per-file via `corp ingest --path <file>` loops, (c) unpack folders and use interactive `--auto` with `--destination`. Phase-1 open question #5 stands, now with mechanics attached.

**Backlog run (after 1–7, per Step-3 dispositions):**

8. **Split the backlog by destiny, not by lane:** RFP corpus (rows 1–8) → hold for R1 KB decision (do NOT W1-route; no extraction — active-RFP gotcha + confidentiality; note the 91 MB CCI docx). Training PDFs (row 9) → the actual W1 pilot: route to the new Training series **with `--no-extract` off only after** rows 10–11 are excluded. Credentials/Participants xlsx → never extract.
9. **Dry-run first:** `corp ingest --dry-run` (batch) prints match/route decisions with zero writes (`router.py:235,249` gates) — use it as the acceptance gate for the v4 registry against the real inbox.

**After the run:**

10. **`corp index rebuild`** — no lane triggers it (`cli/index.py:17-42`; Phase-1 step 9 DANGLING). *Risk:* extracted notes invisible to retrieval; "restart worked" claims untestable.
11. **Verification probes (all read-only):** `ingest_events` gained rows dated today with expected actions; quarantine count matches triage prediction (44 if registry unfixed — should be far lower after v4); `files`/`content_signatures` gain first-ever rows (proves Step-4 fixes); no new top-level dirs in MyWork other than registry-sanctioned ones (structure-drift check); `corp retrieve` returns a Feb-2026 Platform training fact (end-to-end proof, closes W3's "freshest material never enters" gap).
12. **Environment preconditions verified this session:** `cke` on PATH = True; `GEMINI_API_KEY` set = True (presence only). Remaining unknown: CKE extraction cost/quality on 15 PDFs — bounded, fixture-mode-tested engine (Phase-1 5/5).

---

## Backlog-seed table

| Seed | Goal (functional) | Evidence | Depends on | Size gut-feel | Decision required first? |
|---|---|---|---|---|---|
| F0-1 Registry v4 rewrite | Live registry routes only into Council-#24 zones; backlog match-rate >80% on dry-run | Step 2b (6/42 destinations exist; 61% quarantine); Step 3 dry-match | — | M (half-day: rewrite + `--dry-run` iterate) | Yes — keep-or-kill for PreSales/Media sub-zones |
| F0-2 routing_map fate | `corp extract`/`overnight` can't split the vault | Step 2a (literal `{project_id}` mkdir; 4 consumers) | — | S | Yes — rewrite vs guard |
| F0-3 Dedup dependency + parity seams | Batch lane gets hash-dedup + rename; MinHash actually runs | Step 4 (datasketch absent; 4 seams located) | F0-1 | M (code, 4 insertion points, tests exist for pieces) | Lane-choice ruling (Q5) |
| F0-4 naming sync | RFP filename hint; client aliases match registry; doctor checks live copy | Step 2d; `cli/system.py:75` | — | S | No |
| W1-restart pilot (training kit) | 15 Platform PDFs routed + extracted + indexed + retrievable | Step 3 row 9; probes Step 5.11 | F0-1..4 | S-M (one supervised run + rebuild) | Exclusion of rows 10–11 approved |
| R1-seed RFP corpus custody | 41-file curated RFP corpus lands in the R1 KB/style-store design, not scattered by W1 | Step 3 rows 1–8; Phase-1 open Q2 | R1 KB architecture decision (federate/merge) | decision-only now | **Yes — blocks any touch of `raw/`** |
| Config split-brain close-out | One documented source per config file; fossils (`config.json`, `solution_matrix.json` vs missing `platform_matrix.json`) resolved | Step 2c table | F0-1/2 | S | Yes for platform_matrix rename-vs-rebuild |
| Backlog hygiene | `_Review` (consumed-by-nothing), March triage infra files, `_Unmatched/Cognitive_Fridays` leftovers cleared | Steps 2b/3 row 12 | W1 restart done | S | Yes (deletions) |

---

*Audit complete. Read-only discipline held: no pipeline execution, no file moves, no config edits; SQLite opened `mode=ro`; inbox touched metadata-only; no OneDrive path traversed. Deliverable 2 (HTML process map) accompanies this file.*
