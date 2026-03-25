# ADR-07: Obsidian Vault Navigation

**Date:** 2026-03-17 | **Status:** Accepted

## Context

Flat knowledge/ folder was becoming unnavigable. Semantic classification at save
time was required under the old design, violating the zero-triage constraint.

## Decision

Keep source notes flat in `knowledge/`. Build a browsable navigation tree in
`02_Navigate/` using MOC/index notes for Products, Clients, Domains, Recent, Quality.
Six knowledge dimensions expressed as tags, not folders. If flat becomes painful at
5,000+ notes, use alphabetical sharding (a-f, g-l), not semantic partitions.

## Consequences

- No semantic classification required at note-save time
- Obsidian MOC quality is first-class infrastructure, reviewed regularly
- Tags are the metadata lattice; folders are the browsing tree only
