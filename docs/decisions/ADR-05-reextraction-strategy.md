# ADR-05: Re-extraction Strategy

**Date:** 2026-03-15 | **Status:** Accepted

## Context

Upgrading the extraction corpus risked mixing v1 and v2 quality in retrieval,
and manual edits could be silently overwritten by re-extraction.

## Decision

Parallel v2 extraction to a separate location, quality-validated on samples, then
clean cutover. Only minimal on-demand upgrade mechanism built afterward. No nightly
automation, no continuous autonomous re-extraction. Archive projects handled
on-demand only.

## Consequences

- V1 corpus must leave retrieval entirely once v2 equivalent exists (no mixed quality)
- Manual edits stay in separate curated notes linked by `doc_id`, never merged
- Preflight source audit mandatory before any batch run
