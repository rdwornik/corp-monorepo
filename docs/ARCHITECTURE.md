# Architecture Reference -- Corporate OS

> Living document. Updated after structural changes.
> Last updated: 2026-03-30 (dependency layers clarified)

## System Overview

> **Visual diagrams** live in `docs/diagrams/`. Open the `.svg` files directly in VS Code for rendered architecture views (system context, module map, pipeline flow).

Corporate OS is a knowledge management system for Blue Yonder presales. It ingests
files from a MyWork folder hierarchy, extracts structured knowledge via LLM (Gemini/Claude),
stores results as Obsidian vault notes with YAML frontmatter, and serves queries
through a full-text search index. Five CLIs (`corp`, `corp-meta`, `cke`, `cpe`, `com`)
expose all operations.

→ System context diagram: `docs/diagrams/system-context.svg`

## Source Layout

```
src/corp/
  schema/          Taxonomy, models, validation, path config (foundation)
  extractor/       CKE -- knowledge extraction engine (core)
  extraction/      Extraction orchestration: scan, route, emit manifests (foundation)
  ingest/          File routing, classification, dedup, inbox (orchestration)
  ops/             Operational DB facade, content registry, file registry (core)
  retrieve/        Unified retrieval engine, client prep, RFP retrieval (core)
  cleanup/         MyWork file scanner, classifier, proposer, executor (core)
  overnight/       Batch extraction pipeline, state tracking, monitor (core)
  project/         CPE -- project scanning, extraction, rendering (core)
  opportunity/     COM -- opportunity lifecycle, folder management (core)
  rfp/             RFP agent: answer selection, anonymization, Excel/Word (core)
  cli/             Click commands for all operations (interface)
  (root-level)     config, models, vault_io, index_builder, query_engine,
                   intent_router, workflow_engine, chat, built_in_actions,
                   sandbox, audit, freshness_scanner, integrity, task/template mgr
```

## Module Map

### Root-Level Modules

| Module | Responsibility | Key exports |
|--------|---------------|-------------|
| `models.py` | Dataclasses for all domain objects | VaultZone, ProjectInfo, Workflow, Task, IndexStats |
| `config.py` | Frozen AppConfig from .env + agents.yaml | AppConfig, get_config() |
| `vault_io.py` | Single vault writer -- all vault I/O goes here | list_projects(), read_project_info(), write_note() |
| `index_builder.py` | Rebuilds SQLite FTS5 index from vault | rebuild_index(), update_project(), get_index_stats() |
| `query_engine.py` | Queries the FTS5 index (facts, projects, analytics) | search_facts(), search_projects(), get_analytics() |
| `intent_router.py` | Two-stage routing: keywords then LLM | Intent, route() |
| `llm_router.py` | Gemini Flash for intent classification fallback | classify_intent() |
| `workflow_engine.py` | Executes workflow YAML definitions | load_workflows(), execute_workflow() |
| `chat.py` | Interactive Rich terminal chat loop | chat_loop() |
| `built_in_actions.py` | Re-export shim for actions/ package | get_action (via corp.actions) |
| `actions/` | Domain-split action handlers (12 modules) | register_action(), get_action(), ACTION_REGISTRY |
| `routing_types.py` | Shared types for intent/LLM routing | Intent |
| `project_resolver.py` | Fuzzy project name -> concrete paths | resolve_project() |
| `task_manager.py` | Task CRUD via Obsidian vault notes | add_task(), list_tasks(), complete_task() |
| `template_manager.py` | Template registry in 30_Templates/ | scan_templates(), select_template() |
| `sandbox.py` | Isolated pipeline environment for testing | SandboxManager.context() |
| `audit.py` | Read-only MyWork audit + Gemini analysis | run_audit() |
| `freshness_scanner.py` | Detects stale/orphaned vault notes vs sources | scan_vault_freshness() |
| `integrity.py` | Cross-system consistency checks | check_all() |
| `test_pipeline.py` | End-to-end smoke test with sandbox isolation | run_pipeline_test() |

### schema/ -- Taxonomy & Validation

| Module | Responsibility |
|--------|---------------|
| `models.py` | NoteFrontmatter (Pydantic), enums (DocumentType, SourceType, Layer, etc.) |
| `overlays.py` | Pydantic overlay models (Architecture, Security, Commercial, RFP, Meeting) |
| `config.py` | Centralized path resolution: ENV > paths.toml > defaults |
| `pipeline_config.py` | Frozen PipelineConfig dataclass with .production() / .sandbox() |
| `folder_names.py` | MyWork folder name constants (PROJECTS, ARCHIVE, WORKFLOWS, etc.) |
| `normalize.py` | Taxonomy term normalization (products, topics, domains) |
| `validate.py` | Frontmatter validation against taxonomy |
| `products.py` | Product name aliases and mappings |
| `utils.py` | Shared schema utilities |
| `cli.py` | `corp-meta` CLI: validate, normalize, report |

### extractor/ -- CKE (Knowledge Extraction Engine)

| Module | Responsibility |
|--------|---------------|
| `extract.py` | Core extraction: Gemini API calls, prompt building, JSON parsing (1184 LOC) |
| `strategies/` | ExtractionStrategy ABC + PDF/PPTX/Text strategy classes for extract_from_text() |
| `batch.py` | Manifest-driven sequential extraction with resume |
| `batch_api.py` | Google Batch API integration for bulk extraction |
| `tier_router.py` | Cost-optimized routing: LOCAL / TEXT_AI / MULTIMODAL tiers |
| `post_process.py` | Result normalization via corp.schema, unknown term logging |
| `config_loader.py` | Cached YAML config loader with dot-notation access |
| `doc_type_classifier.py` | Classifies documents by type for extraction routing |
| `deep_prompt.py` | Extended extraction prompts for complex documents |
| `taxonomy_prompt.py` | Builds taxonomy context for extraction prompts |
| `text_extract.py` | Local text extraction (PDF, DOCX, PPTX, XLSX, etc.) |
| `manifest.py` | Extraction manifest model (FileStatus, ManifestEntry) |
| `inventory.py` | Source file discovery and metadata |
| `scan.py` | Directory scanning for extractable files |
| `correlate.py` | Cross-file correlation (duplicate detection) |
| `correlate_sessions.py` | Session-level correlation |
| `merge_session.py` | Merge multiple extraction sessions |
| `synthesize.py` | Synthesize extraction results |
| `reextract.py` | Re-extraction of previously processed files |
| `freshness.py` | Source freshness tracking for extractions |
| `compress.py` | Output compression utilities |
| `polarity.py` | Sentiment/polarity analysis |
| `hybrid_loader.py` | Multi-format file loading |
| `transcript.py` | Audio/video transcript parsing |
| `fact_validation.py` | Extracted fact quality validation |
| `providers/base.py` | ExtractionProvider ABC (Strategy pattern) |
| `providers/anthropic_provider.py` | Claude Haiku/Sonnet provider |
| `providers/gemini_provider.py` | Gemini provider (primary) |
| `frames/sampler.py` | Video frame sampling for multimodal extraction |
| `frames/extractor.py` | Frame-level feature extraction |
| `slides/renderer.py` | PPTX slide rendering |
| `slides/pdf_converter.py` | PDF-to-image conversion for multimodal |
| `scripts/run.py` | `cke` CLI entry point |

### extraction/ -- Extraction Orchestration

| Module | Responsibility |
|--------|---------------|
| `scanner.py` | Scan folders for files to extract |
| `folder_policy.py` | Per-folder extraction policy (skip, extract, recurse) |
| `routing.py` | Route files to extraction destinations |
| `manifest_emitter.py` | Build extraction manifests from scan results |
| `contract.py` | Extraction contract definitions |
| `vault_writer.py` | Write extraction results to vault |

### ingest/ -- File Routing Pipeline

| Module | Responsibility |
|--------|---------------|
| `router.py` | Core pipeline: detect -> match -> route -> record -> move -> extract (893 LOC) |
| `inbox.py` | Interactive Rich UI for 00_Inbox routing (1161 LOC) |
| `classifier.py` | TF-IDF + regex file classifier |
| `llm_classifier.py` | Gemini-based classification for quarantined files |
| `renamer.py` | Naming convention enforcement ({YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext}) |
| `naming_config.py` | Type codes (19) and client aliases (15) from naming_config.yaml |
| `dedup.py` | MinHash near-duplicate detection (content_signatures table) |
| `light_scan.py` | Fast file metadata scan (size, mtime, extension) |
| `extractions.py` | Ingest CKE output into vault notes |

### ops/ -- Operational Database

| Module | Responsibility |
|--------|---------------|
| `database.py` | OpsDB class: assets, packages, events, routing feedback (705 LOC) |
| `registry.py` | ContentRegistry: YAML-driven file routing (series -> client -> rules) |
| `file_registry.py` | Content-hash-based file identity tracking |

### Other Modules

| Package | Modules | Responsibility |
|---------|---------|---------------|
| `retrieve/` | engine.py, prep.py, rfp.py | FTS5 retrieval, client prep, RFP context |
| `cleanup/` | scanner, classifier, proposer, executor, disk | MyWork file hygiene |
| `overnight/` | state, preflight, cke_client, classifier, monitor, dedup, safety | Batch extraction pipeline |
| `project/` | cli, config, classifier, extractors, manifest, renderer, models | CPE project scanning/extraction |
| `opportunity/` | cli, config, folder_manager, excel_manager, llm_client, chat, models | COM opportunity lifecycle |
| `rfp/` | llm_router, answer_selector, rfp_excel_agent, rfp_answer_word, vault_adapter, anonymization/ | RFP answering pipeline |
| `cli/` | 18 files | All Click command groups (see CLI Reference below) |

## Dependency Layers

The codebase enforces a 4-layer dependency model via Tach (`tach.toml`).
Modules in higher layers may import from lower layers; the reverse is forbidden
and blocked by pre-commit and CI (`tach check`).

```
interface > orchestration > core > foundation
```

### Layer Assignments

**interface** — user-facing entry points:
`cli/`, `chat.py`, `sandbox.py`, `test_pipeline.py`

**orchestration** — workflow coordination, multi-service operations:
`actions/`, `workflow_engine`, `built_in_actions`, `ingest/`, `query_engine`,
`index_builder`, `task_manager`, `template_manager`

**core** — domain services and business logic:
`extractor/`, `ops/`, `retrieve/`, `intent_router`, `llm_router`, `project/`,
`opportunity/`, `rfp/`, `overnight/`, `vault_io`, `config`, `audit`, `integrity`,
`freshness_scanner`, `cleanup/`, `project_resolver`

**foundation** — shared types, taxonomy, base config:
`schema/` (utility†), `models`, `routing_types` (utility†), `extraction/`

† Utility modules are exempt from layer ordering — they may be imported from any layer.
See `tach.toml` for the canonical module-to-layer mapping.

### Runtime vs Static Depth

Runtime call chains can reach 9 levels deep via lazy imports
(`cli.misc` → `chat` → `workflow_engine` → `built_in_actions` → `task_manager` → `intent_router`).
This is **expected and accepted** — every link uses lazy imports, so static module-level
depth stays within the 4-layer model. Tach enforces static structure only; runtime depth
is not a violation.

**No import cycle violations.** Former `llm_router` ↔ `intent_router`
cycle was resolved by extracting `Intent` to `routing_types.py`.

→ Module map diagram: `docs/diagrams/container-module.svg`

## Database Schemas

### ops.db

Location: `%LOCALAPPDATA%/corp-by-os/ops.db` (WAL mode, foreign keys ON)

| Table | Key Columns | Writer | Purpose |
|-------|------------|--------|---------|
| **assets** | path, content_hash, status, folder_l1, routed_to | ingest/router | File inventory + routing state |
| **packages** | folder_name, source_path, destination_path, status | ingest/router | Folder-level groupings |
| **ingest_events** | asset_id, action, method, confidence, timestamp | ingest/router | Immutable audit trail |
| **files** | content_hash (UNIQUE), current_path, size_bytes | ops/file_registry | Content-hash identity (survives renames) |
| **extractions** | file_id, model, extracted_at, cost_cents | ops/file_registry | Extraction history per model |
| **routing_feedback** | filename, classifier_destination, final_destination, was_overridden | ops/database | Manual routing review decisions |
| **content_signatures** | file_path, hashvalues (BLOB), num_perm | ingest/dedup | MinHash near-duplicate detection |
| **registry_suggestions** | pattern, proposed_series, evidence, status | ops/database | Auto-discovered routing patterns |

### index.db

Location: `%LOCALAPPDATA%/corp-by-os/index.db` (WAL mode)

| Table | Key Columns | Writer | Purpose |
|-------|------------|--------|---------|
| **projects** | project_id (PK), client, status, products, topics, domains | index_builder | Project metadata aggregation |
| **facts** | project_id (FK), fact, source, topics, products | index_builder | Project fact database |
| **facts_fts** | fact, source_title, topics, project_id (FTS5) | trigger on facts | Full-text search on facts |
| **notes** | project_id, client, title, type, topics, products, note_path, rfp_visible | index_builder | CKE vault note index (1,972+ notes) |
| **notes_fts** | title, topics, products, domains, people, client, project_id, doc_type (FTS5) | trigger on notes | Full-text search on notes |
| **meta** | key, value | index_builder | Rebuild timestamps and stats |

FTS sync maintained by SQLite triggers (notes_ai/notes_ad, facts_ai/facts_ad).

### overnight_state.db

Location: `%LOCALAPPDATA%/corp-by-os/overnight_state.db`

| Table | Key Columns | Writer | Purpose |
|-------|------------|--------|---------|
| **runs** | run_id (PK), scope, budget_limit, status, actual_cost | overnight/state | Extraction run tracking |
| **files** | run_id (FK), path, file_hash, status, tier, retry_count | overnight/state | Per-file processing state |
| **batches** | batch_id (PK), run_id (FK), status, file_count | overnight/state | Batch API job tracking |

## Configuration Architecture

| Source | Format | Loader | Purpose |
|--------|--------|--------|---------|
| `config/paths.toml` | TOML | schema.config.get_path() | Centralized path resolution (ENV > TOML > defaults) |
| `config/agents.yaml` | YAML | config._load_agents() | Agent registry (5 agents) |
| `config/workflows.yaml` | YAML | workflow_engine.load_workflows() | Workflow step definitions |
| `config/content_registry.yaml` | YAML | ops.registry.ContentRegistry() | File pattern -> destination routing |
| `config/naming_config.yaml` | YAML | ingest.naming_config | 19 type codes, 15 client aliases |
| `config/extractor/*.yaml` | YAML | extractor.config_loader.get() | LLM settings, categories, prompts, filters |
| `config/project/default.yaml` | YAML | project.config.get_settings() | CPE extraction settings |
| `config/opportunity/default.yaml` | YAML | opportunity.config.load_config() | COM workflow settings |
| `config/rfp/anonymization.yaml` | YAML | rfp.anonymization.config | Blocklist and session settings |
| `config/rfp/product_profiles/` | YAML | rfp.kb_builder | Product capability matrices |
| `~/Documents/.secrets/.env` | dotenv | python-dotenv | API keys (GEMINI_API_KEY, etc.) |

**Resolution order:** Environment variable > config file > Path.home() default.

**Key config classes:**
- `PipelineConfig` (frozen dataclass) -- passed via Click `ctx.obj["config"]`, computes derived DB paths
- `AppConfig` (frozen, lru_cached) -- vault/mywork/project paths + agent registry

## CLI Reference

### corp (main CLI -- 40+ commands)

| Command | Handler | What it does |
|---------|---------|-------------|
| `corp ingest [PATH]` | cli/ingest.py | Route incoming files via content registry |
| `corp ingest-inbox` | cli/ingest.py | Interactive routing from 00_Inbox |
| `corp finalize [--approve-all]` | cli/ingest.py | Review and approve staged files |
| `corp classify` | cli/ingest.py | Classify quarantined files with Gemini |
| `corp freshness` | cli/ingest.py | Check vault note freshness vs sources |
| `corp ingest-extractions <path>` | cli/ingest.py | Ingest CKE output into vault |
| `corp extract <folder>` | cli/extract.py | Extract knowledge via CKE |
| `corp overnight [--scope] [--budget]` | cli/overnight.py | Batch extraction pipeline |
| `corp index rebuild [--project]` | cli/index.py | Rebuild FTS5 index |
| `corp index stats` | cli/index.py | Show index statistics |
| `corp query "terms"` | cli/query.py | Full-text search on facts |
| `corp retrieve "query"` | cli/retrieve.py | Knowledge base retrieval |
| `corp prep <client>` | cli/retrieve.py | Prepare client context |
| `corp rfp answer "question"` | cli/rfp.py | Draft RFP answer from knowledge base |
| `corp project list/show/open` | cli/project.py | Project management |
| `corp vault validate` | cli/vault.py | Validate vault structure |
| `corp analytics report` | cli/analytics.py | Cross-project dashboard |
| `corp analytics products/timeline/clients/overlap/compare/recent` | cli/analytics.py | Analytical queries |
| `corp dedup-report` | cli/analytics.py | Duplicate detection report |
| `corp cleanup-scan` | cli/cleanup.py | Scan MyWork for misplaced files |
| `corp apply-moves <file>` | cli/cleanup.py | Execute approved file moves |
| `corp audit` | cli/cleanup.py | Full MyWork audit with Gemini |
| `corp task add/list/done` | cli/task.py | Task management |
| `corp template list/scan/select` | cli/template.py | Template registry |
| `corp run <workflow>` | cli/workflow.py | Execute a workflow |
| `corp doctor` | cli/system.py | System integrity check |
| `corp chat` | cli/misc.py | Interactive chat mode |
| `corp test-pipeline` | cli/misc.py | End-to-end smoke test |

### Secondary CLIs

| CLI | Entry point | Commands |
|-----|-------------|----------|
| `corp-meta` | schema.cli:main | validate, normalize, report |
| `cke` | extractor.scripts.run:cli | Batch knowledge extraction |
| `cpe` | project.cli:cli | scan, extract, extract-cke, render, show, run |
| `com` | opportunity.cli:cli | new, list, show, prep-deck, chat |

## Data Flow

```
1. File arrives in MyWork/00_Inbox
       |
2. light_scan() reads metadata (size, mtime, extension)
       |
3. ContentRegistry.match_file() routes by pattern (series > client > rules)
       |  (confidence scored: 0.75-0.95)
       |
4. renamer applies naming convention: {YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext}
       |
5. router moves file to destination project folder
       |  (ops.db: asset + ingest_event logged BEFORE move)
       |
6. CKE extracts knowledge (tier_router selects: LOCAL / TEXT_AI / MULTIMODAL)
       |  Gemini API call -> JSON response -> post_process -> normalize
       |
7. vault_writer creates .md note with YAML frontmatter
       |  (source_hash tracked for freshness)
       |
8. index_builder adds note to FTS5 index (notes + notes_fts tables)
       |
9. query_engine / retrieve/ reads from index.db
       |  FTS5 BM25 ranking + metadata filters + vault content loading
```

→ Pipeline diagram: `docs/diagrams/magistrala-pipeline.svg`

## Design Patterns

| Pattern | Where | Quality | Notes |
|---------|-------|---------|-------|
| **Strategy** | extractor/providers/ (ABC + Anthropic/Gemini) | Excellent | Clean interface, easy to add providers |
| **Strategy** | extractor/strategies/ (ABC + PDF/PPTX/Text) | Excellent | extract_from_text() dispatches to 3 strategy classes |
| **Strategy** | extractor/tier_router.py (LOCAL/TEXT_AI/MULTIMODAL) | Good | Cost-optimized routing per file type |
| **Pipeline** | ingest/router.py (detect->match->route->record->move->extract) | Good | Linear stages, crash-safe recording |
| **Facade** | ops/database.py (OpsDB delegates to 5 repos) | Excellent | Split into AssetRepo, PackageRepo, EventRepo, RoutingRepo, SuggestionRepo |
| **Facade** | ops/registry.py (ContentRegistry) | Excellent | Clean match_file()/match_folder() interface |
| **Factory** | schema/pipeline_config.py (.production()/.sandbox()) | Good | Frozen config, test isolation |
| **Repository** | ops/file_registry.py (content-hash identity) | Good | Focused, single entity |
| **Repository** | overnight/state.py (OvernightState) | Good | Separate DB, clear responsibility |
| **Router** | intent_router.py (keywords -> LLM fallback) | Good | Two-stage, deterministic first |
| **Immutable audit** | ingest_events table (reversible flag, never deleted) | Excellent | Full traceability |

## Architecture Assessment

### What Works Well

- **Clean layering**: foundation → core → orchestration → interface (enforced by Tach)
- **Database isolation**: ops.db, index.db, overnight_state.db in %LOCALAPPDATA% (not OneDrive)
- **Content-hash identity**: files survive renames; extraction history tied to content, not path
- **FTS5 triggers**: notes_fts and facts_fts stay in sync automatically
- **Provider abstraction**: Adding a new LLM is one file implementing ExtractionProvider
- **Frozen configs**: PipelineConfig and AppConfig are immutable after creation
- **Audit trail**: Every ingest action logged with timestamp, confidence, reversibility

### Violations & Technical Debt

| Issue | Severity | Location | Status | Description |
|-------|----------|----------|--------|-------------|
| ~~Circular import~~ | ~~Medium~~ | ~~llm_router <-> intent_router~~ | **RESOLVED** | Extracted Intent to routing_types.py |
| ~~God class~~ | ~~Medium~~ | ~~ops/database.py (705 LOC)~~ | **RESOLVED** | Split into 5 per-entity repositories; OpsDB is facade |
| ~~God module~~ | ~~Medium~~ | ~~built_in_actions.py (967 LOC)~~ | **RESOLVED** | Split into actions/ package with 12 domain modules |
| ~~Long functions~~ | ~~Medium~~ | ~~extractor/extract.py (203-line func)~~ | **RESOLVED** | extract_from_text() → strategy dispatcher (1589→1184 LOC) |
| ~~Mixed concerns~~ | ~~Low~~ | ~~ingest/inbox.py (1161 LOC)~~ | **RESOLVED** | Business logic extracted to inbox_ops.py |
| **Deep CLI runtime chain** | Low | cli → chat → workflow → actions → tasks | **ACCEPTED** | Runtime depth 9 via lazy imports; static depth stays within 4-layer model. Each link is a deliberate boundary. |

### Accepted Limitations

| Item | Rationale |
|------|-----------|
| synthesize.py writes to _outputs/ staging | Staging ≠ vault. Invariant "extractor doesn't write vault" is preserved. |
| rfp_feedback.py non-atomic ID | Single-threaded CLI. Race condition impossible in current usage. |
| schema/cli.py missing -> None annotations | Cosmetic. Click commands return None by convention. |

### Key Invariants

1. **corp (ingest/) is SOLE vault writer** -- CKE produces JSON, ingest writes .md
2. **CKE (extractor/) is PURE extraction** -- no vault writes, no database writes
3. **Forward slashes everywhere** in databases and stored paths
4. **API keys in env vars** -- loaded from ~/Documents/.secrets/.env, never in config
5. **OneDrive exclusion** -- cleanup/audit NEVER touch "OneDrive - Blue Yonder" paths
6. **WAL mode** on all SQLite databases for crash safety
7. **Record-before-move** -- ingest logs to ops.db BEFORE filesystem operations
