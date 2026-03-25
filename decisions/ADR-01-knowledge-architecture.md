# ADR-01: Knowledge Management Architecture

**Date:** 2026-03-14 | **Status:** Accepted

## Context

The RFP agent and CKE vault were disconnected, causing split-brain knowledge
fragmentation. No single source of truth existed for retrieved content.

## Decision

Hybrid architecture: manual YAML content registry + SQLite operations. Rule-based
ingest with schema-constrained LLM fallback. FTS5 + metadata retrieval (embeddings
deferred). Provenance fields (`source_path`, `source_hash`, `extracted_at`) mandatory
on every extracted note. Structured queries only — no unstructured RAG.

## Consequences

- corp-rfp-agent's isolated DB must merge with vault index (split-brain eliminated)
- Embeddings deferred indefinitely; FTS5 must fail demonstrably before adding them
- All retrieval failures are explicit errors, never silent empty results
