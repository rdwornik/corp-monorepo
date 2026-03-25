# ADR-08b: Gemini API Capability Adoption

**Date:** 2026-03-18 | **Status:** Accepted

## Context

Several Gemini API features (Structured Outputs, Document Understanding, Thinking
Mode, Function Calling) were available but adoption policy was unclear.

## Decision

Structured Outputs adopted immediately — JSON schema mandatory on all extraction
calls. Document Understanding, Thinking Mode, and Function Calling deferred; each
requires a pilot showing ≥15% quality improvement before adoption. Per-file
extraction remains the atomic unit. URL Context deferred entirely (SSRF risk).

## Consequences

- Extraction contract is normalized JSON in index.db; Markdown is a rendered view only
- Cross-document synthesis is a MapReduce pass after per-file extraction, not a replacement
- New API capabilities require empirical validation gate before production use
