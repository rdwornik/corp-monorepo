# Deep Audit C — Knowledge Extraction (Wave 2)

> **Consumed by:** `docs/audits/2026-07-06-technical-architect-intake.md` (DR register — extraction-path evidence).

**Date:** 2026-07-05 · **Branch:** `docs/deep-extraction` (worktree `cm-deep-extraction`) · **Base:** `2753601` (main, Phase-1 audit merged)
**Method:** read-only. Code reading + `data/_outputs/v3` sampling (203 notes + 203 sidecars, reads only) + `overnight_state.db` via `mode=ro`. No extraction runs, no LLM calls, no OneDrive traversal. Baseline: `docs/audits/2026-07-05-functional-*.md`.
**Scope:** settle the 2026-06-21 brainstorm verify-first triad; establish the emit-side output→vault contract (Audit D owns the consume side); produce R2 gap-fill backlog seeds.

**One-line verdict:** the extraction engine is genuinely strong on the `cke process` lane (scene detection, transcript generation, fact enrichment all real), but the telemetry/vault plumbing around it is systematically unwired — tier, cost, per-fact grounding, provenance, and facts all get computed and then dropped before anything downstream can use them.

---

## Step 1 — Verify-first triad

### 1.1 Frame sampler — VERDICT: EXISTS (scene-aware), with a lane split · brainstorm item SKIP (narrow parity gap remains)

- FFmpeg scene detection is real and current: `extractor/frames/scene_detect.py:31-65` runs `select=gt(scene,0.35)` + `showinfo`, parses `pts_time` from stderr. Post-processing: floor-supplement for long low-change videos (<8 candidates, >10 min → every 45 s), circuit breaker (>60 candidates → even-sample 35), consecutive-frame dedup via **histogram correlation >0.95** (`:102-114, :173-183`), dynamic cap `min(unique+5, 35)`. Fallback to time-based sampler on any ffmpeg failure.
- It is **not pHash** — dedup is HSV-histogram correlation. Prior handoffs saying "FFmpeg scene detection" are accurate; any "pHash" memory is not.
- **Lane split:** `cke process` calls `scene_detect` (`scripts/run.py:439`). The manifest lanes call the dumb uniform sampler `sample_frames` (interval 10 s, max 500) — `batch.py:219`, `batch_api.py:503`. The real v3 corpus was produced by the `process` lane (all 203 sidecars are `{stem}.json`, the `run.py` writer — `batch.py` writes a fixed-name `extract.json`, of which v3 contains **zero**), so production extraction did get scene detection; any future overnight/manifest run would not.
- Dead code found: `frames/extractor.py::extract_frames` (pixel-diff change detection) has **zero callers** — a third, orphaned sampling implementation.

### 1.2 Transcripts — VERDICT: GENERATES (dedicated call); diarization GAP; transcripts never reach the vault

- The system **generates** transcripts — it does not parse existing ones. `transcript.py:50-134` makes a dedicated second Gemini call reusing the already-uploaded video file URI (`gemini_file_uri`), prompt: verbatim transcription, `[MM:SS]` timestamps every 30-90 s, max 32,768 output tokens, 3 retries. Wired at `scripts/run.py:539-556` (video files only, after extraction succeeds).
- **No transcript parsing anywhere:** grep for `.vtt|.srt` = 0 hits in `src/`. `FileType.TRANSCRIPT` exists in inventory, but that just routes an existing text transcript FILE through tiers 1/2 as text — there is no ingestion of subtitle formats.
- **Diarization: prompt-level only.** The prompt asks Gemini to label speakers "(e.g., Speaker 1, Speaker 2, or by name if introduced)". No diarization library (pyannote/whisperX absent). Whisper appears only as legacy config keys (`settings.yaml:330-378`) and an unwired ffmpeg audio-preprocess helper (`scripts/preprocess_audio.py`).
- **Two gaps:** (a) the batch/manifest lane has **no transcript step at all** (`batch.py::_process_single` — none); (b) transcripts are written as `{stem}_transcript.md` and `corp ingest-extractions` **explicitly skips `*_transcript.md`** (`ingest/extractions.py:33`) — so even on the good lane, generated transcripts never leave the package directory. Searchable spoken knowledge dies in `data/_outputs/`.

### 1.3 Per-fact source-span grounding — VERDICT: GAP (confirm the brainstorm item)

What exists (`fact_validation.py` + `extract.py:291-348`):
- **Number cross-referencing only:** every number in a fact is matched (±1 % tolerance) against every number in the locally-extracted source text; anomaly regexes (>100 % percentages, magnitude spreads >400x, future dates). Produces `verification_status` ∈ {verified, unverified, flagged_mismatch}.
- **A fact with no numbers is auto-`verified`** (`fact_validation.py:121-130`) — the 93.6 % verified rate below is inflated by definition.
- **`locator` is an LLM self-reported page/slide number**, validated only for range (1..max_pages), never against content (`extract.py:272-288`). No quoted snippet, no character offsets, no span check. Haiku-enrichment facts always get `locator: null`.
- **Zero downstream consumers of the per-fact `locator`:** grep outside `extractor/` = 0 hits (the similarly-named `source_locator` is a different, path-level field). The whole enriched-facts structure lives only in the JSON sidecar, and the vault ingest **skips all `.json`** (`ingest/extractions.py:32`) — so no vault note, index row, or retrieval path can cite a fact back to a page, let alone a quote.

Real-corpus numbers (all 203 v3 sidecars, 5,046 facts):

| verification_status | count | share |
|---|---|---|
| verified | 4,723 | 93.6 % (inflated by no-number auto-verify) |
| unverified | 206 | 4.1 % |
| flagged_mismatch | 74 | 1.5 % |
| (missing — no source text) | 43 | 0.9 % |

`locator` populated: 2,976 / 5,046 (59 %). `polarity`: unknown 4,067 (81 %), positive 735, negative 244.

**Conclusion for the architect:** claim→cite grounding for R1 is greenfield. The brainstorm item stands as real work: it needs a prompt/schema change (quote + offset per fact), a verifier (span actually occurs in source), and a carrier (facts must survive into the vault/index — today they are sidecar-only).

---

## Step 2 — Tier routing and cost truth

### 2.1 Which tier each file type actually takes (`tier_router.py::route_tier`)

| File type | Tier | Rule |
|---|---|---|
| video / audio | 3 MULTIMODAL | always (`:94-100`) |
| .pptx image-heavy + renderer available | 3 | rendered to PNG, vision call (`:104-119`) |
| .pptx text-heavy | 2 TEXT_AI | local text → text-only call |
| .xlsx / .docx | 2 always | Gemini rejects these MIME types for upload — capped at 2 even when text extraction fails (`:131-158`) |
| .pdf good text | 2 | |
| .pdf partial/none (scanned) | 3 | |
| .txt/.md/transcript < 5,000 chars | 1 LOCAL | no API call |
| everything else with good text | 2 | |

### 2.2 Model strings: three overlapping selectors, and the docs lie

- `TIER_MODELS` (`tier_router.py:52-56`): T2 `gemini-3.1-flash-lite`, T3 `gemini-3.1-pro-preview` — but this feeds **labels and cost estimates**, not the actual call.
- Actual selection is split across: (a) `_get_model` → `config gemini.model` = **`gemini-3-flash-preview`** (`settings.yaml:6`) or `model_override`; (b) `providers/router.select_model` (file-based: pptx/video/pdf → `gemini-3.1-pro-preview`, text → `gemini-3.1-flash-lite`) used at `extract.py:468,1034`; (c) `providers/router.route_model` (tier-based: **T2 default → `claude-haiku-4-5-20251001`** when `ANTHROPIC_API_KEY` present, >190K tokens → Gemini, escalation `claude-sonnet-4-6`) used by `strategies/text_provider.py:87`. Plus `_haiku_enrichment` hardcodes Haiku (`extract.py:770`).
- **Empirical (11-note v3 sample, `model` frontmatter): claude-haiku-4-5 ×6, claude-sonnet-4-6 ×2, gemini-3-flash-preview ×2, gemini-3.1-pro-preview ×1.** The March text tier ran mostly on Anthropic. "CKE = Gemini extraction engine" (module docstrings, tier_router header still says "Gemini 2.5 Flash") is stale on two counts: model family and version strings.

### 2.3 Why all 601 overnight files show `tier=pending`

`cli/overnight.py:128` inserts the literal string `"pending"` into the **tier** column (`state.add_file(..., tier="pending")` — a status word in a tier field). No code path ever updates it: `state.update_file_status` (`overnight/state.py:143-172`) has no tier parameter. Structurally, the tier decision happens **inside the CKE subprocess**, and only aggregate tier counts cross back over the stdout summary parse (`cke_client._parse_extraction_summary`) — corp-side per-file tier can never be backfilled. Verified live (mode=ro): all 601 file rows are exactly `tier='pending', status='done'`.

### 2.4 Per-file cost: averaged, estimated, or dropped — never measured

- Overnight `files.cost` = folder run cost ÷ files done, a uniform average (`cli/overnight.py:239`).
- The run-level "cost" is itself an **estimate**: `TIER_COSTS` constants summed per file (`batch.py:147`), or token-based `_estimate_gemini_cost` on one path (`extract.py:648`). No API-reported usage is recorded.
- `extraction_cost_usd` appears in only **1/11** sampled March notes (the code that emits it postdates most of the corpus).
- The dedicated ledger is shelf-ware: `providers/cost_tracker.py` (`log_cost`, `get_monthly_spend`, `check_budget`) has **zero callers**, and `cost_log.jsonl` does not exist on disk. The monthly budget guard it implements has never run.

### 2.5 Why ops `extractions` has 0 rows

The writer exists (`ops/file_registry.py:137` `record_extraction`) but is wired into exactly one path: the **interactive `corp ingest-inbox` [e]xtract flow** (`ingest/inbox.py:324`), and even there it silently no-ops unless the file already has a `files` registry row (`get_by_hash` gate at `:322`). The two lanes that did all real extraction — bulk `corp ingest-extractions` (2,673 notes) and overnight (601 files) — never call it. The per-model/per-cost extraction history the table was designed for was structurally unreachable from day one.

---

## Step 3 — Overnight pipeline state machine

### 3.1 The 9 runs (overnight_state.db, mode=ro)

| run_id | started | completed | scope | status | files (rows) | cost |
|---|---|---|---|---|---|---|
| 20260312_192817 | 03-12 19:28 | 19:28 | templates | dry_run | 0 | 0 |
| 20260312_214017 | 03-12 21:40 | 22:21 | full-reshape | dry_run | 0 | 0 |
| …8d23c366 | 03-13 11:03 | **NULL** | all-non-project | **running** | 0 | 0 |
| …96f52d1e | 03-13 11:06 | **NULL** | all-non-project | **running** | 0 | 0 |
| …ab173039 | 03-13 11:07 | 12:35 | all-non-project | completed | 0 rows (counters say 270/0) | 0 |
| …290cf2df | 03-13 12:56 | **NULL** | all-non-project | **running** | 61 | 0 |
| …2f549b60 | 03-13 13:09 | **NULL** | all-non-project | **running** | 0 | 0 |
| …227752fe | 03-13 13:09 | 14:08 | all-non-project | completed | 270 | $0.243 |
| …eef5765e | 03-13 23:28 | 23:28 (4 s) | all-non-project | completed | 270 | $0 |

### 3.2 Why 4 runs are stuck `running` — no terminal-state guarantee

- **There is no try/finally.** Any unhandled exception between `create_run` (`cli/overnight.py:105`) and `complete_run` (`:254`) leaves the run `running` forever. Unguarded candidates on that stretch include the bare `routing_map.yaml` open (`:171-173`, FileNotFoundError), scan/manifest build, and `KeyboardInterrupt` during a long CKE subprocess call.
- The timestamps show the classic crash-retry signature: launches at 11:03:47, 11:06:37, 11:07:06 (2.8 and 0.5 minutes apart) — two crashes, then a completed run; again 13:09:03 / 13:09:09 (6 s apart).
- Current code preserves the leak class and adds two explicit no-terminal-write `return` paths in `_run_full_reshape`: dry-run (`:414-416`) and phase-1 scan failure (`:341`) both return without `complete_run`. (The March runs predate the 03-30 refactors, so the exact 2026 crash sites can't be pinned, but the as-built machine today has the same failure mode.)
- **No janitor:** nothing detects or closes stale `running` runs. `--reset` only deletes *pending file rows* (`:55`), never closes runs — and it explains the counter drift: ab173039 says `total_files=270` while owning **zero** file rows.
- The `eef5765e` oddity — 270 files "done" in 4 seconds at $0 — is the resume path: `cke_client.extract_sync` defaults `--resume` (`cke_client.py:183,205-206`), CKE skipped everything already extracted, and corp marked all pending rows done at cost 0.

### 3.3 Batch API — dead-limb assessment

- **Capability:** complete and tested. `extractor/batch_api.py` (649 lines, `BatchJobRunner`: JSONL build → Gemini Batch submit → poll → parse, T2-only, T1 local, T3 sync fallback) + `tests/extractor/test_batch_api.py`; reachable via `corp overnight --batch` and `corp extract --batch` → `cke_client.extract_batch` → `cke process-manifest --batch`.
- **Use:** zero, ever. `batches` table 0 rows — and it could never be otherwise: corp-side `state.create_batch` / `update_batch_status` have **zero callers**. The corp `batches` table is orphaned schema regardless of whether the Batch API is ever used; CKE tracks batch state in its own `status.json`.
- **Kill cost (S):** delete `batch_api.py` + its tests, the two `--batch` CLI flags, `cke_client.extract_batch`, the `--batch*` options on `process-manifest`, and the `batches` table + methods. No other code references them.
- **Revive cost (M):** re-verify the Gemini Batch API surface (untouched since March), wire `create_batch`/`update_batch_status` into the run loop, and reconcile per-file batch status back into corp state.
- **Economics:** the 50 % discount applies to Tier-2 calls priced ~$0.001/file. At March scale (601 files, $0.24 actual) the limb's total value is **~$0.12 per full corpus run**. Input to the decision: KILL unless R2 volume grows two orders of magnitude.

### 3.4 The leaked `overnight_staging/20260312_192817/` dir

The dir name equals the run_id of the first dry_run (03-12 19:28, scope `templates`). Three fossils identify it as **pre-consolidation code output**: (a) the `overnight_staging` string appears nowhere in current `src/` and `git log -S` finds it only in audit docs; (b) scope `templates` is not a valid scope in current code (`OVERNIGHT_SCOPES` = all-non-project/reference/workflows/full-reshape); (c) its runs-row carries `model='gemini-2.5-flash'`, a string purged from the codebase 2026-03-12. So the leak evidences the *old* pipeline's missing teardown — but the **current lane has no teardown either**: nothing cleans `%LOCALAPPDATA%/corp-by-os/staging/{folder}/` after `move_to_vault` (which moves only package dirs, leaving `manifest.json`/`status.json` — the 2026-03-23 leftovers in `staging/` confirm it).

---

## Step 4 — Output→vault contract (EMIT side; Audit D owns consume-from-vault)

### 4.1 Two emit lanes with different contracts

**Lane A — `cke process` → `corp ingest-extractions` (the lane that built the actual vault, 2,673 notes March 26-27):**
```
data/_outputs/{v3}/{scope}/{client}/{pkg}/
├── index.md                          (package rollup — ingest SKIPS)
├── source/{video,docs,notes,frames,slides}/   (originals + kept frames — ingest SKIPS)
└── extract/
    ├── _meta.yaml                    (model, pipeline 2.0.0, prompt_hash — ingest SKIPS)
    ├── {date}_{name}_{hash4}.md      (THE note — the only artifact that reaches the vault)
    ├── {stem}.json                   (31-key sidecar incl. enriched facts — ingest SKIPS)
    ├── {stem}_transcript.md          (ingest SKIPS)
    └── synthesis.md                  (ingest SKIPS)
```
Operator must hand-stage packages into `scope/client/package/` (gotcha: flat dirs → 0 notes). Ingest gates: `title` present, `quality_score` ≥ 25 *if present*, `trust_level=verified` overwrite protection; injects `trust_level: extracted`; writes flat to `01_Knowledge/`; logs `ingest_events`. Index rebuild is a separate manual command.

**Lane B — manifest → `cke process-manifest` → `move_to_vault` (`corp extract`, `corp overnight`; never reached the vault in practice):**
`extraction/manifest_emitter.py` writes v2.1 provenance per entry; `extraction/contract.py` validates it; CKE extracts into `%LOCALAPPDATA%/staging/{folder}/{entry_id}/`; `extraction/vault_writer.move_to_vault` then moves **entire package directories** — sidecars, `_meta.yaml`, `source/` and all — into `vault_root/{vault_target}` with **no quality gate, no quarantine, no ingest events, no trust injection** (only verified-overwrite protection). Two defects: (1) `vault_target` comes verbatim from `routing_map.yaml`, so the `10_Projects` route would create a literal folder named `02_sources/{project_id}` — the placeholder is never substituted (no format call anywhere on the path); (2) the 20/30 targets are `04_evergreen/_generated/*`, zones that exist on disk nowhere (Phase-1: vault has no such dirs — proof Lane B never completed a vault write). Correction to Phase-3: `routing_map.yaml` **does** have registered runtime readers (`corp extract` at `cli/extract.py:56-66`, `corp overnight` at `cli/overnight.py:171-181`); what's phantom is its *targets*, not its *reader*.

### 4.2 The v2.1 handshake break (validated, then dropped)

`content_origin`, `source_category`, `source_locator`, `routing_confidence`: emitted into the manifest (`manifest_emitter.py:113-132`), **required** by corp's own validator (`contract.py:14,100-114`), then **silently discarded** by CKE's parser — `ManifestEntry.from_file` reads only `id/path/doc_type/name/client/project/user_context` (`extractor/manifest.py:56-64`). No CKE template emits them, so the four `notes` columns the index reserves for them (`index_builder.py:687-690`) can never be populated by CKE output. A contract enforced on the wire and ignored by the receiver.

### 4.3 EMIT field table

Produced-in = `config/extractor/templates/extract.md.j2` line, or code. Populated = of 11 sampled real v3 notes (spread across projects + source_library). **[H] = handshake field — join key for Audit D's consume-side table.**

| Field | Produced where | Populated (of 11) | Intended consumer |
|---|---|---|---|
| `source` | j2:2 | 11 | index `notes.source` **[H]** |
| `type` | j2:3 | 11 | index `notes.type` **[H]** |
| `title` | j2:4 | 11 | ingest validation gate; index **[H]** |
| `date` | j2:5 | 11 | index **[H]** |
| `source_type` | j2:6 | 11 | index + `rfp_visible` computation **[H]** |
| `layer` | j2:7 | 11 | index **[H]** |
| `domains`/`topics`/`products`/`people` | j2:8-11 | 11/11/10/6 | index (comma-joined) → retrieval, coverage map **[H]** |
| `confidentiality` | j2:12 | 11 | index **[H]** |
| `authority` | j2:13 | 11 | **none** — not indexed, nothing reads it |
| `client` | j2:14 | 9 | index `notes.client` **[H]** (the 258/488 empty-client problem starts here) |
| `project` | j2:15 | **0** | index `project_id` **[H]** — never populated on Lane A; project grouping dead on arrival |
| `valid_to` | j2:16 | 6 | index |
| `language`, `quality` | j2:17-18 | 11 | index (`quality` is the LLM's self-report string; distinct from `quality_score`) |
| `duration_min` | j2:19 | 1 | none |
| `model` | j2:20 | 11 | index `notes.model` (the tier/model truth that DOES survive) |
| `routing_reason`, `prompt_version` | j2:21-22 | 11 | none (provenance display only) |
| `tokens_used` | j2:23 | 11 | index |
| `quality_score` | j2:24 (always emitted by current code) | **1** | ingest quality gate **[H]** — gate no-ops when absent, i.e. for ~91 % of the March corpus |
| `tag_validation_warnings` | j2:25 | 0 | none |
| `extraction_cost_usd` | j2:26 | 1 | none |
| `source_tool` | j2:27 | 11 | vault-writer invariant test |
| `schema_version` (=2), `extraction_version`, `depth` | j2:28-30 | 11 | index (`extraction_version`, `depth`) |
| `doc_type` | j2:31 | 11 | index + `rfp_visible` **[H]** |
| `key_facts` | j2:32 | 4 | **none** — display only; never indexed |
| `entities_mentioned` | j2:33 | 4 | none |
| `source_path`/`source_hash`/`source_mtime`/`extracted_at` | j2:34-37 (freshness block) | 11 | index dedup (`source_hash`), freshness scanner, resume-skip **[H]** |
| `tags` | j2:38 | 11 | Obsidian only — index does not read tags |
| `{doc_type}_overlay` | j2:39 | (when overlay) | none |
| `trust_level` | **not emitted** — injected at ingest (`extractions.py:295`) | n/a | index `confidence`, overwrite protection **[H]** |
| `content_origin`/`source_category`/`source_locator`/`routing_confidence` | **not emitted** (manifest-only, §4.2) | 0 | index columns exist → **phantom handshake [H]** |
| JSON sidecar (31 keys: enriched `facts` w/ verification_status+locator+polarity, `overlay`, `freshness`, `validation_result`…) | `run.py:603-654` | 203/203 | **no consumer on the vault path** (ingest skips .json). Intended consumers: CPE `render` (expects `extract.json` in `_knowledge/_cke_output/` — wrong name AND wrong place for this corpus) and `extract_training_data.py` (fixtures) |

---

## Step 5 — Quality chain

### 5.1 What `quality_score` computes from (`synthesize.py:82-120`)

`min(100, …)` of: facts count ×2 capped 30 (uses `max(key_facts≥30chars, facts≥30chars)` — the v0.6.0 gotcha fix, confirmed in code) + **verified-ratio ×20** (from `verification_status`, i.e. inherits the no-number auto-verify inflation) + overlay fields ×4 capped 20 + content chars /1000×3 capped 15 + entities ×3 capped 15. Computed at package build for every note by current code — but present in only 1/11 sampled March notes (score 28), so the ingest quality gate (`≥25 if present`) effectively **passed the March corpus unexamined**.

### 5.2 `verification_status` in real outputs

See §1.3 table: 93.6 % verified / 4.1 % unverified / 1.5 % flagged_mismatch across 5,046 facts. Flagged facts do surface in the .md body ("Flagged Facts" section, j2:103-111) — the only place fact validation is visible downstream.

### 5.3 Facts pipeline — the kill-or-fix evidence

The intended chain and its three independent breaks:

```
CKE sidecar (extract.json)                 [break 1: real corpus emits {stem}.json — glob finds 0]
  → cpe render (_load_extractions rglob "extract.json"
     under {project}/_knowledge/_cke_output/)   [break 2: outputs live in data/_outputs + staging;
                                                 0/29 real project folders even have _knowledge/]
  → facts.yaml (key_points>20chars + summaries>50chars,
     with source id/title/topics — NO verification_status, NO locator)
  → index_builder._load_and_insert_facts (vault_path/facts.yaml
     or onedrive _knowledge/facts.yaml)         [break 3: cpe render never ran on a real project —
                                                 no facts.yaml exists anywhere]
  → facts + facts_fts tables → corp query (search_facts)
```

`facts=0 rows ever` is over-determined: any one break suffices; all three exist. Note also that even a repaired chain carries **less** than the sidecar already holds — `_build_facts` (`project/renderer.py:149-179`) strips verification_status/locator/polarity and keeps only key_points and summaries.

**If KILL (operator lean, notes-as-truth-store)** — consequence list:
- Drop/ignore: `facts`, `facts_fts` (+2 triggers), `projects.facts_count`, `meta.total_facts` — all zero today; no data loss.
- `corp query` (`cli/query.py:34` → `query_engine.search_facts`) loses its primary mode — repoint to `notes_fts` or retire (analytics group already covers notes-based queries).
- `cpe render` keeps its `project-info.yaml`/`index.md` halves; the `facts.yaml` half becomes explicitly project-local documentation, not an index feed.
- `actions/brief_actions.py` reads `facts.yaml` directly from the project dir (not the table) — unaffected structurally, still starved of input until `cpe render` runs.
- Tests over the facts tables/query engine need pruning.
- What is genuinely lost: nothing current — but a future fact-granular retrieval (R1 claim→cite) would then have to be built on the sidecar/notes, which is where the verified facts actually live anyway.

**If FIX** — minimum: repoint renderer glob to `{stem}.json` + real output roots; run `cpe render` per project; feed enriched facts (not key_points) so verification lineage survives; add facts.yaml to the vault writer path; rebuild index. That is a new pipeline in all but name, duplicating what `notes_fts` already serves — build only if fact-granular citation becomes an R1 requirement.

---

## Step 6 — R2 gap-fill readiness ("coverage gap triggers targeted extraction")

### 6.1 What exists today for scoped, on-demand extraction

| Capability | State | Evidence |
|---|---|---|
| Per-folder scoped extraction, one command | **EXISTS-UNTESTED** — `corp extract <folder>`: route → policy → manifest → CKE → move_to_vault | `cli/extract.py` (registered, `cli/__init__.py:123`); never used for real (Lane B never wrote to vault) |
| Per-folder opt-out/extension policy | EXISTS — `folder_manifest.yaml` (`enabled`, `allow_extensions`) | `extraction/folder_policy.py`, honored at `cli/extract.py:70-77` |
| Per-folder manifest emit + validation | EXISTS (v2.1 contract; fields dropped by CKE, §4.2) | `manifest_emitter.py`, `contract.py` |
| Resume/idempotency | EXISTS — source_hash skip (`run.py:461-491`) + `--resume` status.json skip (default on sync lane) | verified in code; eef5765e run = 270 skips in 4 s |
| Re-extraction of an existing package | EXISTS — `cke reextract` (history-preserving) | `scripts/run.py:782-796` |
| Staleness detection | EXISTS — freshness scanner runs as an overnight phase, writes `freshness_report.json` | `cli/overnight.py:447-506` |
| Scheduled execution pattern | PROVEN elsewhere — N5 nightly conformance is the one living scheduled loop | Phase-3 N5 |
| **Product-scoped selection** | **MISSING** — scopes are folders (`reference`/`workflows`); the coverage map keys are product families. No product filter exists on any extraction surface | `OVERNIGHT_SCOPES` (`cli/overnight.py:17-22`); coverage map = synthesis §3 |
| **Coverage-gap detection as code** | **MISSING** — the THIN/RICH matrix exists only as an audit table; nothing computes it at runtime (`notes.products` isn't even canonicalized — W5) | telemetry §1.4 |
| **Trigger/schedule for extraction** | **MISSING** — no scheduler invokes any extraction command; overnight is a remembered manual command | no cron/task config anywhere in repo |
| **Auto index rebuild after ingest** | MISSING — rebuild is a separate manual `corp index` step | Phase-3 W2 break/limit |

### 6.2 Cost basis (March telemetry, `mode=ro`)

- Measured: **$0.243 for 270 files** (run 227752fe) and $0.277 total across 601 file rows → **~$0.05-0.09 per 100 files** for a text-dominant corpus (30_Reference/20_Workflows mix). Caveats: these are *estimate-sums* (TIER_COSTS constants), not API-billed figures (§2.4), and the corpus routed almost entirely to Tiers 1-2.
- Multimodal-heavy targets change the picture by ~30x: 100 video/scanned files ≈ **$3.00** at the $0.03 T3 constant (+ transcript second-calls, unpriced in TIER_COSTS).
- Deep-mode re-extraction on Pro (Council #20 rebuild) also runs hotter than the flash-lite estimates. For R2 planning: budget from tier mix, not from the $0.24 headline.

### 6.3 What's missing to make it a mechanism instead of a remembered command

1. **Product→source mapping.** The gap loop's unit is a product family; the extraction unit is a folder. Bridging needs either per-product source folders under 30_Reference (partially true: `Products/`, `Training/`) or manifest filtering by classifier/product tags — neither exists.
2. **A runtime coverage query.** `SELECT products, doc_type FROM notes` + canonicalization (W5) → THIN list. All parts exist (analytics CLI proves the query layer); the composition doesn't.
3. **A trigger.** N5's scheduled-cloud-routine pattern is the proven template; pointing it at `corp extract` requires the Lane B fixes first (§4.1: {project_id} bug, no quality gate, sidecars into vault, no staging teardown) — otherwise scheduled runs write ungated packages into phantom vault zones.
4. **Closing telemetry.** Post-run: auto index rebuild + coverage re-query + delta report (the morning-report scaffold in `overnight/monitor.py` is reusable). Without it the loop can't know a gap closed.

---

## Backlog seeds (R2 inputs — sizes are gut-feel, not estimates)

| Seed | Goal (functional) | Evidence | Depends on | Size gut-feel | Decision required first? |
|---|---|---|---|---|---|
| E1 Per-fact span grounding | A fact carries a quoted snippet + verified span so R1 can cite; facts survive into the index | §1.3: locator = unverified LLM page ref, 0 consumers; sidecars die at ingest | E5 verdict (where facts live), prompt/schema change | M-L | **Yes** — grounding design + carrier choice |
| E2 One extraction lane | Either manifest lane gains scene-detect + transcripts, or `cke process` becomes the only lane and manifest lane is retired | §1.1/§1.2 lane split; real corpus all came from `process` lane | E7 | S-M | Yes — which lane wins |
| E3 Overnight terminal-state hardening | Runs always reach a terminal state; tier + real cost written per file; stale-run janitor; staging teardown | §3.1-3.2: 4 stuck runs, no try/finally, tier=pending literal, cost=average | none | S | No |
| E4 Kill Batch API limb | Remove batch_api.py + flags + orphaned `batches` table (or consciously revive) | §3.3: 0 uses, ~$0.12 value per corpus run, corp-side writers have 0 callers | none | S | **Yes** — operator kill/keep (lean: kill) |
| E5 Facts pipeline verdict | Execute KILL (drop tables, repoint `corp query` to notes_fts) or FIX (new emitter feeding enriched facts) | §5.3: 3 independent breaks, 0 rows ever, notes-as-truth lean | none | S (kill) / L (fix) | **Yes** — architect ruling |
| E6 v2.1 provenance handshake | Manifest provenance actually lands in note frontmatter + index columns (or contract + columns are deleted) | §4.2: validated-then-dropped; 4 index columns permanently empty | E2 | S-M | Yes — propagate vs delete |
| E7 Lane B repair or retirement | `corp extract` writes gated notes (quality gate, no sidecars in vault, real vault_target, `{project_id}` substitution) or is retired for Lane A + ingest-extractions | §4.1: literal `{project_id}` bug, no gates, phantom zones | routing_map target decision (Audit D vault zones) | M | **Yes** — joint with Audit D |
| E8 quality_score coverage | Gate actually gates: re-emit or backfill scores for notes lacking them; decide threshold semantics for R2 ingests | §5.1: 1/11 March notes carry a score; gate no-ops otherwise | none | S | No |
| E9 Product-scoped extraction + coverage query | `corp extract --product <family>` (or equivalent) + runtime THIN/RICH query = the R2 loop's two halves | §6.1 MISSING rows; coverage map is audit-only today | E7, W5 canonicalization | M | Yes — scoping mechanism |
| E10 Cost truth | One measured cost per extraction (API usage → cost_log.jsonl or frontmatter), budget guard live | §2.4: ledger has 0 callers, all figures are constants/averages | none | S | No |
| E11 Transcript-to-vault carrier | Generated transcripts become searchable (ingest stops skipping `*_transcript.md`, or transcript content merges into the note) | §1.2: transcripts generated then stranded in packages | E2 | S-M | Yes — carrier form |

**Sequencing input for the architect:** E3 + E10 are decision-free hygiene and unblock trustworthy R2 telemetry. E5 + E7 are the two rulings everything else waits on. E9 is the R2 loop itself and should not start before E7's lane verdict.

---

*End of Deep Audit C. All DB access `mode=ro`; writes limited to this file. Companion process map: `2026-07-05-deep-extraction.html`.*
