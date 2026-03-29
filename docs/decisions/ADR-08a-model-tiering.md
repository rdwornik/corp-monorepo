# ADR-08a: Model Tiering and Routing

**Date:** 2026-03-18 | **Status:** Accepted

## Context

Manual `--model` flags were the only routing mechanism. No policy existed for when
to use Flash vs Pro vs Sonnet, so engineers guessed.

## Decision

Gemini 3.1 Pro is the deep-tier default pending a blinded 150-document benchmark
(Flash vs Pro vs Sonnet). Policy-based auto-routing by file type and source path
replaces manual flags. Version-gated re-extraction only — requires >5% validated
improvement over current model before triggering.

## Consequences

- Normalization layer post-processes all outputs into canonical schema regardless of model
- Monthly full re-extraction rejected; on-demand version-gated only
- Benchmark results must update this ADR with the permanent routing policy
