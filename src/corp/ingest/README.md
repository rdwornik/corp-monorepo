# corp.ingest -- File Routing Pipeline

## What this module does

Routes incoming files from 00_Inbox and project folders to their correct
destinations. Classifies files by type, enforces naming conventions, detects
near-duplicates via MinHash, and triggers CKE extraction. The SOLE vault
writer in the system.

## Key files

| File | What it does |
|------|-------------|
| router.py | Core pipeline: detect -> match -> route -> record -> move -> extract |
| inbox.py | Interactive Rich UI for 00_Inbox routing (magistrala) |
| classifier.py | TF-IDF + regex file classification |
| llm_classifier.py | Gemini-based classification for quarantined files |
| renamer.py | Naming convention: {YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext} |
| naming_config.py | 19 type codes, 15 client aliases from naming_config.yaml |
| dedup.py | MinHash near-duplicate detection (content_signatures in ops.db) |
| light_scan.py | Fast file metadata scan (size, mtime, extension) |
| extractions.py | Ingest CKE JSON output into vault notes |

## Dependencies

- **Depends on:** corp.schema, corp.ops, corp.extraction, corp.overnight, corp.extractor
- **Used by:** corp.cli.ingest

## Data flow

00_Inbox file -> light_scan -> ContentRegistry.match -> renamer -> router (move + log to ops.db) -> CKE extraction -> vault note
