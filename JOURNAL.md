# Development Journal

Append-only log. 3 lines per session. Never edit old entries.
Claude Code: read last 5 entries before starting work.

---


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
