# Changelog — corp-knowledge-extractor

## [0.8.0] — 2026-03-25

- Monorepo migration (from standalone repo)
- 693 tests passing, 4 skipped
- Tiered extraction: Tier 1 (local), Tier 2 (text AI), Tier 3 (multimodal)
- Gemini Batch API integration (50% cheaper async processing)
- Per-slide visual analysis for PPTX via COM→PDF→PyMuPDF
- Video scene detection + frame sampling via FFmpeg
- Session merge: correlate PPTX + MP4 pairs into unified notes
- Fact validation: cross-reference extracted numbers against source text
- Deep extraction with doc-type-specific overlays
- Deterministic polarity detection for facts (regex, no LLM)
- Multi-provider AI abstraction (Gemini, Anthropic)
- corp-os-meta schema v2 integration (post-process normalization)
- gemini-3-flash-preview as default model

## [0.6.0] — 2026-02-15

- enforce_type_from_extension() for correct doc_type assignment
- classify_from_filename() for RFI/RFP/VA detection
- Fixed quality_score formula to use max(key_facts, facts)

## [0.4.0] — 2025-12-01

- Initial extraction pipeline
- Basic Gemini integration
- PPTX and PDF support
