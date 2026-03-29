---
# ADR-20: Vault Rebuild Strategy

**Date:** 2026-03-27
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

The vault contained ~490 notes extracted at varying quality levels across different CKE
versions. Many v2 notes had low quality scores; deprecated notes were polluting retrieval
results. A clean rebuild was needed without losing any source documents.

## Decision

Re-extract 216 vault notes via CKE batch (gemini-pro deep mode). Add an
`include_deprecated` filter to the retrieve engine so deprecated notes are excluded from
all query paths without being deleted. Rebuild index post-ingest. Quality threshold stays
at 25 (permissive) to avoid discarding valid low-content files.

## Key constraints

- Source documents are never deleted — only extraction output is replaced
- `include_deprecated=False` is the default for all retrieve calls
- Deprecated notes remain in vault for audit trail; they are not purged
- Haiku enrichment failures on all files are expected and non-fatal (returns empty JSON)

## Alternatives rejected

- **Bulk delete and re-ingest from scratch**: rejected — risks losing notes with no source file available
- **Selective re-extract only low-quality notes**: rejected — quality scores from old CKE versions are not comparable

## Revisit triggers

- If deprecated notes accumulate beyond 10% of indexed vault (consider a purge policy)
- If quality threshold 25 lets too many empty/corrupt notes through (raise to 40)
---
