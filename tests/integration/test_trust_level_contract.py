"""Trust level protection works across the ingest boundary."""
from corp_os_meta.models import DocumentType, NoteFrontmatter


def test_trust_levels_are_accepted():
    """Valid trust_level strings are accepted by NoteFrontmatter."""
    valid = ["verified", "extracted", "generated", "draft"]
    for level in valid:
        fm = NoteFrontmatter(
            title="test",
            type=DocumentType.DOCUMENT,
            source_tool="test",
            source_file="test.md",
            trust_level=level,
        )
        assert fm.trust_level == level


def test_trust_level_none_is_accepted():
    """trust_level=None is accepted (legacy notes)."""
    fm = NoteFrontmatter(
        title="test",
        type=DocumentType.DOCUMENT,
        source_tool="test",
        source_file="test.md",
        trust_level=None,
    )
    assert fm.trust_level is None


def test_note_frontmatter_requires_title_and_type():
    """NoteFrontmatter requires title, type, source_tool, source_file."""
    import pytest

    with pytest.raises(Exception):
        NoteFrontmatter()  # Missing required fields
