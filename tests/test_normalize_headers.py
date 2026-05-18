"""Tests for scripts/normalize_headers.py — dated-log entry header normalizer.

Rules (deterministic, idempotent):
  - Date-only entry headers (H2 or H3) -> `### YYYY-MM-DD`
  - Date + " — Topic" suffix -> `### YYYY-MM-DD — Topic` (preserved verbatim)
  - LESSONS pipe-schema entries (`### YYYY-MM-DD | source | ...`) -> unchanged
  - Non-date headings -> unchanged
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import normalize_headers as nh

# ---------------------------------------------------------------------------
# Single-line normalization
# ---------------------------------------------------------------------------

def test_h2_date_only_becomes_h3() -> None:
    assert nh.normalize_line("## 2026-05-16") == "### 2026-05-16"


def test_h3_date_only_unchanged() -> None:
    assert nh.normalize_line("### 2026-05-16") == "### 2026-05-16"


def test_h2_date_with_topic_becomes_h3_preserved() -> None:
    assert (
        nh.normalize_line("## 2026-05-16 — Session D: cleanup")
        == "### 2026-05-16 — Session D: cleanup"
    )


def test_h3_date_with_topic_unchanged() -> None:
    line = "### 2026-05-16 — Session D: cleanup"
    assert nh.normalize_line(line) == line


def test_h3_date_with_hyphen_topic_preserved() -> None:
    assert (
        nh.normalize_line("## 2026-05-16 - hyphen topic")
        == "### 2026-05-16 - hyphen topic"
    )


def test_lessons_pipe_schema_unchanged() -> None:
    line = "### 2026-05-16 | source | the lesson | category | [scope: meta] | action"
    assert nh.normalize_line(line) == line


def test_h2_with_pipe_schema_left_alone() -> None:
    """An H2 that already carries pipe payload is a non-canonical edge case — preserve."""
    line = "## 2026-05-16 | source | lesson | category | [scope: meta] | action"
    assert nh.normalize_line(line) == line


def test_non_date_h2_unchanged() -> None:
    assert nh.normalize_line("## Some Section Heading") == "## Some Section Heading"


def test_non_date_h3_unchanged() -> None:
    assert nh.normalize_line("### Topic with no date") == "### Topic with no date"


def test_h1_unchanged() -> None:
    assert nh.normalize_line("# Lessons Learned") == "# Lessons Learned"


def test_bullet_or_text_unchanged() -> None:
    assert nh.normalize_line("- 2026-05-16 in a bullet") == "- 2026-05-16 in a bullet"
    assert nh.normalize_line("Plain prose 2026-05-16.") == "Plain prose 2026-05-16."


# ---------------------------------------------------------------------------
# Whole-file normalization + idempotency
# ---------------------------------------------------------------------------

MESSY = """# Title

<!-- scope: meta -->

## 2026-05-16
body a

## 2026-05-15 — Topic with em-dash
body b

### 2026-05-14 - hyphen topic
body c

### 2026-05-13 | source | lesson | category | [scope: meta] | action
body d

## Some Non-Date Section
body e
"""

CLEAN = """# Title

<!-- scope: meta -->

### 2026-05-16
body a

### 2026-05-15 — Topic with em-dash
body b

### 2026-05-14 - hyphen topic
body c

### 2026-05-13 | source | lesson | category | [scope: meta] | action
body d

## Some Non-Date Section
body e
"""


def test_known_messy_to_known_clean() -> None:
    assert nh.normalize_text(MESSY) == CLEAN


def test_idempotency_single_pass() -> None:
    """Already-clean input passes through unchanged."""
    assert nh.normalize_text(CLEAN) == CLEAN


def test_idempotency_double_pass() -> None:
    """Running twice produces the same result as running once."""
    once = nh.normalize_text(MESSY)
    twice = nh.normalize_text(once)
    assert once == twice


def test_does_not_touch_fenced_code_blocks() -> None:
    """A '## YYYY-MM-DD' line inside a fenced code block must NOT be rewritten."""
    src = (
        "# Title\n\n"
        "```\n"
        "## 2026-05-16\n"
        "```\n"
    )
    assert nh.normalize_text(src) == src


# ---------------------------------------------------------------------------
# File-level helper (writes only if changed)
# ---------------------------------------------------------------------------

def test_normalize_file_rewrites_messy(tmp_path: Path) -> None:
    p = tmp_path / "JOURNAL.md"
    p.write_text(MESSY, encoding="utf-8")
    changed = nh.normalize_file(p)
    assert changed is True
    assert p.read_text(encoding="utf-8") == CLEAN


def test_normalize_file_noop_on_clean(tmp_path: Path) -> None:
    p = tmp_path / "JOURNAL.md"
    p.write_text(CLEAN, encoding="utf-8")
    mtime_before = p.stat().st_mtime_ns
    changed = nh.normalize_file(p)
    assert changed is False
    # Content unchanged; mtime unchanged (file not rewritten when no diff)
    assert p.read_text(encoding="utf-8") == CLEAN
    assert p.stat().st_mtime_ns == mtime_before
