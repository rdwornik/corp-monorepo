# Changelog — corp-by-os

## [0.3.0] — 2026-03-25

- Monorepo migration (from standalone repo)
- 900 tests passing, 1 skipped
- Unified retrieval engine: prep decks, RFP answers, discovery with confidence ranking
- Intelligent ingest pipeline: content registry + LLM classifier + staged finalization
- Overnight batch extraction orchestrator with preflight, dedup, and safety guards
- OneDrive cleanup: scan → classify → propose → execute with deletion guards
- System doctor: vault, index, ops.db, content_registry, routing_map integrity checks
- Freshness tracking: source-tracking vault note staleness scanner
- Ops database: asset tracking, ingest events, registry suggestions with undo support
- Two-stage intent routing: keyword match → Gemini Flash fallback
- Interactive chat with vault context
- SQLite FTS5 search with BM25 ranking and trust_level metadata
- PRAGMA foreign_keys enabled on overnight_state.db
- Exception chain preservation with `raise from`

## [0.2.0] — 2026-02-01

- Core CLI: project, query, index, vault, template, task commands
- Vault I/O with zone-based mutability
- Index builder with FTS5 search
- Workflow engine with YAML-defined workflows

## [0.1.0] — 2025-11-01

- Initial project structure
- Click CLI skeleton
- Basic project resolver and config
