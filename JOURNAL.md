# Development Journal

Append-only log. 3 lines per session. Never edit old entries.
Claude Code: read last 5 entries before starting work.

---

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