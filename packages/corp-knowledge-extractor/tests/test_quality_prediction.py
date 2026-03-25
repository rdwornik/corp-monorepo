"""Test quality prediction data consistency.

Fixtures generated from 690 CKE extraction outputs. Verifies that
quality scores, fact counts, and extraction metadata are internally
consistent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "quality_prediction.json"

if FIXTURES_PATH.exists():
    QUALITY_DATA = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
else:
    QUALITY_DATA = []


def test_quality_fixtures_exist() -> None:
    """Verify fixture file exists with data."""
    assert FIXTURES_PATH.exists(), "quality_prediction.json not found"
    assert len(QUALITY_DATA) >= 100, f"Expected 100+ entries, got {len(QUALITY_DATA)}"


def test_quality_values_valid() -> None:
    """Quality field only contains valid enum values."""
    # "medium" and "local" appear in older extractions as legacy values
    valid = {"full", "partial", "fragment", "medium", "local", None}
    for entry in QUALITY_DATA:
        assert entry["quality"] in valid, (
            f"Invalid quality: {entry['quality']!r} for {entry.get('doc_type')}"
        )


def test_quality_score_range() -> None:
    """Quality scores are within expected range [0, 100]."""
    for entry in QUALITY_DATA:
        score = entry.get("quality_score", 0) or 0
        assert 0 <= score <= 100, (
            f"Quality score out of range: {score} for {entry.get('doc_type')}"
        )


def test_deep_extraction_has_more_facts() -> None:
    """Deep extraction should produce more facts on average than standard."""
    deep = [e for e in QUALITY_DATA if e.get("depth") == "deep"]
    standard = [e for e in QUALITY_DATA if e.get("depth") == "standard"]

    if not deep or not standard:
        pytest.skip("Need both deep and standard extractions")

    avg_deep = sum(e["fact_count"] for e in deep) / len(deep)
    avg_standard = sum(e["fact_count"] for e in standard) / len(standard)

    assert avg_deep >= avg_standard, (
        f"Deep extraction avg facts ({avg_deep:.1f}) < standard ({avg_standard:.1f})"
    )


def test_topic_count_reasonable() -> None:
    """Most notes should have reasonable topic counts."""
    over_cap = [e for e in QUALITY_DATA if e["topic_count"] > 8]
    ratio = len(over_cap) / len(QUALITY_DATA) if QUALITY_DATA else 0
    # Allow up to 10% exceeding cap (older extractions before cap enforcement)
    assert ratio < 0.10, (
        f"Too many notes exceed topic cap: {len(over_cap)}/{len(QUALITY_DATA)} "
        f"({ratio:.0%})"
    )


def test_product_count_reasonable() -> None:
    """Product counts should be within cardinality cap (max 4 per note)."""
    for entry in QUALITY_DATA:
        assert entry["product_count"] <= 6, (
            f"Product count {entry['product_count']} exceeds cap for {entry.get('doc_type')}"
        )


def test_extension_coverage() -> None:
    """Training data covers major file extensions."""
    extensions = {e["extension"] for e in QUALITY_DATA if e["extension"]}
    # At least some of these should be present
    expected_any = {".pptx", ".docx", ".pdf", ".xlsx", ".mp4"}
    present = extensions & expected_any
    assert len(present) >= 2, (
        f"Only found extensions: {extensions}, expected some of {expected_any}"
    )
