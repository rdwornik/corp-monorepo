# corp.extractor -- CKE (Knowledge Extraction Engine)

## What this module does

Pure extraction engine. Takes source files (PDF, PPTX, DOCX, audio, video),
calls LLM APIs (Gemini primary, Claude fallback), and produces structured JSON
with key facts, topics, products, people, and metadata. Never writes to vault
or databases directly.

## Key files

| File | What it does |
|------|-------------|
| extract.py | Core extraction: prompt building, Gemini API calls, JSON parsing |
| tier_router.py | Cost-optimized routing: LOCAL / TEXT_AI / MULTIMODAL tiers |
| batch.py | Manifest-driven sequential extraction with resume |
| batch_api.py | Google Batch API integration for bulk processing |
| post_process.py | Result normalization via corp.schema |
| providers/base.py | ExtractionProvider ABC (Strategy pattern) |
| providers/gemini_provider.py | Gemini provider (primary) |
| providers/anthropic_provider.py | Claude provider |
| text_extract.py | Local text extraction (PDF, DOCX, PPTX, XLSX) |
| frames/sampler.py | Video frame sampling for multimodal extraction |
| scripts/run.py | `cke` CLI entry point |

## Dependencies

- **Depends on:** corp.schema (taxonomy, normalization)
- **Used by:** corp.ingest, corp.overnight, corp.extraction, corp.cli

## Data flow

Source file -> text_extract / frame sampler -> tier_router -> Gemini/Claude API -> JSON -> post_process -> ExtractionResult
