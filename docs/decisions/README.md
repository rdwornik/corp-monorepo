# Architecture Decision Records

Distilled from AI Council debates. Full transcripts in `docs/decisions/transcripts/`.
Max 20 lines each. Format: Context / Decision / Consequences.

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-01](ADR-01-knowledge-architecture.md) | Knowledge Management Architecture | Accepted |
| [ADR-02](ADR-02-extraction-quality.md) | CKE Extraction Quality | Accepted |
| [ADR-03](ADR-03-model-selection.md) | Model Selection for Text Extraction | Superseded by ADR-08a |
| [ADR-04](ADR-04-vault-structure.md) | Vault Structure | Superseded by ADR-07 |
| [ADR-05](ADR-05-reextraction-strategy.md) | Re-extraction Strategy | Accepted |
| [ADR-06](ADR-06-quality-gate.md) | Ingestion Quality Gate | Accepted |
| [ADR-07](ADR-07-vault-navigation.md) | Obsidian Vault Navigation | Accepted |
| [ADR-08a](ADR-08a-model-tiering.md) | Model Tiering and Routing | Accepted |
| [ADR-08b](ADR-08b-gemini-capabilities.md) | Gemini API Capability Adoption | Accepted |
| [ADR-09](ADR-09-knowledge-dimensions.md) | Knowledge Dimensions and File Organization | Accepted |
| [ADR-10](ADR-10-naming-convention.md) | Vault Naming Convention (type-first) | Superseded by ADR-14 |
| [ADR-11](ADR-11-file-distribution.md) | File Distribution Algorithm | Accepted |
| [ADR-12](ADR-12-execution-patterns.md) | Claude Code Execution Patterns | Accepted |
| [ADR-13](ADR-13-monorepo-architecture.md) | Monorepo Package Architecture | Accepted |
| [ADR-14](ADR-14-naming-convention-v2.md) | Naming Convention v2 (date-first) | Accepted |
| [ADR-15](ADR-15-sandbox-testing.md) | Sandbox Testing Pipeline | Accepted |
| [ADR-16](ADR-16-eval-metrics.md) | Evaluation Metrics and Baseline | Accepted |
| [ADR-17](ADR-17-obsidian-plugins.md) | Obsidian Vault Navigation and Plugin Selection | Accepted |
| [ADR-18](ADR-18-algorithmic-hybrid.md) | Algorithmic Hybrid Classifier | Accepted |
| [ADR-19](ADR-19-light-scan-architecture.md) | Light Scan Architecture | Accepted |
| [ADR-20](ADR-20-vault-restructure.md) | Vault Rebuild Strategy | Accepted |
| [ADR-21](ADR-21-ontology-approach.md) | Knowledge Ontology and Tagging Approach | Accepted |
| [ADR-22](ADR-22-rfp-kb-federation.md) | RFP KB Federation with Vault Search | Superseded by ADR-33 |
| [ADR-23](ADR-23-monorepo-internal-architecture.md) | Monorepo Internal Architecture Refactoring | Accepted |
| [ADR-24](ADR-24-mywork-knowledge-architecture.md) | MyWork Knowledge Architecture | Accepted |
| [ADR-25](ADR-25-diagram-strategy.md) | Diagram Strategy | Accepted |
| [ADR-26](ADR-26-tach-adoption.md) | Tach Import Boundary Enforcement | Accepted |
| [ADR-27](ADR-27-safety-invariants.md) | Safety Invariants — OneDrive Guard Centralization and Vault Writer Narrowing | Accepted |
| [ADR-30](ADR-30-retire-changelog.md) | Retire CHANGELOG.md | Accepted |
| [ADR-31](ADR-31-retire-single-file-handoff.md) | Retire single-file HANDOFF (docs/HANDOFF.md + scripts/update_handoff.py) | Accepted |
| [ADR-33](ADR-33-rfp-kb-federation-index-extra-roots.md) | RFP KB Federation via INDEX_EXTRA_ROOTS (supersedes ADR-22) | Accepted |
| [ADR-34](ADR-34-vault-essence-layer-operating-model.md) | Vault Essence Layer — Amended Operating Model (S0-S3, Link/View Spine) | Accepted |
| [ADR-35](ADR-35-corp-ops-placement-backup-topology.md) | corp-ops Placement and Dual-Leg Backup Topology | Accepted |
| [ADR-36](ADR-36-storage-topology-estate-roles.md) | Storage Topology — Estate Roles (Dev / MyWork / OneDrive / Vault) | Accepted |
| [ADR-37](ADR-37-metadata-canonical-layer-facts-disposition.md) | Metadata Canonical Layer (frontmatter) + Facts-Pipeline Disposition (F7 stay-dead + one projection) | Accepted |

> ADR-28 and ADR-29 are intentionally skipped — reserved for future
> distillations of `DECISION_28_community_patterns_research` and
> `DECISION_29_spec_kit_kiro_research` (Council research debates in
> `docs/decisions/transcripts/` not yet distilled to ADRs).

## How to add a new ADR

1. Copy the canonical ADR template from `.dev-knowledge` (sibling repo at the `Dev/` level — `.dev-knowledge/templates/ADR-template.md`) to `docs/decisions/ADR-NN-{slug}.md`. The template is the source-of-truth per ADR-36; do not maintain a local copy.
2. Assign the next available number
3. Fill in the `Decommission:` field — list files/folders/sections this ADR makes obsolete, or write "none"
4. Keep it under 20 lines (excluding title/metadata)
5. Add a row to this table
6. If superseding an existing ADR, update the old ADR's status line
