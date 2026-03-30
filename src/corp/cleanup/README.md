# corp.cleanup -- MyWork File Hygiene

## What this module does

Scans MyWork directories for misplaced, duplicate, or improperly named files.
Uses Gemini to classify ambiguous files, proposes moves as a YAML manifest,
and executes approved moves. Read-only scan by default; execution requires
explicit approval.

## Key files

| File | What it does |
|------|-------------|
| scanner.py | Scan MyWork for problematic files |
| classifier.py | Gemini-based file classification |
| proposer.py | Generate move proposals as YAML |
| executor.py | Execute approved moves from YAML |
| disk.py | Disk usage analysis |

## Dependencies

- **Depends on:** corp.schema (folder names, config)
- **Used by:** corp.cli.cleanup

## Data flow

MyWork scan -> classify -> propose moves.yaml -> (user review) -> execute moves
