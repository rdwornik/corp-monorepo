"""Tests for the canonical models+pricing registry (Arc-C #25, A3-R5)."""

import pytest

from corp.extractor.extract import _estimate_gemini_cost
from corp.schema.model_pricing import (
    ANTHROPIC_PRICING,
    GEMINI_PRICING,
    MODEL_PRICING,
    blended_rate,
    get_price,
)


def test_provider_dicts_disjoint():
    """LA-R3: the two provider dicts share no keys (guards the {**a, **b} merge)."""
    assert set(ANTHROPIC_PRICING) & set(GEMINI_PRICING) == set()


def test_registry_built_from_providers():
    assert MODEL_PRICING == {**ANTHROPIC_PRICING, **GEMINI_PRICING}
    assert len(MODEL_PRICING) == len(ANTHROPIC_PRICING) + len(GEMINI_PRICING)


def test_get_price_known_and_unknown():
    assert get_price("gemini-3-flash-preview") == {"input": 0.50, "output": 3.00}
    assert get_price("nonexistent-model") is None


def test_blended_rate_matches_formula():
    # 0.8 * input + 0.2 * output
    assert blended_rate("gemini-3.1-pro-preview") == pytest.approx(4.00)
    assert blended_rate("gemini-3-flash-preview") == pytest.approx(1.00)
    assert blended_rate("gemini-3.1-flash-lite") == pytest.approx(0.50)


def test_blended_rate_unknown_uses_default():
    assert blended_rate("nope", default=0.77) == 0.77


@pytest.mark.parametrize("model", list(GEMINI_PRICING))
def test_estimate_cost_consistent_with_registry(model):
    """extract.py's blended estimate must equal the registry's blended_rate.

    Pre-fix this FAILS for gemini-3.1-flash-lite (extract.py hardcoded 0.25 vs
    the registry-derived 0.50) — the single documented behavior change of #25.
    Cost for exactly 1M tokens equals the blended $/1M rate.
    """
    assert _estimate_gemini_cost(model, 1_000_000) == pytest.approx(blended_rate(model))
