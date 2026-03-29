---
# ADR-16: Evaluation Metrics and Baseline

**Date:** 2026-03-26
**Status:** Accepted
**Council debate:** Source: chat session, no Council debate file found
**Panelists:** claude, gemini, deepseek, grok
**Synthesizer:** openai

## Context

Classifier and tagging improvements had no stable baseline to measure against, making it
impossible to tell whether a change was an improvement or a regression.

## Decision

Lock a stratified 80/20 train/test split (248 train / 62 test) using
`create_classifier_split.py`. Primary metrics: classifier accuracy on the held-out test
set and mean tag quality score across the vault. Baselines frozen at 2026-03-26:
classifier 51.3% (filename-only ceiling), mean tag score 0.753. A 30-day eval checkpoint
is set for 2026-04-25.

## Key constraints

- Split is locked — do not re-randomize between eval runs
- Test set is never used for training; validation feedback only goes into train split
- Metrics reported as absolute percentages and delta from baseline, not relative improvement
- Eval script lives in `eval.py`; three-way comparison section (1b) added for hybrid vs regex vs LLM

## Alternatives rejected

- **Cross-validation only**: rejected — unstable between sessions, makes regressions hard to detect
- **LLM-judged quality score**: rejected — too expensive for every merge; reserved for quarterly deep eval

## Revisit triggers

- If training corpus grows by >50% (re-lock the split)
- If tag taxonomy changes materially (tag score baseline becomes invalid)
- At the 2026-04-25 30-day checkpoint
---
