"""Tests for shared utilities."""

import pytest

from corp.schema import parse_llm_json


def test_parse_clean_json():
    """Clean JSON parses directly."""
    result = parse_llm_json('{"a": 1, "b": "hello"}')
    assert result == {"a": 1, "b": "hello"}


def test_parse_markdown_fenced():
    """JSON wrapped in ```json ... ``` parses."""
    text = '```json\n{"key": "value"}\n```'
    assert parse_llm_json(text) == {"key": "value"}


def test_parse_markdown_fenced_no_lang():
    """JSON wrapped in ``` ... ``` (no language tag) parses."""
    text = '```\n{"key": "value"}\n```'
    assert parse_llm_json(text) == {"key": "value"}


def test_parse_with_preamble():
    """JSON with preamble text parses via regex extraction."""
    text = 'Here is the result:\n{"status": "ok", "count": 42}'
    assert parse_llm_json(text) == {"status": "ok", "count": 42}


def test_parse_with_trailing_text():
    """JSON followed by explanation text parses."""
    text = '{"status": "ok"}\nI hope this helps!'
    assert parse_llm_json(text) == {"status": "ok"}


def test_parse_trailing_commas():
    """JSON with trailing commas parses."""
    text = '{"a": 1, "b": 2,}'
    assert parse_llm_json(text) == {"a": 1, "b": 2}


def test_parse_invalid_raises():
    """Completely invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Failed to parse"):
        parse_llm_json("this is not json at all")


# --- Arc-C #27 coverage: edge cases the migrated call sites relied on ---
# Each case below is a behavior a former per-module copy handled (audit.py
# truncation-repair, rfp nested objects, ingest/validator arrays, etc.).
# These are regression guards proving the canonical subsumes every copy
# BEFORE those call sites were repointed to it. See plan LA-R1.


def test_parse_truncated_unclosed_string():
    """Truncated response with an unclosed string value repairs (audit.py copy)."""
    assert parse_llm_json('{"a": 1, "b": "unclosed') == {"a": 1, "b": "unclosed"}


def test_parse_truncated_unclosed_array():
    """Truncated response with an unclosed array repairs (audit.py copy)."""
    assert parse_llm_json('{"items": [1, 2, 3') == {"items": [1, 2, 3]}


def test_parse_truncated_fenced_object():
    """Fenced + truncated response repairs (audit.py copy)."""
    assert parse_llm_json('```json\n{"name": "test", "vals": [1,2') == {
        "name": "test",
        "vals": [1, 2],
    }


def test_parse_nested_object_in_preamble():
    """Nested object embedded in prose parses (rfp answer_selector copy; the
    old {[^{}]*} regex broke on nesting — canonical uses greedy extraction)."""
    text = 'Result: {"outer": {"inner": 1}, "x": 2} done'
    assert parse_llm_json(text) == {"outer": {"inner": 1}, "x": 2}


def test_parse_top_level_array():
    """Top-level JSON array parses (ingest/validator copies)."""
    assert parse_llm_json("[1, 2, 3]") == [1, 2, 3]


def test_parse_fenced_array():
    """Fenced top-level array parses."""
    assert parse_llm_json('```json\n[{"a": 1}, {"b": 2}]\n```') == [
        {"a": 1},
        {"b": 2},
    ]


def test_parse_inline_json_prefix():
    """Inline ```json prefix with no newline parses (validator/rfp fence edge)."""
    assert parse_llm_json('```json{"k": "v"}```') == {"k": "v"}


def test_parse_array_trailing_comma():
    """Array with a trailing comma parses."""
    assert parse_llm_json("[1, 2, 3,]") == [1, 2, 3]
