# corp.ops -- Operational Database & Content Registry

## What this module does

Manages the operational database (ops.db) for asset tracking, ingest audit
trails, routing feedback, and content-hash file identity. Also provides the
ContentRegistry for YAML-driven file routing patterns.

## Key files

| File | What it does |
|------|-------------|
| database.py | OpsDB class: 8 tables (assets, packages, events, files, etc.) |
| registry.py | ContentRegistry: pattern matching (series > client > rules > fallback) |
| file_registry.py | Content-hash identity tracking (survives file renames) |

## Dependencies

- **Depends on:** corp.config, corp.schema
- **Used by:** corp.ingest, corp.cli.system, corp.integrity

## Data flow

Ingest actions -> OpsDB.upsert_asset() / log_event() -> ops.db
File patterns -> ContentRegistry.match_file() -> RegistryMatch (destination + confidence)
