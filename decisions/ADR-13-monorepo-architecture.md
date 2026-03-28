---
# ADR-13: Monorepo Package Architecture

**Date:** 2026-03-25
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

Six standalone corp-* repos had grown independently with duplicated tooling, circular
import risk, and no enforced boundaries between vault writing and knowledge extraction.

## Decision

Consolidate all packages into a single monorepo (`corp-monorepo`). Each package retains
its own `pyproject.toml` and test suite. Cross-package communication is subprocess-only
(no Python imports across package boundaries). `corp-by-os` is the sole vault writer;
`corp-knowledge-extractor` is a pure extraction engine with zero vault writes.

## Key constraints

- Each package has its own `pyproject.toml` — no shared `setup.cfg` or single root install
- Subprocess boundary between CKE and corp-by-os — CKE never imports corp-by-os directly
- Forward slashes everywhere in databases and path strings (Windows safe)
- Feature branches: `feat/`, `fix/`, `refactor/`, `chore/`

## Alternatives rejected

- **Separate repos with pip installs**: rejected — version drift between packages caused silent breakage
- **Shared root pyproject.toml**: rejected — single install surface hides boundary violations

## Revisit triggers

- If subprocess overhead becomes a measurable bottleneck at production scale
- If a third package needs vault write access (reassess sole-writer rule first)
---
