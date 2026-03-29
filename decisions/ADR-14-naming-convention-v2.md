# ADR-14: Naming Convention v2

**Date:** 2026-03-25 | **Status:** Accepted

## Context

ADR-10's type-first naming (`DECK_`, `CERT_`) conflicted with Windows Explorer
sort order and made date-based chronological browsing impossible.

## Decision

New format: `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`. 19 type codes
(RFP, DECK, CERT, QA, PROP, etc.) and 15 client aliases defined in
`config/naming_config.yaml`. Date-first enables natural
chronological sort. Supersedes the type-first convention from ADR-10.

## Consequences

- All new files from 2026-03 onward use the v2 format
- Existing files migrated on-touch (no bulk rename)
- `naming_config.yaml` is the authoritative controlled vocabulary — update it, not code
