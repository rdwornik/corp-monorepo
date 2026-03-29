---
# ADR-21: Knowledge Ontology and Tagging Approach

**Date:** 2026-03-26
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

Tags and product references were inconsistent across vault notes — free-text tags diverged
from the taxonomy, product aliases varied by extractor version, and client name variants
fragmented retrieval results. A controlled vocabulary decision was needed.

## Decision

`taxonomy.yaml` is the single authoritative tag vocabulary — tags not in taxonomy are
rejected at ingest. `product_aliases.yaml` maps product variant spellings to canonical
names. `client_aliases.yaml` in CKE (expanded from 8 to 48 entries) normalises client
name variants before extraction. Retrieval engine expands client queries with OR LIKE
to cover all known aliases. Schema contract (`schema.yaml` in corp-os-meta) enforces
vocabulary at `post_process_extraction()` — warn-only for now.

## Key constraints

- New tags must be added to `taxonomy.yaml` before being used in extraction prompts
- Client alias additions require entries in both `client_aliases.yaml` (CKE) and
  `product_aliases.yaml` (corp-by-os) to take effect end-to-end
- Schema validation is warn-only — hard rejection deferred until extraction accuracy stabilises
- Controlled vocabulary applies to new extractions only; backfill is on-touch

## Alternatives rejected

- **Free-form tags with post-hoc clustering**: rejected — divergence compounds over time; retrieval precision degrades
- **LLM-normalised tags at query time**: rejected — inconsistency source is in storage, not query; fix at write time

## Revisit triggers

- If taxonomy grows beyond 150 tags (consider hierarchical grouping)
- If schema warn-only catches >5% violations per week (promote to hard reject)
---
