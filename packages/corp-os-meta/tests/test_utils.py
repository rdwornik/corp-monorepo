"""Tests for shared utilities."""

import pytest

from corp_os_meta import parse_llm_json


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
