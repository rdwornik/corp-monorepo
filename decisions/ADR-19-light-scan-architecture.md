---
# ADR-19: Light Scan Architecture

**Date:** 2026-03-26
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

Classifiers and dedup checks ran on filenames alone. Content-aware features (first-page
text, slide titles, CSV headers) were locked inside full CKE extraction, which is too
expensive to run pre-classification. A lightweight content peek was needed before routing.

## Decision

Implement `light_scan.py` — a `ScanResult` dataclass with separate `filename_text` and
`content_text` feature spaces, 7 format scanners (pptx, docx, pdf, xlsx, csv, txt/md,
mp4), and tiered fault tolerance (`full` / `degraded` / `filename_only`). Light scan runs
after inbox receipt, before CKE. Inserted as a pipeline hook: after `light_scan`, before
full extraction. Enrichment script retroactively populates 26% of training examples with
real content.

## Key constraints

- Light scan is fail-open: any exception returns `filename_only` tier, never blocks pipeline
- mp4 scanner returns filename-only (no audio transcription at this stage)
- `content_text` must not exceed ~2,000 chars — it is a peek, not a full extract
- `ScanResult` is the interface contract; format scanners are implementation details

## Alternatives rejected

- **First-page PDF text via full Gemini call**: rejected — defeats the cost-saving purpose
- **Filename-only forever**: rejected — content features provide +32pp classifier uplift (see ADR-18)

## Revisit triggers

- If a new format (e.g., .eml, .msg) represents >5% of ingest volume
- If mp4 audio transcription becomes cheap enough to include in `degraded` tier
---
