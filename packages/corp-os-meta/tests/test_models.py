"""Tests for Pydantic frontmatter models."""

from datetime import date

import pytest

from corp_os_meta import DocumentType, NoteFrontmatter


def test_valid_note():
    note = NoteFrontmatter(
        title="Test Note",
        date=date(2026, 2, 21),
        type=DocumentType.PRESENTATION,
        topics=["Disaster Recovery", "SLA"],
        source_tool="knowledge-extractor",
        source_file="test.mkv",
    )
    assert note.title == "Test Note"
    assert note.schema_version == 2


def test_missing_required_field():
    with pytest.raises(Exception):
        NoteFrontmatter(title="No type")


def test_tool_meta_namespace():
    note = NoteFrontmatter(
        title="Test",
        date=date(2026, 1, 1),
        type=DocumentType.MEETING,
        source_tool="test",
        source_file="test.md",
        tool_meta={"knowledge_extractor": {"slide_index": 5}},
    )
    assert note.tool_meta["knowledge_extractor"]["slide_index"] == 5


def test_frontmatter_without_v21_fields():
    """Existing notes without routing fields still validate."""
    fm = NoteFrontmatter(
        title="Legacy Note",
        date=date(2026, 1, 1),
        type=DocumentType.DOCUMENT,
        source_tool="test",
        source_file="test.md",
    )
    assert fm.content_origin is None
    assert fm.source_category is None
    assert fm.source_locator is None
    assert fm.routing_confidence is None


def test_frontmatter_with_v21_fields():
    """New notes with routing fields validate."""
    fm = NoteFrontmatter(
        title="Routed Note",
        date=date(2026, 3, 11),
        type=DocumentType.PRESENTATION,
        source_tool="corp-by-os",
        source_file="Platform_Overview.pptx",
        content_origin="mywork",
        source_category="template",
        source_locator="30_Templates/01_Presentation_Decks/Platform_Overview.pptx",
        routing_confidence=1.0,
    )
    assert fm.content_origin == "mywork"
    assert fm.source_category == "template"
    assert (
        fm.source_locator == "30_Templates/01_Presentation_Decks/Platform_Overview.pptx"
    )
    assert fm.routing_confidence == 1.0


def test_routing_confidence_bounds():
    """routing_confidence must be 0.0-1.0."""
    with pytest.raises(Exception):
        NoteFrontmatter(
            title="Bad Confidence",
            date=date(2026, 1, 1),
            type=DocumentType.DOCUMENT,
            source_tool="test",
            source_file="test.md",
            routing_confidence=1.5,
        )
    with pytest.raises(Exception):
        NoteFrontmatter(
            title="Bad Confidence",
            date=date(2026, 1, 1),
            type=DocumentType.DOCUMENT,
            source_tool="test",
            source_file="test.md",
            routing_confidence=-0.1,
        )


def test_date_optional():
    """date=None should be valid for documents without a meaningful date."""
    note = NoteFrontmatter(
        title="Dateless Note",
        type=DocumentType.DOCUMENT,
        source_tool="test",
        source_file="test.md",
    )
    assert note.date is None


def test_trust_level_field():
    """trust_level accepts valid string values."""
    fm = NoteFrontmatter(
        title="Verified Note",
        type=DocumentType.DOCUMENT,
        source_tool="test",
        source_file="test.md",
        trust_level="verified",
    )
    assert fm.trust_level == "verified"


def test_trust_level_defaults_none():
    """Legacy notes without trust_level still validate."""
    fm = NoteFrontmatter(
        title="Legacy Note",
        type=DocumentType.DOCUMENT,
        source_tool="test",
        source_file="test.md",
    )
    assert fm.trust_level is None


def test_caps_not_exceeded():
    note = NoteFrontmatter(
        title="Test",
        date=date(2026, 1, 1),
        type=DocumentType.DOCUMENT,
        topics=["A", "B", "C", "D", "E", "F", "G", "H"],
        source_tool="test",
        source_file="test.md",
    )
    assert len(note.topics) == 8


@pytest.mark.parametrize("doc_type", [
    DocumentType.SPREADSHEET,
    DocumentType.VENDOR_ASSESSMENT,
    DocumentType.DISCOVERY,
])
def test_new_document_types(doc_type):
    """New document types added for CKE v0.6.0 are valid."""
    note = NoteFrontmatter(
        title=f"Test {doc_type.value}",
        date=date(2026, 3, 24),
        type=doc_type,
        source_tool="knowledge-extractor",
        source_file="test.xlsx",
    )
    assert note.type == doc_type
    assert note.type.value == doc_type.value
