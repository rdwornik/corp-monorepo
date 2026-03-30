"""Tests for extraction/vault_writer.py — sole vault writer per architecture rules."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


class TestReadTrustLevel:
    """Test _read_trust_level() frontmatter parsing."""

    def test_verified_trust_level(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("---\ntrust_level: verified\n---\nContent", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) == "verified"

    def test_extracted_trust_level(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("---\ntrust_level: extracted\n---\nContent", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) == "extracted"

    def test_no_frontmatter(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("Just content, no frontmatter", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) is None

    def test_frontmatter_without_trust_level(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) is None

    def test_malformed_yaml_defaults_to_verified(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("---\n: broken yaml [\n---\nContent", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) == "verified"

    def test_missing_file_defaults_to_verified(self, tmp_path):
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(tmp_path / "nonexistent.md") == "verified"

    def test_unclosed_frontmatter(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("---\ntrust_level: extracted\nno closing marker", encoding="utf-8")
        from corp.extraction.vault_writer import _read_trust_level

        assert _read_trust_level(note) is None


class TestFileHash:
    """Test _file_hash() content identity."""

    def test_same_content_same_hash(self, tmp_path):
        from corp.extraction.vault_writer import _file_hash

        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello", encoding="utf-8")
        b.write_text("hello", encoding="utf-8")
        assert _file_hash(a) == _file_hash(b)

    def test_different_content_different_hash(self, tmp_path):
        from corp.extraction.vault_writer import _file_hash

        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello", encoding="utf-8")
        b.write_text("world", encoding="utf-8")
        assert _file_hash(a) != _file_hash(b)

    def test_empty_file_has_hash(self, tmp_path):
        from corp.extraction.vault_writer import _file_hash

        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        h = _file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex


class TestMoveToVault:
    """Test move_to_vault() — the critical vault write path."""

    def _setup_staging(self, tmp_path):
        """Create a minimal staging structure with one package."""
        staging = tmp_path / "staging"
        pkg = staging / "test-pkg" / "extract"
        pkg.mkdir(parents=True)
        note = pkg / "note.md"
        note.write_text(
            "---\ntrust_level: extracted\ntitle: Test\n---\nContent",
            encoding="utf-8",
        )
        meta = staging / "test-pkg" / "_meta.yaml"
        meta.write_text("source: test.pptx\n", encoding="utf-8")
        vault = tmp_path / "vault"
        vault.mkdir()
        return staging, vault

    def test_new_package_moves_entirely(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging, vault = self._setup_staging(tmp_path)
        moved = move_to_vault(staging, vault, "01_Knowledge")

        assert moved > 0
        dest_pkg = vault / "01_Knowledge" / "test-pkg"
        assert dest_pkg.exists()
        assert (dest_pkg / "extract" / "note.md").exists()
        assert (dest_pkg / "_meta.yaml").exists()
        # Source should be gone
        assert not (staging / "test-pkg").exists()

    def test_creates_vault_target_dir(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging, vault = self._setup_staging(tmp_path)
        move_to_vault(staging, vault, "deep/nested/target")
        assert (vault / "deep" / "nested" / "target" / "test-pkg").exists()

    def test_merge_skips_identical_files(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging, vault = self._setup_staging(tmp_path)
        # Pre-populate vault with identical content (both note.md AND _meta.yaml)
        dest_pkg = vault / "01_Knowledge" / "test-pkg"
        dest_extract = dest_pkg / "extract"
        dest_extract.mkdir(parents=True)
        (dest_extract / "note.md").write_text(
            "---\ntrust_level: extracted\ntitle: Test\n---\nContent",
            encoding="utf-8",
        )
        (dest_pkg / "_meta.yaml").write_text("source: test.pptx\n", encoding="utf-8")

        moved = move_to_vault(staging, vault, "01_Knowledge")
        assert moved == 0  # All files identical, nothing moved

    def test_verified_note_creates_conflict(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging, vault = self._setup_staging(tmp_path)
        # Pre-populate vault with VERIFIED version (different content)
        dest_pkg = vault / "01_Knowledge" / "test-pkg" / "extract"
        dest_pkg.mkdir(parents=True)
        existing = dest_pkg / "note.md"
        existing.write_text(
            "---\ntrust_level: verified\ntitle: Reviewed\n---\nReviewed content",
            encoding="utf-8",
        )

        move_to_vault(staging, vault, "01_Knowledge")
        # Original should be preserved
        assert "Reviewed content" in existing.read_text(encoding="utf-8")
        # Conflict file should exist
        conflicts = list(dest_pkg.glob("*_conflict_*"))
        assert len(conflicts) == 1

    def test_empty_staging_returns_zero(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging = tmp_path / "staging"
        staging.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()
        assert move_to_vault(staging, vault, "01_Knowledge") == 0

    def test_move_failure_raises_oserror(self, tmp_path):
        from corp.extraction.vault_writer import move_to_vault

        staging, vault = self._setup_staging(tmp_path)
        with patch("corp.extraction.vault_writer.shutil.move", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                move_to_vault(staging, vault, "01_Knowledge")
