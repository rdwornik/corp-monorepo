"""Tests for validation and quarantine routing."""

from datetime import date

from corp_os_meta import ValidationResult, validate_frontmatter


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
