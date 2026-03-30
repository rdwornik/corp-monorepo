# corp.project -- CPE (Project Extractor)

## What this module does

Scans project folders, classifies files, extracts text and metadata, and
renders project-info.yaml + facts.yaml + index.md for the vault. Full
pipeline: scan -> extract -> render. Invoked via `cpe` CLI.

## Key files

| File | What it does |
|------|-------------|
| cli.py | `cpe` CLI: scan, extract, extract-cke, render, show, run |
| config.py | Settings from config/project/default.yaml |
| classifier.py | Project file classification |
| extractors.py | Text extraction from supported formats |
| manifest.py | Project file manifest model |
| manifest_generator.py | Generate manifest from scan |
| renderer.py | Render project-info.yaml, facts.yaml, index.md |
| models.py | Project data models |
| cke_invoker.py | Invoke CKE batch processing |

## Dependencies

- **Depends on:** corp.project internal only (Layer 0-1)
- **Used by:** corp.cli.project (via project_resolver)

## Data flow

Project folder -> scan files -> classify -> extract text -> render YAML/MD -> vault
