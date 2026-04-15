# Development Journal

Append-only log. 3 lines per session. Never edit old entries.
Claude Code: read last 5 entries before starting work.

---

## 2026-04-15 (Tach Phase 2)
- **Did:** Resolved 6 baseline Tach violations by reclassifying project_resolver (orchestration→core) and query_engine (interface→orchestration). Ran tach sync to clean stale depends_on entries (exact=true flagged them as unused after reclassification). tach check clean. Zero Python changes.
- **Failed:** Nothing.
- **Next:** Step 12 — reconcile AGENTS.md and ARCHITECTURE.md to use 4-layer taxonomy (foundation/core/orchestration/interface). Currently docs describe 7-layer model, tach.toml uses 4-layer. Active confusion source.

## 2026-04-15 — Tach adoption Phase 1
- **Did:** Bootstrapped tach.toml with 4 layers (foundation/core/orchestration/interface), 34 modules. corp.ingest correctly classified as orchestration (not core) after Codex audit found 3 upward deps in router.py:18,653,743. Ran tach sync — found 6 baseline violations in 3 dependency pairs (intent_router→project_resolver, llm_router→project_resolver, actions→query_engine); documented in docs/audits/2026-04-15-tach-baseline-violations.md. Wired tach check into pre-commit (local hook, triggers only on src/corp/*.py changes) and created .github/workflows/tach.yml (pinned v0.34.0). Added CONTRIBUTING.md with tach sync cultural rules. Replaced AGENTS.md import-direction check with Tach reference. Created ADR-26. **2495 tests passing, 0 failed.** 8 commits, merged to main.
- **Failed:** `always_run: true` in pre-commit hook blocked non-Python commits — removed; hook now triggers only when src/corp/*.py files are staged (correct behavior).
- **Next (Step 12, separate PR):** Update AGENTS.md + ARCHITECTURE.md to use 4-layer taxonomy (foundation/core/orchestration/interface) replacing 7-layer model. Two tach reclassifications resolve all 6 baseline violations: corp.project_resolver core→orchestration(wait, core), corp.query_engine interface→orchestration. See docs/audits/2026-04-15-tach-baseline-violations.md.

## 2026-03-30 — Diagrams v4 Pipeline
- **Did:** Audited per-module READMEs: 12 existed, 1 generated (actions/). Created docs/diagrams/conventions.yaml (style guide, 31 lines). Generated 3 C4 diagrams from ARCHITECTURE.md: system-context (4 internal + 7 external nodes, 11 edges), container-module (4 layers, 14 nodes, 13 edges, vertical layout), magistrala-pipeline (4 phases, 15 nodes, side-channel DBs). All diagrams use 13px font, dark mode themeVariables, classDef colors per layer. Rendered SVGs via mmdc 11.12.0. Removed orphaned README.md from docs/diagrams/. Process: ARCHITECTURE.md + conventions.yaml -> .mermaid -> .svg (Council #25). **2495 tests passing, 0 failed.** 7 commits, merged to main (fast-forward).
- **Failed:** render-diagrams.ps1 Join-Path fix (step 8) was already applied in prior commit 9db4302 — no-op.
- **Next:** Magistrala verification. MISC rate measurement.

## 2026-03-30 (Codex audit fixes)
- **Did:** Fixed 6 findings from first Codex audit: (1) rfp_only filter dropped during product expansion in retrieve() — 1-line bug fix; (2) naming_config.py moved from ingest/ to schema/ — fix layer violation, shim left in ingest/ for compat, all 8 import sites updated; (3) schema normalize --in-place deprecated — now reports instead of writing vault files directly; (4) OneDrive safety guard added to project/renderer.py; (5) note paths in retrieve engine now resolved against vault_root, silent OSError catches now log at DEBUG; (6) CKE manifest paths switched to .as_posix() — forward slashes per invariant. **2495 tests passing, 0 failed.** Merged to main.
- **Failed:** Nothing.
- **Next:** Magistrala verification. MISC rate measurement.

## 2026-03-30 — P0+P1 error handling + scripts fix (Code Quality Audit)
- **Did:** Fixed all 15 error-handling items from audit: 5 critical `except Exception: pass` → specific types + logging (`built_in_actions.py` × 3, `ingest/router.py` × 2); 9 high-severity broad catches narrowed (`integrity.py` × 5, `vault_io.py` × 3, `task_manager.py`, `index_builder.py` × 5, `retrieve/engine.py`). Fixed 4 broken scripts (`packages/` → `tests/extractor/fixtures/`; stale `sys.path` inserts removed; REPO_ROOT depth fixed). Archived 6 one-time migration scripts to `scripts/archive/`. Added `__main__` guards to 3 scripts. Removed hardcoded username from `project/cli.py`. `llm_router.py:212` kept broad — google-genai raises unknown exception hierarchy, already logs. Work landed on `feat/project-scoped-gotchas` (pre-commit stash cycle switched branches after 2nd commit). **2412 tests passing, 0 failed.**
- **Failed:** `llm_router.py` narrowed exception broke `test_api_failure` (mock raises bare `Exception`); reverted. Pre-commit stash/restore switched active branch mid-session — all commits on `feat/project-scoped-gotchas` instead of `fix/p0-p1-error-handling-scripts`.
- **Next:** Merge `feat/project-scoped-gotchas` to main. P2: refactor `extract_knowledge()` (235 lines), `process_file()` (218 lines), `ingest_folder()` (216 lines). Standardize config access pattern.

## 2026-03-29 session 5 — Package consolidation (6 → 1 unified src/corp/)
- **Did:** Completed `feat/consolidate-packages` branch: 4 prior commits moved all 6 packages to `src/corp/`, unified `pyproject.toml`, updated all imports to `corp.*` namespace, removed old `packages/` directory. This session: fixed 6 remaining test failures (RFP CLI smoke cwd resolution 2→3 levels, naming_config test missing `extension_hint` check, `light_scan` `time.time()`→`time.perf_counter()` for Windows precision). Updated CLAUDE.md, `config/agents.yaml`, `.ecosystem/MASTER_HANDOFF.md` for new layout. Verified zero old import references (`corp_os_meta|corp_knowledge_extractor|corp_by_os` etc = 0 matches). All 4 CLIs working (`corp`, `cke`, `cpe`, `com`). **2,404 tests passing, 0 failed.** Merged to main.
- **Failed:** Ruff pre-commit auto-fixed `batch_api.py` on first commit attempt — re-staged and committed successfully.
- **Next:** Corp-rfp-agent Click CLI migration. 30-day skill eval (due 2026-04-25). MinHash wiring. Ontology Q4. RFP Federation (ADR-22).

## 2026-03-29 session 4 — Council #23 Phase 3+4 (ADR-23 Q3/Q4/Q5)
- **Did:** Flattened 3 sub-packages: `doctor/integrity.py` → `integrity.py`, `freshness/scanner.py` → `freshness_scanner.py`, `extraction/non_project/` (5 files) → `extraction/`. Max path depth 6→3 (relative to src). Centralized `parse_llm_json` + `normalize_string_list` in corp-os-meta: added `log.error` before raise; moved `normalize_string_list` from CKE utils to corp-os-meta; deleted CKE `utils.py` entirely (8 import sites updated). Deleted 4 confirmed dead files in corp-rfp-agent: `clean_kb.py`, `scan_kb.py`, `kb_to_markdown.py`, `_paths.py` (test_cli_smoke.py updated). corp-os-meta: 133 pass; CKE: 863 pass; rfp-agent: 179 pass; corp-by-os: 990 pass.
- **Failed:** Pre-commit ruff caught `UP038` (`isinstance(x, (int, float))` → `int | float`) in `contract.py` — fixed manually. Cherry-pick workflow needed to align doctor/freshness commits across phase2/phase3 branches due to background task switching branches accidentally.
- **Next:** Corp-rfp-agent Click CLI migration. 30-day skill eval (due 2026-04-25). MinHash wiring. Ontology Q4.

## 2026-03-29 session 3 — Phase 2 subprocess boundary fix (ADR-23 Q1)
- **Did:** Rewrote `overnight/cke_client.py` (180 → 280 lines) to use subprocess instead of direct CKE imports. Enforces architecture rule: corp-by-os → CKE must use process boundary. `is_available()` uses `shutil.which("cke")`; `extract_batch`/`extract_sync` run `cke process-manifest` with `capture_output=True, encoding="utf-8", errors="replace"` and regex-parse stdout summary ("Done: N", "Errors: N", etc.); `scan_local` uses `cke scan -o <tmp.json>`; `load_cke_config()` reads settings.yaml directly; `estimate_cost()` → NotImplementedError (dead function, no callers). 1015 tests pass, 1 skip. Branch: `feat/phase2-subprocess-boundary`, commits `663a05d` + `775a7d3`. Zero remaining `corp_knowledge_extractor` runtime imports in corp-by-os.
- **Failed:** Ruff E402 (`import os as _os` after constant) — moved `os` import to top-level block.
- **Next:** Merge `feat/phase2-subprocess-boundary` to main. Phase 3 (ADR-23 Q2 remaining) or ADR-22 (RFP federation).

## 2026-03-29 session 2 — Phase 1 CLI modularization (ADR-23 Q2)
- **Did:** Split `cli.py` (3,574 lines, 71 commands) into `cli/` package with `__init__.py` + `_common.py` + 16 domain modules (project, vault, template, index, rfp, task, system, workflow, query, analytics, misc, retrieve, extract, cleanup, ingest, overnight). `__init__.py` thinned to 131 lines (imports + group def + 33 add_command calls). Updated 4 test files (patch targets for get_config; overnight private helper imports). 1014 tests passing. CLI snapshot captured to `eval/cli_snapshot_phase1/` — only invocation name differs vs baseline. Merged via feat/phase1-cli-modularization (commits f7d94ab → 06eb571).
- **Failed:** Ruff pre-commit hook auto-fixed files on first attempt (import sorting, blank lines) — required re-stage and re-commit. Pattern documented.
- **Next:** Phase 2 (further CLI refactoring per ADR-23) or other ADR-23 Q2 work.

## 2026-03-29 session 1 — Council #23 Phase 0 prerequisites
- **Did:** Completed all Phase 0 gates for ADR-23: CKE call volume (3/run, no batching needed), cli.py shared state audit (71 commands, 14-module split plan), CLI help snapshot (55 files in `eval/cli_snapshot_2026-03-28/`), dead code verification (4 corp-rfp-agent files confirmed dead; `kb_to_markdown.py` needs coordinated test update on deletion). MASTER_HANDOFF.md updated (Council 22→23, ADR-23 entry, Open Decisions phases 1–4). Merged `chore/council23-phase0-prerequisites` to main.
- **Failed:** Pre-existing ruff E501 (`query_engine.py:389,423`) and integration test (`IMG` type code) — not introduced, not fixed.
- **Next:** Phase 1 (CLI split): create `cli/` directory with 14 domain modules + `_common.py`; use `eval/cli_snapshot_2026-03-28/` as regression baseline.

## 2026-03-28 session 4 — archive naming cleanup
- **Did:** Enforced `{YYYY-MM-DD}_{TYPE}_{description}.ext` naming on all `.ecosystem/archive/` files. Renamed 13 non-compliant files (date-at-end and undated variants). All 22 archive files now comply. Merged `chore/archive-naming-cleanup` to main.
- **Failed:** -
- **Next:** Per-note v2/v3 deletions (Rob confirms). RFP federation (ADR-22). sandbox_apply.py + doc_type_classifier pattern expansion. MinHash wire into inbox.

## 2026-03-28 session 3 — Phase 4 pending cleanup
- **Did:** v2/v3 01_Product_Docs quality comparison (36 notes matched) — v3 wins 20/36 but NOT clear upgrade: 2 v3-empty files (LifeScience_session1v2, Platform_Editedv2) must keep v2; total facts nearly equal (860 v2 / 850 v3). Cognitive_Friday vault cross-ref: both extractions already ingested. Sandbox review summary for Rob (2.4 GB, 53% MISC rate, apply step not built). 4 rebuild scripts archived to scripts/archive/. Phase 4 resolution report written. All tests green (1015+863+183+133+124+62). Merged chore/phase4 to main.
- **Failed:** -
- **Next:** Per-note v2/v3 deletions (Rob confirms). RFP federation (ADR-22). sandbox_apply.py + doc_type_classifier pattern expansion. MinHash wire into inbox.

## 2026-03-28 session 2 — repo audit + cleanup + governance
- **Did:** Full monorepo audit (plans archived). Phase 2 safe deletions (5 GB freed). Phase 3 governance: ADR-22 written, docs/ date-prefixed, .ecosystem/ root clean, CLAUDE.md + MASTER_HANDOFF.md counts updated (21→22 ADRs). All tests passing. Merged chore/phase3 to main.
- **Failed:** -
- **Next:** Implement ADR-22, .sandbox/ review (Rob), v2/v3 _outputs/ audit.

## 2026-03-28
- **Did:** SQL analytics MVP (6/10 benchmark queries). People added to FTS. Gemini 2.0 Flash-Lite for Tier 2 (-75% cost). Scripts/ to Dev/ migration (11 files, 2673 DB rows). .ecosystem consolidated. ADRs synced (#13-#21). Phase 1 cleanup (archives deleted). Corp-pdf-toolkit archived. Council #22 RFP federation debate. Venvs recreated. Full health check passed.
- **Failed:** -
- **Next:** Ontology Q4 (canonical product map). RFP federation implementation. File renames (585 files). MinHash wire into inbox.

## 2026-03-27 MinHash near-duplicate detection

- **Did:** Implemented `ingest/dedup.py` — MinHash signatures (128 perms, word 3-grams), `content_signatures` table in ops.db, `check_near_duplicate()` pipeline hook (after light_scan, before CKE), `get_dedup_report()` for `corp dedup-report` CLI command. Installed datasketch 1.9.0. 24 new tests, all pass. Full suite: **992 passed, 1 skipped**.
- **Design:** Signatures upsert on re-ingest. LSH index is rebuilt in-memory per query (acceptable for current vault size). Never auto-deletes — report only. `check_near_duplicate` is fail-open (ImportError/any exception → empty list, no pipeline disruption). `datasketch` added as optional dep `[dedup]`.
- **Next:** Wire `check_near_duplicate()` into `inbox.py` process_file() after light_scan call. Consider persisting LSH index if query latency grows with vault size.

## 2026-03-26 hybrid TF-IDF classifier pipeline

- **Did:** Full dual-vectorizer hybrid classifier — 8 steps: (1) Locked stratified 80/20 train/test split (`create_classifier_split.py` → 248 train, 62 test). (2) Trained `LogisticRegression` with char n-gram filename vectorizer + word n-gram content vectorizer, JSON serialization (no pickle) — CV 85.5% combined, +3.2pp content uplift. (3) JSON loader `hybrid_loader.py` with `lru_cache`, zero pickle risk. (4) One-time test eval: **85.5% hybrid vs 53.2% regex (+32.3pp)**, 0 high-confidence errors; at 0.5 threshold → 100% acc on 45% of files, 18% LLM fallback. (5) `classify_doc_type_hybrid()` integrated into `doc_type_classifier.py` — TF-IDF → regex → None pipeline with `USE_TFIDF` flag. (6) `eval.py` updated with three-way comparison section (1b). (7) 11 tests in `test_hybrid_classifier.py`. (8) Full suite: **863 CKE tests pass**. Merged `feat/hybrid-classifier` to main.
- **Errors:** ruff E402 on multi-line imports needed `# noqa` on `from ... import (` line not inner line. ruff E741 ambiguous `l` → `lbl`. `multi_class` removed in sklearn 1.7+ (lbfgs multinomial default).
- **Next:** Wire `classify_doc_type_hybrid()` into live extraction pipeline (inventory.py or tier_router.py). Consider expanding enriched training set for higher content %.

## 2026-03-26 light_scan module + classifier/tag improvements

- **Did:** (1) Classifier: added 6 high-priority filename patterns to `doc_type_classifier.py` (cognitive.shorts/friday, demo2win, iso22301/cybersecurity, extended product_doc/architecture terms) — accuracy 51.3% → **57.1%** (+18 correct, 0 false positives). Fixed architecture pattern ordering bug (cognitive content was matching architecture before training). (2) Tags: added `inventory-ops-agent`, `logistics-emissions-calculator`, `demand-edge` to `taxonomy.yaml` + `_TAG_ALIASES` + `product_aliases.yaml` — mean tag score 0.791 → **0.797**. (3) Light scan: implemented `light_scan.py` (Council Decision #19) — `ScanResult` dataclass with separate `filename_text`/`content_text` feature spaces, 7 format scanners (pptx/docx/pdf/xlsx/csv/txt-md/mp4), tiered fault tolerance (`full`/`degraded`/`filename_only`). 25 tests all pass. (4) Enrichment: `enrich_training_data.py` retroactively scanned 310 training examples — 82 (26%) enriched with real content, 228 filename-only fallback. Output: `classifier_training_enriched.json`. Merged `feat/light-scan` to main. **968 tests pass**.
- **Errors:** ruff pre-commit blocked twice (redundant `"r"` mode, line-too-long E501) — fixed and recommitted. Unicode `→` in log string broke Windows cp1252 console — fixed to plain text.
- **Next:** Use `content_text` + `filename_text` dual-vectorizer in classifier training. Consider running enrich on machines with more source files available.

## 2026-03-26 client normalization migration

- **Did:** Full client normalization migration on branch `fix/client-normalization-migration`. (1) Vault audit: 583 notes, 22 distinct client values, key splits found (Lenzing AG/Group, JLR/Jaguar Land Rover, Pepsi variants, SGDBF long-forms, etc.). (2) Expanded `client_aliases.yaml` in CKE from 8 to 48 entries covering all vault variants. (3) Added `get_client_variants()` to corp-by-os + OR LIKE expansion in retrieve engine — `corp prep "JLR"` now finds 3 sources (was 1). (4) Created `scripts/migrate_client_names.py` (dry-run + --apply); applied migration: 77 vault notes normalised. (5) Rebuilt index: 493 notes. (6) Added `schema.yaml` contract to corp-os-meta + `validate_against_schema()` (warn-only). (7) Wired schema check into CKE `post_process_extraction()`. Eval: no regression. 970 tests pass (6 pre-existing Jinja2 failures unrelated).
- **Errors:** 6 pre-existing test failures (TemplateNotFound: meta.yaml.j2) — not caused by this work, present on main too.
- **Next:** Merge `fix/client-normalization-migration` to main. Consider fixing the 6 pre-existing Jinja2 template test failures separately.

## 2026-03-26 early morning (continued)
- **Did:** v2 bulk ingest (387 notes, 493 total indexed, 25 projects). Vault now has real data. corp retrieve returns 30 results across topics.
- **Failed:** 2 Cognitive Friday YAML parse errors (unquoted hyphen in session_id)
- **Next:** Git hygiene (179 uncommitted ruff files). RFP KB + vault merge (Council). Obsidian optimization. 30-day eval (2026-04-25).

## 2026-03-26 v2 bulk ingest

- **Did:** Ran v2 bulk ingest (387 notes ingested, 2 YAML errors, 0 quarantined). Index rebuild: 583 vault notes found → 90 deduped by source_hash → 493 unique notes indexed (25 projects). Net new unique v2 notes: ~292. `corp retrieve "demand planning"` → 30 results, Sufficient (unchanged from v3-only — engine caps at 30). Vault now fully populated with v3 + v2 extractions.
- **Errors:** 2 YAML parse failures (`Cognitive Friday Season 2` files — `session_id: "cognitive-friday-season-2` unquoted hyphen truncates string). Notes skipped, not quarantined.
- **Next:** Re-extract the 2 failing Cognitive Friday notes (fix YAML), re-extract low-quality JLR notes (score 28–29), run `scripts/extract_training_data.py` to refresh fixtures, RFP KB + vault merge decision (Council).

## 2026-03-26 v3 bulk ingest, IndexStats fix, gotcha added

- **Did:** Fixed `IndexStats.total_facts` AttributeError in cli.py:3099 (was `total_facts`, correct attr is `facts_indexed`). 39/39 ingest tests pass. Added CKE path structure gotcha to `~/.claude/skills/gotchas/gotchas.md`. Ran v3 bulk ingest: 203 notes ingested (2 deduped identical source_hash → 201 unique), 0 quarantined, 0 skipped, index rebuilt in 2.0s (201 notes, 25 projects, 0 facts). `corp retrieve "demand planning"` → 30 results, Sufficient. `corp retrieve "WMS picking methodologies"` → 28 results, Sufficient (was 2 JLR-only before).
- **Quality distribution:** Only 3/203 notes have quality_score (the 3 JLR pilot notes at 28/29/85). All 200 pre-quality-era notes pass gate by design (None → pass). Vault now has 210 total notes (203 v3 + 7 pre-existing).
- **Next:** Run `scripts/extract_training_data.py` to refresh fixtures from new v3 extractions. Consider re-extracting low-quality JLR notes (score 28–29) with deeper prompt.

## 2026-03-26 JLR pilot end-to-end ingest

- **Did:** Ran JLR pilot ingest — diagnosed path structure mismatch (`jlr_pilot/` is flat, `ingest-extractions` expects `scope/client/pkg/extract/` hierarchy). Created `jlr_staged/projects/Jaguar_Land_Rover_TMS_WMS_OMS/` with 3 packages. Dry-run confirmed 3→01_Knowledge, 0 quarantined. Live ingest succeeded. Index rebuilt. `corp retrieve "JLR TMS"` returns 3/3. `corp retrieve "WMS picking methodologies"` returns 2/2 (Sufficient: No — needs more WMS depth coverage). Minor display bug: `IndexStats.total_facts` AttributeError post-rebuild (cosmetic only).
- **Issues:** `jlr_pilot/` flat structure incompatible with `ingest-extractions` — requires wrapping in `projects/CLIENT/` scope. Two low-quality notes (score 28–29) passed because DEFAULT_QUALITY_THRESHOLD=25. Full v3 ingest (203 notes) pending — would address health check finding of empty 01_Knowledge vault.
- **Next:** Run full v3 ingest to populate vault. Fix `IndexStats.total_facts` display bug in CLI. Consider re-extracting the 2 low-quality JLR notes with a deeper prompt.

## 2026-03-26 ecosystem health check

- **Did:** Read-only comprehensive health audit across 8 phases: test results (2,291/2,298 pass, 7 skip), CLI ops (7 agents OK), sandbox E2E (5/5 pass), CKE outputs (749 notes, 613 JSON, 20.2GB), databases (ops.db 1,116 rows, index.db 2,677 rows), vault (1,325 indexed notes but 01_Knowledge empty — investigate), git history (438 commits, main clean, 6 active branches), MyWork (794 files). Generated `.ecosystem/archive/2026-03-26_HEALTH_CHECK.md` report.
- **Issues:** 277 ruff linting errors found (213 auto-fixed, 64 remaining E402/E501 formatting); vault 01_Knowledge empty despite index.db showing 1,325 notes (routing mismatch?); live E2E test timeout expected (real API calls).
- **Next:** Investigate vault note storage paths. Fix E402 imports. Update training fixtures. Monitor live test performance.

## 2026-03-25 night session
- **Did:** Monorepo complete (6 packages, 2,153 tests). Naming convention v2 (19 type codes, 15 client aliases). Code review fixes (2 critical, 4 high). Training data fixtures from 690 extractions. Routing feedback table. Trust_level protection. Vault ingest pipeline.
- **Failed:** Standalone repo folder rename blocked by Windows file locks. CKE had 6 pre-existing test failures (fixed).
- **Next:** Integration tests, pre-commit hooks, coverage gaps (CPE classifier, RFP anonymization), pilots.

## 2026-03-25 late night
- **Did:** Workflow improvements: JOURNAL.md, integration tests (6 new → 23 total), pre-commit hooks (ruff), dev-check.ps1, session-start.ps1, Session Protocol + Prompt Decision Rule in CLAUDE.md.
- **Failed:** sample_output.json is deep extraction format (qa_pairs/slide_breakdown), not frontmatter — test adapted accordingly.
- **Next:** Coverage gaps (CPE classifier, RFP anonymization), Hypothesis tests, ADR conversion.

## 2026-03-25 continuation
- **Did:** 79 CPE classifier tests (all 20 priority rules, priority ordering, edge cases). 25 RFP anonymization tests (core + middleware, all patched via mock). 5 Hypothesis property-based tests. 14 ADRs distilled from AI Council debates into decisions/.
- **Failed:** \bpayload\b doesn't match payload_inbound (underscore is \w — word boundary lesson). \bstrategy\b doesn't match supply_chain_strategy same reason. Fixed test inputs.
- **Next:** Run dev-check.ps1 full quality gate, consider adding hypothesis to monorepo pyproject.toml dev deps.

## 2026-03-25 full day session
- **Did:** Monorepo complete (6 packages, 2,276 tests). CKE v0.8.0 namespace migrated. Naming convention v2 (19 types, 15 clients). Code review (20 issues found, 8 fixed). Training data fixtures (690 notes → 7 fixtures). Coverage gaps filled (CPE +79, RFP +25). Hypothesis tests. 14 ADRs. Workflow improvements (JOURNAL, integration tests, pre-commit, dev-check). Closed learning loop with Last triggered. VERIFY-LOG. Settings optimized (opusplan, haiku subagents). 3 Council decisions (monorepo, routing feedback, naming, workflow optimization).
- **Failed:** Standalone repo folder rename blocked by Windows file locks. Baseline tasks for skill evaluation — skills deployed before baseline.
- **Next:** Pilots (JLR vault ingest → corp prep → corp retrieve). 30-day skill evaluation (2026-04-25). Local LLM exploration. AI Council CLI integration. Obsidian optimization.
## 2026-03-25 sandbox phase 1
- **Did:** PipelineConfig dataclass in corp-os-meta (production() + sandbox() classmethods, 10 tests). Threaded config through vault_io (resolve_vault_path, list_projects, validate_vault), index_builder (rebuild_index, update_project), ops/database (OpsDB), overnight/state (OvernightState). All functions backward-compatible (None → production()). index_extra_roots added to PipelineConfig for INDEX_EXTRA_ROOTS env var. Path audit confirmed hardcoded paths isolated to legacy AppConfig only.
- **Failed:** noqa inside triple-quoted SQL string doesn't work (comment becomes part of the SQL). Fixed by reformatting the CASE expressions across 2 lines.
- **Next:** Phase 2: sandbox fixture in conftest.py, migrate test monkeypatching to PipelineConfig.sandbox(), thread CLI entry points via Click ctx.obj.

## 2026-03-25 sandbox phase 2
- **Did:** Step 1: Threaded PipelineConfig through 13 CLI commands via @click.pass_context on root group + @click.pass_obj on each command. Backward-compatible (fallback to production()). Step 2: SandboxManager in sandbox.py — create(), _init_databases() (delegates to real OpsDB/OvernightState/index_builder _SCHEMA), stage_files(), snapshot_production(), teardown() with retry, context() CM. Step 3: fixture corpus (5 minimal files + manifest.json with expected type_code/client). Step 4: sandbox + sandbox_with_corpus fixtures in conftest.py. 925 tests passing throughout. Merged feat/sandbox-phase2 to main.
- **Failed:** ruff E501 on 3 pre-existing long lines touched by the merge context (fixed). ruff changed import sort order in conftest.py on second hook run (staged and re-committed).
- **Next:** Migrate existing test monkeypatching to use sandbox fixture. Add integration tests that use sandbox_with_corpus to exercise ingest → OpsDB roundtrip.

## 2026-03-25 sandbox phase 3
- **Did:** test_pipeline.py module (StepResult, PipelineTestReport, run_pipeline_test(), format_report(), 5 step functions). `corp test-pipeline` CLI command with --live/--keep-sandbox/--verbose/--output. 9 tests (sandbox isolation, report structure, keep_sandbox, format_report). All 2,153+ tests passing. Manual smoke test: 5/5 steps pass in ~0.1s. Merged feat/test-pipeline-command to main.
- **Failed:** ruff E501 on 3 lines across cli.py + test_pipeline.py (long Rich markup strings) — fixed with if/else blocks. Corpus type codes DECK/NOTE absent from naming_config.yaml — used deterministic SOW/PRES/LENZ/JLR/GEN checks instead.
- **Next:** Live mode (--live flag exercises real CKE API). Migrate existing monkeypatching tests to use sandbox fixture. Integration tests using sandbox_with_corpus for ingest → OpsDB roundtrip.

## 2026-03-26 test-pipeline --record
- **Did:** Added `--record` flag to `corp test-pipeline`. `--record` implies `--live`, calls real CKE API per corpus file, saves `{hash[:12]}_{tier}.json` fixtures + `manifest.json` to `tests/fixtures/pipeline/recorded/`. Future fixture runs replay from these JSONs. PipelineTestReport gains `recorded_fixtures`/`recording_cost` fields. CLI prints "Recorded N fixtures, total cost $X.XX". 2 new tests (fields default + graceful CKE-unavailable skip). 936 passed, 1 skipped. Merged feat/test-pipeline-record to main.
- **Failed:** Nothing new — "file modified since read" on test_pipeline.py due to ruff auto-format between sessions (existing gotcha).
- **Next:** Live pilots (corp test-pipeline --live → verify against real CKE). Migrate existing monkeypatching to sandbox fixture. Integration tests for ingest → OpsDB roundtrip.

## 2026-03-26 early morning
- **Did:** Health check (HEALTHY), JLR pilot (3 notes ingested, retrieve works), v3 bulk ingest (201 notes, 0 quarantined), IndexStats bug fixed, gotcha added
- **Failed:** jlr_pilot flat structure required manual staging (gotcha added)
- **Next:** v2 bulk ingest (763 notes), RFP KB + vault merge decision (Council), Obsidian optimization, 30-day eval

## 2026-03-26 morning
- **Did:** Eval baseline (classifier 51.3%, tags 0.753). JLR real usage test (useful output). Client alias fix (retrieve + prep). Obsidian setup (8 MOCs, plugin recs). Lint cleanup. v2/v3 bulk ingest (493→587 vault notes). Context scope in ROUTING.md.
- **Failed:** Classifier still 51.3% (filename-only ceiling, LLM needed for 70%+)
- **Next:** Council CLI integration. Obsidian plugins install. Lenzing normalization. RFP KB + vault merge.

## 2026-03-28
- **Did:** SQL analytics MVP (6/10 benchmark queries). People added to FTS. Gemini 2.0 Flash-Lite for Tier 2 (-75% cost). Scripts/ to Dev/ migration (11 files, 2673 DB rows). .ecosystem consolidated. ADRs synced (#13-#21). Phase 1 cleanup (archives deleted). Corp-pdf-toolkit archived. Council #22 RFP federation debate. Venvs recreated. Full health check passed.
- **Failed:** -
- **Next:** Ontology Q4 (canonical product map). RFP federation implementation. File renames (585 files). MinHash wire into inbox.

## 2026-03-28 session 2 — repo audit + cleanup + governance
- **Did:** Full monorepo audit (2026-03-28_CLEANUP_PLAN.md, 2026-03-28_REPO_INVESTIGATION.md → archived). Phase 2 safe deletions: rebuild_staging (2 GB), misc/01_Product_Docs temp_frames (2.4 GB), Python caches (~0.3 GB), flattened _outputs/_outputs/ nesting. Phase 3 governance: ADR-22 written (RFP KB federation), docs/ phase reports date-prefixed, .ecosystem/ root clean (only MASTER_HANDOFF.md remains), CLAUDE.md council count 21→22, MASTER_HANDOFF.md ADR count + council #22 summary updated.
- **Failed:** -
- **Next:** Implement ADR-22 (corp rfp-index + rfp_entries table + grouped corp retrieve). .sandbox/ review (Rob). v2/v3 _outputs/ per-note quality audit (01_Product_Docs only).

## 2026-03-27 vault rebuild (Council Decision #20)

- **Did:** Re-extracted 216 vault notes via CKE batch (gemini-3.1-pro-preview, deep mode). Ingested with quality-threshold 25, index rebuilt. Added `include_deprecated` filter to retrieve engine — deprecated notes excluded from all query paths. Added missing Compliance MOC. All 943 corp-by-os tests passing.
- **Errors:** 41 extraction errors, Haiku enrichment failures on all files (non-fatal, expected — returns empty JSON), `source_type=presentation` schema mismatch (pre-existing warn-only).
- **Next:** Monitor trust-status drift. Consider `source_type` enum expansion for presentation/workshop. Eval baseline updated.

## 2026-03-29 — refactor/centralize-hardcoded-paths

- **Did:** Zero-blast-radius refactor centralizing all MyWork/vault folder name strings into `src/corp/schema/folder_names.py`. Replaced hardcoded literals across 20+ files in 4 batches (4 commits). Added `INBOX`, `PROJECTS`, `TEMPLATES`, `RFP`, `SOURCE_LIBRARY`, `ADMIN`, `ARCHIVE`, `SYSTEM`, `STAGING`, `UNMATCHED`, `QUARANTINE`, `ALL_MYWORK_FOLDERS`, `SCAN_SKIP_FOLDERS` constants. Final grep confirms zero hardcoded folder literals remain in `src/corp/` outside the canonical module.
- **Gotcha:** Ruff pre-commit hook reformats import blocks in-place, causing "unstaged files" conflicts. Fix: always re-stage (git add) the modified file after a ruff-failed commit, then recommit. Happened 4× during this session.
- **Tests:** 2412 passed, 6 skipped throughout all batches (no regressions).
- **Next:** Step 5 (YAML config annotation), Step 6 (test assertion literals), merge to main.

## 2026-03-29 — fix/stale-docs-post-consolidation

- **Did:** Cleaned up all stale references from the 6-package → unified `src/corp/` consolidation. Tier 1: fixed `run-all-tests.ps1` (6-package loop → single `pytest tests/`) and `dev-check.ps1` (`packages/` → `src/`). Tier 2: rewrote README.md for unified layout, updated MASTER_HANDOFF.md (council count 22→23, gotcha count 37→41), fixed ADR-14 config path, updated 20 verify: paths in `~/.claude/skills/gotchas/gotchas.md`. Tier 3: fixed `.env.example` (stale CKE_PATH comment), fixed `.gitignore` (`packages/cke/_outputs/` → `data/_outputs/`), moved 3 phase reports from `docs/` to `.ecosystem/archive/`, removed empty `docs/`, created `CHANGELOG.md` with 1.0.0 consolidation summary.
- **Commits:** `453a0e3` (Tier 1), `39b95cb` (Tier 2), `7350265` (Tier 3), merged to main.
- **Failed:** -
- **Next:** Step 5 (YAML config annotation), Step 6 (test assertion literals), merge `refactor/centralize-hardcoded-paths` to main.

## 2026-03-29 — Council #24: MyWork Knowledge Architecture

- **Did:** Implemented Council #24 binding decisions. Rewrote `folder_names.py` (7 canonical folders + `.corp`). Removed TEMPLATES/SOURCE_LIBRARY/RFP/SYSTEM constants; added WORKFLOWS/REFERENCE/COMPLIANCE/CORP_INFRA + subfolder constants. Updated 17 source files (classifier routing, overnight scopes, integrity checks, path flattening SYSTEM/.corp/X → .corp/X). Updated all test files. Added 16 missing client aliases. Restructured MyWork on disk: created 90_Archive + .corp, moved 9 stale projects to archive, migrated pipeline infra from 90_System to .corp, deleted empty 40_Media and 90_System, merged legacy subdirs in 20_Workflows and 30_Reference.
- **Tests:** 2412 passed, 6 skipped (no regressions across all steps).
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).

## 2026-03-30 — refactor/align-with-playbook

- **Did:** Eliminated `.ecosystem/`. Moved: `MASTER_HANDOFF.md` → `docs/HANDOFF.md`, `archive/` (32 files) → `docs/archive/`, `council_transcripts/` (25 files) → `docs/decisions/transcripts/`, root `decisions/` (25 ADRs + README) → `docs/decisions/`. Updated all active references in `CLAUDE.md`, `update_handoff.py`, `extract_training_data.py`, `quarantine_fragments.py`, `tag_legacy_notes.py`, `docs/decisions/README.md`, `scripts/archive/*.py`. Updated `.gitignore` (`.ecosystem/rebuild_staging/` → `docs/staging/`). One convention, universally applied.
- **Failed:** Nothing.
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).

## 2026-03-30 — fix/stale-package-references

- **Did:** Purged all stale old-package name references following the 6→1 consolidation. 4 commits: (1) fixed 3 broken runtime paths in `cke_client.py`, `cke_invoker.py`, `extract_training_data.py`; (2) renamed agent keys in `agents.yaml`/`workflows.yaml` to CLI names (com, cpe, rfp); (3) updated `CLAUDE.md` source layout and CLI table; (4) updated docstrings in ~25 src/ files. Preserved intentionally: `%LOCALAPPDATA%/corp-by-os/` paths, `source_tool`/`generated_by` DB values, 3 excluded files. 20 remaining grep hits all confirmed intentional.
- **Failed:** Nothing — 2495 tests passed.
- **Next:** Merge fix/stale-package-references → main.

## 2026-03-30 — chore/todo-audit-cleanup

- **Did:** Full TODO/FIXME/HACK audit across all repo files. Found zero actual comment markers anywhere in the codebase. All 10 hits were false positives: (1) `TaskStatus.TODO` enum values in `models.py`/`task_manager.py`/tests — legitimate code; (2) English noun "hacks" (e.g., "sys.path hacks") in frozen `docs/archive/` and `docs/decisions/transcripts/` — accurate technical prose; (3) "XXXX" substring in a template filename embedded in JSON data/fixture files. No docs needed editing. Added `todo-tree.filtering.excludeGlobs` to `corp-monorepo.code-workspace` — excludes `docs/archive/`, `docs/decisions/`, `*.json`, `JOURNAL.md`, `CHANGELOG.md`, `.venv`, `__pycache__`, `models/`, `data/`, `eval/`. Also added `todo-tree.general.tags` and `defaultHighlight` for explicit tag config. Merged to main.
- **Failed:** Nothing.
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).
