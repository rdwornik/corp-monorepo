# ADR-09: Knowledge Dimensions and File Organization

**Date:** 2026-03-19 | **Status:** Accepted

## Context

No clear policy separated reusable knowledge assets from client-specific derivatives,
causing master decks to be edited in place and polluted with client context.

## Decision

Three operational zones: Projects (client-specific), Workflows (reusable execution
assets), Reference (stable reusable knowledge). Security/Compliance as a top-level
constraint zone. Reusable masters are never edited for client context; client
derivatives live in Projects.

## Consequences

- Folders define operational ownership; metadata (tags) define meaning
- Filenames carry max 3-4 meaningful tokens; heavier schemas abandoned
- 11 knowledge dimensions (Product, Industry, Technology, etc.) expressed as tags only
