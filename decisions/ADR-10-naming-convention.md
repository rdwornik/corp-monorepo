# ADR-10: Vault Naming Convention

**Date:** 2026-03-20 | **Status:** Accepted

## Context

Inconsistent filenames made automated routing unreliable. CKE could not derive
metadata from paths without a controlled vocabulary.

## Decision

Five top-level zones: `00_Inbox`, `10_Projects`, `20_Workflows`, `30_Reference`,
`50_RFP`, `60_Source_Library`, `80_Compliance`, `90_System`. Type-first naming
within zones (`DECK_`, `CERT_`, `RFP_`, etc.). Controlled vocabulary in
`naming_config.yaml`; aliases normalized on intake.

## Consequences

- CKE derives vault frontmatter from folder path + filename tokens + extracted content
- Path length ≤220 chars enforced to prevent OneDrive sync conflicts
- Tier 1 migration (certs, master deck) done immediately; Tier 2 rename on touch; Tier 3 archive
