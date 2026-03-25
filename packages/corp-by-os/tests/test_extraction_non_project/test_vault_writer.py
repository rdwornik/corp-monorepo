"""Tests for vault_writer.py -- atomic vault write."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from corp_by_os.extraction.vault_writer import _read_trust_level, move_to_vault


def _make_package(staging: Path, pkg_name: str, files: dict[str, bytes]) -> None:
    """Helper to create a fake CKE output package in staging."""
    pkg = staging / pkg_name
    for rel_path, content in files.items():
        f = pkg / rel_path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(content)


def test_move_to_vault_creates_dir(tmp_path):
    """Creates vault target directory if it doesn't exist."""
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/extract.json": b'{"test": 1}'})

    vault = tmp_path / "vault"
    move_to_vault(staging, vault, "04_evergreen/_generated/template")

    assert (vault / "04_evergreen" / "_generated" / "template" / "pkg-001").is_dir()


def test_move_to_vault_moves_files(tmp_path):
    """Files moved from staging to vault target."""
    staging = tmp_path / "staging"
    _make_package(
        staging,
        "doc-001",
        {
            "extract/extract.json": b'{"id": "doc-001"}',
            "extract/readme.md": b"# Doc 001",
        },
    )

    vault = tmp_path / "vault"
    count = move_to_vault(staging, vault, "target")

    dest = vault / "target" / "doc-001"
    assert (dest / "extract" / "extract.json").exists()
    assert (dest / "extract" / "readme.md").exists()
    assert count == 2


def test_move_to_vault_skips_identical(tmp_path):
    """Files with identical hash not overwritten."""
    content = b"identical content"

    # Pre-populate vault with identical file
    vault = tmp_path / "vault"
    dest = vault / "target" / "pkg-001" / "extract"
    dest.mkdir(parents=True)
    (dest / "extract.json").write_bytes(content)

    # Staging has same content
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/extract.json": content})

    count = move_to_vault(staging, vault, "target")
    assert count == 0  # Nothing moved -- identical


def test_move_to_vault_overwrites_changed(tmp_path):
    """Files with different hash are overwritten."""
    # Pre-populate vault with old content
    vault = tmp_path / "vault"
    dest = vault / "target" / "pkg-001" / "extract"
    dest.mkdir(parents=True)
    (dest / "extract.json").write_bytes(b"old content")

    # Staging has new content
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/extract.json": b"new content"})

    count = move_to_vault(staging, vault, "target")
    assert count == 1
    assert (dest / "extract.json").read_bytes() == b"new content"


def test_move_to_vault_returns_count(tmp_path):
    """Returns correct count of files moved."""
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-a", {"extract/a.md": b"a"})
    _make_package(staging, "pkg-b", {"extract/b.md": b"b", "extract/b.json": b"{}"})

    vault = tmp_path / "vault"
    count = move_to_vault(staging, vault, "target")
    assert count == 3


def test_move_to_vault_empty_staging(tmp_path):
    """Empty staging dir returns 0."""
    staging = tmp_path / "staging"
    staging.mkdir()
    vault = tmp_path / "vault"
    count = move_to_vault(staging, vault, "target")
    assert count == 0


def test_move_to_vault_skips_verified(tmp_path):
    """Files with trust_level=verified in vault must not be overwritten."""
    vault = tmp_path / "vault"
    dest = vault / "target" / "pkg-001" / "extract"
    dest.mkdir(parents=True)
    (dest / "note.md").write_text(
        "---\ntitle: Verified Note\ntrust_level: verified\n---\nOriginal.\n",
        encoding="utf-8",
    )

    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/note.md": b"---\ntitle: New\n---\nReplaced.\n"})

    count = move_to_vault(staging, vault, "target")
    assert count == 0
    assert "Original" in (dest / "note.md").read_text(encoding="utf-8")


def test_move_to_vault_creates_conflict_for_verified(tmp_path):
    """Verified notes get a _conflict_ file instead of overwrite."""
    vault = tmp_path / "vault"
    dest = vault / "target" / "pkg-001" / "extract"
    dest.mkdir(parents=True)
    (dest / "note.md").write_text(
        "---\ntitle: Verified\ntrust_level: verified\n---\nOriginal.\n",
        encoding="utf-8",
    )

    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/note.md": b"---\ntitle: New\n---\nReplaced.\n"})

    move_to_vault(staging, vault, "target")

    # Original unchanged
    assert "Original" in (dest / "note.md").read_text(encoding="utf-8")

    # Conflict file created
    conflicts = list(dest.glob("*_conflict_*.md"))
    assert len(conflicts) == 1
    assert "New" in conflicts[0].read_text(encoding="utf-8")


# --- Fix 1: shutil.move error handling ---


def test_move_to_vault_raises_on_move_failure(tmp_path):
    """shutil.move failure raises OSError, doesn't silently continue."""
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/note.md": b"content"})
    vault = tmp_path / "vault"

    with patch("corp_by_os.extraction.vault_writer.shutil.move", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            move_to_vault(staging, vault, "target")


def test_move_to_vault_merge_raises_on_move_failure(tmp_path):
    """shutil.move failure during merge raises OSError."""
    vault = tmp_path / "vault"
    dest = vault / "target" / "pkg-001" / "extract"
    dest.mkdir(parents=True)
    (dest / "note.md").write_bytes(b"old content")

    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/note.md": b"new content"})

    with patch("corp_by_os.extraction.vault_writer.shutil.move", side_effect=OSError("permission denied")):
        with pytest.raises(OSError, match="permission denied"):
            move_to_vault(staging, vault, "target")


def test_move_to_vault_logs_error_on_failure(tmp_path, caplog):
    """Move failure is logged at ERROR level before re-raising."""
    staging = tmp_path / "staging"
    _make_package(staging, "pkg-001", {"extract/note.md": b"content"})
    vault = tmp_path / "vault"

    with patch("corp_by_os.extraction.vault_writer.shutil.move", side_effect=OSError("boom")):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(OSError):
                move_to_vault(staging, vault, "target")
    assert "Failed to move" in caplog.text


# --- Fix 2: _read_trust_level safe defaults ---


def test_trust_level_reads_verified(tmp_path):
    """Reads trust_level=verified from well-formed frontmatter."""
    note = tmp_path / "note.md"
    note.write_text("---\ntitle: Test\ntrust_level: verified\n---\nBody\n", encoding="utf-8")
    assert _read_trust_level(note) == "verified"


def test_trust_level_reads_extracted(tmp_path):
    """Reads trust_level=extracted from frontmatter."""
    note = tmp_path / "note.md"
    note.write_text("---\ntitle: Test\ntrust_level: extracted\n---\nBody\n", encoding="utf-8")
    assert _read_trust_level(note) == "extracted"


def test_trust_level_returns_none_when_missing(tmp_path):
    """Returns None when trust_level key is absent (normal extracted note)."""
    note = tmp_path / "note.md"
    note.write_text("---\ntitle: Test\n---\nBody\n", encoding="utf-8")
    assert _read_trust_level(note) is None


def test_trust_level_defaults_verified_on_read_error(tmp_path):
    """Defaults to 'verified' when file cannot be read (safe)."""
    note = tmp_path / "nonexistent.md"
    assert _read_trust_level(note) == "verified"


def test_trust_level_defaults_verified_on_parse_error(tmp_path):
    """Defaults to 'verified' when YAML parsing fails (safe)."""
    note = tmp_path / "note.md"
    note.write_text("---\n{{{invalid yaml\n---\nBody\n", encoding="utf-8")
    assert _read_trust_level(note) == "verified"


def test_trust_level_logs_warning_on_read_error(tmp_path, caplog):
    """Read errors produce a WARNING log."""
    note = tmp_path / "nonexistent.md"
    with caplog.at_level(logging.WARNING):
        _read_trust_level(note)
    assert "Defaulting to 'verified'" in caplog.text


def test_trust_level_no_frontmatter(tmp_path):
    """Returns None for files without YAML frontmatter."""
    note = tmp_path / "note.md"
    note.write_text("Just plain text, no frontmatter.", encoding="utf-8")
    assert _read_trust_level(note) is None
