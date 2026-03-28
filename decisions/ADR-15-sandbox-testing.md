---
# ADR-15: Sandbox Testing Pipeline

**Date:** 2026-03-25
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

Integration tests were monkey-patching production paths, risking accidental vault writes
during CI. There was no isolated environment to run full pipeline tests without side effects.

## Decision

Introduce a `PipelineConfig` dataclass (`production()` / `sandbox()` classmethods) threaded
through all vault, index, and ops-db entry points. `SandboxManager` creates an isolated
temp directory with real schema, stages a small fixture corpus, and tears down cleanly.
`corp test-pipeline` CLI command exercises the full ingest chain in sandbox mode.

## Key constraints

- `PipelineConfig.sandbox()` must never resolve to production vault paths
- `SandboxManager.teardown()` retries on Windows file-lock errors — never silently skips
- `--record` flag on `corp test-pipeline` saves live CKE fixtures for future replay
- Sandbox fixtures live in `tests/fixtures/pipeline/`; recorded ones in `.../recorded/`

## Alternatives rejected

- **Mock-only tests**: rejected — mocks hide schema drift and real path resolution bugs
- **Separate test database**: rejected — `PipelineConfig` threading gives real isolation with less overhead

## Revisit triggers

- If sandbox teardown reliability degrades on new Windows versions
- If fixture corpus grows stale and no longer represents production file types
---
