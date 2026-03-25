# ADR-06: Ingestion Quality Gate

**Date:** 2026-03-16 | **Status:** Accepted

## Context

Bad extractions (malformed frontmatter, empty content, hallucinated fields) were
entering the vault silently, degrading retrieval quality without any signal.

## Decision

Centralized quality gate in corp-by-os with graduated response: pass / soft-fail /
hard-fail / degraded-ingest. Hard-fail triggers one automatic re-extraction; on
second failure, ingest with degraded ranking. Batch-level anomaly detection added.
Retrieval smoke tests in Phase 1.5.

## Consequences

- Never auto-patch frontmatter; log corrections, use them to improve upstream prompts
- Quality gate logs drive CKE prompt engineering iterations
- corp-by-os owns the gate; CKE never self-approves its own output
