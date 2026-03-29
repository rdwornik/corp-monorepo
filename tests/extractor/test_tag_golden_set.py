"""Test tag generation and normalization against real extraction data.

Fixtures generated from 690 CKE extraction outputs. Verifies that
_normalize_tag produces consistent, well-formed tags.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "tag_golden_set.json"

if FIXTURES_PATH.exists():
    GOLDEN_TAGS = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
else:
    GOLDEN_TAGS = []


@pytest.mark.parametrize(
    "tag_entry",
    GOLDEN_TAGS[:50],
    ids=lambda t: t["tag"][:50],
)
def test_tag_is_well_formed(tag_entry: dict) -> None:
    """Tags in golden set follow expected format: prefix/slug."""
    tag = tag_entry["tag"]
    assert "/" in tag, f"Tag missing prefix: {tag!r}"
    prefix, slug = tag.split("/", 1)
    assert prefix in {
        "topic",
        "product",
        "domain",
        "type",
        "source",
        "client",
        "layer",
        "depth",
    }, f"Unknown tag prefix: {prefix!r} in {tag!r}"
    assert slug, f"Empty slug in tag: {tag!r}"


@pytest.mark.parametrize(
    "tag_entry",
    GOLDEN_TAGS[:50],
    ids=lambda t: t["tag"][:50],
)
def test_tag_normalization_idempotent(tag_entry: dict) -> None:
    """Normalizing an already-normalized tag slug produces the same result."""
    from corp_knowledge_extractor.post_process import _normalize_tag

    tag = tag_entry["tag"]
    _, slug = tag.split("/", 1)
    # The slug part should already be normalized
    renormalized = _normalize_tag(slug)
    assert renormalized == slug, f"Tag slug not idempotent: {slug!r} → {renormalized!r}"


def test_golden_set_exists() -> None:
    """Verify golden set has substantial data."""
    assert FIXTURES_PATH.exists(), "tag_golden_set.json not found"
    assert len(GOLDEN_TAGS) >= 50, f"Expected 50+ tags, got {len(GOLDEN_TAGS)}"


def test_high_frequency_tags_stable() -> None:
    """Top tags by frequency should be canonical forms (no normalization needed)."""
    from corp_knowledge_extractor.post_process import _normalize_tag

    # Top 10 most frequent tags
    top_tags = sorted(GOLDEN_TAGS, key=lambda t: -t["count"])[:10]
    for entry in top_tags:
        tag = entry["tag"]
        _, slug = tag.split("/", 1)
        assert _normalize_tag(slug) == slug, f"High-frequency tag not canonical: {tag!r} (count={entry['count']})"


def test_no_duplicate_tags_in_golden_set() -> None:
    """Golden set should not contain duplicate tags."""
    tags = [t["tag"] for t in GOLDEN_TAGS]
    assert len(tags) == len(set(tags)), "Duplicate tags found in golden set"
