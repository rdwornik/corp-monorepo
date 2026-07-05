# Functional Audit — Scenario Walkthroughs (Phase 2)

**Date:** 2026-07-05 · **Branch:** `docs/2026-07-05-functional-audit` · **HEAD:** `fb9b2dd` (+1 audit commit)
**Method:** static code trace (read-only) by three parallel subagents + one gated sandbox execution (§3.4, the only execution in this audit). Status vocabulary: ALIVE / DORMANT / EXISTS-UNTESTED / BROKEN / PHANTOM / MISSING. Code-level findings are merged with Phase-1 telemetry (`2026-07-05-functional-telemetry.md`) to produce final statuses.

---

## 1. S1 — RFP answering (priority scenario)

### 1.1 Load-bearing architectural fact: there are TWO disjoint RFP stacks

| Stack | Entry | Retrieval | Output | Doc write-back |
|---|---|---|---|---|
| **A. Console Q&A** | `corp rfp answer` (`src/corp/cli/rfp.py:14`) | `retrieve/rfp.py:answer_rfp` → `retrieve/engine.py` (index.db `notes`/`notes_fts` only) | One answer printed to terminal | No |
| **B. Document agents** | standalone scripts `rfp/rfp_excel_agent.py` / `rfp/rfp_answer_word.py` (run via `python`, **not registered as `corp` subcommands**) | `LLMRouter`/`KBRetriever` → `vault_adapter` (shells `corp retrieve --rfp-only`, else direct index.db); ChromaDB fallback points at absent `data/kb/chroma_store` | Answers written into `.xlsx`/`.docx` copies | Yes |

The hypothesis scenario ("Excel arrives → grounded answers written back") is served **only by Stack B**, which shares nothing with Stack A but index.db. Neither stack reaches the 1,329-file RFP KB at `corp_data/rfp_kb/` (§1.3).

**Use telemetry:** `data/output/` (Excel agent's save target, `rfp_excel_agent.py:673`) **does not exist**; `data/kb/` (feedback/Chroma tree) **does not exist**; no JOURNAL entry records answering a real RFP with either stack. → both stacks **EXISTS-UNTESTED**.

### 1.2 Nine-stage map (target process vs. implementation)

| Stage | What should happen | What code does | Status | Evidence |
|---|---|---|---|---|
| 0 intake/parse | Parse Excel/Word, extract questions | Excel: green-cell (FF00FF00) scan + column heuristics. Word: bold/numbering heading detection → section tree → answerable blocks | EXISTS-UNTESTED | `rfp_excel_agent.py:350-414`; `rfp_answer_word.py:128-256` |
| 1 classify (category × product × policy) | Per-question product + answer-policy | Product = ONE operator flag for the whole document (`--solution`/`--family`); no per-question classification, no answer-policy concept | PARTIAL / MISSING | `rfp_excel_agent.py:589`; `llm_router.py:189-193`; `rfp_answer_word.py:625-630` |
| 2 coverage check | Facts for THIS product? gap-fill trigger | `_find_coverage_gaps` exists only in Stack A's engine; doc agents never check coverage. `vault_adapter.retrieve_for_rfp` returns NO_DATA/LOW_CONFIDENCE statuses but has **no caller** | MISSING in doc flow | `engine.py:545-572`; `vault_adapter.py:73-109` |
| 3 dual retrieval (truth ∥ style) | Product-scoped facts + product-agnostic style | Single retrieval only; product filter is a coarse `n.products LIKE ?` post-filter; no style pass | MISSING | `engine.py:128-152,176-181`; `llm_router.py:243-257` |
| 4 reuse-vs-derive gate | source_hash staleness on past answers | No staleness gate anywhere in the answer flow. `answer_selector.py` (KEEP/REPLACE/ADD engine) has **no src caller** (tests only) and uses date recency, not hashes | DORMANT (selector) / MISSING (gate) | `answer_selector.py:468-570,295-297` |
| 5 compose | facts=content, precedent=form, style knobs | LLM synthesis from one prompt template; "style" = prompt text only | EXISTS-UNTESTED | `llm_router.py:306-371`; `config/rfp/prompts/rfp_system_prompt_universal.txt` |
| 6 verify + abstain | claim→cite, forbidden_claims gate, `[NEEDS INPUT]` | No claim→cite step. `check_forbidden_claims` exists but is called **only** from KB-correction tooling, never at answer time. Abstention = prompt instruction only | MISSING (gating) | `rfp_feedback.py:153-166` (sole call site `:362`) |
| 7 operator review | accept/edit/reject persisted as labels | Word `--interactive` review (Y/E/N/A/Q) filters an in-memory list; **nothing is persisted**. Excel has no review | EXISTS-UNTESTED, unpersisted | `rfp_answer_word.py:564-614` |
| 8 write-back + anonymize | approved answers → style store, fresh hash | Answers written into the document only; **no KB/style-store write-back**. Anonymization wraps the LLM call in the Excel agent only, flag-gated default OFF; Word path never anonymizes | PARTIAL | `rfp_excel_agent.py:440-448,591,636-654`; `rfp_answer_word.py:774-785` |

Stages implemented in any form: 0, 1 (partial), 5, 7 (in-memory), 8 (doc half). Stages with no implementation on the answering path: 2, 3, 4, 6, 8 (style-store half).

### 1.3 Key answers

- **Federation (ADR-22): PHANTOM.** No `rfp_entries` table, no `corp rfp-index` command anywhere in `src/` — `BACKLOG.md:20` says "refs ADR-22 (ratified, not built)"; `JOURNAL.md:412` "Next: Implement ADR-22" (2026-03-28, never done). Retrieval reaches only index.db; the `--rfp-only` flag filters vault notes on `rfp_visible=1` (`engine.py:205-206`) = 182 notes, **not** the 1,329 `rfp_kb` files. The RFP KB is reached by neither stack.
- **Product scoping:** exists as a single-sided `LIKE` filter (`engine.py:128-152`); operator supplies one product per document run. No fact/style separation, no cross-product leak protection beyond the filter.
- **Staleness:** no source_hash check gates answer reuse anywhere. (`rfp_feedback._content_hash` is an audit-trail hash for KB corrections, `rfp_feedback.py:46-48`.)
- **Review capture:** `data/kb/feedback_log.jsonl` writer exists (`rfp_feedback.py:124-134`) but the `data/kb/` tree is absent and the log has **no reader** in `src/`. Nothing captures accept/edit/reject.
- **Gating:** `config/rfp/product_profiles/_effective/*.yaml` (`forbidden_claims`, e.g. `wms.yaml:53-68`) are loaded only by the correction CLI — **dead YAML at answer time**. `config/rfp/overrides.yaml` has no loader at all.
- **Broken references:** `config/rfp/platform_matrix.json` referenced (`rfp_excel_agent.py:103,114`) but absent → `--solution` choice list is empty; `validate_profiles.py:428` imports non-existent `merge_profiles` → `--merge` raises ImportError; module docstrings still cite pre-monorepo paths.
- **Which product families S1 could honestly serve today** (Phase-1 coverage map, vault notes only since rfp_kb is unreachable): Platform (231), Demand Planning (185), Supply Planning (101), Azure (127) are servable; WMS (66) / TMS (54) are document-heavy but presentation-thin; Workforce Mgmt (12), Network Design (10), OMS (9), Commerce (4), CatMan (0) could not be honestly served.

---

## 2. S2 — Deal intake → archive (D1, D5)

### 2.1 Load-bearing fact: the scenario is split across two disconnected CLIs

`com` (opportunity manager) owns intake; the archive mechanism lives in the **`corp` chat action registry**; no code connects them, and the Salesforce + SharePoint legs exist in neither.

| Step | What should happen | What code does | Status | Evidence |
|---|---|---|---|---|
| SF team-add trigger | SF Opportunity Team add starts intake | No Salesforce API/webhook/poll anywhere; intake = manual `com new CLIENT -p PRODUCT` | MISSING | grep: only comments (`config/project/schemas/facts_template.yaml:7`) |
| Read Project_Codes.xlsm | Look up client row | Reads cols C/D/G/H/M via openpyxl read-only, temp-copy fallback if locked; env `PROJECT_CODES_EXCEL` | Code ALIVE-capable | `excel_manager.py:55-94`; `opportunity/config.py:67` |
| Write back to xlsm | Record folder link | Writes folder path to col M only; never creates rows | Code ALIVE-capable | `excel_manager.py:97-123` |
| Create local project folder | Scaffold `{Client}_{Product}/` | Creates folder + `_knowledge/` + deck-template copy + `project-info.yaml` + `notes.md` under `PROJECTS_ROOT` | **EXISTS-UNTESTED (misconfigured)** | `folder_manager.py:22-79`; see 2.2 |
| SharePoint team leg | Create/mirror team folder via Graph | **Nothing.** `com new` prints a dim reminder "Add Teams channel link"; `pyproject.toml:42` declares `graph = ["msal>=1.24"]` extra that nothing imports | MISSING | `cli.py:94`; grep msal/graph/office365 = 0 imports |
| Win/Loss detection | Stage=Closed Won/Lost drives archive | Stage (col H) is read for display only; nothing consumes it. Archive trigger = typing "archive/won/lost" keywords in `corp chat` | MISSING (trigger) | `excel_manager.py:35`; `workflows.yaml:117`; `intent_router.py:52-62,487-492` |
| Archive everywhere | Move + update all systems | `archive_project` moves folder → `archive_root/{year}/` + stamps vault `project-info.yaml`; never touches xlsm/SharePoint/SF. OneDrive guard means the synced copy **cannot** be archived by design | EXISTS-UNTESTED | `archive_actions.py:20-86`; `_helpers.py:103-134` |

### 2.2 Use telemetry and a configuration break

- **Zero real use:** all 29 real folders in `MyWork/10_Projects` lack `_knowledge/` (checked 2026-07-05) — no folder was ever created or touched by `com new`/`cpe render`. MyWork `90_Archive` has 0 files ever. No JOURNAL mention of `com` use.
- **BROKEN for real use as configured:** `PROJECTS_ROOT` env is unset, and `corp.opportunity.config` defaults it to `./test_projects` (CWD-relative; `opportunity/config.py:63`) — not to `MyWork/10_Projects` (which is the *`corp`-side* PipelineConfig default, `pipeline_config.py:83`). Running `com new` today would scaffold into a `test_projects/` folder created wherever the shell happens to be, not into the real projects zone. `test_projects` exists nowhere on disk — corroborating that it never ran.
- `com list` falls back to listing `PROJECTS_ROOT` dirs when the xlsm env isn't set; `com show` reads `_knowledge/project-info.yaml` (of which zero exist); `com chat` (Gemini intent parsing, 8 handlers) has **no archive handler** (`chat.py:301-310`).

### 2.3 Deck-brief Q1 — `com prep-deck`

**Stub-level: a renamed file copy, not assembly.** It prefix-matches the project folder, resolves the single configured template (`Blue_Yonder_Corporate_Presentation_Deck.pptx`, `config/opportunity/default.yaml:8`), and runs `shutil.copy2(source, dest)` with `dest = {client}_{date}_{topic}.pptx` in the project folder (`opportunity/cli.py:160-201`, copy at `:199-200`). No content generation, no KB grounding, no LLM. (The `corp`-side `brief_actions.generate_project_brief` builds a markdown one-pager from `facts.yaml` — a brief, not a deck.)

### 2.4 CPE's role

`cpe` (project/) is a file-scanning knowledge extractor over *existing* project folders — `scan → manifest.yaml → extract → render` producing `_knowledge/{project-info.yaml, facts.yaml, index.md}` (`project/renderer.py:24-86`). It is orthogonal to opportunity lifecycle: consumes folders humans/`com` created, knows nothing of stage/Win-Loss/xlsm. The archive workflow calls `cpe render` as its pre-archive step (`config/workflows.yaml:124-126`). OneDrive guard sits at the top of `render_project` (`renderer.py:38-52`), fail-closed. Zero `_knowledge/` dirs on disk → **EXISTS-UNTESTED** against real projects.

---

## 3. S3 — Knowledge capture → vault (W1–W2)

### 3.1 Static trace

Two entry lanes diverge sharply: **batch** `corp ingest` (`ingest/router.py`) and **interactive** `corp ingest-inbox` (`ingest/inbox.py`).

| Step | What should happen | What code does | Status (code) | Evidence |
|---|---|---|---|---|
| 1 land in Inbox | File appears in 00_Inbox | Both lanes enumerate loose files + depth-1 folders | WIRED | `router.py:101-152`; `inbox.py:912-913` |
| 2 classify | Destination + confidence | Pure `ContentRegistry` fnmatch/regex (series→client→rule→fallback). No ML | WIRED (heuristic-only) | `registry.py:71-103,147-229` |
| 2b near-dup check | Skip version-dupes | MinHash `check_near_duplicate` called **only in interactive lane**; absent from batch router; fails open | DANGLING in batch | `inbox.py:739-741`; `router.py` grep=0; `dedup.py:271-289` |
| 3 rename | Canonical `{YYYY-MM}_{TYPE}_{CLIENT}` name | **Interactive lane only.** Batch `corp ingest` moves files under their original names | Interactive only | `inbox.py:749`; `router.py:253,264` |
| 4 route | Confidence-based dest / _Staging / _Unmatched | Threshold 0.75, auto-accept ≥0.90 | WIRED | `router.py:204-221` |
| 5 record | ops.db before move | Both lanes record (assets/events; interactive adds routing_feedback log) | WIRED | `router.py:236-285`; `inbox.py:679-703` |
| 6 move | Relocate file | `shutil.move` with collision counter | WIRED | `router.py:264` |
| 7 extract | Hand to CKE | Writes `manifest.json` to `%LOCALAPPDATA%/corp-by-os/staging/ingest/<id>/`, then **subprocess `cke` CLI** (gated on `shutil.which("cke")`) | WIRED (blocking subprocess) | `router.py:292-312,720-810`; `cke_client.py:63-66,162-171` |
| 8 vault write | Note → vault zone | `move_to_vault(..., "01_Knowledge")` — zone **hardcoded** | WIRED to 01_Knowledge | `router.py:714,794`; `vault_writer.py:57-145` |
| 9 index update | FTS refresh | **NOT triggered by ingest.** Manual `corp index rebuild` required (exceptions: `ingest-extractions --rebuild-index`; interactive `--undo --full`) | DANGLING (no auto-hook) | `cli/index.py:17-42`; `router.py` grep=0 |

**Exact commands for inbox→vault→index today:** `corp ingest` (or `corp ingest-inbox`) **then** `corp index rebuild`. Out-of-band CKE output: `corp ingest-extractions <path> --rebuild-index`.

### 3.2 Phantom config surfaces (current state, reconciling the 2026-06-16 finding)

- **`40_Media/{Meetings,Demos,Training}`** — 3 content-registry destinations (`content_registry.yaml:310-332`) whose zone exists neither on disk nor in `folder_names.py:28-30`. Still live phantoms; a destination-rule for orphan meeting recordings routes into one of them (`:516-521`).
- **`routing_map.yaml` (MyWork/.corp) is entirely dead:** its reader `extraction/routing.py:resolve_route` has **no runtime caller**, and all its `vault_target`s (`02_sources/{project_id}`, `04_evergreen/_generated/*`, `01_projects/*`) are zones absent from disk. The live writer hardcodes `01_Knowledge`. This resolves the CLAUDE.md §5 / ADR-27 wording: the protected "`02_sources/`" zone is a **name that exists only in governance docs and dead config** — the enforced-by-test invariant actually protects `vault_io.write_note`'s real path.
- `fallback.review_destination: 00_Inbox/_Review` has no `folder_names.py` constant and no router consumer.
- `models.py:VaultZone` legacy members (`SOURCES="02_sources"`, `EVERGREEN="04_evergreen"`, `PROJECTS="projects"`) point at nothing; `index_builder._collect_project_dirs` scans `vault/projects` → 0 project dirs indexed (explains `facts=0`, `projects` table filled from note metadata instead).
- Hybrid TF-IDF classifier (85.5% accuracy, trained 2026-03-26): wired inside `corp.extractor` for doc_type decisions, but the live pipeline calls CKE **as a subprocess** and never uses it for routing → effectively DORMANT behind the process boundary.

### 3.3 Use telemetry recap (from Phase 1)

Interactive lane used ~22 times ever; batch `ingest-extractions` moved 2,673 notes on 2026-03-26/27; nothing since. 75 files sit in 00_Inbox (newest 2026-04-10). `content_signatures`=0 forever. → W1 capture **DORMANT** (last real use 2026-03-27; inflow stopped 2026-04-10).

### 3.4 S3 empirical — sandboxed e2e run (the only execution)

**Gate (fail-closed), passed:**
1. `PipelineConfig.sandbox(tmp_root)` puts every path under `tmp_root` (`pipeline_config.py:91-104`); `corp test-pipeline` creates `tmp_root` via `tempfile.mkdtemp(prefix="corp_pipeline_test_")` (`test_pipeline.py:118`) → resolves under `C:\Users\1028120\AppData\Local\Temp` (verified; `AppData\Local` is never OneDrive-redirected).
2. Hard assert: sandbox root is NOT under MyWork and NOT under any OneDrive path — confirmed by echoing `$env:TEMP` and the run's own output (`Sandbox: C:\Users\1028120\AppData\Local\Temp\corp_pipeline_test_z_spebpr`).
3. Default fixture mode makes **zero API calls** (`test_pipeline.py:6,123`).

**Run:** `corp test-pipeline --verbose` → **5/5 PASS** (exit 0): `sandbox_init` (3 DBs + inbox + vault), `classify_and_rename` (5 naming checks), `vault_ingest` (2 mock notes → sandbox `01_Knowledge`, 0 errors), `index_rebuild` (2 notes indexed), `retrieve` (query ok, 2 results).

**Cleanup verified:** `corp_pipeline_test_*` dirs in `%TEMP%` before run: 0; after: 0. The CLI path tears down via `shutil.rmtree` in `finally` (`test_pipeline.py:161-163`). (The separate suspicion stands at the library level: `SandboxManager.context()` never calls `teardown()` — `sandbox.py:156-158` — but its only callers pass pytest `tmp_path`, which pytest manages. Two stale leftovers from March exist elsewhere: `%LOCALAPPDATA%/corp-by-os/overnight_staging/20260312_192817/` and empty pre-Council-#24 zone dirs `staging/50_RFP`, `staging/60_Source_Library` — reported, not deleted.)

**Verdict on the capture process ("magistrala unverified since Council #24"):** **ALIVE-in-sandbox** for the legs the smoke test covers (naming config, `ingest_extractions` → vault write to `01_Knowledge`, index rebuild, FTS query) — these all work with post-Council-#24 paths. **Caveat:** fixture mode does not exercise ContentRegistry routing of real inbox files nor the CKE subprocess leg. Supplementary evidence that the CKE engine itself still runs: `output/test/extract/` contains live extraction artifacts re-generated on dev-session days through **2026-06-16**.

---

## 4. Deck-brief questions (Q1–Q5)

**Q1 — `com prep-deck`:** stub — a `shutil.copy2` of the one configured corporate template into the project folder, renamed `{client}_{date}_{topic}.pptx` (`opportunity/cli.py:160-201`). No assembly, no KB grounding. See §2.3.

**Q2 — citations/provenance in `corp retrieve` / `corp prep`:** `retrieve/engine.py` returns per-note provenance: `note_id`, absolute `note_path`, BM25 `relevance_score` re-weighted by trust tier (`CONFIDENCE_BOOST {verified:0, extracted:10, generated:50, draft:100}`, `engine.py:75-90`), and a human citation string `"[{title}] (client: …, source: {source_type})"` (`engine.py:291-295`). `corp prep` instructs the LLM to cite `[Note Title]` inline and force `[NOT IN KNOWLEDGE BASE]` for gaps (`prep.py:56,102-104`); output records `*Sources: N notes*` but **not file paths** — title-string citations only. Vault note frontmatter is rich provenance (verbatim sample in agent trace): `source_path`, `source_hash`, `source_mtime`, `model`, `prompt_version`, `extraction_version`, `trust_level`, `key_facts`, overlays. Notably the sampled note's `source_path` points at `MyWork/60_Source_Library/...` — a zone that no longer exists → `trust_level: deprecated`, `rebuild_status: source_inaccessible`: the March folder restructure orphaned note→source links.

**Q3 — intermediate manifest in RFP agents:** both build an **in-memory** structure (Excel: `green_cells` list of question/answer-column dicts, `rfp_excel_agent.py:400-412`; Word: `AnswerableBlock` list with breadcrumb + insertion anchor, `rfp_answer_word.py:101-109`), then write answers directly into the document. **No persisted manifest file** exists between questions and document.

**Q4 — `template_manager`:** manages binary Office templates (`.pptx/.xlsx/.docx` — **not `.potx`**, `template_manager.py:23,165`); registry written to `vault/.corp/template_registry.yaml`. Carries stale path labels (`30_Templates/`, `90_System/` in docstrings and `rel_path`/`copy_template` prefixes, `:2-4,186,349`) that match neither disk (`20_Workflows` is the real templates root, `config.py:82-85`) nor the vault (`99_System`). **No `KM_v2` template is registered anywhere** — `grep KM_v2` across the repo = 0 matches.

**Q5 — generated-artifact paths:** all resolve outside OneDrive — `%LOCALAPPDATA%/corp-by-os/` (DBs + `staging/ingest/<id>`), `ObsidianVault/01_Knowledge` (notes), `MyWork/<project>/_corp_prep` or `MyWork/.corp/_corp_prep` (prep briefs, `cli/retrieve.py:198-200`), repo `data/output/` (Excel agent target, currently absent). OneDrive appears in config **only** as `[safety] excluded_paths` (`paths.toml:18-20`). Confirmed from code+config without OneDrive traversal.

---

*End of Phase 2. No writes performed outside this file; the only execution was the gated sandbox smoke test (§3.4).*
