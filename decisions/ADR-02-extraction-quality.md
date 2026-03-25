# ADR-02: CKE Extraction Quality

**Date:** 2026-03-14 | **Status:** Accepted

## Context

CKE was running single-pass extraction on all documents at equal depth, wasting
cost on low-value files and producing shallow output for high-value ones.

## Decision

Tiered extraction: universal base schema for all files, 3-5 deep overlays for
high-value documents only. Budget target: $2-4/month. Re-extraction is on-demand
(triggered by retrieval access), never nightly batch. Validate quality on pilot
samples before any bulk re-extraction run.

## Consequences

- Only 15-20% of documents qualify for deep extraction
- Manual curated edits live in separate linked notes, never merged into regenerated output
- Preflight source audit required before batch runs; all files must exist locally first
