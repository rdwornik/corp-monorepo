# corp.cli -- Click Command Interface

## What this module does

Top-level CLI layer. All 40+ commands are Click groups/commands registered
under the `corp` entry point. Each file maps to a command group. This is
the interface layer (top of the 4-layer stack) -- it imports from all subsystems.

## Key files

| File | What it does |
|------|-------------|
| __init__.py | Main `corp` group, loads PipelineConfig.production() |
| ingest.py | ingest, ingest-inbox, finalize, classify, freshness, ingest-extractions |
| extract.py | extract (CKE from MyWork folder) |
| overnight.py | overnight batch pipeline |
| index.py | index rebuild, index stats |
| query.py | query, folder-review |
| retrieve.py | retrieve, prep |
| rfp.py | rfp answer |
| project.py | project list/show/open |
| vault.py | vault validate |
| analytics.py | analytics report/products/timeline/clients/overlap/compare/recent |
| cleanup.py | cleanup-scan, apply-moves, cleanup, audit |
| task.py | task add/list/done |
| template.py | template list/scan/select |
| workflow.py | run (execute workflow) |
| system.py | doctor, trust-status, routing-review |
| misc.py | chat, test-pipeline |

## Dependencies

- **Depends on:** all corp.* modules
- **Used by:** end user via terminal

## Data flow

User command -> Click parsing -> PipelineConfig -> delegate to appropriate module -> Rich output
