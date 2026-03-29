# ADR-11: File Distribution Algorithm

**Date:** 2026-03-21 | **Status:** Accepted

## Context

Routing new files to the correct vault zone required either pure rules (brittle for
edge cases) or pure LLM (expensive and non-deterministic).

## Decision

Rules-dominant hybrid: deterministic rules handle the common case; constrained LLM
fallback (temperature=0, enum-constrained, cached, logged) handles ambiguous files.
Successful LLM patterns promoted to deterministic rules quarterly. Review queue rate
tracked as a health metric — target <5%; >10% is a product defect.

## Consequences

- Identical LLM inputs always produce identical outputs (cached routing)
- Path-primary identity now; hash-secondary via `corp repair-paths` planned for v2
- Rename on ingest; surgical correction only for files without existing extractions
