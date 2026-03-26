"""Tests for file registry — content-hash-based identity and extraction tracking."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp_by_os.ops.database import OpsDB
from corp_by_os.ops.file_registry import ExtractionRecord, FileRecord, FileRegistry


@pytest.fixture()
def ops(tmp_path: Path) -> OpsDB:
    db = OpsDB(tmp_path / "test_ops.db")
    yield db
    db.close()


@pytest.fixture()
def registry(ops: OpsDB) -> FileRegistry:
    return FileRegistry(ops.conn)


# --- FileRecord CRUD ---


class TestRegisterFile:
    def test_register_new_file(self, registry: FileRegistry) -> None:
        """New file → inserted with first_seen_at."""
        rec = registry.register_file(
            content_hash="abc123",
            filename="test.pptx",
            path="C:/MyWork/00_Inbox/test.pptx",
            size_bytes=1024,
        )
        assert isinstance(rec, FileRecord)
        assert rec.content_hash == "abc123"
        assert rec.original_name == "test.pptx"
        assert rec.current_path == "C:/MyWork/00_Inbox/test.pptx"
        assert rec.size_bytes == 1024
        assert rec.first_seen_at == rec.last_seen_at

    def test_register_existing_updates_path(self, registry: FileRegistry) -> None:
        """Same hash, different path → current_path updated."""
        registry.register_file("hash1", "v1.pptx", "C:/old/path.pptx", 100)
        rec = registry.register_file("hash1", "v1.pptx", "C:/new/path.pptx", 100)
        assert rec.current_path == "C:/new/path.pptx"

    def test_register_existing_updates_last_seen(self, registry: FileRegistry) -> None:
        """Same hash, same path → last_seen_at updated."""
        rec1 = registry.register_file("hash1", "f.pptx", "C:/p.pptx", 100)
        rec2 = registry.register_file("hash1", "f.pptx", "C:/p.pptx", 100)
        assert rec2.file_id == rec1.file_id
        # last_seen_at >= first_seen_at (may be equal if same second)
        assert rec2.last_seen_at >= rec1.first_seen_at

    def test_register_preserves_original_name(self, registry: FileRegistry) -> None:
        """Re-registration with different filename keeps original_name."""
        rec1 = registry.register_file("hash1", "original.pptx", "C:/a.pptx", 100)
        rec2 = registry.register_file("hash1", "renamed.pptx", "C:/b.pptx", 100)
        assert rec2.original_name == "original.pptx"

    def test_register_normalizes_backslashes(self, registry: FileRegistry) -> None:
        """Windows backslashes in path are normalized to forward slashes."""
        rec = registry.register_file("hash1", "f.pptx", "C:\\Users\\test\\f.pptx", 100)
        assert "\\" not in rec.current_path


class TestGetByHash:
    def test_found(self, registry: FileRegistry) -> None:
        registry.register_file("deadbeef", "f.pptx", "C:/p.pptx", 100)
        rec = registry.get_by_hash("deadbeef")
        assert rec is not None
        assert rec.content_hash == "deadbeef"

    def test_not_found(self, registry: FileRegistry) -> None:
        assert registry.get_by_hash("nonexistent") is None


class TestUpdatePath:
    def test_update_path(self, registry: FileRegistry) -> None:
        registry.register_file("hash1", "f.pptx", "C:/old.pptx", 100)
        registry.update_path("hash1", "C:/new/location/f.pptx")
        rec = registry.get_by_hash("hash1")
        assert rec.current_path == "C:/new/location/f.pptx"


# --- Extraction tracking ---


class TestExtractions:
    def test_record_extraction(self, registry: FileRegistry) -> None:
        """Record extraction → stored with model, cost, vault path."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        ext = registry.record_extraction(
            file_id=rec.file_id,
            model="gemini-3-flash",
            vault_note_path="01_Knowledge/test_pkg",
            cost_cents=42,
        )
        assert isinstance(ext, ExtractionRecord)
        assert ext.model == "gemini-3-flash"
        assert ext.vault_note_path == "01_Knowledge/test_pkg"
        assert ext.cost_cents == 42
        assert ext.file_id == rec.file_id

    def test_latest_extraction(self, registry: FileRegistry) -> None:
        """Multiple extractions → returns newest."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        registry.record_extraction(rec.file_id, "haiku", "01_Knowledge/v1")
        registry.record_extraction(rec.file_id, "sonnet", "01_Knowledge/v2")

        latest = registry.latest_extraction(rec.file_id)
        assert latest is not None
        assert latest.model == "sonnet"
        assert latest.vault_note_path == "01_Knowledge/v2"

    def test_get_extractions_ordered(self, registry: FileRegistry) -> None:
        """Multiple extractions → ordered by date descending."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        registry.record_extraction(rec.file_id, "model_a", "01_Knowledge/a")
        registry.record_extraction(rec.file_id, "model_b", "01_Knowledge/b")
        registry.record_extraction(rec.file_id, "model_c", "01_Knowledge/c")

        exts = registry.get_extractions(rec.file_id)
        assert len(exts) == 3
        # Newest first
        assert exts[0].model == "model_c"
        assert exts[-1].model == "model_a"

    def test_no_extractions(self, registry: FileRegistry) -> None:
        """File with no extractions → empty list."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        assert registry.get_extractions(rec.file_id) == []
        assert registry.latest_extraction(rec.file_id) is None

    def test_extraction_normalizes_vault_path(self, registry: FileRegistry) -> None:
        """Windows backslashes in vault_note_path are normalized."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        ext = registry.record_extraction(rec.file_id, "model", "01_Knowledge\\test\\pkg")
        assert "\\" not in ext.vault_note_path

    def test_extraction_cost_optional(self, registry: FileRegistry) -> None:
        """cost_cents can be None."""
        rec = registry.register_file("h1", "f.pptx", "C:/f.pptx", 100)
        ext = registry.record_extraction(rec.file_id, "model", "01_Knowledge/p")
        assert ext.cost_cents is None


# --- Schema ---


class TestSchema:
    def test_tables_created(self, ops: OpsDB) -> None:
        """files and extractions tables exist in ops.db."""
        tables = ops.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "files" in table_names
        assert "extractions" in table_names

    def test_content_hash_unique(self, registry: FileRegistry) -> None:
        """content_hash has UNIQUE constraint."""
        registry.register_file("same_hash", "a.pptx", "C:/a.pptx", 100)
        # Second register with same hash should update, not insert duplicate
        registry.register_file("same_hash", "b.pptx", "C:/b.pptx", 200)
        rec = registry.get_by_hash("same_hash")
        assert rec is not None
        # Only one file record
        count = registry.conn.execute(
            "SELECT COUNT(*) FROM files WHERE content_hash = 'same_hash'"
        ).fetchone()[0]
        assert count == 1
