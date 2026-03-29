# ADR-03: Model Selection for Text Extraction

**Date:** 2026-03-14 | **Status:** Superseded by ADR-08a

## Context

Gemini vs Claude was being chosen on preference rather than evidence. Monthly
re-extraction schemes were proposed without cost/quality justification.

## Decision

Empirical benchmarking required before committing to any model. No unsubstantiated
preferences. Zero Data Retention required before processing sensitive documents.
Monthly re-extraction schemes rejected universally.

## Consequences

- All re-extraction policy decisions deferred pending benchmark results
- Superseded by ADR-08a which establishes the tiered routing policy
