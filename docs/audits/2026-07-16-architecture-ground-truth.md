# Architecture Ground-Truth Recon — 2026-07-16

> **Purpose:** witnessed dependency + contract map for the upcoming target-architecture ruling (cleanup, interface unification, seam tests). Read-only audit — no src/ changes. Extends (does not re-derive) `docs/audits/2026-07-06-code-quality-audit.md` and `docs/audits/2026-07-06-technical-architect-intake.md`.
> **Method:** 12 parallel read-only recon subagents (8 package clusters, 4 root-module clusters grouped by tach layer), each reporting OUTBOUND edges only with verbatim grep evidence; central orchestrator ran `tach check`/`tach map` (tach 0.34.0), the §5 fragmentation sweep (known-symbol + discovery greps), the §6 dead-weight verification (whole-repo caller greps), and a spot-check pass over drift/zero-caller claims before assembly. `NOT-FOUND` is a literal witnessed token, never an omission.
> **Scope:** all 13 packages + 20 root modules under `src/corp/`.

## 0. Headline findings

1. **The codemap is ~90% wrong or missing.** 90 witnessed static unit-edges vs 8 drawn; of the 8, only 3 are correct-as-drawn, 7 named targets are phantom, and `rfp → retrieve` is a subprocess edge drawn as an import (§4.1).
2. **cli imports none of extractor/project/opportunity/rfp** — the four "CLI fan-out" edges everyone reasons from don't exist; `cke`/`cpe`/`com` are sibling entry points, and `corp rfp answer` uses `corp.retrieve.rfp` (§1a, §4.1).
3. **The corp→CKE boundary is subprocess-only, implemented twice** (`overnight/cke_client.py` + `project/cke_invoker.py`), with a fragile stdout-literal-line response contract that **no test exercises** (§1b, §2, §5.8).
4. **The vault-writer invariant as written doesn't match reality:** the repo's only `write_note` call writes `01_Knowledge/` flat; `02_sources/` is populated by actions via `copy_to_vault`; and `project/cli.py --copy-to-vault` writes an arbitrary unguarded path (§4.2 D1/D6).
5. **`src/corp/test_pipeline.py` is silently exempt from tach** (`test_*.py` exclude) despite 13 real outbound edges; ADR-27's `safety/onedrive.py` centralization was never built (§4.2 D4/D5).
6. **Fragmentation grew since 2026-07-06:** frontmatter parsers 5→9, LLM-JSON parsers 3→8, pricing tables 3→5 (two of which disagree on the same model's price), config systems 5→7+, plus ~19 scattered model-string literals (§5).
7. **DR-4 needs re-scoping before Arc-B deletes anything:** `move_to_vault` has 6 live call sites (the "kill" is one dead lane, not the function); the facts pipeline's "0 rows ever" is now mechanically explained (producer/consumer path mismatch) but has 3 live consumer paths; rfp's KB JSON is an orphan input with no producer and a nonexistent `data/kb/` (§6).
8. **Contract-test coverage is asymmetric:** foundation dataclasses (22 types) and ~18 of 20 CLI command groups have no shape-asserting tests; the strongest genuine seams are `corp retrieve --format json` (producer only — the rfp consumer side is never integration-tested), ops.db DDL, and the ADR-27 actions AST scanner (§2).

---

## 1. Edges (witnessed)

Three kinds, kept separate. An edge is `source unit → target unit` where a unit is a package (`src/corp/<pkg>/`) or a root module (`src/corp/<name>.py`). Same-unit imports are excluded.

### 1a. Static import edges

Source of truth: `tach map` (tach 0.34.0, `exact=true`, `forbid_circular_dependencies=true`; `tach check` = `[OK] All modules validated!` on this tree), cross-confirmed by per-cluster grep (`^from corp\.|^import corp\.` + indented in-function forms). **90 unit-level edges witnessed** — 83 from `tach map` (all grep-confirmed) + 7 outbound edges of `test_pipeline` that tach cannot see (see blind-spot note below) — vs **8 in the ARCHITECTURE.md codemap** (see §4). Table rows below collapse multi-target lines (e.g. row 55 = 3 edges), so row count ≠ edge count.

| # | edge | witnessed at (representative file:line) |
|---|------|------------------------------------------|
| 1 | cleanup → schema | `src/corp/cleanup/disk.py:19`, `scanner.py:14` (`from corp.schema.folder_names import …`) |
| 2 | overnight → schema | `src/corp/overnight/cke_client.py:21`, `classifier.py:14-24`, `monitor.py:15`, `preflight.py:15` |
| 3 | overnight → config | `src/corp/overnight/monitor.py:22`, `state.py:67` (indented in-function `from corp.config import get_config`) |
| 4 | config → schema | `src/corp/config.py:17` (`folder_names`) |
| 5 | vault_io → models | `src/corp/vault_io.py:25-34` (8-name block) |
| 6 | vault_io → schema | `src/corp/vault_io.py:35` (`pipeline_config.PipelineConfig`), `:520-521` (in-function `validate_frontmatter`) |
| 7 | intent_router → models | `src/corp/intent_router.py:17` (`Workflow`) |
| 8 | intent_router → routing_types | `src/corp/intent_router.py:18` (re-export, noqa F401) |
| 9 | intent_router → llm_router | `src/corp/intent_router.py:147` (in-function `classify_intent`) |
| 10 | intent_router → project_resolver | `src/corp/intent_router.py:301`, `:355` |
| 11 | llm_router → models | `src/corp/llm_router.py:17` |
| 12 | llm_router → routing_types | `src/corp/llm_router.py:18` |
| 13 | llm_router → project_resolver | `src/corp/llm_router.py:131` |
| 14 | audit → schema | `src/corp/audit.py:20-25` (`folder_names` block) |
| 15 | integrity → schema | `src/corp/integrity.py:15-25` (`folder_names` block) |
| 16 | project_resolver → config | `src/corp/project_resolver.py:13` |
| 17 | project_resolver → models | `src/corp/project_resolver.py:14` |
| 18 | extractor → schema (**its only outbound target**) | `src/corp/extractor/post_process.py:15-24` (5 schema submodules), `extract.py:36`, `synthesize.py:40`, `batch_api.py:49`, `scripts/run.py:58` + 3 more |
| 19 | ingest → ops | `src/corp/ingest/router.py:18-19`, `inbox.py:34-35`, `inbox_ops.py:17`, `classifier.py:13`, `inbox.py:215,287` (`file_registry`) |
| 20 | ingest → schema | `src/corp/ingest/router.py:20`, `extractions.py:25`, `naming_config.py:6`, `llm_classifier.py:17`, `inbox.py:36,186` |
| 21 | ingest → vault_io | `src/corp/ingest/extractions.py:26` (`read_frontmatter, write_note`) |
| 22 | ingest → extraction | `src/corp/ingest/router.py:649,712,739,792` (in-function: `manifest_emitter`, `vault_writer.move_to_vault`) |
| 23 | ingest → overnight | `src/corp/ingest/router.py:653,743` (in-function: `cke_client.extract_sync, is_available`) |
| 24 | ingest → index_builder | `src/corp/ingest/inbox.py:550` (in-function `rebuild_index`) |
| 25 | actions → config | `src/corp/actions/_helpers.py:14` + 7 action modules |
| 26 | actions → models | `src/corp/actions/__init__.py:12` + 10 action modules (`StepResult`, `VaultZone`) |
| 27 | actions → schema | `src/corp/actions/inbox_actions.py:10` |
| 28 | actions → cleanup | `src/corp/actions/_helpers.py:13` (`OneDriveSafetyError`) |
| 29 | actions → query_engine | `src/corp/actions/analytics_actions.py:18`, `knowledge_actions.py:16` (in-function) |
| 30 | actions → vault_io | `src/corp/actions/brief_actions.py:22`, `monitoring_actions.py:24`, `vault_actions.py:81,109` (in-function) |
| 31 | actions → template_manager | `src/corp/actions/deck_actions.py:21,74` (in-function) |
| 32 | actions → index_builder | `src/corp/actions/index_actions.py:16` (in-function) |
| 33 | actions → task_manager | `src/corp/actions/task_actions.py:16,45` (in-function) |
| 34 | actions → project_resolver | `src/corp/actions/_helpers.py:48,84` (in-function) |
| 35 | sandbox → schema | `src/corp/sandbox.py:24` (`pipeline_config`) |
| 36 | sandbox → index_builder | `src/corp/sandbox.py:66` (in-function `_SCHEMA as INDEX_SCHEMA`) |
| 37 | sandbox → ops | `src/corp/sandbox.py:67` (in-function `OpsDB`) |
| 38 | sandbox → overnight | `src/corp/sandbox.py:68` (in-function `OvernightState`) |
| 39 | chat → intent_router | `src/corp/chat.py:15` |
| 40 | chat → workflow_engine | `src/corp/chat.py:16` |
| 41 | chat → project_resolver | `src/corp/chat.py:130` (in-function) |
| 42 | chat → task_manager | `src/corp/chat.py:205` (in-function) |
| 43 | chat → vault_io | `src/corp/chat.py:206` (in-function) |
| 44 | test_pipeline → schema | `src/corp/test_pipeline.py:38` (top-level `PipelineConfig`), `:255` (`naming_config`) |
| 45 | test_pipeline → sandbox | `src/corp/test_pipeline.py:114` (in-function) |
| 46 | test_pipeline → ingest | `src/corp/test_pipeline.py:292,384,385,502` (in-function: `extractions`, `router`) |
| 47 | test_pipeline → index_builder | `src/corp/test_pipeline.py:338` |
| 48 | test_pipeline → query_engine | `src/corp/test_pipeline.py:356` |
| 49 | test_pipeline → extraction | `src/corp/test_pipeline.py:383` (`manifest_emitter._resolve_doc_type`) |
| 50 | test_pipeline → overnight | `src/corp/test_pipeline.py:386,543` (`cke_client`) |
| 51 | \_\_main\_\_ → cli | `src/corp/__main__.py:1` (relative `from .cli import cli` — invisible to `^from corp` grep, resolved manually) |
| 52 | ops → schema | `src/corp/ops/registry.py:17` (`folder_names.CORP_INFRA`) |
| 53 | ops → config | `src/corp/ops/database.py:175`, `registry.py:24` (in-function `get_config`) |
| 54 | retrieve → schema | `src/corp/retrieve/engine.py:30` (`naming_config.get_client_variants`), `:130` (`products.expand_product_query`) — both in-function, try/except-wrapped |
| 55 | index_builder → config / models / schema | `src/corp/index_builder.py:20,21,22` (+ in-function `:363` `VaultZone`) |
| 56 | task_manager → config / models | `src/corp/task_manager.py:15,16` |
| 57 | task_manager → intent_router | `src/corp/task_manager.py:116` (in-function `_strip_diacritics` — a private-symbol reach) |
| 58 | template_manager → config / models / schema | `src/corp/template_manager.py:16,17,18` |
| 59 | workflow_engine → config / models | `src/corp/workflow_engine.py:17,18-24` |
| 60 | workflow_engine → built_in_actions | `src/corp/workflow_engine.py:286` (in-function `get_action`) |
| 61 | built_in_actions → actions | `src/corp/built_in_actions.py:7-21` (pure re-export shim, 8 import statements, all `noqa: F401`) |
| 62 | query_engine → index_builder / models | `src/corp/query_engine.py:19` (**private symbols `_connect, _ensure_schema`**), `:20` |
| 63 | cli → schema | `src/corp/cli/__init__.py:87` + 12 more files (`pipeline_config`, `folder_names`, `naming_config`) |
| 64 | cli → config | `src/corp/cli/analytics.py:11`, `cleanup.py:13`, `extract.py:9`, `ingest.py:9`, `overnight.py:13`, `retrieve.py:10`, `rfp.py:6`, `system.py:10`, `template.py:7` |
| 65 | cli → index_builder | `src/corp/cli/analytics.py:23,88,112,139,163,188,228`, `index.py:22,48`, `query.py:27`, `retrieve.py:49,179`, `rfp.py:38`, `ingest.py:608`, `system.py:64` |
| 66 | cli → query_engine | `src/corp/cli/analytics.py:24,89,113,140,164,189,229`, `query.py:34,53` |
| 67 | cli → ops | `src/corp/cli/analytics.py:280,338,353,388`, `ingest.py:37-38,239-240,321,387-388,559`, `system.py:66,180,230` |
| 68 | cli → ingest | `src/corp/cli/ingest.py:30,233,320,386,553`, `analytics.py:275`, `query.py:95` |
| 69 | cli → cleanup | `src/corp/cli/cleanup.py:27-29,73,125` |
| 70 | cli → audit | `src/corp/cli/cleanup.py:250,297` |
| 71 | cli → extraction | `src/corp/cli/extract.py:45-48,129`, `overnight.py:121,165-168` |
| 72 | cli → overnight | `src/corp/cli/extract.py:49,112`, `overnight.py:52,61,97-99,112,169,316-319,355,377` |
| 73 | cli → retrieve | `src/corp/cli/retrieve.py:50,180`, `rfp.py:39` (`corp.retrieve.rfp.answer_rfp` — a `retrieve` submodule, **NOT the top-level `corp.rfp` package**) |
| 74 | cli → freshness_scanner | `src/corp/cli/ingest.py:464`, `overnight.py:454` |
| 75 | cli → integrity | `src/corp/cli/system.py:65` |
| 76 | cli → project_resolver | `src/corp/cli/project.py:10`, `task.py:9`, `vault.py:9`, `workflow.py:10` |
| 77 | cli → vault_io | `src/corp/cli/project.py:12`, `vault.py:11` |
| 78 | cli → task_manager | `src/corp/cli/task.py:24,41,81,95` |
| 79 | cli → template_manager | `src/corp/cli/template.py:18,49,74` |
| 80 | cli → workflow_engine | `src/corp/cli/workflow.py:38` |
| 81 | cli → built_in_actions | `src/corp/cli/analytics.py:33` |
| 82 | cli → test_pipeline | `src/corp/cli/misc.py:60` |
| 83 | cli → chat | `src/corp/cli/misc.py:102` |

**cli negative witness (the codemap's four phantom edges):** `grep -rn "corp\.extractor|corp\.project\b|corp\.opportunity|corp\.rfp" src/corp/cli/*.py` → **zero matches** in any form (top-level or indented). All four packages exist on disk; none is imported by cli. `cke`/`cpe`/`com` are independent `[project.scripts]` entry points (`pyproject.toml:53-58`), siblings of `corp`, not imports.

**Edge-count reconciliation:** `tach map` yields 83 unit-level edges; grep confirms all of them and adds the 7 outbound units of `test_pipeline` (invisible to tach via the `test_*.py` exclude) — **90 witnessed static unit-edges total** vs the codemap's 8.

Also zero-outbound (static): **`rfp/`** — zero cross-package `corp.*` imports (all 5 grep hits are `corp.rfp.*` internal; indented-form grep: no matches at all). rfp's only outbound reach is the subprocess edge in §1b and the read-only index.db fallback in §1c. And **retrieve does NOT import corp.ops anywhere** (dedicated grep for `corp.ops` + every repo class name: exit 1) — contradicting ARCHITECTURE.md line 37.

Also zero-outbound: **`project/` and `opportunity/`** — zero cross-package `corp.*` imports of any form (witnessed NOT-FOUND; every hit is same-package). Both contradict the ARCHITECTURE.md codemap (`project → schema`, `opportunity → schema` at lines 39-40) and match `tach.toml:94-100` (no `depends_on`, `exact = true`).

> **Tach blind spot witnessed:** `tach map` reports `test_pipeline → (nothing)`, but `src/corp/test_pipeline.py:38` carries a **top-level** corp import plus 12 in-function outbound edges (rows 44-50). Cause: `tach.toml`'s `exclude` list contains `test_*.py`, which matches `src/corp/test_pipeline.py` — the module is silently exempt from all layer enforcement.

Also zero-outbound: `freshness_scanner.py` (grep NOT-FOUND — reads vault notes via raw stdlib, no corp.* import at all).

**Zero-outbound units witnessed (grep NOT-FOUND on `^from corp|^import corp` incl. indented forms):** `models.py` (303 lines), `routing_types.py` (20 lines) — pure dataclass/enum containers, no I/O call sites of any kind (subprocess, sqlite3, file-write greps all NOT-FOUND; the only pattern hits are field names/comments: `models.py:102,112` `vault_path` fields, `:243` MyWork comment). Also zero-outbound: `schema/` (all `corp.*` hits resolve same-package — `cli.py:29,34`, `pipeline_config.py:17,56`, `validate.py:14`) and `extraction/` (zero `corp.*` imports of any form — uses only bare relative imports; full import audit in agent evidence). Both confirmed foundation leaves.

### 1b. Subprocess/CLI edges

| source file:line | mechanism | exact command | functional target |
|---|---|---|---|
| `src/corp/overnight/cke_client.py:169-175` (invoked from `extract_batch` `:196-202`) | `subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")` | `<cke> process-manifest <manifest_path> --batch --batch-poll-interval=N --batch-timeout=N [--model M] [--resume]`; binary resolved 3-way in `_resolve_cke_cmd()` `:34-60` (CKE venv python + run.py → `shutil.which("cke")` → `sys.executable` + run.py) | **corp.extractor (CKE)** — deliberate process boundary; docstring `:1-6`: "no direct Python imports from corp.extractor" |
| `src/corp/overnight/cke_client.py:241-249` (`extract_sync`) | same `_run_cke` → `subprocess.run` | `<cke> process-manifest <manifest_path> --max-rpm=N [--model M] [--resume]` | corp.extractor (CKE), sync mode |
| `src/corp/overnight/cke_client.py:291-298` (`scan_local`) | same | `<cke> scan <path> -o <tmp.json> [--no-recursive] [--exclude …]` | corp.extractor (CKE) `scan`, Tier-1 local |
| **`src/corp/rfp/vault_adapter.py:138`** (argv built `:123-136`) | `subprocess.run(cmd, capture_output=True, text=True, timeout=30)` | `["corp", "retrieve", query, "--format", "json", "--rfp-only", "--top", str(limit)]` + `["--product", prod]` per product | **corp.cli.retrieve → corp.retrieve.engine** — THE edge ARCHITECTURE.md's codemap mis-draws as an import (`rfp/ → retrieve`, line 41) |
| `src/corp/project/cke_invoker.py:84-89` (argv `:70-79`, resolution `:26-47`) | `subprocess.run(cmd, cwd=str(cke), capture_output=False, text=True)` | `[*prefix, "process-manifest", str(manifest_path), "--max-rpm", str(max_rpm)] (+ "--resume")` | corp.extractor (CKE) — **a second, independent CKE subprocess wrapper duplicating `overnight/cke_client.py`** (see §5.8) |
| `src/corp/chat.py:230-236` (cmd string `:226`) | `subprocess.run(["corp"] + shlex.split(cmd_str), …, timeout=60)` | `corp <user-supplied subcommand>` (chat's `!cmd` escape) | corp.cli (self-invocation through own CLI) |
| `src/corp/ingest/light_scan.py:321` (argv `:311-319`) | `subprocess.run(cmd, …, timeout=3)` | `["ffprobe","-v","quiet","-print_format","json","-show_format", path]` | external binary (media probe) |
| `src/corp/extractor/` — 10 sites (`compress.py:94`, `frames/scene_detect.py:50`, `scan.py:239`, `slides/pdf_converter.py:71,87`, `slides/renderer.py:112`, `scripts/compress_video.py:42`, `scripts/preprocess_audio.py:36,113,174`) | `subprocess.run` | ffmpeg / ffprobe / LibreOffice `soffice --headless --convert-to pdf` / `sys.executable -c <PowerPoint COM script>` | external binaries only — **extractor invokes no corp CLI** (CLI-token grep: sole hit is `post_process.py:210` org-suffix set `"corp"`, not a command) |

| `src/corp/cli/system.py:42-49` (`doctor`) | `subprocess.run([check_cmd, "--help"], …, timeout=10)` | `<agent-cli> --help` — resolved at runtime from `config/agents.yaml` (`com`, `cpe`, `cke`, `corp-meta`, ai-council; `rfp:` has `cli: TBD` and is skipped `:34-36`) | liveness check only, not a data invocation; no hardcoded CLI-name literals anywhere in cli/ |
| `src/corp/workflow_engine.py:243` (`_execute_agent_step` `:235`; command built `_build_agent_command` `:314-331`) | `subprocess.run(cmd, …)` | dynamic — from workflow-YAML `step.command` or `agents.yaml` `agent_info["cli"]` | config-driven agent CLI (no static token; target depends on workflow definitions) |

Cleanup/, schema/, extraction/, ops/, retrieve/, opportunity/, actions/, models, routing_types, index_builder, task_manager, template_manager, built_in_actions, query_engine, sandbox, test_pipeline, \_\_main\_\_: subprocess greps **NOT-FOUND**.

### 1c. Data edges (ops.db / index.db / overnight_state.db / vault-FS / MyWork-FS)

| source file:line | store | R/W | evidence |
|---|---|---|---|
| `src/corp/overnight/state.py:81` | overnight_state.db | connect | `sqlite3.connect(str(self.db_path))`; path computed independently `:65-69` |
| `src/corp/overnight/state.py:19,34,49` | overnight_state.db | WRITE (DDL) | `CREATE TABLE IF NOT EXISTS runs/files/batches` |
| `src/corp/overnight/state.py:101,136,209` (INSERT), `:112,170,177,231,284` (UPDATE), `:119-122,184-195,243-275` (SELECT) | overnight_state.db | WRITE / READ | verbatim SQL in agent evidence |
| `src/corp/overnight/monitor.py:47-50,77-80` (status), `:60-61` (jsonl log), `:86-89,143` (report) | other-FS: `overnight_status.json` + logs under MyWork `.corp/` | WRITE | `self.status_path.write_text(json.dumps(status, indent=2))` |
| `src/corp/cleanup/disk.py:359` (`target.unlink()`), `:398-399` (`d.rmdir()`), `:337,386-387` (deletion log) | MyWork-FS | WRITE (delete + log) | guarded by `_guard_onedrive` `disk.py:28`, call site `:351` |
| `src/corp/cleanup/executor.py:217` (`source.unlink()`), `:235-236` (`shutil.move`) | MyWork-FS | WRITE (delete/move) | guarded by `_guard_onedrive` `executor.py:22`, call site `:211` |
| `src/corp/cleanup/proposer.py:62-63` / `executor.py:182-183` | other-FS: moves.yaml | WRITE / READ | `yaml.dump(...)` / `yaml.safe_load(f)` → `MoveEntry.from_dict` `:189` |
| `src/corp/extraction/manifest_emitter.py:156` | other-FS: extraction manifest JSON | WRITE | `with open(manifest_path, "w", encoding="utf-8")` |
| `src/corp/extraction/vault_writer.py:105,120,133` | vault-FS | WRITE (relocate) | `shutil.move(...)` — relocates staged packages; authors no note content (docstring `:1-5`; `_read_trust_level` `:20-45` READ) |
| `src/corp/vault_io.py:184` (`write_note`) → `:148` (`path.write_text` in `_write_with_retry` `:143-157`), `:403` (`copy_to_vault` `shutil.copy2`), `:218-220` (conflict-file side-write) | vault-FS | WRITE | the canonical vault content writer; reads `:171,179` |
| `src/corp/integrity.py:234,238,278` | ops.db | READ | **direct `sqlite3.connect(str(ops_db_path))`** — bypasses `corp.ops` facade |
| `src/corp/integrity.py:323,325` | index.db | READ | **direct `sqlite3.connect(str(index_db_path))`** — bypasses `index_builder` helpers |
| `src/corp/llm_router.py:101,111` | other-FS: usage.json (LLM daily-cap) | READ/WRITE | `path.write_text(json.dumps(data))` |
| `src/corp/audit.py:98` (scan), `:359-371` (vault coverage) | MyWork-FS + vault-FS | READ (module docstring `:1-7`: "READ ONLY — never moves, renames, deletes") | rglob scan |
| `src/corp/freshness_scanner.py:61,73` | vault-FS | READ | raw `open(filepath,"rb")` / `read_text` — **bypasses vault_io** |
| `src/corp/ops/database.py:207` (connect; path `:177`), DDL `:33,61,77,100,114,128,148,160` (8 tables: assets, packages, ingest_events, files, extractions, routing_feedback, content_signatures, registry_suggestions) | ops.db | WRITE (owner) | repo write sites: `asset_repo.py:49,60,104`, `event_repo.py:53,96`, `file_registry.py:77,92,149,168`, `package_repo.py:36,81`, `routing_repo.py:37,115`, `suggestion_repo.py:31,53` |
| `src/corp/ingest/` — `dedup.py:143-148` (INSERT content_signatures), `inbox_ops.py:94-137` (upsert_asset/update_asset_status/log_event), `inbox.py:333-337` (UPDATE ingest_events), `router.py:469-473,800-808`, `extractions.py:343-350` | ops.db | WRITE (via `corp.ops` facade + 2 raw `conn.execute` sites: `inbox.py:334`, `router.py:470`) | reads: `dedup.py:153-155`, `inbox.py:350-357,421-424` |
| `src/corp/ingest/extractions.py:298` | vault-FS | WRITE | `write_note(dest, note_fm, body, mode="upsert", force=force)` — **the ONLY `write_note` call site in the entire repo**; dest hardcoded to `01_Knowledge/` flat (`_resolve_dest` `:102-112`, Council Decision #7) — NOT `02_sources/` |
| `src/corp/ingest/extractions.py:196` (quarantine), `:327` (cover copy) | vault-FS | WRITE | `dest.write_text(...)` / `shutil.copy2(cover, cover_dest)` |
| `src/corp/ingest/router.py:715,795` | vault-FS | WRITE (relocate) | `move_to_vault(staging_dir, config.vault_path, vault_target)` |
| `src/corp/ingest/inbox.py:194,525` (undo paths), `:544` (staging cleanup) | vault-FS / other-FS | WRITE (delete) | `shutil.rmtree(...)` |
| `src/corp/ingest/` — `router.py:264,573,873`, `inbox_ops.py:66`, `inbox.py:475`, `llm_classifier.py:270` | MyWork-FS | WRITE (move) | `shutil.move(...)` (inbox routing) |
| `src/corp/ingest/router.py:701,780` | other-FS: CKE staging manifest (`app_data_path/staging/ingest/{pkg}/manifest.json`) | WRITE | `json.dump(manifest, fh, indent=2)` |
| `src/corp/retrieve/engine.py:156` (connect), `:221-223,253-255,533` (queries) | index.db | READ (pure reader — zero write SQL witnessed) | **direct `sqlite3.connect(str(db_path))`, not via corp.ops** — tables `notes`, `notes_fts` |
| `src/corp/retrieve/prep.py:170` | other-FS: briefing output | WRITE | `output_path.write_text(full_content)` |
| `src/corp/rfp/vault_adapter.py:183` (read-only URI connect), `:212` | index.db | READ | `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)` — FTS fallback when CLI path fails |
| `src/corp/rfp/vault_adapter.py:247` | vault-FS | READ | `p.read_text(...)` (note body via index.db note_path) |
| `src/corp/rfp/` — `anonymization/config.py:38`, `answer_selector.py:635`, `rfp_feedback.py:61,79`, `validate_profiles.py:275`, `rfp_answer_word.py:785`, `rfp_excel_agent.py:680` | other-FS: config/rfp YAML+JSON, data/kb, output docx/xlsx | WRITE | (no vault/DB writes anywhere in rfp — `write_note`/SQL-write/`shutil` greps NOT-FOUND) |
| `src/corp/extractor/` — 18+ write sites (`synthesize.py:274,423,460-462,493,548`, `batch.py:308`, `batch_api.py:103,620`, `manifest.py:96`, `scripts/run.py:172,188,256,652,864`, +copies) | other-FS: caller-supplied `output_dir` package tree | WRITE | **zero vault_path/MyWork/DB tokens in all 52 files** — "pure" holds at identifier level; purity is caller-discipline, no in-package guard |
| `src/corp/extractor/post_process.py:610-625` | other-FS: **repo-tracked `config/extractor/taxonomy_review.yaml`** | READ+WRITE | extraction side-effect mutates a git-tracked config file |
| `src/corp/extractor/providers/cost_tracker.py:31-32` | other-FS: `src/corp/extractor/data/cost_log.jsonl` | WRITE (append — invisible to `open(...,'w')` grep, found by read) | zero src/ callers (§6 D-5) |
| `src/corp/sandbox.py:71-86` | ops.db + index.db + overnight_state.db (sandbox copies) | WRITE (init) | delegates DDL to owners (`OpsDB`, `OvernightState`, `index_builder._SCHEMA` via `:66-68,83-84`) — **no DDL duplication witnessed**; fragile-by-reference on `_SCHEMA` symbol |
| `src/corp/sandbox.py:127`, `test_pipeline.py:163` | sandbox tree (all stores) | WRITE (delete) | `shutil.rmtree(tmp_root)` |
| `src/corp/test_pipeline.py:314,436,524` (MyWork staging), `:316,474,527` (vault via `ingest_extractions`), `:460,485` (fixture-store) | MyWork-FS / vault-FS (sandboxed) | WRITE | in-process pipeline driver |
| `src/corp/project/` — `renderer.py:76,303`, `models.py:77`, `manifest.py:166`, `extractors.py:71`, `manifest_generator.py:172-173` | other-FS: project `_knowledge/` under project folder | WRITE | guarded by `renderer.py:38-52` OneDrive check |
| **`src/corp/project/cli.py:284-289`** | **arbitrary user-supplied "vault" path** | WRITE | `--copy-to-vault` flag: `shutil.copy2(knowledge_dir/"index.md", vault_dir/"index.md")` — **no OneDrive/ADR-27 guard on destination; bypasses vault_io entirely** |
| `src/corp/opportunity/` — `folder_manager.py:104,111-112,127`, `chat.py:174`, `cli.py:200`, `excel_manager.py:63` | other-FS: opportunity project folders + Excel workbook | WRITE | package-local FS only, no vault/DB |
| `src/corp/actions/` — `analytics_actions.py:97-99`, `monitoring_actions.py:154-156` (DASHBOARDS), `archive_actions.py:63-74,96-111`, `vault_actions.py:37-63` (METADATA), `brief_actions.py:39-94` (BRIEFS) | vault-FS (ADR-27 whitelist zones) | WRITE (7 direct write-primitive sites) | note: `analytics_actions.py:97` uses literal `"00_dashboards"` vs `VaultZone.DASHBOARDS.value` (`"dashboards"`) — aliased drift, flagged by the invariant test itself (`test_vault_writer_invariant.py:73-78`) |
| `src/corp/index_builder.py:155` (connect; path `:147`), DDL `:26-141` (`_SCHEMA`: 7 objects — projects `:27`, facts `:45`, facts_fts `:57`, meta `:62`, notes `:74`, notes_fts `:109` + 4 triggers `:114-140`) | index.db | WRITE (sole DDL owner) | writes: DROP/rebuild `:176-186`, `:207,228,229,289,290`, facts INSERT `:525-527`, notes INSERT `:657`, dedup DELETE `:719-721`; reads vault + OneDrive facts.yaml `:483,489` |
| `src/corp/query_engine.py:52-73,117-234,269-286,344-447` | index.db | READ (zero writes witnessed) | tables facts_fts/facts/projects/notes_fts/notes; `search_facts` falls through to `notes_fts` `:91-97` when facts is empty |
| `src/corp/task_manager.py:172,330` | vault-FS (DASHBOARDS/tasks zone, path `:26`) | WRITE | task markdown files with YAML frontmatter |
| `src/corp/template_manager.py:271-274,358` | vault-FS (CORP_INFRA registry, path `:73`) | WRITE | registry yaml + `shutil.copy2` template copy |
| `src/corp/cli/` — reads: `analytics.py:283-395` (ops.db via OpsDB), `system.py:180-207` | ops.db | READ (+1 WRITE: `system.py:230-239` `mark_routing_reviewed`) | **no direct `sqlite3.connect` anywhere in cli** — all DB access via facade classes |
| `src/corp/cli/overnight.py:52-56` | overnight_state.db | WRITE | `state.conn.execute("DELETE FROM files WHERE status = 'pending'")` — raw SQL through the state object from the interface layer |
| `src/corp/cli/` — `overnight.py:502-505,609`, `cleanup.py:261-370`, `misc.py:87-92` | MyWork-FS / other-FS | WRITE | reports, scan JSONs, `shutil.move` |

---

## 2. Seam contracts & test coverage

| seam | contract (format + defining file:line) | asserting test or NONE |
|---|---|---|
| foundation types: vault models (`VaultZone` `models.py:13`, `Mutability` `:36`, `ZONE_MUTABILITY` `:45`, `VaultPath` `:61`, `ProjectInfo` `:71`, `ProjectSummary` `:92`, `ValidationIssue` `:117`, `ValidationReport` `:126`) → consumed by `vault_io.py:25-34`, actions/* (4 files), `project_resolver.py:14`, `index_builder.py:363`, `task_manager.py:16` | dataclass/enum, `src/corp/models.py` | NONE (no direct shape assertion; `tests/safety/test_vault_writer_invariant.py:43,326-343` imports `VaultZone` but asserts writer policy, not type shape) |
| foundation types: workflow family (`WorkflowStep` `models.py:143`, `WorkflowParam` `:156`, `Workflow` `:165`, `StepResult` `:178`, `WorkflowResult` `:190`) → `workflow_engine.py:18-24`, `llm_router.py:17`, `intent_router.py:17`, all 11 actions/* files | dataclass, `src/corp/models.py` | NONE (behavioral tests only — `tests/test_workflow_engine.py`, `tests/test_chat.py:112` construct them; none assert fields) |
| foundation types: task family (`TaskStatus` `models.py:202`, `TaskPriority` `:211`, `Task` `:220`) → `task_manager.py:16` | dataclass/enum | NONE |
| foundation types: index/query family (`IndexStats` `models.py:256`, `FactResult` `:267`, `ProjectResult` `:279`, `AnalyticsReport` `:291`, `TemplateInfo` `:237`) → `index_builder.py:21`, `query_engine.py:20`, `template_manager.py:17` | dataclass | NONE |
| `ResolvedProject` (`models.py:106`) → `project_resolver.py:14` | dataclass | NONE |
| `Intent` (`routing_types.py:13`) → `llm_router.py:18`, re-exported `intent_router.py:18` (backward-compat noqa) | enum | NONE |

**Foundation contract-test verdict (whole-tests-tree search):** the only `__dataclass_fields__`-style shape assertions in the entire `tests/` tree target `RetrievedNote`/`RetrievalResult` (`tests/integration/test_retrieve_contract.py`) — none of the 22 foundation types in `models.py`/`routing_types.py` has a direct contract test.

| seam | contract (format + defining file:line) | asserting test or NONE |
|---|---|---|
| `PipelineConfig` precedence (ENV > paths.toml > home defaults) | docstring `src/corp/schema/pipeline_config.py:3`; fields `:28-40`; `get_path()` impl `src/corp/schema/config.py:46-58` | `tests/schema/test_pipeline_config.py::TestProduction::test_env_var_overrides_vault_path` (:53) — real `PipelineConfig.production()` + monkeypatch, not mocked |
| note frontmatter schema (corp-meta) | `NoteFrontmatter` `src/corp/schema/models.py:81-178`, `SCHEMA_VERSION = 2` `:12` | `tests/schema/test_models.py::test_valid_note` (:10), `::test_frontmatter_with_v21_fields` (:55) |
| `folder_names` constants | `src/corp/schema/folder_names.py:11-36` | `tests/schema/test_folder_names.py::test_folder_name_values` (:22) |
| `parse_llm_json` | `src/corp/schema/utils.py:10` | `tests/schema/test_utils.py::test_parse_clean_json` (:8) + 6 siblings |
| extraction manifest shape (ingest → CKE crossing) | `build_manifest()` `src/corp/extraction/manifest_emitter.py:96-150`; top-level keys `:137-148`, file-entry keys `:124-134` | `tests/test_extraction/test_manifest_emitter.py::TestBuildManifest::test_structure` (:91), `::test_file_entry_fields` (:105) |
| `move_to_vault` trust-gated conflict behavior | `src/corp/extraction/vault_writer.py:57-145`; trust gate `_read_trust_level` `:20-45` | `tests/test_extraction/test_vault_writer.py::TestMoveToVault::test_verified_note_creates_conflict` (:152) — real files, real `shutil.move` |
| ADR-14 naming convention | **defined in `src/corp/ingest/renamer.py:3` (NOT in extraction/vault_writer — the codemap-adjacent assumption that vault_writer owns naming is unsupported; witnessed NOT-FOUND)** | (see ingest cluster row) |
| overnight_state.db schema | `_SCHEMA` `src/corp/overnight/state.py:19-62` (3 tables + 2 indexes); WAL+FK pragmas `:83-84` | `tests/test_overnight/test_state.py::test_foreign_keys_enabled` (:134), `::test_foreign_key_rejects_orphan_file` (:139), `::test_foreign_key_rejects_orphan_batch` (:149) — real on-disk sqlite |
| **cke_client ↔ CKE (the corp→CKE process boundary)** | CLI argv (`cke_client.py:196-202,241-244,291-295`) out; response = **regex parse of stdout literal lines** `_parse_summary()` `cke_client.py:109-159` (expects `"Done: N"`, `"Errors: N"`, `"Skipped: N"`, `"Total: N"`, `"Estimated API cost: $N"`, `"Tiers: local=…"`); `scan_local` crosses via JSON temp file (`-o`, read back `:308`) | **NONE** — `tests/test_test_pipeline.py:160` mocks `cke_client.is_available` (mocked-away); no test runs the real subprocess or asserts the literal-line stdout contract or scan JSON shape |
| cleanup moves.yaml / `MoveEntry` | `@dataclass MoveEntry` `src/corp/cleanup/executor.py:74-134`; traversal/absolute-path rejection `:92-121`; every raw entry wrapped `:189` (2026-04-21 hotfix intact) | `tests/test_cleanup/test_onedrive_safety_p1_2.py::test_move_entry_schema_rejects_parent_traversal` (:138), `::test_move_entry_schema_rejects_absolute_source` (:152) |
| status.json concurrent-read protocols (two distinct files — see §4.2 D7) | **CKE-side `status.json`**: `save_status`/`load_status` `src/corp/extractor/manifest.py:76-97` — retry wrapper EXISTS (the CLAUDE.md graduated rule's subject). **Overnight-side `overnight_status.json`**: flat dict `monitor.py:41-50,71-80` — only a single non-retrying try/except `monitor.py:66-70` (low risk: monitor reads its own file back) | CKE side: `tests/extractor/test_manifest.py::test_load_status_retries_on_json_decode_error` (:170), `::test_load_status_raises_after_all_retries_exhausted` (:194) — real file I/O. Overnight side: `tests/test_overnight/test_monitor.py::test_mark_complete` (:59) asserts final JSON only — race/except branch untested |
| `vault_io.write_note` (THE vault content-writer contract) | signature `src/corp/vault_io.py:184-190`; render `_render_note` `:132-137`; verified-note protection `:213-226` | `tests/test_vault_io.py::TestWriteNote::test_write_read_roundtrip`, `::test_verified_note_not_overwritten`, `::test_verified_note_creates_conflict_file` + 3 siblings — real fs, unmocked |
| `vault_io.is_writable_by_actions` (ADR-27 Decision 2 predicate) | `src/corp/vault_io.py:56-65`; whitelist `_ACTIONS_WRITE_WHITELIST = {DASHBOARDS, METADATA, BRIEFS}` `:51-53` | `tests/safety/test_vault_writer_invariant.py:44,320` — AST scanner walks `src/corp/actions/*`, asserts every direct write zone is whitelisted (genuine) |
| `corp.config.AppConfig` precedence | fields `src/corp/config.py:20-32`; actual impl `:74-97` = **ENV > hardcoded home defaults, no paths.toml step** (`rg "paths\.toml" src/corp/config.py` → 0) | **NONE** — no test exists for this module's precedence (whole-tests-tree paths.toml sweep: only `corp.schema.config`/`pipeline_config` are tested) |
| routing decision type `Intent` | `src/corp/routing_types.py:12-20` (broken out to kill the intent_router↔llm_router cycle, docstring `:1-5`); returned by `route()` `intent_router.py:124` and `classify_intent()` `llm_router.py:139` | keyword path: `tests/test_intent_router.py::TestRoute::test_keyword_route` + 2 siblings (:331-345, genuine, `use_llm=False`). **Live LLM-fallback seam (`intent_router.py:147`): NONE** — only exercised under `patch("google.genai.Client")` in `tests/test_llm_router.py:212+` (mocked-away) |
| audit.py report | `build_report()` `src/corp/audit.py:418-505` (8 top-level keys) | `tests/test_audit.py::TestBuildReport::test_report_structure` + fixtures (real tmp trees) |
| integrity.py report | `IntegrityReport` `src/corp/integrity.py:41-53`; `check_all()` `:56-74` | `tests/test_doctor/test_integrity.py::test_healthy_system` etc. (:191-423) — builds **real sqlite DBs**, genuine |
| freshness_scanner results | `FreshnessResult` `src/corp/freshness_scanner.py:28-41`, `FreshnessSummary` `:44-55`, `scan_vault_freshness()` `:252-291` | `tests/test_freshness/test_scanner.py::test_fresh_note` + 8 siblings (:91-317) — real note files |
| **`corp retrieve --format json` — producer side** (THE cross-process seam rfp consumes) | JSON dict `src/corp/cli/retrieve.py:74-101`: `{query, total_found, sufficient, coverage_gaps, notes[].{note_id,title,client,project_id,content,topics,products,domains,source_type,note_type,confidence,relevance_score,source_path,extracted_at,citation,overlay_data}}` | `tests/test_retrieve/test_json_output.py::TestJSONFormat::test_has_required_fields` (:116) + 5 siblings — genuine end-to-end: real sqlite fixture + `CliRunner().invoke(cli, ["retrieve", …, "--format", "json"])`, asserts every key |
| `corp retrieve` JSON — **consumer side** (`rfp.vault_adapter` parse `:151-157`: expects `notes[]`, per-note `confidence, relevance_score, content, note_id`) | `src/corp/rfp/vault_adapter.py:117-157` | **NONE** — every test in `tests/rfp/test_vault_adapter.py` patches `subprocess.run` (e.g. `:58`); the real cross-process boundary is never exercised. Producer and consumer are each tested against their own copy of the shape; nothing pins them together |
| rfp product-profile YAML (`config/rfp/product_profiles/_effective/*.yaml`) | `validate_profile()` `src/corp/rfp/validate_profiles.py:72`; `BOOL_TO_SERVICE_KEY`/`FIELD_FORBIDDEN_PATTERNS` `:44-64`; readers `rfp_feedback.py:142-149`, `validate_profiles.py:355-376` | `tests/rfp/test_validate_profiles.py::test_validate_all_scans_directory` (:463) — real YAML on tmp_path, genuine |
| rfp KB canonical JSON (`data/kb/canonical/RFP_Database_UNIFIED_CANONICAL.json`) | list of `{kb_id, domain, …}` — path `src/corp/rfp/llm_router.py:54`, `rfp_answer_word.py:69`; read `:211-213`/`:332-333` | **NONE** — `tests/rfp/test_router_acceptance.py:293` injects `router.kb_lookup` directly; **no producer of this file exists in-repo and `data/kb/` is absent on disk** (see §6 D-7) |
| rfp anonymization config (`config/rfp/anonymization.yaml`) | `DEFAULT_CONFIG` `src/corp/rfp/anonymization/config.py:14-23`, load/save `:26-41` | **NONE** — `tests/rfp/test_anonymization.py:1-4` states all tests patch get_blocklist/get_session |
| ops.db row schemas (the ingest↔ops↔cli seam) | 8 tables DDL `src/corp/ops/database.py:33-160` | `tests/test_ops/test_database.py::TestSchema::test_create_database` (:28) — real sqlite, asserts `sqlite_master` table names |
| retrieve in-process result shape | `RetrievalFilter` `src/corp/retrieve/engine.py:38`, `RetrievedNote` `:53`, `RetrievalResult` `:93` | `tests/test_retrieve/test_engine.py::TestFallbackSearch::test_fallback_on_fts_error` (:432) — real FTS5 fixture; also `tests/integration/test_retrieve_contract.py` (`__dataclass_fields__` assertions — the only direct shape-pinning test in the repo) |
| index.db schema as consumed by retrieve tests | `notes`/`notes_fts` DDL `src/corp/index_builder.py:74,109` | **duplicated by hand** — `tests/test_retrieve/test_engine.py:25-74` and `test_json_output.py:14-52` each carry their own `_TEST_SCHEMA` replica instead of importing `index_builder._SCHEMA`; the copies can drift from the real DDL undetected |
| index.db schema (owner side) | `_SCHEMA` `src/corp/index_builder.py:26-141` | `tests/test_index_builder.py::TestSchema::test_creates_tables` (:92-104) — real sqlite, asserts table names (carries regression comment "notes table missing — code was deleted") |
| query_engine result shape | `FactResult` `src/corp/models.py:266-276`; `search_facts()` `src/corp/query_engine.py:25-100` | `tests/test_query_engine.py::TestSearchFacts::test_returns_client_name` (:160-163), `::test_returns_source_title` (:165-168) — real fixture |
| task persistence format (task_manager) | markdown + YAML frontmatter, write `src/corp/task_manager.py:169-172`, rewrite `:328-330` | `tests/test_task_manager.py::TestAddTask::test_frontmatter_fields` (:123-135) — real file, asserts literal frontmatter lines |
| workflow_engine ↔ built_in_actions action registry | `_ACTIONS` registry `src/corp/actions/__init__.py:18`, `@register_action` `:21-25`, `get_action` `:31-33`; consumed `workflow_engine.py:286` | half-covered: `tests/test_built_in_actions.py::TestActionRegistry::test_registered_actions` (:28-38, genuine) + `tests/test_workflow_engine.py::TestPythonStep::test_unknown_action` (:337-347, genuine miss-path). **The positive dispatch path is only tested mocked** (`::test_action_dispatched` `:357-374` patches `get_action`) — no unmocked end-to-end dispatch test exists |
| `corp` CLI command surface (~20 command groups: prep, rfp answer, overnight, doctor, trust-status, routing-*, project, vault, index, query, folder-review, analytics ×7, dedup-report, files-stats, naming-stats, task, template, run, cleanup ×4, ingest ×6, chat, test-pipeline) | click registrations across `src/corp/cli/*.py` (root group `__init__.py:90`, entry `pyproject.toml:54`) | **NONE for all but two** — only `corp retrieve --format json` (test_json_output.py, above) and `corp extract` (`tests/test_extraction_non_project/test_extract_command.py::test_extract_dry_run_no_cke_call` + 2 siblings, genuine CliRunner) have command-surface tests |
| ingest → cke_client (`extract_sync` request/response) | argv `cke_client.py:241-249`; response dict `{total, done, error, skipped, cost, tiers}` from `_parse_summary` `:109-159` | **NONE** — `tests/test_ingest/test_inbox.py:418-420,465-467` patches `corp.ingest.router._run_extraction` itself (mocked-away); nothing drives the router→cke_client path against even a fake CKE |
| ingest → ops rows (`upsert_asset`/`update_asset_status`/`log_event`) | `OpsDB.update_asset_status` signature `src/corp/ops/database.py:284-297` ("Every state change goes through here") | `tests/test_ingest/test_router.py::TestIngestFile::test_records_in_ops_db` (:370-384) — real OpsDB on tmp_path, genuine |
| ADR-14 naming (ingest → vault filenames) | pattern `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` — ADR text `docs/decisions/ADR-14-naming-convention-v2.md:12`; impl `src/corp/ingest/renamer.py:289` | `tests/test_ingest/test_renamer.py::TestProposeName::test_full_rename_series` (:271-283) — genuine |
| ingest-extractions staging hierarchy (`scope/client/package/`) | `_collect_packages` `src/corp/ingest/extractions.py:115-149`; dest flattening `_resolve_dest` `:102-112` | `tests/test_ingest_extractions.py::TestCollectPackages::test_projects_have_client` (:127), `::test_knowledge_scopes_have_no_client` (:137) — real fixture dirs, genuine |
| project manifest / CKE-facing manifest | `Manifest` dataclass `src/corp/project/models.py:53-73`; CKE manifest `manifest_generator.py:155-162` (`schema_version: 1`) | `tests/project/test_manifest_generator.py::TestGenerateCkeManifest::test_basic_generation` — genuine end-to-end against tmp files |
| project cke_invoker crossing | argv contract `src/corp/project/cke_invoker.py:70-89` | **NONE** — `grep "invoke_cke_batch\|cke_invoker\|process-manifest" tests/` → 0 hits |
| opportunity folder naming (`{client}_{product}`) | `folder_name()` `src/corp/opportunity/templates.py:8-10` — verbatim case, no `.lower()`; consumer-side normalization only in `actions/_helpers.py:41-43` (`folder_name.lower()`) — **asymmetric fix for the known case-mismatch gotcha** | `tests/opportunity/test_templates.py:8-9` locks in the verbatim-case behavior; no test asserts lowercase normalization on the opportunity side |
| actions/* wrapper functions (the seam cli/workflows actually call) | 11 action modules under `src/corp/actions/` | **NONE** — only `archive_actions`/`_helpers` are imported by any test (`tests/test_actions/test_archive_onedrive_safety.py:16-17`, `tests/test_cleanup/test_onedrive_safety_symlink.py:23`); the other 9 wrappers have no direct tests |
| sandbox environment contract (fabricates all 3 DBs + 7 dirs) | dirs `src/corp/sandbox.py:48-58`; DB init by delegation `:60-87` (no DDL duplication — verified against owners `ops/database.py:33-180`, `overnight/state.py:19-72`, `index_builder.py:26-74`) | `tests/test_test_pipeline.py::test_pipeline_creates_sandbox`, `::test_report_format_pass` (drives real `_test_sandbox_init` `test_pipeline.py:226-244`); no direct SandboxManager unit test beyond `tests/conftest.py:112-132` fixtures |
| chat → intent_router/workflow_engine seam | `Intent` + `WorkflowResult`/`StepResult` cross at `chat.py:15-16,74,112-180` | **NONE (genuine)** — `tests/test_chat.py::TestChatLoop::test_workflow_execution` (:105-139) patches BOTH `corp.chat.route` and `corp.chat.execute_workflow` — asserts chat's wiring, never the real contract |
| test_pipeline end-to-end contract | `run_pipeline_test() -> PipelineTestReport` `src/corp/test_pipeline.py:16-24`; 5 steps `:226,247,277,330,348` | `tests/test_test_pipeline.py::test_no_production_impact` (real fs check that prod vault is untouched), `::test_report_format_pass` (asserts 5 steps + all_passed) — strongest genuine e2e suite among the interface modules |

---

## 3. README freshness

All 13 packages carry a `README.md`; the 20 root modules carry none (N/A — verified by glob).

| package | README last commit | code last commit | days README behind |
|---|---|---|---|
| schema/ | `5ea65b3` 2026-04-15 | `7a89d45` 2026-05-28 | **43** |
| extraction/ | `5ea65b3` 2026-04-15 | `eb66044` 2026-03-30 | −16 (README newer than code) |
| cleanup/ | `698d5f6` 2026-03-30 | `811faa8` 2026-04-21 | **22** |
| overnight/ | `698d5f6` 2026-03-30 | `0ebcb65` 2026-03-30 | 0 |
| extractor/ | `698d5f6` 2026-03-30 | `7d9cfb2` 2026-07-16 | **108** |
| ingest/ | `698d5f6` 2026-03-30 10:18 | `3c8bd52` 2026-03-30 12:36 | ~0 — but **content-stale**: `README.md:26` claims "Depends on: … corp.extractor", contradicted by the witnessed import graph (no such import exists) |
| cli/ | `5ea65b3` 2026-04-15 | `eb66044` 2026-03-30 | −16 — but **content-stale**: `README.md:33` claims "Depends on: all corp.* modules"; witnessed: cli imports 0 of extractor/project/opportunity/rfp. The 2026-04-15 touch was a one-line repo-wide relabel (`git show 5ea65b3`) |
| ops/ | `698d5f6` 2026-03-30 | `ba7eb48` 2026-03-30 | 0 |
| retrieve/ | `698d5f6` 2026-03-30 | `b6e6a0c` 2026-03-30 | 0 |
| rfp/ | `698d5f6` 2026-03-30 | `eeb907a` 2026-03-30 | 0 (README newer by ~7h) |
| project/ | `5ea65b3` 2026-04-15 | `d09ab29` 2026-04-21 | 6 |
| opportunity/ | `5ea65b3` 2026-04-15 | `bd5d317` 2026-03-30 | −17 (README newer) |
| actions/ | `96b4773` 2026-03-30 | `4b9812d` 2026-04-21 | **22** |

Caveat (applies to every ~0/negative row): "days behind" measures the last-commit timestamp pair only, not semantic currency — the two content-stale READMEs above both have *fresh-looking* timestamps.

---

## 4. ARCHITECTURE.md drift list

Diff of the witnessed edge map (§1) against the hand-authored codemap (`ARCHITECTURE.md` lines 34–41, `CODEMAP:START/END`) and adjacent claims. Verdict per codemap line, then broader claim drift.

### 4.1 Codemap edge verdicts (all 8 lines)

| codemap line | claim | verdict | witnessed evidence |
|---|---|---|---|
| :34 | `cli → ingest, retrieve, extractor, project, opportunity, rfp` | **4 of 6 targets PHANTOM** | cli→ingest ✓, cli→retrieve ✓ (§1a rows 68, 73). cli→extractor/project/opportunity/rfp: zero imports in any form (negative-witness grep, §1a); `corp rfp answer` delegates to `corp.retrieve.rfp` (`cli/rfp.py:39`), not the `corp.rfp` package. Also **grossly incomplete**: cli's witnessed outbound set is 21 units (§1a rows 63–83) |
| :35 | `ingest → extractor, ops, schema` | **extractor PHANTOM** | ingest→ops ✓, →schema ✓, but no `corp.extractor` import exists anywhere in ingest (negative grep; the only mention is the stale `README.md:26`). Real CKE reach: ingest→overnight (`router.py:653,743`) → subprocess `cke process-manifest` (`cke_client.py:241-249`). Missing edges: ingest→{vault_io, extraction, overnight, index_builder} (§1a rows 21–24) |
| :36 | `extractor → extraction, schema` | **extraction PHANTOM** | extractor→schema ✓ (its ONLY outbound target, §1a row 18); no `corp.extraction` import in any of extractor's 52 files |
| :37 | `retrieve → ops, schema` | **ops PHANTOM** | retrieve→schema ✓ (in-function). retrieve→ops: dedicated grep for `corp.ops` + all 5 repo class names → exit 1. Reality: direct `sqlite3.connect` on index.db (`engine.py:156`). ARCHITECTURE.md **contradicts itself** — line 380 correctly says "query_engine / retrieve/ reads from index.db" |
| :38 | `ops → schema` | ✓ correct | `ops/registry.py:17` (+ unmapped ops→config, `database.py:175`) |
| :39 | `project → schema` | **PHANTOM** | project/ imports nothing outside itself (witnessed NOT-FOUND; `tach.toml:94-97` declares no depends_on with `exact=true`) |
| :40 | `opportunity → schema` | **PHANTOM** | opportunity/ imports nothing outside itself (same witness) |
| :41 | `rfp → retrieve` | **WRONG KIND** — drawn as a Tach-enforced import edge ("each edge = a higher layer importing a lower one") | it is a **subprocess CLI edge**: `rfp/vault_adapter.py:138` runs `["corp","retrieve",…,"--format","json"]`; rfp has zero static cross-package imports. Arrow also functionally lands on `corp.cli.retrieve` first, then `corp.retrieve.engine` |

**Net: of 8 hand-drawn edges, 3 are correct-as-drawn (`ingest→ops`, `ingest→schema` (one line), `ops→schema`), 1 is the wrong kind, and 7 named targets are phantom — while 90 witnessed static unit-edges (§1a) plus 5 functional subprocess edge-families (§1b) go undrawn.** The codemap also omits all 20 root modules, which carry the densest real coupling (cli↔18 root/package units, actions↔10).

### 4.2 Non-codemap claim drift

| # | claim (source) | witnessed reality | evidence |
|---|---|---|---|
| D1 | "corp (ingest/) is SOLE writer for `02_sources/` .md notes" (CLAUDE.md §5 rule 4, ARCHITECTURE.md Key Invariant #1, ADR-27) | ingest's `write_note` call (the only one in the repo) writes to **`01_Knowledge/` flat** (`extractions.py:102-112`, Council Decision #7) — not `02_sources/`. `02_sources/` is populated by `actions/vault_actions.py:131-135` via `vault_io.copy_to_vault` (a different vault_io function, actions-side) | §1c ingest rows; `grep "02_sources" src/corp` |
| D2 | CKE purity: "Never writes to vault or databases" (extractor README:5-8, Key Invariant #2) | holds at identifier level (zero vault_path/MyWork/DB tokens in 52 files) — but purity is **caller discipline, not a guard**: extractor writes 18+ FS sites to caller-supplied `output_dir`, mutates repo-tracked `config/extractor/taxonomy_review.yaml` (`post_process.py:610-625`) as an extraction side-effect, and appends `cost_log.jsonl` under its own package tree. No safety test covers extractor (the AST scanner is hardcoded to `src/corp/actions/`, `test_vault_writer_invariant.py:46`) | §1c extractor rows |
| D3 | "Config: centralized in config/paths.toml; ENV > config > default" (CLAUDE.md §4) | true only for `corp.schema.config`/`pipeline_config`; **`corp.config.get_config` (31 importing files — the majority consumer) never reads paths.toml** (`config.py:74-97`, `rg "paths\.toml" src/corp/config.py` → 0) | §2 AppConfig row; confirms 2026-07-06 audit finding, unfixed |
| D4 | tach/codemap coverage implies layer enforcement over `src/corp/` | `src/corp/test_pipeline.py` is **silently exempt** — `tach.toml` `exclude` contains `test_*.py`, which matches it; module has a top-level corp import + 12 in-function edges invisible to `tach map`/`tach check` | §1a tach-blind-spot note |
| D5 | ADR-27 Decision 1: guards centralized into `src/corp/safety/onedrive.py` | **`src/corp/safety/` does not exist**; 4 scattered guards remain, `actions/_helpers.py:111-112` docstring still promises "future centralization (ADR-27)" | §5.5 |
| D6 | ADR-27 Decision 2 whitelist enforced for all vault writes | enforcement (AST scan) covers `src/corp/actions/` only; **`project/cli.py:284-289` `--copy-to-vault` writes an arbitrary user-supplied path with no guard, outside vault_io and outside any scanner scope** | §1c project rows |
| D7 | `overnight_status.json` concurrent-read retry (CLAUDE.md graduated rule: "status.json concurrent reads must use try/except with 2-3 retries") | the CKE-side `status.json` retry **exists and is tested** (`extractor/manifest.py:76-97`; `tests/extractor/test_manifest.py::test_load_status_retries_on_json_decode_error` :170, `::test_load_status_raises_after_all_retries_exhausted` :194). The **overnight-side** `overnight_status.json` has only a single non-retrying try/except (`overnight/monitor.py:66-70`) — low risk today (monitor reads its own file) but the graduated rule's verify-grep would pass on the wrong file |
| D8 | cli README:33 "Depends on: all corp.* modules"; ingest README:26 "Depends on: … corp.extractor" | both contradicted by witnessed import graph | §3 content-stale rows |
| D9 | ARCHITECTURE.md Module Map / data-flow step 6 ("CKE extraction (tier_router)") implies corp drives extractor in-process | witnessed: 2 independent subprocess wrappers (`overnight/cke_client.py`, `project/cke_invoker.py`) invoke the `cke` CLI; no in-process call path from corp to extractor exists | §1b |

---

## 5. Fragmentation inventory

Re-verified fresh 2026-07-16 (not re-derived): every instance witnessed by grep this session. Families seeded from the 2026-07-06 code-quality audit §3.a, **plus one pattern-level discovery sweep per family** (`class .*Config|load_config`, `rg -in onedrive`, `gemini-|claude-|gpt-`, `price|cost_per|token_cost`, `yaml\.(safe_)?load` + `---` splits, `json\.loads`, `PRODUCT_|TAXONOMY|resolve_product|_ALIASES`). Instances the 2026-07-06 audit did not list are flagged **[NEW-vs-2026-07-06]** (present in today's discovery sweep; whether they existed on 2026-07-06 or appeared since is not distinguished here).

### 5.1 Config systems (family verdict 2026-07-06: SYSTEMIC — confirmed, now 7+ instances)

| instance | file:line | callers (witnessed 2026-07-16) |
|---|---|---|
| `AppConfig` / `get_config()` | `src/corp/config.py:21`, `:57` | 31 files import `corp.config` (up from 26 on 2026-07-06) |
| `PipelineConfig` (the "designed" one: ENV > paths.toml > defaults) | `src/corp/schema/pipeline_config.py:21` | 22 files reference `pipeline_config`/`PipelineConfig` |
| `schema.config` `load_config()`/`get_path()`/`vault_path()` | `src/corp/schema/config.py:24` | only `src/corp/schema/pipeline_config.py:56` (+ own docstring `:6`) |
| extractor raw-dict YAML loader | `src/corp/extractor/config_loader.py:70` (`_load_config`), `:98` (`load_config`) | 5 files reference `config_loader` |
| opportunity package-local | `src/corp/opportunity/config.py:20` (`AppConfig` — name-collides with root `corp.config.AppConfig`), `:34` (`load_config`); + `OpportunityConfig` `src/corp/opportunity/models.py:11` **[NEW-vs-2026-07-06]** | 8 files across opportunity+project use package-local config |
| project package-local | `src/corp/project/config.py:57` (`ExtractionConfig`) | (same 8-file pool as above) |
| rfp anonymization local loader **[NEW-vs-2026-07-06]** | `src/corp/rfp/anonymization/config.py:26` (`load_config`) | rfp/anonymization internal |

### 5.2 Vocabulary homes (verdict 2026-07-06: SYSTEMIC, "no owner" — confirmed, now 8+ homes)

| instance | file:line | usage witnessed |
|---|---|---|
| `resolve_product_key` (canonical product vocab) | `src/corp/schema/products.py:72` (exported `schema/__init__.py:32,61`) | **zero src/ callers** (only def + export); 42 tests in `tests/schema/test_products.py` — see §6 |
| `PRODUCT_ALIASES` **[NEW-vs-2026-07-06]** | `src/corp/intent_router.py:25` | in-file `:338`, `:346` |
| `_BUILTIN_PRODUCT_ALIASES` + `extractor/data/product_aliases.yaml` | `src/corp/extractor/post_process.py:140` (fallback wiring `:157`) | in-file |
| `_TAG_ALIASES` | `src/corp/extractor/post_process.py:498` | in-file `:569` |
| `TAXONOMY_MAP` **[NEW-vs-2026-07-06]** | `src/corp/extractor/post_process.py:585` | in-file `:593` |
| taxonomy.yaml loader/cache (schema-side vocab home) | `src/corp/schema/normalize.py:16-17`, `:37-44` | schema validate/normalize path |
| `DEPRECATED_TERMS`/`BY_TERMS`/`MODERN_TERMS` | `src/corp/rfp/answer_selector.py:62`, `:72`, `:102` | in-file `:143`, `:223`, `:236` |
| `BOOL_TO_SERVICE_KEY` + `FIELD_FORBIDDEN_PATTERNS` | `src/corp/rfp/validate_profiles.py:44`, `:56` | in-file `:88`, `:106`, `:223`, `:227-228` |

### 5.3 Model registries (verdict 2026-07-06: SYSTEMIC, 5 registries — confirmed, plus ~19 scattered model-string literals)

Registries proper:

| instance | file:line |
|---|---|
| `MODELS` | `src/corp/rfp/llm_router.py:63` (entries `:65-70`) |
| `TIER_MODELS` | `src/corp/extractor/tier_router.py:54-55` |
| provider router constants (`ANTHROPIC_MODELS`/`GEMINI_MODELS`/`DEFAULT_*`/`ESCALATION_MODEL`) | `src/corp/extractor/providers/router.py:21-28` + inline `MODEL_MAP` `:86` |
| `MODEL_MAP` duplicated **twice in the same file** | `src/corp/extractor/scripts/run.py:338` and `:725` (byte-identical dicts) |
| hardcoded enrichment model | `src/corp/extractor/extract.py:778` (`claude-haiku-4-5-20251001`) |

Scattered default-model literals (discovery sweep; each a shadow registry entry): `src/corp/audit.py:273,330` · `src/corp/cleanup/classifier.py:98,150` · `src/corp/cli/ingest.py:368` · `src/corp/cli/cleanup.py:243` · `src/corp/cli/rfp.py:18` · `src/corp/cli/retrieve.py:158` · `src/corp/llm_router.py:169` · `src/corp/opportunity/llm_client.py:101` **[NEW-vs-2026-07-06]** · `src/corp/ingest/llm_classifier.py:133,187` **[NEW]** · `src/corp/extractor/config_loader.py:41` · `src/corp/extractor/frames/tagger.py:47` **[NEW]** · `src/corp/extractor/reextract.py:58` · `src/corp/extractor/synthesize.py:212,308` · `src/corp/extractor/transcript.py:84` · `src/corp/extractor/extract.py:132,483` · `src/corp/retrieve/prep.py:113` · `src/corp/retrieve/rfp.py:91`.

### 5.4 Pricing tables (2026-07-06: 3 — witnessed today: 5 (+1 estimate constant))

| instance | file:line | note |
|---|---|---|
| blended $/1M dict | `src/corp/extractor/extract.py:141-144` | known |
| inline cost math (0.5/3.0 per 1M) | `src/corp/retrieve/prep.py:261-263` | known |
| `GEMINI_PRICING` **[NEW-vs-2026-07-06]** | `src/corp/extractor/providers/gemini_provider.py:15-18` (fallback `:69`) | disagrees with `extract.py:143` on `gemini-3-flash-preview` (0.50 input vs 1.00 blended) |
| `ANTHROPIC_PRICING` **[NEW-vs-2026-07-06]** | `src/corp/extractor/providers/anthropic_provider.py:15-17` (fallback `:49`) | |
| `cost_tracker` (`COST_LOG`) | `src/corp/extractor/providers/cost_tracker.py:11` | zero src/ callers — see §6 |
| `cost_per_call = 0.001` estimate **[NEW-vs-2026-07-06]** | `src/corp/ingest/llm_classifier.py:209` | budget-gate constant |

### 5.5 OneDrive guards (2026-07-06: 4 scattered — confirmed, still 4; ADR-27 centralization NOT implemented)

| instance | file:line | note |
|---|---|---|
| `_guard_onedrive` | `src/corp/cleanup/disk.py:28` (blocked-literal `:24`, call site `:351`) | |
| `_guard_onedrive` | `src/corp/cleanup/executor.py:22` (literal `:19`, call site `:211`) | |
| `_guard_writable` (+ `_ONEDRIVE_BLOCKED`) | `src/corp/actions/_helpers.py:103-129` (literal `:18`; docstring `:111-112` says "Mirrors cleanup/executor._guard_onedrive and cleanup/disk._guard_onedrive so future centralization (ADR-27)") | |
| inline synced-path check | `src/corp/project/renderer.py:47-49` | |
| shared error type | `src/corp/cleanup/errors.py:11` (`OneDriveSafetyError`) | the only centralized piece |

**Witnessed: `src/corp/safety/` does not exist** (glob `src/corp/safety/**` → no files). ADR-27 Decision 1 (centralize into `src/corp/safety/onedrive.py`) is unexecuted in the current tree; discovery sweep (`rg -in onedrive src/corp`) found no additional guard sites beyond the four above.

### 5.6 Frontmatter parsers (2026-07-06: 5 — discovery sweep witnesses **9** distinct parse implementations)

| instance | file:line | kind |
|---|---|---|
| canonical: `vault_io._parse_frontmatter` | `src/corp/vault_io.py:110` (+ `read_frontmatter` `:175`, `FRONTMATTER_SEP` `:39`, renderer `:132`) | index/split + yaml |
| `schema/cli.py` `extract_yaml_frontmatter` | `src/corp/schema/cli.py:39-49` | regex-based |
| `extraction/vault_writer._read_trust_level` | `src/corp/extraction/vault_writer.py:21-43` | split + yaml |
| `cli/system.py` inline | `src/corp/cli/system.py:135-140` | split + yaml |
| `task_manager._parse_task_file` + `_update_task_status` | `src/corp/task_manager.py:279-285`, `:314-330` | split + yaml, parse **and re-emit** |
| `freshness_scanner.parse_frontmatter` **[NEW-vs-2026-07-06]** | `src/corp/freshness_scanner.py:67-86` | split + yaml |
| `index_builder._parse_frontmatter` **[NEW-vs-2026-07-06]** | `src/corp/index_builder.py:550-563` | split + yaml |
| `ingest/extractions.py` inline **[NEW-vs-2026-07-06]** | `src/corp/ingest/extractions.py:269-274` | split + yaml (also imports the canonical `read_frontmatter` at `:26` — both in one file) |
| `ingest/inbox_ops.py` inline **[NEW-vs-2026-07-06]** | `src/corp/ingest/inbox_ops.py:231-234` | split + yaml |

### 5.7 LLM-JSON parsers (2026-07-06: 3–4 — discovery sweep witnesses **8** implementations)

| instance | file:line | kind |
|---|---|---|
| canonical: `parse_llm_json` | `src/corp/schema/utils.py:10-52` (exported `schema/__init__.py:34,60`) | fence-strip + repair |
| `audit.py` hand-rolled repair machine | `src/corp/audit.py:157-235` (loads `:170`, `:174`) | known |
| `cleanup/classifier.py` | `src/corp/cleanup/classifier.py:84-92` | known |
| `rfp/answer_selector._parse_llm_json_obj` | `src/corp/rfp/answer_selector.py:373-402` | known (reimplements canonical) |
| `ingest/llm_classifier._parse_llm_json` **[NEW-vs-2026-07-06]** | `src/corp/ingest/llm_classifier.py:83-107` | fence + brace regex |
| `llm_router.py` inline **[NEW-vs-2026-07-06]** | `src/corp/llm_router.py:226-266` | fence-strip + match |
| `extractor/providers/validator.py` inline **[NEW-vs-2026-07-06]** | `src/corp/extractor/providers/validator.py:60-66` | fence-strip |
| `extractor/frames/tagger.py` brace-slice **[NEW-vs-2026-07-06]** | `src/corp/extractor/frames/tagger.py:104` | brace slice |

Canonical `parse_llm_json` IS used in extractor (`extract.py:36,270`, `synthesize.py:40,225`, `batch_api.py:49,448`) — the fragmentation is that 7 other implementations coexist with it.

### 5.8 CKE subprocess wrappers (discovery find — 2 independent implementations) **[NEW-vs-2026-07-06]**

| instance | file:line | notes |
|---|---|---|
| `overnight/cke_client.py` | `_resolve_cke_cmd` `:34-60`, `_run_cke` `:169-175`, `extract_batch`/`extract_sync`/`scan_local` `:196-298` | 3-way binary resolution; stdout regex-parsed by `_parse_summary` `:109-159`; used by ingest + cli |
| `project/cke_invoker.py` | resolution `:26-47`, invoke `:84-89` | independent reimplementation of the same 3-way resolution + `process-manifest` argv; `capture_output=False` (no summary parse); zero tests (§2) |

Both build the same `process-manifest` command against the same CKE CLI with separately-maintained resolution logic — same-family drift risk as the model registries.

---

## 6. Dead-weight ledger

**No deletions performed or proposed here** — this ledger seeds the Arc-B deletion manifest. Every zero-caller claim below was re-verified centrally with a whole-repo grep this session. DR-4 kill targets from `docs/audits/2026-07-06-technical-architect-intake.md`.

| # | item | evidence (file:line) | caller-count evidence (witnessed 2026-07-16) | status vs DR-4/prior audit |
|---|---|---|---|---|
| D-1 | **Facts pipeline** (DR-4 kill: "0 rows ever; repoint `corp query` to notes_fts") | DDL: `src/corp/index_builder.py:45` (`facts`), `:57` (`facts_fts`), triggers `:131-140`; loader `_load_and_insert_facts` `:473-540` (facts INSERT `:525-527`); rebuild hooks `:181-184,201,228,289-307` | **Code is fully wired, not orphaned:** `query_engine.search_facts` `src/corp/query_engine.py:25-100` queries `facts_fts`; live callers `src/corp/cli/query.py:34-36`, `src/corp/actions/knowledge_actions.py:16-28`, `src/corp/test_pipeline.py:356-358`. **Starvation mechanism traced:** the loader reads `facts.yaml` from `info["vault_path"]` (`:483`) or OneDrive `_knowledge/` (`:489`); the ONLY `facts.yaml` producer in src/ is `project/renderer.py:75`, which writes to project `_knowledge/` folders — nothing ever writes `facts.yaml` where the vault branch looks (`grep -rn "facts.yaml" src/`: 1 writer, 2 readers) | "0 rows ever" (intake DR-4) is now mechanically explained, not just asserted. `search_facts` already falls through to `notes_fts` (`query_engine.py:91-97`), and a notes_fts→`FactResult` path exists (`:260-299`) — partial DR-4 execution in place. Kill = DDL+triggers+loader+facts branch of `search_facts`+tests (`tests/test_index_builder.py:237,246`, `tests/test_query_engine.py` facts fixtures) |
| D-2 | **Lane B `move_to_vault`** (DR-4 kill: "inbox path, never completed a write") | def `src/corp/extraction/vault_writer.py:57` | **DISPUTED as stated — 6 live src/ call sites witnessed:** `src/corp/ingest/router.py:712-715`, `:792-795`; `src/corp/cli/overnight.py:168,250`; `src/corp/cli/extract.py:129-131` | The DR-4 target must be narrowed to the specific dead *lane* (inbox path) inside `ingest/router.py`, not the `move_to_vault` function, which is the live vault-write path for overnight + extract flows. Arc-B must scope this kill precisely before deleting anything |
| D-3 | **N4 task manager** (DR-4 kill: "zero use") | `src/corp/task_manager.py` (persistence: frontmatter task files, `:271-334`) | Static importers exist: `src/corp/cli/task.py`, `src/corp/actions/task_actions.py`, `src/corp/chat.py` (via tach map `task_manager` edges); "zero use" is a runtime/usage claim from intake, not static | Kill would cascade: `cli/task.py`, `actions/task_actions.py`, chat wiring, `models.py` Task types (`src/corp/models.py:202-235`), 25 tests |
| D-4 | `schema/products.py::resolve_product_key` — zero-caller limb | def `src/corp/schema/products.py:72`; exported `src/corp/schema/__init__.py:32,61` | **Zero src/ callers** (whole-repo grep: only def + export + tests) | Confirms 2026-07-06 finding ("canonical but zero call sites") — still true |
| D-5 | `extractor/providers/cost_tracker.py` — zero-caller limb | `src/corp/extractor/providers/cost_tracker.py:11-46` | **Zero src/ callers** (whole-repo grep `cost_tracker|log_cost|read_cost`: only the module itself + tests) | Confirms 2026-07-06 "dead code" finding — still true |
| D-6 | Tests maintained for dead limbs | `tests/schema/test_products.py` — **42 test functions** for D-4; `tests/extractor/test_providers.py:203-274` — 2 test functions (`test_log_and_read_cost`, budget test) for D-5; `tests/test_task_manager.py` — **25 test functions** for D-3 | counted via `grep -c "def test"` | These are the "tests-for-dead-modules" the intake flagged (51 across the two dead modules ≈ 42+2 witnessed for D-4/D-5; D-3's 25 additional) |

| D-7 | **rfp KB canonical JSON — orphan input** | consumers: `src/corp/rfp/llm_router.py:54,211-213`, `rfp_answer_word.py:69,332-333` | **No producer of `RFP_Database_UNIFIED_CANONICAL.json` exists anywhere in-repo** (whole-repo grep: only the 2 consumers), and **`data/kb/` does not exist on disk in this checkout** — the KB read path can never have succeeded here | not in DR-4; new ledger entry. The whole rfp KB/feedback surface (`rfp_feedback.py` counter+drafts, `answer_selector.py:635` improve_report) writes into the same absent `data/kb/` tree |
| D-8 | index.db test-schema hand-copies | `tests/test_retrieve/test_engine.py:25-74`, `tests/test_retrieve/test_json_output.py:14-52` (`_TEST_SCHEMA` replicas of `index_builder._SCHEMA`) | not dead code, but maintained duplication that will silently diverge from `src/corp/index_builder.py:26-141` | drift-risk ledger entry for the seam-test workstream |

Additional zero-caller candidates surfaced by cluster agents are integrated below their cluster findings in §1/§2 (each was re-verified whole-repo before inclusion; none silently dropped).

---

## 7. Baseline extension (extends 2026-07-06 §1 — do not re-derive)

| date | pytest | duration | provenance |
|---|---|---|---|
| 2026-07-06 | 2,564 passed / 6 skipped | 160.14s | `docs/audits/2026-07-06-code-quality-audit.md` §6 (verbatim, untouched tree) |
| 2026-07-16 (JOURNAL) | 2,607 passed / 5 skipped | — | `JOURNAL.md` entry 2026-07-16 (post transcript-mime fix) — as recorded, not re-run |
| 2026-07-16 (this audit, witnessed) | **2,583 passed / 6 skipped / 1 warning** | 201.33s | `python -m pytest -x -q` on this tree (branch `docs/2026-07-16-architecture-ground-truth`, clean off `main` @ 14a1b09), Git Bash. rc=0 |

Note the 2,607 (JOURNAL) vs 2,583 (witnessed today, same-day) discrepancy is unexplained by this audit; the witnessed number is authoritative for HEAD 14a1b09. Radon/vulture/ruff tables from 2026-07-06 are NOT re-run here (out of scope per spec); their per-package rows remain the standing breadth baseline.

---

## Appendix A — central tooling evidence

- `tach check` → `[OK] All modules validated!` (rc=0), 2026-07-16, tach 0.34.0 at `.venv/Scripts/tach.exe`.
- `tach map` → 118 files with dependencies; aggregated to 83 unit-level edges (aggregation script: package = `src/corp/<pkg>/`, root module = `src/corp/<name>.py`; same-unit edges dropped).
- pytest full-suite run: see §7 row 3.
- Discovery-grep patterns per §5 family: listed in §5 preamble.

## Appendix B — per-cluster raw-evidence pointers

Each cluster agent produced a raw-evidence appendix (verbatim grep output per claim). Retained in the session transcript; representative file:line sites are embedded in the tables above.

---

## Addendum A — Codex cross-derivation reconciliation (appended 2026-07-16)

> **Amendment marker (append-only; CLAUDE.md §5 rule 3 — audits are immutable, supersede via a new file or an in-file amendment marker).** This addendum was appended after the audit's original assembly to reconcile an **independent second derivation** of the `src/corp/` dependency map. **Nothing in §0–§7 or Appendices A/B above was rewritten** — the original §1c tables stand as-witnessed. Cross-derivation source, pinned into the evidence library this session: `docs/audits/2026-07-16-codex-edge-diff.md` (gpt-5.6-sol, local Codex `sol` config).

### A.1 Provenance & method delta

The Codex derivation read **`src/corp/` Python source only** — it did **not** read `ARCHITECTURE.md` or this audit's body (a separate comparison pass read only this audit's §1). So the agreements below are genuine double-derivation, not an echo. Codex's normalization frame (verbatim from the diff header):

- **Static:** distinct unit-level absolute `from corp.*` / `import corp.*` edges; **relative imports excluded by definition**.
- **CLI:** distinct unit-level subprocess edges to `corp`/`cke`/`cpe`/`com`/`corp-meta` or a dynamically-configured agent CLI; external-tool subprocesses excluded.
- **Data:** distinct unit × **production-store** × direction tuples — **defaults bound to Vault/MyWork count; temporary sandbox / test-pipeline analogues and arbitrary caller-supplied destinations do not.**

### A.2 Static imports + subprocess: double-derivation agreement (89 + 6)

| kind | agreements | Codex-found-but-audit-missed | audit-has-but-Codex-disputes |
|---|---|---|---|
| static import edges | **89** | 0 | 1 (definitional — below) |
| subprocess / CLI edges | **6** | 0 | 0 |

- **Subprocess boundary is cleanly double-derived** — 6 agreements, zero disputes. §1b's subprocess-only corp→CKE finding (and the `rfp → corp retrieve` subprocess edge mis-drawn as an import in the codemap) is independently confirmed.
- **Sole static dispute — `__main__ → cli` (§1a row 51) — is definitional, not substantive.** Codex excludes it because `src/corp/__main__.py:1` is the **relative** import `from .cli import cli`, outside Codex's "absolute `corp.*`" task definition. This audit witnessed the *same line* and recorded it exactly as such ("relative `from .cli import cli` — invisible to `^from corp` grep, resolved manually"). Both derivations agree on the fact; they differ only on whether a relative import counts as an in-scope edge. **Nothing changes** — the edge is real, the frames just draw the scope line differently.

### A.3 Data edges: normalization-frame reconciliation + read-binding table

Data-set arithmetic after Codex's normalization (from the diff): Codex in-scope set **71** (ops.db 7 + index.db 11 + overnight_state.db 4 + Vault 24 + MyWork 25); this audit's normalized in-scope set **32**; **intersection 32** (the audit's normalized set is a strict subset of Codex's). The **~39-edge delta is not contradiction** — §1c deliberately enumerated store *owners* and WRITE/relocate sites plus representative reads, whereas Codex enumerated **per-consumer READ bindings** at finer grain. The two are complementary; the delta is read-binding enumeration §1c did not spell out row-by-row.

**Spot-verification:** an independent read-only agent re-checked a **10-of-39 sample (~26%)** against source at the cited `file:line` — **10/10 CONFIRMED** (verbatim snippets recorded in the session transcript, e.g. `SELECT key, value FROM meta` for index.db→index_builder; `output_path.write_text(...)` for retrieve→MyWork). The table below transcribes Codex's full 39-edge delta; ✓ marks the spot-checked rows.

| store | edge (direction) | witnessed at (Codex) | spot-checked |
|---|---|---|---|
| ops.db | ops.db → ops **READ** | `ops/database.py:225,463-483` | ✓ |
| index.db | index.db → index_builder **READ** | `index_builder.py:322` | ✓ |
| index.db | index.db → actions **READ** | `actions/analytics_actions.py:18-20`; `actions/knowledge_actions.py:16-28` | |
| index.db | actions → index.db **WRITE** | `actions/index_actions.py:16-18` | |
| index.db | index.db → cli **READ** | `cli/analytics.py:24-30`; `cli/index.py:48-55` | ✓ |
| index.db | cli → index.db **WRITE** | `cli/index.py:22-36` | |
| index.db | ingest → index.db **WRITE** | `ingest/inbox.py:550-553` | |
| overnight_state.db | overnight_state.db → cli **READ** | `cli/overnight.py:205,260,286` | ✓ |
| vault | vault → actions **READ** | `actions/brief_actions.py:39-43`; `actions/archive_actions.py:63-67` | |
| vault | vault → chat **READ** | `chat.py:205-209` | ✓ |
| vault | vault → cli **READ** | `cli/system.py:116-134` | |
| vault | cli → vault **WRITE** | `cli/extract.py:129-131`; `cli/overnight.py:248-250` | |
| vault | vault → extraction **READ** | `extraction/vault_writer.py:86-93` | |
| vault | vault → ingest **READ** | `ingest/extractions.py:248-252`; `ingest/inbox_ops.py:215-230` | |
| vault | vault → integrity **READ** | `integrity.py:327-332` | |
| vault | vault → intent_router **READ** | `intent_router.py:355-365` (via production-default `resolve_project`) | |
| vault | vault → overnight **READ** | `overnight/preflight.py:45-48,67-69` | |
| vault | vault → project_resolver **READ** | `project_resolver.py:105-112` | |
| vault | vault → retrieve **READ** | `retrieve/engine.py:441,457` | ✓ |
| vault | vault → task_manager **READ** | `task_manager.py:197,274,317` | ✓ |
| vault | vault → template_manager **READ** | `template_manager.py:211-215` | |
| MyWork | MyWork → actions **READ** | `actions/inbox_actions.py:18-29` | |
| MyWork | actions → MyWork **WRITE** | `actions/archive_actions.py:47-59` | |
| MyWork | MyWork → chat **READ** | `chat.py:205-209` | |
| MyWork | MyWork → cli **READ** | `cli/cleanup.py:32-35`; `cli/extract.py:53-63` | |
| MyWork | MyWork → extraction **READ** | `cli/extract.py:80-95`; `extraction/scanner.py:44-68,133` | |
| MyWork | MyWork → extractor **READ** | `cli/extract.py:89-95`; `extractor/extract.py:577,585` | |
| MyWork | MyWork → freshness_scanner **READ** | `freshness_scanner.py:160-184` | |
| MyWork | MyWork → ingest **READ** | `ingest/router.py:111-125,671` | ✓ |
| MyWork | MyWork → integrity **READ** | `integrity.py:393-394,414-430` | |
| MyWork | MyWork → intent_router **READ** | `intent_router.py:301-303,355-358` (production-default) | |
| MyWork | MyWork → llm_router **READ** | `llm_router.py:131-133` (production-default) | |
| MyWork | MyWork → ops **READ** | `ops/registry.py:24-26,59` | |
| MyWork | MyWork → overnight **READ** | `overnight/monitor.py:66-68`; `overnight/preflight.py:55-60` | |
| MyWork | MyWork → project_resolver **READ** | `project_resolver.py:55-61,120-122` | |
| MyWork | MyWork → retrieve **READ** | `cli/retrieve.py:187-200` | |
| MyWork | retrieve → MyWork **WRITE** | `cli/retrieve.py:200`; `retrieve/prep.py:170` | ✓ |
| MyWork | MyWork → template_manager **READ** | `template_manager.py:157-168,350-358` | |
| MyWork | MyWork → vault_io **READ** | `vault_io.py:309-310` | ✓ |

### A.4 Disputed data edges: both frames recorded, nothing resolved

Codex disputes three data-edge families the audit's §1c includes. Each is a **normalization-frame difference** (production-default binding vs any-access), **not a factual disagreement** — the underlying code is identical in both derivations. Per the reconciliation mandate, both frames are recorded and **nothing is resolved here**:

| disputed edge | audit §1c frame (any-access) | Codex frame (production-store only) | disposition |
|---|---|---|---|
| `sandbox → {ops.db, index.db, overnight_state.db}` **WRITE** (`sandbox.py:71-86`) | counted — sandbox writes DDL/rows into the three DB files (copies) | excluded — "temporary sandbox copies, not production stores" | frame difference; both correct in-frame — **unresolved** |
| `test_pipeline → {MyWork, vault}` **WRITE** (`test_pipeline.py:314-316,436-474,524-527`) | counted — writes to MyWork/vault filesystems | excluded — "operates on the temporary sandbox pipeline, not production filesystems" | frame difference — **unresolved** |
| `project → vault` **WRITE** (`project/cli.py:284-289`) | counted (§1c project row; **§4.2 D6**) — a write to a "vault" path | excluded — "destination is only arbitrary `--copy-to-vault` input; **no production/default vault binding**" | see below |

**The `project → vault` dispute independently confirms the Arc-N1 hole.** Codex's exclusion reason — *"arbitrary `--copy-to-vault` input, no production/default vault binding"* — is a second, blind derivation of exactly what §4.2 **D6** flagged: `project/cli.py:284-289` writes an **arbitrary, unguarded, user-supplied destination** with no vault-root binding and no OneDrive/ADR-27 guard. The two derivations agree on the fact (unbound arbitrary destination); they differ only on whether to *count* it as a data edge. Its disposition is not a counting question — it is the **Arc-N1 `--copy-to-vault` guard** (OneDrive raise + vault-root containment), tracked separately.
