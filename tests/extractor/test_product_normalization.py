"""Test product name normalization against real extraction data.

Fixtures generated from 690 CKE extraction outputs. Verifies that
normalize_product_names correctly canonicalizes product names seen
in real extractions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "product_normalization.json"

if FIXTURES_PATH.exists():
    ALL_PRODUCTS = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
else:
    ALL_PRODUCTS = []

# Known short-form → canonical mappings that should be normalized
KNOWN_DUPLICATES = [
    ("Demand Planning", "Blue Yonder Demand Planning"),
    ("Supply Planning", "Blue Yonder Supply Planning"),
    ("Control Tower", "Blue Yonder Control Tower"),
    ("WMS", "Blue Yonder WMS"),
    ("TMS", "Blue Yonder TMS"),
    ("OMS", "Blue Yonder OMS"),
    ("Platform", "Blue Yonder Platform"),
]


@pytest.mark.parametrize(
    "short,canonical",
    KNOWN_DUPLICATES,
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_short_form_normalizes_to_canonical(short: str, canonical: str) -> None:
    """Short product name normalizes to full BY-prefixed canonical form."""
    from corp.extractor.post_process import normalize_product_names

    result = normalize_product_names([short])
    assert result == [canonical], f"{short!r} → {result}, expected [{canonical!r}]"


@pytest.mark.parametrize(
    "short,canonical",
    KNOWN_DUPLICATES,
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_dedup_when_both_present(short: str, canonical: str) -> None:
    """When both short and canonical forms are present, dedup to canonical."""
    from corp.extractor.post_process import normalize_product_names

    result = normalize_product_names([short, canonical])
    assert result == [canonical], f"[{short!r}, {canonical!r}] → {result}"


def test_third_party_products_preserved() -> None:
    """Third-party products (Azure, Snowflake, SAP) are preserved as-is."""
    from corp.extractor.post_process import normalize_product_names

    third_party = ["Azure", "Snowflake", "SAP"]
    result = normalize_product_names(third_party)
    assert result == third_party


def test_product_fixtures_exist() -> None:
    """Verify fixture file exists with significant products."""
    assert FIXTURES_PATH.exists(), "product_normalization.json not found"
    assert len(ALL_PRODUCTS) >= 20, f"Expected 20+ products, got {len(ALL_PRODUCTS)}"


def test_no_empty_products_in_fixtures() -> None:
    """No empty or whitespace-only product names in fixtures."""
    for p in ALL_PRODUCTS:
        assert p["product"].strip(), f"Empty product name found: {p}"
