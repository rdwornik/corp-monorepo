"""Tests for validation and quarantine routing."""

from datetime import date

from corp_os_meta import ValidationResult, validate_frontmatter
from corp_os_meta.validate import validate_against_schema


def test_valid_note():
    data = {
        "title": "Test",
        "date": date(2026, 1, 1),
        "type": "presentation",
        "topics": ["SLA"],
        "source_tool": "test",
        "source_file": "test.md",
    }
    result, note, issues = validate_frontmatter(data)
    assert result == ValidationResult.WARNINGS  # no summary = warning
    assert note is not None


def test_fully_valid_note():
    data = {
        "title": "Test",
        "date": date(2026, 1, 1),
        "type": "presentation",
        "topics": ["SLA"],
        "domains": ["Product"],
        "summary": "A test note about SLAs.",
        "source_tool": "test",
        "source_file": "test.md",
    }
    result, note, issues = validate_frontmatter(data)
    assert result == ValidationResult.VALID


def test_invalid_note_quarantined():
    data = {"title": "Missing everything"}
    result, note, issues = validate_frontmatter(data)
    assert result == ValidationResult.QUARANTINE
    assert note is None
    assert len(issues) > 0


def test_invalid_type_quarantined():
    data = {
        "title": "Bad type",
        "date": date(2026, 1, 1),
        "type": "invalid_type",
        "source_tool": "test",
        "source_file": "test.md",
    }
    result, note, issues = validate_frontmatter(data)
    assert result == ValidationResult.QUARANTINE


# ---------------------------------------------------------------------------
# validate_against_schema — warn-only schema contract checks
# ---------------------------------------------------------------------------


def test_schema_clean_note_no_warnings():
    data = {
        "title": "Clean Note",
        "type": "presentation",
        "source_tool": "cke",
        "source_file": "file.pptx",
    }
    warnings = validate_against_schema(data)
    assert warnings == []


def test_schema_missing_required_field():
    data = {"title": "Missing source_tool", "type": "presentation", "source_file": "f.md"}
    warnings = validate_against_schema(data)
    assert any("source_tool" in w for w in warnings)


def test_schema_unknown_field_flagged():
    data = {
        "title": "Test",
        "type": "presentation",
        "source_tool": "cke",
        "source_file": "f.pptx",
        "some_new_field": "unexpected",
    }
    warnings = validate_against_schema(data)
    assert any("some_new_field" in w for w in warnings)


def test_schema_allowed_value_violation():
    data = {
        "title": "Test",
        "type": "presentation",
        "source_tool": "cke",
        "source_file": "f.pptx",
        "quality": "high",  # valid in old CKE output, not in schema
    }
    warnings = validate_against_schema(data)
    assert any("quality" in w for w in warnings)


def test_schema_cardinality_violation():
    data = {
        "title": "Test",
        "type": "presentation",
        "source_tool": "cke",
        "source_file": "f.pptx",
        "topics": ["a", "b", "c", "d", "e", "f", "g", "h", "i"],  # 9, max is 8
    }
    warnings = validate_against_schema(data)
    assert any("topics" in w for w in warnings)


def test_schema_valid_quality_no_warning():
    data = {
        "title": "Test",
        "type": "presentation",
        "source_tool": "cke",
        "source_file": "f.pptx",
        "quality": "full",
    }
    warnings = validate_against_schema(data)
    assert not any("quality" in w for w in warnings)
