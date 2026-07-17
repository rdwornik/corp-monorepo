# Arc-B Deletion Manifest (SIGNED) — 2026-07-17

> **Purpose:** the operator-signable deletion contract for Arc B. This document is the
> contract; **execution is a separate, operator-signed arc.** Zero deletions were performed
> in the session that produced this manifest — no `src/`, `tests/`, or `main` change. Each
> row is pre-filled `PROPOSED-*`; the operator flips it to a signed ruling in the sign-off
> block below, then a later arc executes the signed rows as independently-revertable commits.
>
> **Governing:** Layer-1 operator ruling A3-R4/R5 (target-architecture ruling, ratified
> off-repo 2026-07-17; repo codification pending in the primary checkout) + witnessed
> evidence: ground-truth audit §6 D-1/D-2/D-3 and headline #7
> (`docs/audits/2026-07-16-architecture-ground-truth.md`). Extends — does not re-derive —
> that audit's §6 dead-weight ledger, the code-quality audit §1.4/RC-8/14/15
> (`docs/audits/2026-07-06-code-quality-audit.md`), intake DR-4
> (`docs/audits/2026-07-06-technical-architect-intake.md:80`), and the Codex edge-diff +
> Addendum A.3 read-binding table (`docs/audits/2026-07-16-codex-edge-diff.md`).
>
> **Method:** every KILL/GATED row carries three legs re-derived **fresh this session**
> against worktree HEAD `f0592be` (NOT quoted from the audits): (a) whole-repo caller
> re-grep (source + tests), verbatim in the per-batch fences; (b) Codex data-binding
> cross-check (a zero-caller module with a live data-READ binding is **not** zero-use);
> (c) docs/ + config reference grep. A row missing any leg is stamped **UNVERIFIED** and
> cannot be signed.

## Freshness caveats (read before signing)

- Re-greps are against HEAD `f0592be` (post night-batch v2). Two ground-truth claims are
  **already resolved** and deliberately excluded from this manifest: D-8 `_TEST_SCHEMA`
  hand-copies were killed in Arc N2 (`56e476e`); `src/corp/safety/onedrive.py` now exists.
- The intake's "**51 tests for dead modules**" figure is misleading — it counts the 42
  `resolve_product_key` tests, which are **KEEP** (exclusion). Deletable-as-KILL tests
  = **2** (cost_tracker, 2 of 23 methods in `test_providers.py`) + **25** (task_manager,
  whole file) + facts fixtures in `test_query_engine.py` / `test_index_builder.py`.
- "A3-R5's canonical pricing registry" does **not** exist as a module. `cost_tracker` is
  superseded by the de-facto live per-provider dicts `ANTHROPIC_PRICING`
  (`anthropic_provider.py:15`) / `GEMINI_PRICING` (`gemini_provider.py:15`), not a registry.

---

## Sign-off block

```
Signed:      Rob                             (operator)
Date:        2026-07-17
Scope-hash:  ba011e700d127536b02d97f7e31eeaa693db9777b8b86cf71ccd6508c91b6f4f  (sha256 of this manifest at sign-off; computed with this value left blank as ____)

Per-batch rulings (operator flips PROPOSED-* → signed):
  Batch 1  cost_tracker .................  [x] KILL   [ ] DEFER   [ ] KEEP
  Batch 2  facts pipeline (repoint) .....  [x] KILL   [ ] DEFER   [ ] KEEP
  Batch 3  inbox lane (router internals)   [x] KILL   [ ] DEFER   [ ] KEEP
  Batch 4  N4 task-manager cascade ......  [x] KILL (requires explicit zero-use word)  [ ] DEFER  [ ] KEEP
  Batch 5  zero-caller dead limbs .......  [x] KILL   [ ] DEFER   [ ] KEEP
  Exclusions (KEEP) confirmed ..........  [x] yes
  DEFER field acknowledged (not signable) [x] yes
```

**Batch 4 zero-use confirmation** (operator's verbatim word, recorded at sign-off — his word is the evidence):

> "Na razie nic nie używam — całe repozytorium wymaga połączenia, żeby zaczęło działać jako agent."

Architect note for the record: the zero-use is **blanket** (the system is pre-operational; no
feature is in use), so the usage gate is satisfied *a fortiori*. The design-intent authority for
killing N4 specifically is the ratified DR-4 kill (intake decision register) carried into A3-R4.

**Ruling legend:** `PROPOSED-KILL` = re-grep supports deletion, awaiting signature ·
`PROPOSED-GATED` = deletion blocked until the operator's explicit confirmation (his word
is the evidence) · `PROPOSED-KEEP` = re-grep contradicts deletion, exclusion · `DEFER` =
visibility-only, **not signable as KILL in this manifest**.

**Column key:** `# · Target · Class · Evidence (file:line) · Callers re-grep (summary; raw
in fence) · Data bindings (Codex A.3) · LOC · Risk · Revert plan · Ruling`.

---

## Batch 1 — `cost_tracker` (clean KILL)

| # | Target | Class | Evidence | Callers re-grep | Data bindings | LOC | Risk | Revert plan | Ruling |
|---|--------|-------|----------|-----------------|---------------|-----|------|-------------|--------|
| 1.1 | `src/corp/extractor/providers/cost_tracker.py` — whole file (`log_cost`, `get_monthly_spend`, `check_budget`, `COST_LOG`) | DR-4-adjacent / zero-caller limb (§6 D-5) | def `cost_tracker.py:14/35/54`; ledger `:11` | **0 src callers.** Only `tests/extractor/test_providers.py` (see fence) | None (`cost_log.jsonl` absent on disk) | 74 | LOW (leaf; superseded by live per-provider pricing dicts) | Single commit revert restores file | **PROPOSED-KILL** |
| 1.2 | `tests/extractor/test_providers.py` → remove **2 of 23** methods only: `test_log_and_read_cost:203`, `test_budget_check:251` | test-for-dead-module | `test_providers.py:203,251` | n/a (test file; 21 non-cost tests STAY) | None | ~70 (2 methods) | LOW | Revert restores methods; **do NOT delete the file** | **PROPOSED-KILL** |

**Verbatim re-grep** (`rg -n "cost_tracker|log_cost|get_monthly_spend|check_budget" src/ tests/`):

```
tests/extractor/test_providers.py:205:        from corp.extractor.providers import cost_tracker
tests/extractor/test_providers.py:211:        original = cost_tracker.COST_LOG
tests/extractor/test_providers.py:212:        cost_tracker.COST_LOG = tmp_path
tests/extractor/test_providers.py:219:            assert cost_tracker.get_monthly_spend() == 0.0
tests/extractor/test_providers.py:221:            cost_tracker.log_cost(
tests/extractor/test_providers.py:228:            cost_tracker.log_cost(
tests/extractor/test_providers.py:236:            total = cost_tracker.get_monthly_spend()
tests/extractor/test_providers.py:247:            cost_tracker.COST_LOG = original
tests/extractor/test_providers.py:253:        from corp.extractor.providers import cost_tracker
tests/extractor/test_providers.py:258:        original = cost_tracker.COST_LOG
tests/extractor/test_providers.py:259:        cost_tracker.COST_LOG = tmp_path
tests/extractor/test_providers.py:266:            assert cost_tracker.check_budget(20.0) is True
tests/extractor/test_providers.py:269:            cost_tracker.log_cost("test", "test", 0, 0, 25.0)
tests/extractor/test_providers.py:272:            assert cost_tracker.check_budget(20.0) is False
tests/extractor/test_providers.py:274:            cost_tracker.COST_LOG = original
src/corp/extractor/providers/cost_tracker.py:14:def log_cost(
src/corp/extractor/providers/cost_tracker.py:35:def get_monthly_spend() -> float:
src/corp/extractor/providers/cost_tracker.py:54:def check_budget(budget: float, alert_threshold: float | None = None) -> bool:
src/corp/extractor/providers/cost_tracker.py:59:    spend = get_monthly_spend()
```

Supersessor confirmed live: `anthropic_provider.py:15 ANTHROPIC_PRICING`, `:49` used;
`gemini_provider.py:15 GEMINI_PRICING`, `:69` used. **Codex A.3:** `cost_tracker` is absent
from the read-binding KEEP list → no live data binding.

---

## Batch 2 — facts pipeline (repoint, **NOT** a clean severance)

**This is a refactor, not an amputation.** `search_facts` has **3 live consumers**; killing
the DDL + loader requires repointing `search_facts` to `_search_notes_fts` only (the
notes_fts fallback is already live at `query_engine.py:89-98`). The `notes_fts` path and
`_search_notes_fts:260` **STAY**.

| # | Target | Class | Evidence | Callers re-grep | Data bindings | LOC | Risk | Revert plan | Ruling |
|---|--------|-------|----------|-----------------|---------------|-----|------|-------------|--------|
| 2.1 | `index_builder.py` facts DDL — `facts` table `:45`, `facts_fts` `:57`, triggers `:133-140`, `projects.facts_count` col `:38` | DR-4 kill / §6 D-1 | `index_builder.py:38,45,57,133-140` | Schema always created at rebuild; no external caller of the tables except via `search_facts` | index.db WRITE (index_builder) — Codex A.3 lists `index_builder` READ `:322`; facts tables specifically are write-then-unread | ~30 | **HIGH** | Single commit revert | **PROPOSED-KILL** |
| 2.2 | `index_builder.py` facts loader `_load_and_insert_facts:473-540` + rebuild bookkeeping threading `facts_count` (`:191,201-207,228,244,260,268,299-307,439,450,464`) | DR-4 kill / §6 D-1 | `index_builder.py:473`; bookkeeping lines listed | Called only within `index_builder` (`:201,:299`) | Producer path mismatch → "0 rows ever" | ~68 + bookkeeping | **HIGH** (unthread `facts_count` from the rebuild DTO too) | Single commit revert | **PROPOSED-KILL** |
| 2.3 | `query_engine.py search_facts:25-101` — repoint to notes_fts branch only | DR-4 kill / §6 D-1 | `query_engine.py:25`; facts SQL `:50-73` | **3 live src consumers:** `cli/query.py:36`, `actions/knowledge_actions.py:28`, `test_pipeline.py:358`; + `tests/test_query_engine.py:148-175` | vault READ via notes_fts (KEEP path) | ~40 (rewrite, not delete) | **HIGH** (behavior change to `corp query`) | Single commit revert | **PROPOSED-KILL** |
| 2.4 | `_search_notes_fts:260-299` + fallback `:89-98` | **sub-KEEP** | `query_engine.py:89,260` | live within `search_facts`; also live in `retrieve/engine.py:221`, `rfp/vault_adapter.py:196` | vault READ (live) | — | — | **must NOT be deleted** | **PROPOSED-KEEP** |
| 2.5 | facts test fixtures — `tests/test_query_engine.py` (7 `search_facts` asserts), `tests/test_index_builder.py:122,126,176,237,242,246` | test-for-dead-module | listed | n/a | None | — | MED (some assert notes_fts behavior post-repoint — rewrite, not blanket-delete) | Revert restores | **PROPOSED-KILL** |

**On-disk artifact disposition (operator ruling — sign against the complete picture):**
killing the DDL + loader leaves **existing `index.db` instances with orphaned `facts` /
`facts_fts` tables and a stale `projects.facts_count` column**. Ruling: the orphaned tables
are **harmless-in-place** — after the repoint (2.3) nothing reads them — and they **disappear
on the next full index rebuild** (`_SCHEMA` no longer creates them; the rebuild recreates the
DB from the post-kill schema). **Named cleanup path:** `corp index rebuild` (→
`index_builder.rebuild_index`, `cli/index.py:17-36`). So the complete change surface is:
**code change (2.1–2.3) + behavior change to `corp query` + on-disk residue cleared by
`corp index rebuild`.** No data migration required; no reader depends on the residue.

**Verbatim re-grep** (`rg -n "search_facts" src/ tests/`):

```
tests/test_query_engine.py:14:    search_facts,
tests/test_query_engine.py:148:        results = search_facts("SAP", db_path=populated_index)
tests/test_query_engine.py:152:        results = search_facts("SAP", project_filter="lenzing_planning", db_path=populated_index)
tests/test_query_engine.py:157:        results = search_facts("blockchain quantum", db_path=populated_index)
tests/test_query_engine.py:161:        results = search_facts("demand", db_path=populated_index)
tests/test_query_engine.py:166:        results = search_facts("SOC2", db_path=populated_index)
tests/test_query_engine.py:171:        results = search_facts("SAP", limit=1, db_path=populated_index)
tests/test_query_engine.py:175:        results = search_facts("demand planning", db_path=populated_index)
src/corp/test_pipeline.py:356:    from corp.query_engine import search_facts
src/corp/test_pipeline.py:358:    results = search_facts(query="test", db_path=sb.config.index_db_path)
src/corp/actions/knowledge_actions.py:16:    from corp.query_engine import search_facts
src/corp/actions/knowledge_actions.py:28:    results = search_facts(query, project_filter=project_filter)
src/corp/cli/query.py:34:        from corp.query_engine import search_facts
src/corp/cli/query.py:36:        results = search_facts(search_terms, project_filter=project, limit=limit)
src/corp/query_engine.py:25:def search_facts(
```

---

## Batch 3 — inbox lane in `ingest/router.py` (narrow scope; **`move_to_vault` KEEPS**)

Per §6 **D-2**, the DR-4 "Lane B `move_to_vault`" kill must be **narrowed to the dead inbox
lane**, NOT the function. **Honesty note:** the extraction internals below are **not**
zero-caller in the import graph — `_run_extraction` is called at `router.py:295` (by
`ingest_file`) and `_run_package_extraction` at `:596` (by `ingest_folder`). The "dead lane"
designation rests on the **runtime** evidence that Lane B never completed a write
(`deep-magistrala.md` §Step 1), not a zero-caller grep. **The exact dead-boundary must be
witnessed at execution — do NOT blanket-delete `router.py`.**

| # | Target | Class | Evidence | Callers re-grep | Data bindings | LOC | Risk | Revert plan | Ruling |
|---|--------|-------|----------|-----------------|---------------|-----|------|-------------|--------|
| 3.1 | `ingest/router.py` inbox-lane extraction internals — `_run_extraction:720-810`, `_run_package_extraction:633-717` | DR-4 kill (narrowed) / §6 D-2 | `router.py:633,720`; callers `:295,:596` | Reachable from `ingest_file:155`/`ingest_folder:490`/`ingest_all:315` — **live in import graph**; "dead" is a runtime claim | MyWork READ (ingest) `router.py:111-125,671` — Codex A.3 KEEP for the *scan* path | ~176 | **HIGH** (boundary precision; must not sever the live `corp ingest` path) | Single commit; boundary documented at execution | **PROPOSED-KILL** (boundary to be witnessed) |
| 3.2 | `move_to_vault` (`extraction/vault_writer.py:57`) | **exclusion** | `vault_writer.py:57` | **6 live sites:** `router.py:715,795`, `cli/extract.py:131`, `cli/overnight.py:250` (+11 tests in 2 files) | vault WRITE (live) — Codex A.3 KEEP | — | — | must NOT be deleted | **PROPOSED-KEEP** |

**Verbatim re-grep** (`rg -n "move_to_vault" src/`; test callers elided — 11 in
`tests/test_extraction/test_vault_writer.py` + `tests/test_extraction_non_project/test_vault_writer.py`):

```
src/corp/extraction/vault_writer.py:57:def move_to_vault(
src/corp/cli/overnight.py:168:    from corp.extraction.vault_writer import move_to_vault
src/corp/cli/overnight.py:250:            moved = move_to_vault(out_dir, cfg.vault_path, route.vault_target)
src/corp/ingest/router.py:712:    from corp.extraction.vault_writer import move_to_vault
src/corp/ingest/router.py:715:    move_to_vault(staging_dir, config.vault_path, vault_target)
src/corp/ingest/router.py:792:    from corp.extraction.vault_writer import move_to_vault
src/corp/ingest/router.py:795:    moved = move_to_vault(staging_dir, config.vault_path, vault_target)
src/corp/cli/extract.py:129:        from corp.extraction.vault_writer import move_to_vault
src/corp/cli/extract.py:131:        moved = move_to_vault(out_dir, cfg.vault_path, route.vault_target)
```

---

## Batch 4 — N4 task-manager cascade (**PROPOSED-GATED**)

**Gated:** the whole group is blocked until the operator's **explicit zero-use confirmation
at sign-off** — his word is the evidence; nothing here executes without it. **Tension to
sign against:** `task_manager` is in the Codex A.3 KEEP list (live vault READ at
`task_manager.py:197,274,317`) — the code *works*; the *feature* is unused. The only
runtime consumer outside the group is the chat status hook (`chat.py:205`), itself part of
the intended cascade. No consumer in `retrieve/`, `ops/`, `extraction/`, or `schema/` touches it.

| # | Target | Class | Evidence | Callers re-grep | Data bindings | LOC | Risk | Revert plan | Ruling |
|---|--------|-------|----------|-----------------|---------------|-----|------|-------------|--------|
| 4.1 | `src/corp/task_manager.py` (whole) | DR-4 kill / §6 D-3 | `task_manager.py:1` | consumers all in-cascade (see fence) | vault READ `:197,274,317` (Codex A.3) — the gate rationale | 335 | MED (gated) | one revertable commit for the whole cascade | **PROPOSED-GATED** |
| 4.2 | `src/corp/cli/task.py` (whole) + registration `cli/__init__.py:83` (`import task_group, tasks_shortcut`) **and `:107`** (`cli.add_command(tasks_shortcut)`) | cascade | `cli/task.py:1`; `cli/__init__.py:83,107` | — | none | 126 (+2 lines) | MED | same commit | **PROPOSED-GATED** |
| 4.3 | `src/corp/actions/task_actions.py` (whole) + re-export `actions/__init__.py:47` + doc `actions/README.md:18` | cascade | `task_actions.py:1`; `actions/__init__.py:47`; `README.md:18` | — | none | 71 (+2 refs) | MED | same commit | **PROPOSED-GATED** |
| 4.4 | `src/corp/models.py:202-235` — `TaskStatus:202`, `TaskPriority:211`, `Task:220` | cascade (Task models) | `models.py:202,211,220` | consumed only by `task_manager` | none | ~34 | MED | same commit | **PROPOSED-GATED** |
| 4.5 | `src/corp/chat.py` status wiring `:202-215` (`from corp.task_manager import list_tasks` `:205`) | cascade (chat hook) | `chat.py:205` | in-cascade only | vault READ (via list_tasks) | ~14 | MED (chat status panel loses the todo count) | same commit | **PROPOSED-GATED** |
| 4.6 | `tach.toml:140` (`path = "corp.task_manager"`) + `:155` (`depends_on [...]`) | config scrub | `tach.toml:140,155` | tach layer entry | n/a | 2 | LOW | same commit | **PROPOSED-GATED** |
| 4.7 | `tests/test_task_manager.py` (whole, 25 tests) + eval fixtures `eval/cli_snapshot_2026-03-28/task*.txt` | test-for-dead-module | 25 `def test` | n/a | none | 246 | LOW | same commit | **PROPOSED-GATED** |

**Verbatim re-grep** (`rg -n "task_manager|task_actions|task_group|tasks_shortcut" src/ tests/ tach.toml`):

```
tach.toml:140:path = "corp.task_manager"
tach.toml:155:depends_on = ["corp.template_manager", "corp.task_manager", "corp.index_builder", "corp.query_engine"]
src/corp/actions/README.md:18:- `task_actions` — task add/list/done actions
src/corp/actions/task_actions.py:16:    from corp.task_manager import add_task
src/corp/actions/task_actions.py:45:    from corp.task_manager import list_tasks
src/corp/actions/__init__.py:47:    task_actions,
src/corp/chat.py:205:        from corp.task_manager import list_tasks
src/corp/cli/task.py:24:    from corp.task_manager import add_task
src/corp/cli/task.py:41:    from corp.task_manager import list_tasks
src/corp/cli/task.py:81:    from corp.task_manager import complete_task
src/corp/cli/task.py:95:    from corp.task_manager import list_tasks
src/corp/cli/__init__.py:83:from corp.cli.task import task_group, tasks_shortcut
src/corp/cli/__init__.py:107:cli.add_command(tasks_shortcut)
tests/test_task_manager.py:12:from corp.task_manager import (
```

---

## Batch 5 — zero-caller dead limbs (re-verified)

| # | Target | Class | Evidence | Callers re-grep | Data bindings | LOC | Risk | Revert plan | Ruling |
|---|--------|-------|----------|-----------------|---------------|-----|------|-------------|--------|
| 5.1 | `src/corp/extractor/frames/tagger.py` (whole, `tag_frames`) | zero-caller limb | `tagger.py:27` | **0 callers** (only its own def) | none | 116 | LOW | single commit | **PROPOSED-KILL** |
| 5.2 | `src/corp/extractor/frames/extractor.py` (whole, `extract_frames`) | zero-caller limb | `extractor.py:24` | **0 callers** (only own def + docstring example `:9,:12`) | none | 167 | LOW | single commit | **PROPOSED-KILL** |

**Scope-worry disproved:** `tagger.py` carries **no live model-string catalog** — it is a
single config-default lookup (`tagger.py:47 get("settings","llm.tagger_model","gemini-3.1-flash-lite")`;
config value `config/extractor/settings.yaml:328`). Nothing to preserve → flips from
"re-verify KEEP/KILL" to **KILL with evidence**. `frames/` package STAYS (`sampler.py`,
`scene_detect.py` are live).

**Verbatim re-grep:**

```
# rg -n "tag_frames|frames.tagger|import tagger" src/ tests/
src/corp/extractor/frames/tagger.py:27:def tag_frames(frames: list[dict], batch_size: int = None) -> list[dict]:

# rg -n "extract_frames|frames.extractor|frames import extractor" src/ tests/
src/corp/extractor/frames/extractor.py:9:    from corp.extractor.frames.extractor import extract_frames
src/corp/extractor/frames/extractor.py:12:    frames = extract_frames(video_path, output_dir, config)
src/corp/extractor/frames/extractor.py:24:def extract_frames(
```

---

## Exclusions — explicit KEEP (do not delete)

| Target | Reason | Evidence | Callers re-grep | Ruling |
|--------|--------|----------|-----------------|--------|
| `resolve_product_key` (`schema/products.py:72-110`) + export `schema/__init__.py:32,61` + `tests/schema/test_products.py` (42 tests) | A3-R4 exclusion: T1-charter / FR-10 designated product-vocab owner (RC-7 plans to wire it at the index-build seam). Aspirational — 0 runtime callers today, but charter-designated. | `schema/products.py:72`; `schema/__init__.py:32,61` | 0 src callers (only export + tests) — **verified**, but KEEP by charter | **PROPOSED-KEEP** |
| `move_to_vault` | 6 live call sites (Batch 3.2) | `vault_writer.py:57` | see Batch 3 fence | **PROPOSED-KEEP** |
| `BatchJobRunner` (`batch_api.py:304`) | **Re-grep flip — the flagship "audit say-so ≠ truth" catch.** Scope listed it as a zero-caller limb; RC-15 wants it killed (`batches` table 0 rows, `state.create_batch` zero callers). But a **live instantiation exists** behind the `--batch` flag → cannot be signed KILL. | `batch_api.py:304`; **live** `scripts/run.py:748,750` | see fence below | **PROPOSED-KEEP** (conflict recorded) |

**Verbatim re-grep** (`rg -n "BatchJobRunner" src/ tests/`):

```
src/corp/extractor/batch_api.py:304:class BatchJobRunner:
src/corp/extractor/scripts/run.py:748:        from corp.extractor.batch_api import BatchJobRunner
src/corp/extractor/scripts/run.py:750:        runner = BatchJobRunner(manifest, config, force_tier=tier, resume=resume, force=force)
tests/extractor/test_batch_api.py:374:        runner = BatchJobRunner(manifest, {"prompts": {"extract": "test"}, "gemini": {}})
tests/extractor/test_force_flag.py:70:        runner = BatchJobRunner(manifest, {}, force=True)
tests/extractor/test_force_flag.py:79:        runner = BatchJobRunner(manifest, {})
```

---

## DEFER field (visibility-only — **NOT signable as KILL in this manifest**)

Recorded so the operator sees the full adjacent field. Each needs its own re-verification
arc before it could be signed; none is proposed for deletion here.

| Target | Why deferred | Evidence (existence re-confirmed this session) |
|--------|--------------|-----------------------------------------------|
| ChromaDB fallbacks — `rfp/llm_router.py` (`_init_chromadb_fallback`, `_retrieve_chromadb`), `rfp/rfp_answer_word.py` (`_init_chromadb_fallback`, `_query_chromadb`) | Backing store gone (ADR-33) but methods wired inside **live** RFP classes; needs vault-primary path confirmed before removal | `rfp/llm_router.py:204`, `rfp/rfp_answer_word.py:311` |
| rfp KB canonical JSON orphan (§6 D-7) | Orphan **input** (no in-repo producer; `data/kb/` absent). Not in DR-4 — different class (missing producer, not dead consumer) | `rfp/llm_router.py:54`, `rfp_answer_word.py:69` |
| RC-14 dead-code sweep set | Beyond the scope-enumerated set; own future manifest | `extraction/routing.py:30 _load_routing_map`; `audit.py:328 analyze_all_folders`; `extraction/scanner.py:26 ScanSecurityError`; `overnight/cke_client.py:97 estimate_cost` (stub); + `contract.py:31 validate_manifest`, `schema/config.py:63 get_excluded_paths`, `:87 rfp_kb_path`, `vault_adapter.retrieve_for_rfp`, duplicate `_log_ingest_event`, `extractor/scripts/{batch_compress,compress_video,preprocess_audio}.py` |

---

## Execution contract (for the separate signed arc — NOT this session)

1. Execute only rows the operator signed KILL/GATED in the sign-off block above.
2. One commit per batch (each row-group is scoped to be independently revertable).
3. Batch 2 additionally: repoint `search_facts` → notes_fts, then run `corp index rebuild`
   to clear the on-disk `facts`/`facts_fts`/`facts_count` residue.
4. Batch 3: witness the exact dead-lane boundary before cutting; never sever the live
   `corp ingest` path or `move_to_vault`.
5. Batch 4 fires only with the operator's explicit zero-use word recorded at sign-off.
6. Run `./scripts/run-all-tests.ps1` after each batch; `./scripts/dev-check.ps1` before PR.

---

**Produced:** 2026-07-17 · worktree `arc-b-manifest` · HEAD `f0592be` · read-only session
(zero deletions). **Governing authority:** operator ruling A3-R4/R5 (off-repo) + ground-truth
audit §6 D-1/D-2/D-3 + headline #7.
