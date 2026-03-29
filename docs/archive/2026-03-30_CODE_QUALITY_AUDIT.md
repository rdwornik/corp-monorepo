# Code Quality Audit — 2026-03-30

## Executive Summary

| Metric | Value |
|--------|-------|
| Total source files reviewed | 167 |
| Total source lines | 40,359 |
| Critical issues | 9 |
| High issues | 16 |
| Medium issues | 18 |
| Low issues | 12 |
| **Security vulnerabilities** | **0** |

**Overall assessment:** The codebase is **structurally sound** with strong security practices, no dead code, and excellent type hint coverage in critical modules. The main debt areas are: (1) error handling patterns that silently swallow failures in important paths, (2) complexity hotspots in extraction/ingest functions, (3) inconsistent config access patterns, and (4) 76% of modules lacking unit tests.

---

## Critical Issues (fix before new features)

| # | File:Line | Issue | Category | Suggested Fix |
|---|-----------|-------|----------|---------------|
| 1 | built_in_actions.py:392 | `except Exception: pass` silently swallows facts.yaml parse errors in project brief generation | Error handling | Catch `yaml.YAMLError`, log warning |
| 2 | built_in_actions.py:921 | `except Exception: pass` in project resolution — falls back to slugified name silently | Error handling | Catch specific errors, log fallback |
| 3 | built_in_actions.py:944 | `except Exception: pass` in OneDrive path resolution — returns None silently | Error handling | Catch `OSError`, log warning |
| 4 | ingest/router.py:307 | Broad Exception catch in extraction failure — swallowed in critical asset routing path | Error handling | Catch specific errors; re-raise on non-recoverable |
| 5 | ingest/router.py:567 | Broad Exception catch in package extraction — can silently poison subsequent processing | Error handling | Catch specific errors; surface to caller |
| 6 | extractor/extract.py:460 | `extract_knowledge()` is 235 lines — mixes model selection, API calls, response parsing | Complexity | Split into `_select_model()`, `_prepare_request()`, `_call_api()`, `_parse_response()` |
| 7 | ingest/inbox.py:827 | `process_file()` is 218 lines with 9 params — state machine as `while True` with 20+ branches | Complexity | Extract state pattern; separate interactive UI from business logic |
| 8 | ingest/router.py:374 | `ingest_folder()` is 216 lines with 8 params — mixes validation, routing, orchestration | Complexity | Split into `_validate_folder()`, `_route_files()`, `_orchestrate_ingest()` |
| 9 | scripts/eval.py:32-36 | Broken `packages/` paths — script will crash at runtime | Stale refs | Update to `src/corp/` layout |

---

## High Issues (fix within 2 weeks)

| # | File:Line | Issue | Category | Suggested Fix |
|---|-----------|-------|----------|---------------|
| 10 | integrity.py:102,141,167,290,364 | 5x bare `Exception` catches in system integrity checks | Error handling | Catch `yaml.YAMLError`, `sqlite3.Error`, `OSError` specifically |
| 11 | vault_io.py:205 | `except Exception: return None` in `_read_project_info_from_path` — callers assume success | Error handling | Catch `(OSError, yaml.YAMLError)`, log warning |
| 12 | vault_io.py:452,527 | Broad Exception in schema validation — YAML/file errors swallowed | Error handling | Catch `(FileNotFoundError, yaml.YAMLError)` |
| 13 | task_manager.py:275 | `except Exception: return None` — malformed tasks disappear silently | Error handling | Log warning, don't silently drop |
| 14 | llm_router.py:212 | Broad Exception in Gemini API call — masks timeout, auth, parse errors | Error handling | Catch API-specific exceptions |
| 15 | index_builder.py:416,441,501,554,563 | 5x silent swallow in index metadata reads — index may be incomplete | Error handling | Log skipped entries at WARNING level |
| 16 | retrieve/engine.py:32 | `except Exception: return [client]` — conflates ImportError with other failures | Error handling | Catch `ImportError` only |
| 17 | extractor/extract.py:795 | `_try_pdf_multimodal()` is 206 lines | Complexity | Extract PDF conversion and API call logic |
| 18 | extractor/extract.py:1167 | `extract_from_text()` is 205 lines | Complexity | Extract prompt building and response parsing |
| 19 | ingest/inbox.py:222 | `_log_ingest_event()` has 9 parameters | Complexity | Use an EventLog dataclass |
| 20 | ingest/inbox.py:615 | `_undo_event()` is 94 lines | Complexity | Split undo logic by event type |
| 21 | cli/ingest.py:216 | `ingest_inbox_command()` has 10 CLI params (worst in codebase) | Complexity | Use `@click.pass_context` + subcommands |
| 22 | scripts/enrich_training_data.py:28,75 | Broken `packages/` paths | Stale refs | Update to `src/corp/` layout |
| 23 | scripts/eval_classifier.py:21 | Broken `packages/` sys.path insert | Stale refs | Update to `src/corp/extractor` |
| 24 | scripts/create_classifier_split.py:19 | Broken `packages/` fixture path | Stale refs | Update to `tests/fixtures/` |
| 25 | cli.py:227 | Hardcoded personal username in help text output | Hardcoded | Use config variable or relative path |

---

## Medium Issues (fix opportunistically)

| # | File:Line | Issue | Category | Suggested Fix |
|---|-----------|-------|----------|---------------|
| 26 | built_in_actions.py:507 | Broad Exception in metadata update — logged but not re-raised | Error handling | Catch `(FileNotFoundError, PermissionError, yaml.YAMLError)` |
| 27 | built_in_actions.py:544 | Broad Exception in archive metadata step | Error handling | Catch specific error types |
| 28 | intent_router.py:161,319,378 | 3x bare Exception in intent routing — degraded routing silently | Error handling | Catch specific types, log degradation |
| 29 | ops/database.py:198,644,659,677,698 | 5x broad Exception in ops.db — state may be inconsistent | Error handling | Catch `sqlite3.Error` specifically |
| 30 | schema/utils.py:64 | `except Exception: pass` in json-repair fallback | Error handling | Catch `(ImportError, ValueError)` |
| 31 | cleanup/classifier.py:127 | Broad Exception in file classification — may skip files | Error handling | Catch specific errors |
| 32 | opportunity/llm_client.py:173 | Bare Exception in Gemini API call | Error handling | Catch API-specific exceptions |
| 33 | extraction/vault_writer.py:28,41 | Broad Exception in trust_level extraction | Error handling | Catch `(FileNotFoundError, yaml.YAMLError)` |
| 34 | extractor/extract.py:1001 | `_try_pptx_pdf_multimodal()` is 166 lines | Complexity | Extract conversion + API steps |
| 35 | extractor/extract.py:1372 | `extract_pptx_multimodal()` is 164 lines | Complexity | Split into smaller steps |
| 36 | ingest/router.py:155 | `ingest_file()` is 160 lines | Complexity | Extract validation from orchestration |
| 37 | rfp/rfp_excel_agent.py:59 | `call_llm_with_retry()` missing all type hints | Type hints | Add return type + param annotations |
| 38 | Multiple files | 4 competing config access patterns across codebase | Consistency | Standardize on PipelineConfig |
| 39 | 16 library files | Mix of `print()` and `logging` in same module | Consistency | Use logging in library code, print only in CLI |
| 40 | 12 files | `os.path.join` mixed with `pathlib.Path` | Consistency | Standardize on pathlib for filesystem ops |
| 41 | scripts/archive_scan.py | Missing `__main__` guard — executes on import | Scripts | Add `if __name__ == "__main__":` |
| 42 | scripts/check_api_keys.py | Missing `__main__` guard | Scripts | Add guard |
| 43 | scripts/check_db.py | Missing `__main__` guard | Scripts | Add guard |

---

## Low Issues (nice to have)

| # | File:Line | Issue | Category | Suggested Fix |
|---|-----------|-------|----------|---------------|
| 44 | cli/system.py:57,143 | Broad Exception in diagnostic health checks | Error handling | Catch `(FileNotFoundError, yaml.YAMLError)` |
| 45 | ingest/extractions.py:65 | `except Exception: return {}` — acceptable fallback but too broad | Error handling | Catch `(yaml.YAMLError, OSError)` |
| 46 | cli/system.py:182,234 | Broad Exception in routing review commands | Error handling | Catch `sqlite3.DatabaseError` |
| 47 | overnight/cke_client.py:311 | Broad Exception in subprocess wrapper | Error handling | Catch `(FileNotFoundError, json.JSONDecodeError)` |
| 48 | overnight/classifier.py:106,246,288 | `.get(...) or ""` patterns without None checks | Error handling | Minor — graceful fallbacks |
| 49 | extractor/pdf_converter.py:116-117 | Hardcoded LibreOffice paths (Windows) | Hardcoded | Acceptable — fallback after `shutil.which()` |
| 50 | extractor/renderer.py:169-170 | Hardcoded LibreOffice paths (Windows) | Hardcoded | Acceptable — fallback after `shutil.which()` |
| 51 | Multiple | Hardcoded LLM model names (gemini-3-flash-preview, etc.) | Hardcoded | Acceptable — overridable via config |
| 52 | test_cross_package.py:13,44 | Old function names `test_corp_by_os_*` | Stale refs | Cosmetic — rename for clarity |
| 53 | 6 files | Delayed imports inside functions to avoid circular deps | Consistency | Document known circular dep chains |
| 54 | Multiple | Mixed return conventions (None vs raise vs empty collection) | Consistency | Document per-module convention |
| 55 | extractor/scan.py:10 | Example path `C:/Users/docs` in docstring | Hardcoded | Cosmetic — docstring only |

---

## Dead Code Candidates

| File | Function/Class | Evidence |
|------|---------------|---------|
| *(none found)* | — | All examined functions have callers in production code or tests |

**Assessment:** No actionable dead code detected. The consolidation was thorough — all functions in `src/corp/` are referenced somewhere in the codebase or test suite. No commented-out code blocks found.

---

## Stale References (old package names)

| File:Line | Old Reference | Should Be |
|-----------|--------------|-----------|
| scripts/eval.py:32 | `packages/corp-knowledge-extractor/tests/fixtures` | `tests/fixtures` |
| scripts/eval.py:35 | `packages/corp-knowledge-extractor/src` | (remove — already on path) |
| scripts/eval.py:36 | `packages/corp-os-meta` | (remove — already on path) |
| scripts/eval_classifier.py:21 | `packages/corp-knowledge-extractor/src` | (remove — already on path) |
| scripts/create_classifier_split.py:19 | `packages/corp-knowledge-extractor/tests/fixtures/` | `tests/fixtures/` |
| scripts/enrich_training_data.py:28 | `packages/corp-knowledge-extractor/tests/fixtures/` | `tests/fixtures/` |
| scripts/enrich_training_data.py:75 | `packages/corp-by-os/src` | (remove — already on path) |

**No stale references found in active source code** (`src/corp/`). All stale refs are in scripts only.

---

## Test Coverage Gaps

### Modules Without Any Test File (Critical Business Logic)

| # | Source Module | Path | Criticality |
|---|-------------|------|-------------|
| 1 | vault_writer | src/corp/extraction/vault_writer.py | **Critical** — sole vault writer per architecture rules |
| 2 | contract | src/corp/extraction/contract.py | **Critical** — extraction contract validation |
| 3 | routing | src/corp/extraction/routing.py | **Critical** — extraction routing logic |
| 4 | scanner | src/corp/extraction/scanner.py | High — extraction file scanning |
| 5 | folder_policy | src/corp/extraction/folder_policy.py | High — folder routing policy |
| 6 | manifest_emitter | src/corp/extraction/manifest_emitter.py | High — manifest generation |
| 7 | deep_prompt | src/corp/extractor/deep_prompt.py | High — core prompt engineering |
| 8 | doc_type_classifier | src/corp/extractor/doc_type_classifier.py | High — document classification |
| 9 | providers/* | src/corp/extractor/providers/*.py | High — LLM provider abstraction (6 files) |
| 10 | tier_router | src/corp/extractor/tier_router.py | High — extraction tier routing |
| 11 | anonymization/* | src/corp/rfp/anonymization/*.py | High — PII anonymization (3 files) |
| 12 | answer_selector | src/corp/rfp/answer_selector.py | High — RFP answer selection |
| 13 | vault_adapter | src/corp/rfp/vault_adapter.py | High — RFP vault integration |
| 14 | overnight/* | src/corp/overnight/*.py | Medium — overnight pipeline (7 files) |
| 15 | cleanup/* | src/corp/cleanup/*.py | Medium — cleanup pipeline (5 files) |

**Coverage summary:** 36/148 modules (24%) have dedicated test files. The remaining 112 modules (76%) have no unit tests. Many are covered indirectly by integration tests, but lack edge case and error path coverage.

---

## Scripts Assessment

| # | Script | Status | Action |
|---|--------|--------|--------|
| 1 | eval.py | **BROKEN** — references `packages/` | Fix paths or archive |
| 2 | eval_classifier.py | **BROKEN** — references `packages/` | Fix paths or archive |
| 3 | create_classifier_split.py | **BROKEN** — references `packages/` | Fix paths or archive |
| 4 | enrich_training_data.py | **BROKEN** — references `packages/` | Fix paths or archive |
| 5 | archive_scan.py | Missing `__main__` guard | Add guard |
| 6 | check_api_keys.py | Missing `__main__` guard | Add guard |
| 7 | check_db.py | Missing `__main__` guard | Add guard |
| 8 | extract_training_data.py | **OK** — functional | Keep |
| 9 | train_classifier.py | **OK** — functional | Keep |
| 10 | dev-check.ps1 | **OK** — dev workflow | Keep |
| 11 | run-all-tests.ps1 | **OK** — CI workflow | Keep |
| 12 | update_handoff.py | **OK** — session workflow | Keep |
| 13 | session-start.ps1 | **OK** — session workflow | Keep |
| 14 | ecosystem-snapshot.ps1 | **OK** — monitoring | Keep |
| 15 | phase1_archive_copy.py | One-time migration | Archive |
| 16 | phase2_presales_rename.py | One-time migration | Archive |
| 17 | migrate_client_names.py | One-time migration | Archive |
| 18 | vault_restructure.py | One-time migration | Archive |
| 19 | quarantine_fragments.py | One-time migration | Archive |
| 20 | tag_legacy_notes.py | One-time migration | Archive |
| 21 | sandbox_dedup_preview.py | Utility | Keep |
| 22 | sandbox_rename_preview.py | Utility | Keep |
| 23 | sandbox_report.py | Utility | Keep |
| 24 | create_cleanup_sample.py | Utility | Keep |
| 25 | eval_extraction.py | Training/eval | Keep (verify paths) |
| 26 | test_api_keys.py | Diagnostic | Keep |
| 27 | archive/* (4 files) | Already archived | No action |

---

## Complexity Hotspots (functions >50 lines)

### Top 10 by Size

| # | File | Function | Start Line | Lines | Recommendation |
|---|------|----------|-----------|-------|----------------|
| 1 | extractor/extract.py | `extract_knowledge()` | 460 | 235 | Split into model selection + request prep + API call + response parse |
| 2 | ingest/inbox.py | `process_file()` | 827 | 218 | Extract state pattern; separate UI from logic |
| 3 | ingest/router.py | `ingest_folder()` | 374 | 216 | Split validation / routing / orchestration |
| 4 | extractor/extract.py | `_try_pdf_multimodal()` | 795 | 206 | Extract PDF conversion step |
| 5 | extractor/extract.py | `extract_from_text()` | 1167 | 205 | Extract prompt building |
| 6 | extractor/extract.py | `extract_pptx_multimodal()` | 1372 | 164 | Split PPTX conversion from API call |
| 7 | extractor/extract.py | `_try_pptx_pdf_multimodal()` | 1001 | 166 | Extract conversion + call |
| 8 | ingest/router.py | `ingest_file()` | 155 | 160 | Separate validation from ingest |
| 9 | ingest/inbox.py | `_undo_event()` | 615 | 94 | Split by event type |
| 10 | ingest/router.py | `_run_extraction()` | 677 | 93 | Extract error handling |

### Functions with >5 Parameters

| File | Function | Line | Params |
|------|----------|------|--------|
| cli/ingest.py | `ingest_inbox_command()` | 216 | 10 |
| ingest/inbox.py | `process_file()` | 827 | 9 |
| ingest/inbox.py | `_log_ingest_event()` | 222 | 9 |
| ingest/router.py | `ingest_folder()` | 374 | 8 |
| ingest/router.py | `ingest_file()` | 155 | 7 |
| extractor/batch.py | `run_batch()` | (varies) | 7 |
| rfp/rfp_excel_agent.py | `process_worksheet()` | (varies) | 7 |

---

## Patterns to Standardize

### 1. Config Access (HIGH priority)
**Current state:** 4 competing patterns
| Pattern | Files Using It |
|---------|---------------|
| Direct `os.environ.get()` | ~22 files |
| `load_config()` function | ~16 files |
| `PipelineConfig` class | ~19 files |
| Direct `yaml.safe_load()` | ~39 files |

**Recommended standard:** `PipelineConfig` for structured config, `os.environ` only for secrets (API keys). Deprecate direct YAML loading in application code.

### 2. Logging vs Print (HIGH priority)
**Current state:** 30 files use `print()` (555 occurrences total), 16 files mix both patterns
| Where | Pattern | Status |
|-------|---------|--------|
| CLI output | `console.print()` (Rich) | Correct |
| Library code | `logger.info/warning/error` | Correct |
| Library code | `print()` | **Incorrect** — 16 files |

**Recommended standard:** `logging` in all library code (`src/corp/` non-CLI modules). `console.print()` in CLI commands only. Zero `print()` in library code.

### 3. Path Handling (MEDIUM priority)
**Current state:** 3 paradigms
| Pattern | Usage |
|---------|-------|
| `pathlib.Path` | 60+ files (dominant, correct) |
| Forward-slash strings | 27+ files (database/Obsidian paths — correct by design) |
| `os.path.join` | 12 files (legacy, mostly scripts) |

**Recommended standard:** `pathlib.Path` for all filesystem operations. Forward-slash strings only for database/Obsidian vault paths (by design — see gotchas). Migrate remaining `os.path.join` usage.

### 4. Error Return Conventions (MEDIUM priority)
**Current state:** No consistent convention
| Pattern | When Used |
|---------|-----------|
| Return `None` | Parsing, lookups |
| Raise exception | Validation, initialization |
| Return empty collection | Search operations |

**Recommended standard:** Document per-module: raise on programmer errors, return None/empty on user-input issues. Always log when returning None on unexpected failures.

---

## Security Assessment

**No critical or high-severity security issues found.**

| Category | Status |
|----------|--------|
| API key management | All keys from env vars only |
| SQL injection | All queries parameterized (`?` placeholders) |
| Subprocess safety | List args + `shlex.split()`, no `shell=True` in production |
| Deserialization | `yaml.safe_load()` only, no pickle/eval/exec |
| Path traversal | Click validates paths, `.resolve()` used |
| Secrets in logs | None found |

---

## Recommendations by Priority

### P0 — Fix before new features (1-2 days)
1. Fix 5 critical `except Exception: pass` instances (items #1-5)
2. Fix 4 broken scripts with `packages/` paths (items #9, 22-24)

### P1 — Fix within 2 weeks
3. Add specific exception types to 10 high-severity error handlers (items #10-16)
4. Add `__main__` guards to 3 scripts (items #41-43)
5. Archive 6 one-time migration scripts

### P2 — Fix opportunistically (next sprint)
6. Refactor `extract_knowledge()` (235 lines → 4 functions)
7. Refactor `process_file()` (218 lines → state pattern)
8. Refactor `ingest_folder()` (216 lines → 3 functions)
9. Standardize config access pattern
10. Replace `print()` with `logging` in 16 library files

### P3 — Strategic (next quarter)
11. Add unit tests for 15 critical untested modules (especially vault_writer, extraction pipeline, RFP anonymization)
12. Introduce custom exception hierarchy (`VaultIOError`, `ExtractionError`, `ConfigError`)
13. Standardize path handling — migrate remaining `os.path.join` to pathlib
14. Document error return conventions per module

---

*Generated by Claude Code quality audit — 2026-03-30*
*Reviewed: 167 files, 40,359 lines across src/corp/ and scripts/*
