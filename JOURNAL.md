# Development Journal

Append-only log. 3 lines per session. Never edit old entries.
Claude Code: read last 5 entries before starting work.

---

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
