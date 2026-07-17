"""Canonical models + pricing registry (Arc-C #25, A3-R5).

Single source of truth for per-model LLM token pricing, BUILT from the live
per-provider dicts. Both extraction providers and the cost estimators read from
here — there are no per-file pricing dicts anymore.

Prices are per-1,000,000 tokens (USD). This module is foundation/utility
(``corp.schema``), so every layer may import it with no new dependency edges.
"""

from __future__ import annotations

# ── Per-provider source-of-truth dicts (relocated verbatim) ──────────────────
# Anthropic — from the former extractor/providers/anthropic_provider.py
ANTHROPIC_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}

# Gemini — from the former extractor/providers/gemini_provider.py
GEMINI_PRICING: dict[str, dict[str, float]] = {
    "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
    "gemini-3.1-flash-lite": {"input": 0.25, "output": 1.50},
    "gemini-3.1-pro-preview": {"input": 2.00, "output": 12.00},
}

# ── The unified registry — BUILT from the per-provider dicts ──────────────────
# The two provider dicts share no keys (guarded by a test), so the merge is
# lossless.
MODEL_PRICING: dict[str, dict[str, float]] = {**ANTHROPIC_PRICING, **GEMINI_PRICING}

# Default blend for collapsing input/output pricing into one "$/1M" figure —
# input-heavy assumption (~80% input, ~20% output).
_DEFAULT_INPUT_WEIGHT = 0.8


def get_price(model: str) -> dict[str, float] | None:
    """Return ``{"input", "output"}`` per-1M-token USD for *model*.

    Returns ``None`` for an unknown model — callers supply their own fallback
    (mirrors the former per-provider ``PRICING.get(model, <fallback>)`` sites).
    """
    return MODEL_PRICING.get(model)


def blended_rate(
    model: str,
    input_weight: float = _DEFAULT_INPUT_WEIGHT,
    default: float = 1.00,
) -> float:
    """Single blended ``$/1M`` rate for *model*.

    ``input_weight * input + (1 - input_weight) * output``. For a model absent
    from the registry, returns *default* (lets callers preserve legacy-alias
    estimates).
    """
    price = MODEL_PRICING.get(model)
    if price is None:
        return default
    return input_weight * price["input"] + (1 - input_weight) * price["output"]
