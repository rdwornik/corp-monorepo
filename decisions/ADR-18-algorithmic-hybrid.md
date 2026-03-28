---
# ADR-18: Algorithmic Hybrid Classifier

**Date:** 2026-03-26
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

The regex-only document type classifier plateaued at 51–57% accuracy (filename-only
ceiling). LLM classification for every file was too expensive. A fast, offline middle
layer was needed before falling back to LLM.

## Decision

Train a dual-vectorizer hybrid: char n-gram vectorizer over filenames combined with a
word n-gram vectorizer over content text, using `LogisticRegression`. Model is serialized
to JSON (no pickle) and loaded with `lru_cache`. At threshold 0.5, the hybrid achieves
85.5% accuracy on the held-out test set vs 53.2% regex (+32.3 pp), with 18% LLM fallback
and 0 high-confidence errors. Pipeline: TF-IDF → regex → LLM.

## Key constraints

- No pickle — JSON serialization only (cross-platform, no deserialization attack surface)
- `USE_TFIDF` env flag allows hot-disabling without code change
- Model is retrained whenever training corpus grows by >20% (see ADR-16 split)
- Content text comes from `light_scan.py` (see ADR-19) — classifier depends on light scan being present

## Alternatives rejected

- **LLM-only classification**: rejected — cost-prohibitive for bulk ingest; ~$0.002–0.004 per file at scale
- **Regex expansion only**: rejected — diminishing returns above 57%; word-boundary edge cases compound

## Revisit triggers

- If hybrid accuracy drops below 75% after training corpus refresh
- If `light_scan` content coverage improves enough to shift the content vectorizer weight
---
