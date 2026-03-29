---
# ADR-17: Obsidian Vault Navigation and Plugin Selection

**Date:** 2026-03-26
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

The Obsidian vault had no structured navigation layer. Users had to know file names to
find content; there was no entry point for topic-based browsing or cross-project discovery.

## Decision

Establish 8 Maps of Content (MOCs) as the primary navigation layer: one per major
knowledge domain (Projects, Clients, Document Types, Timeline, Products, RFP, Compliance,
and a missing-Compliance MOC added in a later session). Plugin selection follows a
minimal-core-only policy: only plugins that solve a specific friction point are installed;
community plugins are evaluated against the risk of vault lock-in.

## Key constraints

- MOCs are hand-maintained — do not auto-generate MOC content from scripts
- Each new knowledge domain gets a MOC before ingesting more than ~20 notes to that domain
- Plugins that modify note format (frontmatter, links) require explicit approval before install
- `taxonomy.yaml` is the authoritative tag vocabulary; Obsidian tags must match it

## Alternatives rejected

- **Folder-only navigation**: rejected — deep nesting is opaque; MOCs expose cross-cutting relationships
- **Dataview-heavy approach**: rejected — query-first navigation is fragile when field names change

## Revisit triggers

- If MOC maintenance burden exceeds 5 minutes per ingest session
- If a community plugin addresses a friction point with negligible lock-in risk
---
