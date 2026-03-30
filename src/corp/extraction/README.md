# corp.extraction -- Extraction Orchestration

## What this module does

Orchestrates the extraction pipeline: scans folders for extractable files,
applies per-folder policies, routes files to extraction destinations, emits
manifests, and writes extraction results to the vault.

## Key files

| File | What it does |
|------|-------------|
| scanner.py | Scan directories for files matching extraction criteria |
| folder_policy.py | Per-folder extraction policy (skip, extract, recurse) |
| routing.py | Route files to extraction destinations |
| manifest_emitter.py | Build extraction manifests from scan results |
| contract.py | Extraction contract definitions |
| vault_writer.py | Write extraction results to vault as .md notes |

## Dependencies

- **Depends on:** corp.schema (no other corp.* deps -- Layer 0)
- **Used by:** corp.cli.extract, corp.overnight, corp.ingest

## Data flow

Folder scan -> folder_policy filter -> routing -> manifest -> (CKE extraction) -> vault_writer
