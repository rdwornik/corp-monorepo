# ADR-04: Vault Structure

**Date:** 2026-03-14 | **Status:** Superseded by ADR-07

## Context

Source-origin folder structure was used to classify knowledge, causing semantic
meaning to be encoded in paths rather than metadata.

## Decision

Semantic meaning belongs in frontmatter metadata, not folder names. Stable note
identity (deterministic hash or `note_id`) enables clean rebuilds without losing
relationships.

## Consequences

- New knowledge dimensions require new frontmatter fields, not folder additions
- Superseded by ADR-07 which defines the full five-zone structure
