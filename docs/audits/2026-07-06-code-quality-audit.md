# Code Quality Audit — `src/corp/` (for the technical architect)

> **Date:** 2026-07-06 · **Scope:** read-only code-quality assessment of `src/corp/` (193 files, 41,715 LOC) · **Method:** tool metrics (radon 6.0.1, vulture 2.16, ruff 0.15.8 `--select ALL` report-only) + whole-module deep reads of the R1-critical set + cross-cutting inventories · **Baseline proof:** `pytest -x -q` on the untouched tree = **2,564 passed, 6 skipped** (160s).
>
> Companion to the functional handover (`2026-07-06-technical-architect-intake.md`): the intake says WHAT to build; this says WHAT THE CODE UNDERNEATH IS LIKE. Functional findings (seams, dead processes) are cited from the six `2026-07-05-deep-*.md` audits, not re-litigated. Analysis tools were installed into the venv for this session only — nothing added to `pyproject.toml`.

---

## 0. Executive verdict (read this first)

1. **The codebase is bimodal, not uniformly messy.** One half is house-standard and genuinely good (`extraction/`, `ops/`, `retrieve/`, `vault_io`, `integrity`, most of `schema/`); the other half carries almost all the debt.
2. **Where you can build immediately:** `extraction/`, `ops/`, `retrieve/` (after two S-size fixes), `vault_io.py`, `schema/`. These are dataclass-typed, logged, narrow-except, tested.
3. **Where you refactor first:** the retrieval **score contract** (one field, two scales — the intake's "score-inversion fix first") and the **silent filter-drop retry** — both S/M and both directly gate FR-1's "zero cross-product leakage" metric.
4. **Where you rewrite:** `rfp/` as a composition target. It is a March-era pre-monorepo transplant (argparse+print island, module-level dotenv, broken startup, one ImportError-on-use, lint suppressions pasted into an LLM prompt). Salvage parts (anonymization, Word/Excel mechanics, `answer_selector` scoring logic); do not extend it.
5. **The systemic debt is fragmentation, not rot:** 5 config systems (2 rival "canonical" objects), 5+ vocabulary homes, 5 model registries, 3 pricing tables, 4 OneDrive guards, 5 frontmatter parsers, 3 LLM-JSON parsers, 3 live folder taxonomies.
6. **Dead weight is measured and mostly already decided:** DR-4 kills (facts pipeline, Lane B, N4) plus ~2,000 LOC of zero-caller limbs (650-line `BatchJobRunner`, `cost_tracker`, frames×2, scripts×3, ChromaDB fallbacks) — and 51 passing tests maintained for two dead modules.
7. **Zero of the 2026-04-17 dead-code findings have been fixed** (BACKLOG #11, re-confirmed today by vulture + grep) — dead code does not self-heal here; it needs scheduled removal.
8. **The repo refactors for real:** four March god-object findings are genuinely RESOLVED (ops facade, actions split, extract strategy chain, inbox split). What you are inheriting is the *residue* of an active cadence — shims, half-finished dedup — not neglect.
9. **Tach-clean ≠ decoupled:** the `rfp → retrieve` dependency exists only as a subprocess call to the repo's own CLI, invisible to Tach and mis-drawn as an import edge in ARCHITECTURE.md's codemap.
10. **Era debt is localized** to `rfp/` and `extractor/scripts/` (100% of the 322 `print` calls, all argparse, all old typing). Fixing two zones fixes the era problem — this is tractable, not endemic.

---

## 1. Breadth metrics (whole `src/corp/`, tool-generated)

### 1.1 Per-package table

Provenance: LOC/annotation from AST script (`metrics.py`, session scratchpad); CC/MI from `radon cc -j` / `radon mi -j`; print/blind-except from `ruff --select T201,BLE001`; vulture at `--min-confidence 60`.

| Package | Files | LOC | Largest file | Public defs annotated | avg CC | max CC | CC>10 | mean MI | worst MI (file) | T201 print | BLE001 | vulture hits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| actions | 12 | 1,183 | monitoring_actions.py 164 | 100% | 5.5 | 14 | 2 | 64.8 | 47.9 analytics_actions | 0 | 1 | 15 (FP: registry) |
| cleanup | 7 | 1,115 | disk.py 431 | 100% | 4.0 | 13 | 2 | 72.1 | 46.7 disk | 0 | 0 | — |
| cli | 18 | 3,767 | ingest.py 622 | 98% | 8.3 | 31 | 17 | 53.7 | 27.6 analytics | 0 | 12 | 20 (FP: Click) |
| extraction | 7 | 790 | manifest_emitter.py 160 | 100% | 5.0 | 23 | 4 | 72.2 | 60.6 vault_writer | 0 | 0 | 5 |
| extractor | 52 | 11,012 | extract.py 1,185 | 84% | 6.0 | **79** | 38 | 66.6 | **19.4** extract | **98** | **36** | 31 |
| ingest | 11 | 3,929 | inbox.py 952 | **69%** | 5.8 | 28 | 16 | 56.4 | 23.3 inbox | 0 | 25 | 11 |
| opportunity | 10 | 1,461 | chat.py 351 | 100% | 3.8 | 13 | 1 | 66.1 | 32.4 chat | 0 | 0 | 5 |
| ops | 9 | 1,461 | database.py 543 | 99% | **2.0** | 11 | 1 | 71.2 | 43.1 database | 0 | 0 | 10 |
| overnight | 8 | 1,487 | cke_client.py 316 | 97% | 4.0 | 15 | 3 | 65.7 | 48.3 state | 0 | 1 | 7 |
| project | 10 | 2,173 | extractors.py 497 | 100% | 6.0 | 60 | 7 | 57.8 | 27.2 extractors | 0 | 10 | 8 |
| retrieve | 4 | 1,015 | engine.py 573 | 100% | 7.2 | 42 | 3 | 63.6 | 28.3 engine | 0 | 2 | 2 |
| rfp | 12 | 4,263 | rfp_excel_agent.py 861 | **63%** | 6.1 | 29 | 14 | 56.1 | 25.6 rfp_answer_word | **224** | 13 | 8 |
| root-modules | 21 | 6,484 | index_builder.py 729 | 100% | 5.0 | 25 | 21 | 56.9 | 32.8 index_builder | 0 | 13 | 16 |
| schema | 12 | 1,575 | products.py 213 | 90% | 3.8 | 22 | 4 | 69.2 | 48.2 cli | 0 | 0 | **84** (mostly enum-member FP + speculative constants) |
| **TOTAL** | **193** | **41,715** | — | **89%** (547/617) | — | — | **129** | — | 54 files MI<50 | **322** | **113** | 222 |

### 1.2 Complexity hotspots (radon, worst functions)

`process` CC=79 (`extractor/scripts/run.py:317`) · `classify_file` CC=60 (`project/classifier.py:70` — see §2.8: a *documented decision table*, benign) · `build_package` CC=52 (`extractor/synthesize.py:279`) · `retrieve` CC=42 (`retrieve/engine.py:105`) · `post_process_extraction` / `classify_doc_type` CC=35 · `ingest_command` CC=31 (`cli/ingest.py:19` — display branching, not logic) · `BatchJobRunner.run` CC=30 (`extractor/batch_api.py:330` — zero callers) · `process_excel_file` CC=29 · `process_file` CC=28 (`ingest/inbox.py:716`). Files with MI<20: `extractor/extract.py` (19.4), `extractor/scripts/run.py` (19.8).

### 1.3 Ruff full-rule picture (committed config vs reality)

Committed `.ruff.toml` selects only `E,F,I` (ignores E501) → **1 violation** under it. Under `--select ALL` (report-only, no `--fix`): **3,673 violations**. Top families: E501×601, PLC0415 import-outside-top-level×365, **T201 print×322** (house standard is logging — ALL 322 in `rfp/` (224) + `extractor/` (98)), COM812×305, **BLE001 blind-except×113**, PLR2004 magic-values×104, FBT001 bool-positional×101, PTH123 builtin-open×97, ANN001 missing-arg-annotation×95, C901 too-complex×64, DTZ005 naive-datetime×63, PLR0913 too-many-args×57, ERA001 commented-out-code×8.

### 1.4 Vulture + delta vs the 2026-04-17 dead-code audit

The 2026-04-17 audit file itself is not in git history; its surviving record is **BACKLOG.md #11** (re-confirmed 2026-06-03, findings H1–H4, M1, M3). Status today — **all six classes still present, zero fixed**:

| 2026-04-17 finding | Today (verified by vulture ≥60 + grep) |
|---|---|
| H1/H2 dead PDF helpers `_try_pdf_multimodal` / `_try_pptx_pdf_multimodal` | Still present (`extract.py:934,946`) — now explicit "backward-compat shims" kept alive **only** by zombie test `tests/extractor/test_pdf_multimodal.py` |
| H3/H4 orphans `frames/extractor.py`, `frames/tagger.py` | Still present; vulture re-flags `extract_frames:24`, `tag_frames:27` |
| M1 duplicate `_log_ingest_event` | Both copies live: `ingest/extractions.py:335` AND `ingest/inbox_ops.py:70` |
| M3 unpackaged `extractor/scripts/{batch_compress,compress_video,preprocess_audio}.py` | All three still present |

**New dead code beyond the baseline** (zero callers, grep-verified): `extraction/routing.py:30 _load_routing_map` · `audit.py:328 analyze_all_folders` · `schema/config.py:87 rfp_kb_path` (relevant to DR-1 — see register RC-6) · `extraction/scanner.py:26 ScanSecurityError` · test-only zombies `extraction/contract.py:31 validate_manifest`, `schema/config.py:63 get_excluded_paths` · plus the deep-extraction-documented limbs: `extractor/batch_api.py` (650-line `BatchJobRunner`, `batches` table 0 rows ever, `state.create_batch` zero callers — deep-extraction §3.3), `providers/cost_tracker.py` (shelf-ware, §2.4), `cke_client.estimate_cost` (`NotImplementedError` stub, cke_client.py:97-106), rfp ChromaDB fallback paths (deep-rfp B4b), `vault_adapter.retrieve_for_rfp` (no callers). Vulture's 222 raw candidates include large false-positive classes (Click commands, `@register_action` registry dispatch, Pydantic enum members) — the list above is the caller-verified residue.

**Contradiction resolved:** the March 2026-03-30 quality audit claimed "no dead code." The July deep audits and this pass disprove that; the March claim should be treated as superseded.

---

## 2. Deep-read assessments (judgment layer)

Whole-module reads: all of `rfp/`, all of `retrieve/`, `ingest/router.py`, `extractor/extract.py`, `index_builder.py`, plus the 5 highest-complexity modules (`extractor/scripts/run.py`, `project/classifier.py`, `extractor/synthesize.py`, `retrieve/engine.py`, `extractor/post_process.py`). Each with ≥3 cited examples.

### 2.1 `rfp/` (12 files, 4,263 LOC) — a pre-monorepo island; the R1-critical package is the repo's worst

**How it reads:** like four standalone scripts sharing a folder. argparse + `print("[INFO] ...")` throughout (house standard is Click+Rich+logging); module-level `load_dotenv` side effects on import (`rfp_excel_agent.py:49-54`, `llm_router.py:14-20`, `rfp_answer_word.py:38-44` — the same block copy-pasted); `PROJECT_ROOT = Path(__file__).resolve().parents[3]` anchoring (breaks on installed wheel); old `Dict/List/Optional/Tuple` typing; docstrings still say `python src/rfp_feedback.py` (pre-monorepo layout).

**Broken plumbing (verified directly):**
- `rfp_answer_word.py` fails at startup: `load_family_config()` opens `data/kb/schema/family_config.json` with no existence check (`:68,:115`, called at `:673`) and `data/kb/` does not exist (deep-rfp headline #3 confirmed).
- `validate_profiles.py:428` — `from merge_profiles import merge_all`: the module exists **nowhere** in the repo (git grep = 0), so `--auto-fix --merge` dies with ImportError. Stale sibling-file import.
- `config/rfp/platform_matrix.json` absent → `get_available_solutions()` returns `[]` → argparse `choices=None` → zero validation (deep-rfp B2 confirmed).

**The score-contract defect (R1-critical, exact mechanism):** `retrieve/engine.py` exports `relevance_score` = FTS5 BM25 rank (negative, lower=better) + trust boost `{verified:0 … draft:100}`, sorted ascending — internally coherent (`engine.py:75-90`). `rfp/vault_adapter.py` consumes it as a 0–1 higher-is-better similarity: sorts by `-(relevance_score)` (`:63-68`, inverting within-tier order), applies `LOW_CONFIDENCE_THRESHOLD = 0.25` (`:20,:96`, meaningless on the BM25 scale) — while its own SQLite fallback path *does* convert (`_bm25_to_score`, `:265-277` feeding `:227`). Same field name, two scales, one consumer. Downstream, `rfp_answer_word.py:381-383` converts score→distance, `:738-739` threshold-filters, and `:741` **silently falls back to `matches[:2]` when the filter empties** (deep-rfp W2). This chain is why the intake orders "score-inversion fix first."

**Patch-smell exhibit A:** lint suppressions pasted *inside the LLM prompt string* — `rfp_answer_word.py:451,467,471` contain literal `# noqa: E501` text that is sent to the model as part of the prompt.

**Duplication inside one package:** two LLM retry implementations with different policies (`rfp_excel_agent.py:60` vs `llm_router.py:93`); two near-verbatim ChromaDB fallback inits (`llm_router.py:204-233` vs `rfp_answer_word.py:311-342`); twin column detectors (`rfp_excel_agent.py:207` vs `:272`); a local 3-strategy LLM-JSON parser (`answer_selector.py:373`) reimplementing the canonical `schema.utils.parse_llm_json`.

**Stringly-typed error contract:** answers and errors share the string channel — `return f"ERROR: {e}"` (`rfp_excel_agent.py:452`), error detection via `.startswith("ERROR")` (`:715`) and `"429" in result` (`:70`); `llm_router.generate_answer` returns `"Error: ..."` strings from a bare `except Exception` (`:370-371`).

**Dormant machinery:** `answer_selector.py` (637 lines + numpy dependency) has tests-only callers (deep-rfp Step 2) yet hardcodes a 4th product-vocabulary home (`BY_TERMS`/`DEPRECATED_TERMS`, `:62-110`); `rfp_feedback.py` targets the nonexistent `data/kb/` tree; `rfp/README.md` claims consumers ("Used by: corp.cli.rfp, corp.retrieve.rfp") that import nothing from it (deep-rfp headline #7) — an authoritative-looking dead doc.

**What is worth salvaging:** `vault_adapter.py` is visibly newer-era (logging, narrow excepts, modern hints) apart from the scale bug and a `subprocess.run(text=True)` without `encoding=` (`:138-143` — the documented cp1252 gotcha class); `anonymization/` is small and coherent (though `save_config` writes runtime session state into repo-tracked `config/rfp/anonymization.yaml`, `:35-41` — the stale-hardcoded-customer, deep-rfp B3); `answer_selector`'s staged scoring design is sound as KB-maintenance tooling; `rfp_answer_word.py`'s `Section`/`AnswerableBlock` dataclasses and backwards-insertion Word mechanics (`:774-776`) are good; the interactive review loop is the natural FR-1 stage-8 capture point.

### 2.2 `retrieve/` (4 files, 1,015 LOC) — house-standard era; the best-designed core

Good: a declared single seam ("This is the ONLY retrieval function. All workflows call this", `engine.py:115`), `RetrievalFilter`/`RetrievedNote`/`RetrievalResult` dataclasses, logging, coverage-gap concept, FTS5 with LIKE fallback, graceful LLM degradation with explicit sentinels (`prep.py:239-273`).

Debits, all cited: (1) the **silent filter-drop retry** — empty filtered result silently retries unfiltered (`rfp.py:118-125`, duplicated `prep.py:133-143`); logged at INFO, but the answer carries no provenance marker — the cross-product leak vector (deep-rfp A3). (2) `retrieve()` is a 240-line monolith (CC=42, `engine.py:105-343`) doing query build + filters + supplement + hydration + ranking. (3) **Double file read per note** — `_load_note_content` and `_load_note_metadata` each `read_text()` the same file (`:280-281` → `:441,:457`). (4) Magic sentinel ranks in the score channel (`999 as rank` `:252`, `0 as rank` `:537`). (5) `rfp.py:101` imports the *private* `_call_llm` from `prep.py` — a shared utility living as a sibling's private. (6) A third copy of `_parse_json_field` (`engine.py:494`; also `rfp/vault_adapter.py:252`). (7) Inline hardcoded pricing (`prep.py:261-263`).

### 2.3 `ingest/router.py` (894 LOC) — designed, later-era, with patch marks

Good: record-before-move discipline (comment at `:228`), dataclasses, keyword-only flags, extracted helpers (`_preflight_folder`, `_determine_folder_route`, `_register_folder_assets`), collision handling, dry-run. Debits: `except (ValueError, Exception)` (`:889` — a widened-except patch); hardcoded backslash join `dest_full.replace("/", "\\")` (`:564`, violates repo rule 7, inconsistent with `:250`); **twin ~60-line manifest-builder bodies** (`_run_extraction:720` vs `_run_package_extraction:633`); cross-package *private* imports (`from corp.extraction.manifest_emitter import _make_entry_id, _resolve_doc_type`, `:649,:739` — coupling Tach can't see); SHA-256 computed for every file (`:202`) but never checked for dedup (deep-magistrala confirmed); type-by-comment `config=None  # PipelineConfig | None` ×5 (`:163,:322,:498,:639,:728` — why ingest sits at 69% annotation); collision-rename loop duplicated (`:255-261`, `:864-870`). The `move_to_vault` calls (`:715,:795`) are the DR-4 Lane-B kill's neighborhood — removal must distinguish the live sync lane from the dead inbox Lane B.

### 2.4 `extractor/extract.py` (1,185 LOC, MI 19.4) — mid-refactor state

`ExtractionResult` is a **35-field god-record with visible era strata** — comment-labelled layers "Schema v2 knowledge dimensions" / "RFP agent enrichment" / "Deep extraction" / "Freshness" / "Provenance" (`:56-106`); ~8 fields are DEAD per the vault-metadata field-survival table (`authority`, `layer`, `quality`, `tokens_used`, `facts`→killed pipeline…). The good news: the March-era 200-line functions were genuinely refactored — `extract_from_text` now walks a documented strategy chain (`:985-1001`), and the two "dead PDF helpers" are explicit shims (`:934-955`) that exist only to keep the zombie test green. Refactor residue: the deep-video branch (`:522-545`) still duplicates `_build_sampled_frame_contents` (`:368-397`); a comment celebrates "(eliminates ~45 lines of duplication)" (`:1107`). Other debits: pricing table hardcoded (`:137-144`, home #3); `_haiku_enrichment` hardcodes `claude-haiku-4-5-20251001` (`:770`, model home #5); raw-dict config threading throughout (`config.get("gemini", {})…`); token budget computed as `depth="multimodal"` even for documents (`:718-722`); broad-except-and-degrade in PDF helpers (`:863,:887,:908` — acceptable posture, silent class).

### 2.5 `index_builder.py` (729 LOC) — the seam where consistency defects become data defects

- **Two serializations for the same data shape in one file:** `_insert_project` stores list fields as `json.dumps` (`:457-460`) while `_index_cke_notes` comma-joins them via `_join_list` (`:649-650`) — the exact round-trip that garbles "IDSP (Integrated Demand, Supply & Inventory Planning)" (deep-vault §4.2); readers (`_parse_json_field` in retrieve + rfp) already prefer JSON.
- **Both config systems in one module:** `get_config()` (`:146`) and `PipelineConfig.production()` (`:170`).
- **The DR-4-killed facts pipeline still fully maintained here:** `facts`/`facts_fts` tables + triggers + `_load_and_insert_facts` (~100 lines, `:45-60,:131-140,:473-540`).
- **Scar-tissue banners** — "NOTES TABLE — DO NOT REMOVE … If you see 0 notes after rebuild, this code was accidentally deleted" (`:67-73`, `:543-547`): process fear baked into comments after a real incident.
- `_compute_rfp_visible` (`:578-604`) reproduces the deprecated-leak: `deprecated` trust falls through to source/doc-type rules (deep-vault §2.4). The `notes` table carries 31 columns, ~10 of them dead/phantom per the field-survival table.

### 2.6 `extractor/scripts/run.py` (872 LOC; `process` CC=79, worst in repo)

`process` is a 356-line, 9-phase pipeline inlined into one Click handler (`:317-672`) — a grown script, linear with numbered phase comments, not spaghetti; still the first extraction candidate. Fossils: a pre-monorepo `sys.path.insert` hack whose computed paths (`src/corp/extractor` + `src/corp/extractor/src`) no longer exist (`:20-22`); a `HAS_RICH` try/except + markup-stripping `_print` shim (`:67-84`) though Rich is a hard dependency; `MODEL_MAP` literal duplicated in-file (`:338`, `:725`). Risk: a hand-maintained 25-key dict re-serializes `ExtractionResult` (`:618-651` — field-drift risk vs the dataclass); the resume path builds a 4-field partial `ExtractionResult` (`:482-488`) that downstream steps consume as if full. `--batch` (`:747-751`) is the only door to the dead `BatchJobRunner`.

### 2.7 `extractor/synthesize.py` (551) + `post_process.py` (626)

`build_package` (CC=52) is dominated by a single `tmpl.render(...)` with ~40 kwargs (`:360-412`) mirroring the god-record — and it renders `source_file` into a template whose output field is `source:`, the template-betrays-validator break measured at 813/813 notes failing (deep-vault §1.1; `config/extractor/templates/extract.md.j2:2`). `post_process.py` is where two of the disjoint vocabulary systems live: `_BUILTIN_PRODUCT_ALIASES` + `extractor/data/product_aliases.yaml` (`:140-157`) and `_TAG_ALIASES` (`:498`), plus a second client-alias home (`:66-73`) parallel to `schema.naming_config`. Structure is otherwise clean (lru-cached loaders, delegation to `corp.schema`).

### 2.8 `project/classifier.py` (212 LOC, CC=60) — the counter-example

Radon's #2 hotspot is in fact the most readable decision logic in the repo: a flat, first-match-wins rule table with all 20 priorities documented in the docstring, one guard-return per rule, confidence constants, and regex quirks explained where they bite (`:106` "\b doesn't work across underscores"). High measured complexity, low actual reading cost — graded accordingly. One dead branch: rule 19's CSV fallback (`:208`) is unreachable (rule 7 catches `.csv` at HIGH).

### 2.9 Packages characterized by structured skim (evidence via secondary read pass)

- **`extraction/`** — uniformly high quality: `from __future__ import annotations`, dataclass results, custom exceptions, narrow excepts only; `scanner.py` is security-first (path jail `:30`, symlink-escape `:110-118`); `vault_writer.py` is a clean extraction-side writer (SHA-256 identity `:48`, verified-note conflict protection `:97-116`).
- **`ops/`** — the March "god class" is genuinely RESOLVED: `OpsDB` is a 24-method facade over 5 repositories (lazy-init `:213-217`), avg CC 2.0, zero `except Exception` in `database.py`. Residue: the `_ = self.conn  # ensure repos initialized` side-effecting no-op ×~15 (`:259,:266,:271,…`) and an untyped `config` param (`:190`).
- **`overnight/`** — `cke_client.py` funnels all subprocess calls through `_run_cke` with `encoding="utf-8", errors="replace"` and a documented cp1252 rationale (`:162-175`) — the gotcha done right. `estimate_cost` is a retained `NotImplementedError` stub (`:97-106`). The known lifecycle gap (no try/finally around runs; stale `running` rows forever; no janitor — deep-extraction §3.2) lives at the `cli/overnight.py` call sites.
- **`cleanup/`** — strongest safety engineering in the repo (`executor.py`: load-time `MoveEntry` schema rejecting traversal `:92-121` + runtime `_assert_within_root` `:137-157` + OneDrive guard). But `classifier.py`'s LLM prompt speaks a **dead folder taxonomy** (`30_Templates/`, `50_RFP/`, `60_Source_Library/`, `:19-58`) that contradicts canonical `folder_names.py`, hardcodes `gemini-3-flash-preview` (`:98,:151`), and carries its own LLM-JSON parser (`:84`).
- **`opportunity/`** — a self-contained parallel mini-app with its OWN config (`config.py:34-80` — neither `AppConfig` nor `PipelineConfig`) and a third folder taxonomy (`folder_standards.py:15-28`). Byte-equivalent duplicate helpers between `chat.py:316-324` and `cli.py:204-212`; near-duplicate Excel updaters; `chat.py`'s MI=32 comes from volume + inline Rich markup, not a monolith (8 flat handlers behind a registry `:301-310`). Operator ruling: COM is "unfinished, not unwanted — verdict FIX" (deep-dealloop).
- **`project/`** — `extractors.py`'s CC is spread over 5 per-filetype extractors (readable except `extract_xlsx:292-394`); `except (UnicodeDecodeError, Exception)` (`:415`) is the second pointless-tuple except; `renderer.py` hand-rolls frontmatter (`:213-236`, bypassing `NoteFrontmatter`) and carries the **4th** OneDrive-guard variant (`:38-52`); known functional breaks cited: `cpe render` clobbers COM's `project-info.yaml` (deep-dealloop §2.3-2), dead `clients.yaml` path (§2.3-1), Dataview phantom zone (§2.3-3); `manifest.py`/`models.py` mix `Optional[...]` with modern unions.
- **`actions/`** — consistent `@register_action` registry; OneDrive guard present (`_helpers.py:103-134`, self-documented as copy 3-of-4 pending centralization). Smells: structured data laundered through YAML strings between workflow steps (`monitoring_actions.py:104-105` → `:119`); sibling drift — `analytics_actions.py:97` hardcodes `"00_dashboards"` while `VaultZone.DASHBOARDS.value == "dashboards"` and monitoring uses the enum (`:154`) — a wrong-path write waiting; frontmatter hand-rolled again (×2); the vault stamp silently no-ops into a nonexistent zone (deep-dealloop §4.3).
- **`cli/`** — the **dual-config idiom in essentially every command** (`config = (obj or {}).get("config") or PipelineConfig.production()` beside `cfg = get_config()` — `ingest.py:40-41`, `overnight.py:50,63`, `analytics.py:282,355,391`, `system.py:182,232`). `ingest_command` CC=31 is presentation branching (delegates to router). `overnight.py` is a genuine fat orchestrator — `_run_folder_extraction:85-269` and `_run_full_reshape:301-444` hold scan→manifest→CKE→vault→state logic that belongs in `overnight/`, with parameters annotated `cfg: AppConfig` under `# noqa: F821` because the names are never imported (fake annotations), plus the third pointless-tuple except (`:183`). `analytics.py`'s MI 27.6 is copy-paste: the index-existence guard duplicated verbatim in 7 commands, plus a private import through a shim (`from corp.built_in_actions import _write_analytics_dashboard`, `:33`).
- **`schema/`** — solid foundation with era wobble: mixed `Optional[...]`/`X | None` inside `models.py` (`:8,:91,:112`); mutable module cache globals in `products.py` (`:13-16`); `resolve_product_key` exported but **zero call sites** outside `__init__` (the canonical normalizer nothing uses); `cli.py` runs `load_dotenv` at import (`:14-22`) and reimplements frontmatter parsing (`:39-49`); `folder_names.py` is exemplary (zero imports by design). `utils.parse_llm_json` (`:10`) is the canonical 4-strategy parser others fail to reuse.
- **root modules** — split verdicts. Exemplary: `vault_io.py` (the ADR-27 `write_note` seam is clean — mode guards, verified-conflict handling `:214-226`, retry/backoff `:143-157`, whitelist `:51-65`, every except narrow; the March `except→return None` finding is fixed), `integrity.py` (visitor pattern, narrow excepts, `fix_hint`s), `models.py` (StrEnum, frozen dataclasses — though `VaultZone` carries three overlapping taxonomy generations at once, `:13-33`, and a stale `00_dashboards/tasks/` docstring `:221`). Over-built but clean: the `chat → intent_router → workflow_engine → actions` stack (~1,200 lines of bilingual NL→YAML-workflow dispatch for a handful of personal workflows) — kept, because FR-9 explicitly revives it. Offenders: `audit.py` (hand-rolled 60-line truncated-JSON repair machine `:177-235` — third LLM-JSON parser; all-raw-dicts pipeline; hardcoded model + zones), `task_manager.py`/`template_manager.py` (kill candidates that also duplicate frontmatter I/O, embed a 78-word Polish stop-word list `:36-114`, import a sibling's private `_strip_diacritics` `:116`, and hardcode the phantom `30_Templates/` path `:186,:349`), `query_engine.py` (positional row access `:79-86`; facts-as-JSON vs notes-as-CSV serialization split `:315,:328`; imports private `_connect,_ensure_schema` from index_builder `:19`), `chat.py` (silent `except Exception: pass` at `:135`).

---

## 3. Cross-cutting consistency findings

### 3.a Duplication — same logic, multiple homes

**Vocabulary normalization (the "three disjoint systems," confirmed + two more homes):**

| # | Home | Evidence |
|---|---|---|
| 1 | `schema/data/products.yaml` + `schema/products.py::resolve_product_key` (canonical, **unused** — zero call sites outside `__init__`) | grep; only `expand_product_query` is consumed (`retrieve/engine.py:130`) |
| 2 | `extractor/data/product_aliases.yaml` + `_BUILTIN_PRODUCT_ALIASES` | `post_process.py:140-157` |
| 3 | `_TAG_ALIASES` in code | `post_process.py:498` — "wired to the dead surface" (deep-vault §4.2) |
| 4 | `BY_TERMS`/`DEPRECATED_TERMS`/`MODERN_TERMS` | `rfp/answer_selector.py:62-110` (dormant module) |
| 5 | `BOOL_TO_SERVICE_KEY` + `FIELD_FORBIDDEN_PATTERNS` | `rfp/validate_profiles.py:44-64` |

Client vocabulary: `schema.naming_config.get_client_variants` (canonical) AND `extractor/data/client_aliases.yaml` (`post_process.py:66-73`) AND `content_registry.yaml` client_patterns ("two vocabularies … already disagreeing" — deep-magistrala §2d). **Verdict: SYSTEMIC — vocabulary has no owner; every consumer grew its own.**

**Model/pricing registries (5 + 3 homes):** `rfp/llm_router.py:63 MODELS` · `extractor/tier_router.py:52 TIER_MODELS` · `providers/router.py select_model/route_model` · `run.py:338 + :725 MODEL_MAP` (duplicated in-file) · `extract.py:770` hardcoded Haiku. Pricing: `extract.py:137-144` · `retrieve/prep.py:261-263` · `providers/cost_tracker.py` (dead). **SYSTEMIC.**

**Mechanical duplication (each: same function, ≥2 homes):** `_log_ingest_event` ×2 (`ingest/extractions.py:335`, `inbox_ops.py:70`) · `_parse_json_field` ×2 (`engine.py:494`, `vault_adapter.py:252`) · ChromaDB init ×2 (rfp) · LLM retry ×2 (rfp, different policies) · manifest builders ×2 (`router.py:633/:720`) · collision-rename ×2 (`router.py:255/:864`) · stop-word lists ×2 (`engine.py:355-419`, `rfp_feedback.py:169-215`) · dotenv secret-block ×5 files · **OneDrive guard ×4** (`cleanup/disk.py:28`, `cleanup/executor.py:22`, `actions/_helpers.py:103`, `project/renderer.py:38-52` — each docstring promising ADR-27 centralization) · **frontmatter parse/emit ×5** (`vault_io.py` canonical; `schema/cli.py:39`, `extraction/vault_writer.py:20`, `cli/system.py:133-146`, `task_manager.py:279-330`) · **LLM-JSON parser ×3** (`schema/utils.parse_llm_json` canonical; `cleanup/classifier.py:84`; `audit.py:157,177-235`) · opportunity byte-equivalent helpers ×2. **Verdict: rfp-internal duplication is LOCAL (the island); guard/frontmatter/parser/vocabulary/model duplication is SYSTEMIC.**

### 3.b Shim inventory (consolidation era)

| Shim | Consumers (grep-verified) | Removable? |
|---|---|---|
| `built_in_actions.py` — whole-module re-export → `corp.actions` | `workflow_engine.py`, `cli/analytics.py`, 2 test files | Yes — ~6 import repoints + `tach.toml` edge edit |
| `ingest/naming_config.py` — 6-line star re-export → `schema.naming_config`, self-marked DEPRECATED | ONE: `ingest/renamer.py:21` | Trivially |
| `intent_router.py:18` — `Intent` re-export ← `routing_types` | `chat.py:15`, `tests/test_chat.py:111` | Trivially |
| `ingest/inbox.py:23` — re-exports `inbox_ops` names | `cli/ingest.py:233`, inbox tests | Verify names at removal |
| `extract.py:934,:946` — `_try_*` strategy shims | zombie test `test_pdf_multimodal.py` only | Yes, WITH test rewrite (BACKLOG #11 H1/H2) |
| `extract.py:140` — legacy pricing row "kept for backward compat" | — | Trivially |

**Verdict: LOCAL and small — 6 shims, each an S-size removal.**

### 3.c Config access — five systems, two rivals

1. **`corp.config.get_config` → `AppConfig`** (26 files): frozen dataclass, lru-cached, ENV > **hardcoded home defaults** — does NOT read `config/paths.toml`, violating the declared "ENV > config > default" chain.
2. **`corp.schema.pipeline_config.PipelineConfig`** (21 files): ENV > paths.toml > defaults, `sandbox()` support — the designed one.
3. `corp.schema.config.get_path/vault_path` (2 files; `rfp_kb_path` dead).
4. `corp.extractor.config_loader` (5 files): raw-dict YAML threading.
5. `opportunity/config.py` + `project/config.py`: package-local, env-based (shared env-var namespace with corp/config.py; paths.toml gap — deep-dealloop §1.2).

Plus `load_dotenv` at module import in **11 files / 21 sites**. `AppConfig` and `PipelineConfig` are near-duplicate six-field frozen dataclasses used side by side in the same modules (`index_builder.py:146/:170`; every `cli/` command; deep-magistrala's "dual config in one command"). ARCHITECTURE.md §Configuration Architecture documents 9 config files with 8 loaders and does not even mention the two biggest systems. **Verdict: SYSTEMIC — the single highest-leverage consistency fix, and F0-coupled (DR-1's `INDEX_EXTRA_ROOTS` is parsed independently in BOTH rivals — `config.py:100-101` and `pipeline_config`).**

### 3.d Error handling

Counts: `except Exception` at **121 sites** (BLE001 113): extractor 36, ingest 25, rfp 13, root 13, cli 12, project 10, retrieve 2, actions 1, overnight 1 — and **zero** in the strongest modules (`ops/database.py`, `vault_io.py`, `integrity.py`, `extraction/*`). Single-line silent forms: `except→pass` ×5, `except→return empty/None` ×6 (multiline forms additional). Two `except (X, Exception)` nonsense tuples (`ingest/router.py:889`, `project/extractors.py:415`) plus `(PolicyError, Exception)` (`cli/overnight.py:183`). The worse class is silent **design** no-ops (cited from deep audits, not re-derived): MinHash dedup ImportError→`[]` at DEBUG (`dedup.py:284-286`); filter-drop retry (`rfp.py:118-125`); `matches[:2]` fallback (`rfp_answer_word.py:741`); `record_extraction` no-op without a `files` row (deep-extraction §2.5); no try/finally around overnight runs (§3.2); vault stamp writing to a nonexistent zone (deep-dealloop §4.3). Error CONTRACTS span 5 conventions: exceptions (`ExtractionError`) / None returns / empty collections / `"Error: ..."` strings / status dicts (`"NO_DATA"`). **Verdict: SYSTEMIC — not the count but the absent convention plus silent-continue posture on load-bearing paths.**

### 3.e Era-mixing

argparse+print: `rfp/` (5 files) + `extractor/scripts/{batch_compress,compare_reports,compress_video}` — nothing else. All 322 prints in `rfp` (224) + `extractor` (98). Old typing imports: 5 files (rfp/anonymization ×3, rfp_excel_agent, compare_reports), plus `Optional[...]` residue in project/ and schema/models. Module-level side effects: rfp dotenv ×3, `run.py` stale sys.path hack, `schema/cli.py` dotenv, `opportunity/cli.py` stdout re-wrap. Scar-tissue comments: `index_builder.py:67-73,:543-547`. Three folder taxonomies live simultaneously: canonical `folder_names.py` (`10_Projects/20_Workflows/30_Reference`), the dead `30_Templates/50_RFP/60_Source_Library` scheme (cleanup classifier prompt, template_manager), and `VaultZone`'s current+legacy+virtual generations (`models.py:13-33`). **Verdict: LOCALIZED, not diffuse — the March-era rfp transplant and the CKE scripts tail carry ~100% of the era debt. Remediation is two zones, not fourteen.**

---

## 4. Per-package scorecard

Dimensions: **A** architecture fit · **R** readability · **C** consistency · **P** patch-smell · **S** simplicity/efficiency. Anchors: A exemplary → E rework cheaper than reuse.

| Package | A | R | C | P | S | Top issue (evidence) | Safe to build on? |
|---|---|---|---|---|---|---|---|
| schema | B | B | C | B | B | Canonical normalizer nobody calls (`resolve_product_key`, 0 call sites); typing eras mixed in one file (`models.py:8/:91/:112`); dotenv at import (`cli.py:14-22`) | **YES** — wire it in rather than around it |
| extractor | C | C | C | **D** | **D** | Dead-limb density: 650-line `BatchJobRunner` 0-callers (§3.3), frames×2, cost_tracker, scripts×3, zombie-test shims (`extract.py:934-955`); 5 model + 3 pricing homes; 35-field god-record; MI 19.4 | Core tiered path: yes-with-care (it works and is cheap); the limbs: no — remove |
| extraction | A | A | A | B | A | Two dead functions (`routing.py:30`, `scanner.py:26`); receiver drops its own validated contract (deep-extraction §4.2 — CKE-side) | **YES** — model package |
| ingest | B | B | B | C | B | Twin manifest builders (`router.py:633/:720`); hash-computed-never-checked (`:202`); `except (ValueError, Exception)` (`:889`); 69% annotation (type-by-comment ×5); 25 blind excepts | Mostly — refactor alongside the W1/DR-6 restart |
| ops | A | A | A | B | A | `_ = self.conn` lazy-init no-op ×15 (`database.py:259…`); untyped `config` param (`:190`) | **YES** — facade refactor landed well |
| retrieve | B | A | A | B | B | Silent filter-drop retry (`rfp.py:118-125`); 240-line `retrieve()` (CC=42); exported score semantics trap (`engine.py:75-90`); double file read per note (`:280-281`) | **YES** — after the two S-size fixes (RC-1, RC-2) |
| cleanup | B | B | C | C | B | Classifier prompt speaks a dead taxonomy (`classifier.py:19-58` vs `folder_names.py`); guard duplicated 2× in-package; own LLM-JSON parser (`:84`); hardcoded model (`:98,:151`) | Executor/disk: YES (best safety engineering); classifier: fix taxonomy first |
| overnight | B | B | B | B | B | Run lifecycle without try/finally or janitor — stale `running` rows forever (deep-extraction §3.2; sites in `cli/overnight.py:105/:254`); `estimate_cost` NotImplementedError stub (`cke_client.py:97-106`) | **YES** — subprocess hygiene is the gotcha done right (`_run_cke:162-175`) |
| project | C | B | C | C | B | Renderer bypasses schema models + 4th OneDrive-guard variant (`renderer.py:213-236,:38-52`); COM-clobber seam + dead `clients.yaml` path (deep-dealloop §2.3); pointless-tuple except (`extractors.py:415`) | With care — fix the two seams inside FR-6 work |
| opportunity | C | B | C | C | B | Parallel mini-app: own config (`config.py:34-80`), 3rd taxonomy (`folder_standards.py:15-28`), byte-identical duplicate helpers (`chat.py:316`/`cli.py:204`) | Per operator ruling FIX — config-fix (DR-8) + dedup inside FR-6 |
| rfp | **D** | C | **D** | **E** | C | Pre-monorepo island: broken startup (`rfp_answer_word.py:68/:673`), broken import (`validate_profiles.py:428`), score-scale misread (`vault_adapter.py:63-68`), noqa-in-prompt (`:451,:467,:471`), dead README, 224 prints, 63% annotation | **NO** — salvage parts, rebuild the seam (this IS the R1 build) |
| cli | C | C | C | C | B | Dual-config idiom in every command (`ingest.py:40-41` et al.); `overnight.py` fat orchestrator with fake `F821` annotations (`:88,:273,:303,:447`); analytics guard copy-pasted ×7; private import through shim (`analytics.py:33`) | Thin commands: yes; `overnight.py`: relocate logic first |
| actions | B | B | C | C | B | Stringly inter-step state (`monitoring_actions.py:104-119`); sibling path drift `"00_dashboards"` vs `VaultZone.DASHBOARDS` (`analytics_actions.py:97` vs `models.py:20`); silent vault-stamp no-op (deep-dealloop §4.3) | YES for the registry pattern; fix path drift |
| root-modules | C | B | C | C | C | Rival config object (`config.py` vs `pipeline_config`); killed facts pipeline + comma-join seam (`index_builder.py:649`); dead managers w/ 51 passing tests; `audit.py` 3rd JSON parser + all-dicts; `VaultZone` 3 taxonomy generations | vault_io/integrity/models: YES. index_builder: after RC-5/RC-8. task/template managers: NO (kill/repoint) |

**Consistency spot-checks (3, per protocol):** (1) *rfp P=E* — verified directly: `merge_profiles` ImportError by repo-wide grep; startup break by absent `data/kb/` + no existence check; noqa-in-prompt read in file — E stands. (2) *retrieve C=A* — verified against Step 1: T201=0, BLE001=2, house style in all 4 files — A stands. (3) *extractor S=D* — verified: `batch_api.py` 0 callers (deep-extraction §3.3 + `state.create_batch` zero callers), 3 sampling implementations (§1.1), 5 model homes counted in §3.a — D stands.

---

## 5. Refactor-candidate register (ranked for the architect)

Priority rule, in order: **1** blocks/endangers R1 (FR-1) → **2** blocks F0 substrate → **3** systemic hygiene → **4** over-engineering removals → **5** cosmetic. Removals are first-class. **Fold** = do inside the named feature work; **Standalone** = its own change arc. DR-4 kills are cited as **decided** (intake §5), not re-proposed.

| ID | What | Where | Why it matters (FR/phase) | Size | Risk | Priority / mode |
|---|---|---|---|---|---|---|
| RC-1 | **Fix the retrieval score contract**: one scale for `relevance_score` (convert at the engine boundary or type the two channels apart); kill magic sentinel ranks (999/0) | `retrieve/engine.py:75-90,:252,:537` · `rfp/vault_adapter.py:20,:63-68,:227,:265-277` · `rfp_answer_word.py:381-383,:738-741` | R1/FR-1 stages 4–7 — every threshold in Stack B is meaningless until this lands; intake orders "score-inversion fix first" | M | M (tests exist for engine; add contract test) | **1 — fold into R1** |
| RC-2 | **Remove silent filter-drop retry + silent `matches[:2]` fallback**; empty-after-filter must surface as honest NO_DATA/abstain with provenance | `retrieve/rfp.py:118-125` · `retrieve/prep.py:133-143` · `rfp_answer_word.py:741` | R1/FR-1 — the cross-product leak vector; FR-1's pilot metric is *zero* leakage + honest abstains | S | Low | **1 — fold into R1** |
| RC-3 | **Retire `rfp/` as the R1 composition target; salvage list**: keep anonymization/, Word-Excel I/O mechanics (Section/AnswerableBlock, backwards insertion, green-cell scan), answer_selector scoring as KB-maintenance tooling; rebuild the 9-stage pipeline on the `retrieve/` side of the seam; rewrite `rfp/README.md` (currently false) | `src/corp/rfp/*` (4,263 LOC; broken plumbing at `rfp_answer_word.py:68`, `validate_profiles.py:428`; island idioms §2.1) | R1/FR-1 — building FR-1's 9 stages *onto* the island imports its E-grade patch debt into the priority process | L | M | **1 — this IS the R1 build; decision to architect** |
| RC-4 | If (contra RC-3) any rfp agent is salvaged as-is: fix startup config load, delete dead `merge_profiles` import, add `encoding=` to subprocess, stop writing session state into tracked `config/rfp/anonymization.yaml` | `rfp_answer_word.py:68,:115` · `validate_profiles.py:428` · `vault_adapter.py:138-143` · `anonymization/config.py:35-41` | R1 — conditional on RC-3 outcome | S | Low | **1-conditional — fold** |
| RC-5 | **Store list fields as JSON in the `notes` table** (kill `_join_list` comma-join; readers already prefer JSON) — fixes the IDSP comma-split class at the seam | `index_builder.py:649-650` (writer) · readers `engine.py:494`, `vault_adapter.py:252` | F0/FR-5 — taxonomy canonicalization at the index-build seam is the ratified enforcement point (deep-vault §4.3); also feeds DR-5 overlay/key_facts indexing | S | Low (rebuild is full-drop `:176-186`) | **2 — fold into F0 vault repair** |
| RC-6 | **Config consolidation**: collapse `AppConfig` into `PipelineConfig` (or vice versa — ONE canonical object reading ENV > paths.toml > defaults), single dotenv entry point, retire `schema.config` or make it the impl detail; migrate `cli/` dual-idiom call sites; opportunity/project local configs read paths.toml | `config.py` (26 files) vs `schema/pipeline_config.py` (21 files) · `cli/*` dual sites (`ingest.py:40-41` …) · 11 dotenv files | F0 — DR-1's `INDEX_EXTRA_ROOTS` is parsed independently in BOTH rivals (`config.py:100-101`); registry v4 + zone renames (DR-6/DR-7) all flow through config; every future FR touches this | M/L | M (mechanical but wide; suite is green as harness) | **2 — standalone, before/with F0** |
| RC-7 | **Give vocabulary one owner**: wire `schema.products.resolve_product_key` at the index-build seam; merge extractor product/client aliases + `_TAG_ALIASES` into schema data; retire rfp-local term lists with RC-3 | homes listed in §3.a | F0/FR-5 (canonicalize at index seam) + DR-13 answer-policy classifier needs ONE product taxonomy | M | M | **2 — fold into F0 vault repair** |
| RC-8 | **Execute the DR-4 kills** (decided; execution is the work): facts pipeline out of `index_builder` (tables+triggers+loader ~100 LOC) + repoint `corp query` to notes_fts (`query_engine`); N4 task_manager + CLI/workflow/intent wiring + 25 tests; Lane B `move_to_vault` inbox path | `index_builder.py:45-60,:131-141,:473-540` · `task_manager.py` + `cli/task.py` + workflows.yaml · inbox Lane B sites | Systemic hygiene with R1 relevance (`corp query` repoint touches retrieval surface); DECIDED in intake DR-4 — needs only sequencing | M | M (test updates; keep `corp query` behavior) | **3 — standalone arc** |
| RC-9 | **Centralize the OneDrive guard** (4 copies → one `corp.schema`/`cleanup.errors` home; each copy's docstring already requests this per ADR-27) | `cleanup/disk.py:28` · `cleanup/executor.py:22` · `actions/_helpers.py:103` · `project/renderer.py:38-52` | Systemic + safety-critical: 4 divergent copies of the P0 invariant (renderer variant is substring-only style) | S/M | M (safety tests exist: `tests/safety/`) | **3 — standalone** |
| RC-10 | **One frontmatter I/O home** (vault_io canonical; retire 4 reimplementations) | `schema/cli.py:39` · `extraction/vault_writer.py:20` · `cli/system.py:133-146` · `task_manager.py:279-330` (dies with RC-8) | Systemic; S1 contract fix (FR-5, 0%→87%) needs ONE place where frontmatter is written | S/M | Low | **3 — fold into F0 vault repair** |
| RC-11 | **One LLM-JSON parser** (`schema.utils.parse_llm_json`; retire audit.py's 60-line repair machine + cleanup/classifier copy + rfp copy) | `audit.py:157,:177-235` · `cleanup/classifier.py:84` · `rfp/answer_selector.py:373` | Systemic; parser divergence = divergent failure modes on every LLM call | S | Low | **3 — standalone sweep** |
| RC-12 | **Error-convention pass on load-bearing paths**: fix 3 pointless-tuple excepts; convert silent-empty returns in retrieval/ingest hot paths to logged statuses; make MinHash dedup absence LOUD (it currently no-ops the entire near-dup check at DEBUG) | `router.py:889` · `extractors.py:415` · `cli/overnight.py:183` · `dedup.py:284-286` · §3.d list | Systemic; P3/P4 pillars (revertability, heartbeat) presuppose failures are visible | M | Low | **3 — standalone, checklist-driven** |
| RC-13 | **Retire dead taxonomies**: fix cleanup classifier prompt folders; kill `VaultZone` legacy aliases after consumer migration (integrity/audit/query_engine); `template_manager` phantom paths resolved by its E12 kill-or-repoint decision | `cleanup/classifier.py:19-58` · `models.py:24-27` · `template_manager.py:186,:349` | Systemic; live misroute risk in cleanup; joins DR-7 zone renames at the registry-v4 moment | M | M | **3 — fold into registry v4 (DR-6/DR-7)** |
| RC-14 | **Dead-code sweep** (removals, batched): BACKLOG #11 set (frames×2, scripts×3, dup `_log_ingest_event`, PDF shims + zombie test rewrite) + new verified set (`_load_routing_map`, `analyze_all_folders`, `ScanSecurityError`, `cost_tracker`, `estimate_cost` stub, ChromaDB fallbacks ×2, `retrieve_for_rfp`, `compare_models` harness) + the 6 shims (§3.b) | §1.4 + §3.b lists | Over-engineering removal; ~2,000+ LOC and misleading-surface reduction; BACKLOG #11 already carries operator intent | M (batch of S) | Low (all zero-caller-verified; tests must be pruned with them) | **4 — standalone sweep; needs deletion sign-off per house rule** |
| RC-15 | **Kill `extractor/batch_api.py` (650-line BatchJobRunner)** + `--batch*` flags + `cke_client.extract_batch` + `batches` table/methods | `batch_api.py` · `run.py:685-687,:747-751` · `cke_client.py:178` · overnight state | Over-engineering: zero uses ever; kill cost S per deep-extraction §3.3; **lean KILL but NOT in DR-4 — needs operator sign-off (seed E4)** | S | Low | **4 — standalone, after sign-off** |
| RC-16 | **Overnight lifecycle hardening**: try/finally around create_run…complete_run + stale-`running` janitor; relocate `_run_folder_extraction`/`_run_full_reshape` from `cli/overnight.py` into `overnight/`; fix fake `F821` annotations | `cli/overnight.py:85-269,:301-444,:88,:105,:254` | R2 (FR-4 scheduled gap-fill loop) + P4 heartbeat pillar need a run ledger that can't wedge | M | M | **3/R2 — fold into R2 build** |
| RC-17 | **ExtractionResult slimming**: drop dead fields (authority, layer, quality, tokens_used… per field-survival), replace `run.py`'s hand-maintained 25-key dict with dataclass serialization, finish the frames-branch dedup | `extract.py:56-106,:522-545` · `run.py:618-651` | R2/FR-4 (grounding fields land in this record; slim before extending); DR-5 keeps key_facts/overlays — do together | M | M | **3 — fold into FR-4 grounding work** |
| RC-18 | **Small correctness fixes** (batch): analytics dashboard path `"00_dashboards"`→`VaultZone.DASHBOARDS` value; vault-stamp phantom zone (deal-loop §4.3); unreachable CSV rule (`classifier.py:208`); `retrieve()` double-file-read; `rfp.py` private `_call_llm` promotion; opportunity duplicate helpers | `analytics_actions.py:97` · `vault_actions.py` · `project/classifier.py:208` · `engine.py:280-281` · `prep.py:229` · opportunity §2.9 | Hygiene; each S; several are bugs-in-waiting rather than style | S | Low | **3/4 — batch standalone; opportunity items fold into FR-6** |
| RC-19 | **Ruff-format the committed tree** (BACKLOG #12): make `ruff format --check src/` pass so `dev-check.ps1` stops mutating the tree; consider widening `.ruff.toml` select AFTER the D/E zones are addressed (else 3,673-violation noise) | `.ruff.toml` · whole `src/` | Cosmetic but process-hazard (documented gotcha: ~100-file phantom diffs in unrelated tasks) | S | Low | **5 — standalone chore** |
| RC-20 | Typing-era cleanup (Optional→unions in project/, schema/models, rfp/anonymization); f-string→lazy logging; docstring rot (`80_Archive`, `00_dashboards/tasks/`) | §3.e list | Cosmetic | S | Low | **5 — opportunistic, inside touching changes** |

**Explicitly NOT proposed:** killing the `chat → intent_router → workflow_engine` stack (FR-9 revives it — RC-8's task/template removals shrink it naturally); any change to COM beyond DR-8's decided config fix (operator ruling: FIX, not kill); re-deciding the DR-4 items (decided — RC-8 is execution only); `merge_profiles`-style repair of modules RC-3 retires.

---

## 6. Method appendix

- Tools: radon 6.0.1 (`cc -j`, `mi -j`), vulture 2.16 (`--min-confidence 60`, cross-checked ≥80), ruff 0.15.8 (`--select ALL --statistics --exit-zero --no-cache`; committed `.ruff.toml` = E,F,I minus E501). All installed venv-only for this session; nothing committed to `pyproject.toml`; no `--fix` anywhere.
- Deep-read set per protocol: `rfp/` complete, `retrieve/` complete, `ingest/router.py`, `extractor/extract.py`, `index_builder.py`, + 5 highest-CC modules from Step 1. Remaining packages characterized by a structured evidence pass (file:line observations, same 5 dimensions).
- Prior evidence honored, not re-derived: six `2026-07-05-deep-*.md` audits, `2026-07-06-technical-architect-intake.md` (DR register + derivation order), `2026-03-30_CODE_QUALITY_AUDIT.md` (March baseline), BACKLOG #11 (surviving record of the 2026-04-17 dead-code audit — the audit file itself is absent from git history; noted as a provenance gap).
- Baseline test proof: `pytest -x -q` = 2,564 passed, 6 skipped (160.14s) on the untouched tree, 2026-07-06.
