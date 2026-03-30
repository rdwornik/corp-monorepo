# ADR-25: Diagram Strategy

**Date:** 2026-03-30
**Status:** Accepted
**Debate:** Council #25 (4-model panel, synthesizer: OpenAI)

## Decision

Mermaid source files (.mermaid) as ground truth in docs/diagrams/. Generated SVGs alongside for viewing in VS Code editor tabs. PowerShell render script converts source to output.

3 diagrams: system-context, container-module, magistrala-pipeline.

## Format: 1B (Mermaid + SVG)
## Location: 2A (standalone in docs/diagrams/) with text pointer from ARCHITECTURE.md
## Sync: 3B (Mermaid source of truth, SVG via render script)

## Key constraint
SVG image refs in markdown do NOT render inline in VS Code editor. Must open .svg files directly.

## Convention
- Edit .mermaid files only, never hand-edit .svg
- Run scripts/render-diagrams.ps1 after structural changes
- Max 3 diagrams (hard limit per Council)
