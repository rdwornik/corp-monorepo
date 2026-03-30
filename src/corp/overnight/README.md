# corp.overnight -- Batch Extraction Pipeline

## What this module does

Runs unattended extraction jobs across project folders. Manages state in
overnight_state.db for crash recovery and resume. Supports scopes
(all-non-project, reference, workflows, full-reshape), budget limits,
and batch API mode.

## Key files

| File | What it does |
|------|-------------|
| state.py | OvernightState: SQLite-backed run/file/batch tracking |
| preflight.py | Pre-run validation (API keys, disk space, scope) |
| cke_client.py | CKE invocation wrapper |
| classifier.py | File classification for overnight routing |
| monitor.py | Run progress monitoring |
| dedup.py | Cross-run deduplication |
| safety.py | Safety checks (budget, error rate limits) |

## Dependencies

- **Depends on:** corp.config, corp.schema, corp.extractor
- **Used by:** corp.cli.overnight, corp.ingest.router

## Data flow

Scope selection -> preflight -> file discovery -> tier routing -> CKE extraction -> state tracking -> completion
