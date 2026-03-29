"""Tests for ops.db — operational database."""

from __future__ import annotations

from pathlib import Path

import pytest
from corp.ops.database import OpsDB
from corp.schema.folder_names import (
    INBOX,
    PROJECTS,
    REFERENCE,
    WORKFLOWS,
)


@pytest.fixture()
def db(tmp_path: Path) -> OpsDB:
    ops = OpsDB(db_path=tmp_path / "test_ops.db")
    # Access .conn to trigger schema init
    _ = ops.conn
    yield ops
    ops.close()


class TestSchema:
    def test_create_database(self, db: OpsDB) -> None:
        """OpsDB creates all 4 tables on init."""
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "assets" in table_names
        assert "packages" in table_names
        assert "ingest_events" in table_names
        assert "registry_suggestions" in table_names

    def test_schema_idempotent(self, db: OpsDB) -> None:
        """Running _init_schema twice does not raise."""
        db._init_schema()
        db._init_schema()


class TestAssets:
    def test_upsert_asset_new(self, db: OpsDB) -> None:
        """New asset is inserted with correct fields."""
        aid = db.upsert_asset(
            path=f"{PROJECTS}/Lenzing/demo.pptx",
            filename="demo.pptx",
            extension=".pptx",
            size_bytes=5000,
            mtime="2026-03-14T10:00:00",
            folder_l1=PROJECTS,
            folder_l2="Lenzing",
        )
        assert isinstance(aid, int)
        asset = db.get_asset(f"{PROJECTS}/Lenzing/demo.pptx")
        assert asset is not None
        assert asset["filename"] == "demo.pptx"
        assert asset["size_bytes"] == 5000
        assert asset["status"] == "discovered"
        assert asset["folder_l1"] == PROJECTS
        assert asset["folder_l2"] == "Lenzing"

    def test_upsert_asset_existing(self, db: OpsDB) -> None:
        """Existing asset (same path) is updated, not duplicated."""
        db.upsert_asset(
            "test/file.txt",
            "file.txt",
            ".txt",
            100,
            "2026-03-14T10:00:00",
            PROJECTS,
        )
        db.upsert_asset(
            "test/file.txt",
            "file.txt",
            ".txt",
            200,
            "2026-03-14T11:00:00",
            PROJECTS,
        )
        asset = db.get_asset("test/file.txt")
        assert asset is not None
        assert asset["size_bytes"] == 200
        # Should not duplicate
        count = db.conn.execute(
            "SELECT COUNT(*) FROM assets WHERE path = 'test/file.txt'",
        ).fetchone()[0]
        assert count == 1

    def test_get_asset_not_found(self, db: OpsDB) -> None:
        """Non-existent asset returns None."""
        assert db.get_asset("does/not/exist.pdf") is None

    def test_get_assets_by_status(self, db: OpsDB) -> None:
        """Filter assets by status."""
        db.upsert_asset("a.txt", "a.txt", ".txt", 10, "2026-01-01T00:00:00", INBOX)
        db.upsert_asset("b.txt", "b.txt", ".txt", 20, "2026-01-01T00:00:00", INBOX)
        assets = db.get_assets_by_status("discovered")
        assert len(assets) == 2

    def test_get_assets_by_folder(self, db: OpsDB) -> None:
        """Filter assets by L1 folder."""
        db.upsert_asset(
            f"{PROJECTS}/a.pdf", "a.pdf", ".pdf", 10, "2026-01-01T00:00:00", PROJECTS
        )
        db.upsert_asset(
            f"{WORKFLOWS}/b.pptx", "b.pptx", ".pptx", 20, "2026-01-01T00:00:00", WORKFLOWS
        )
        projects = db.get_assets_by_folder(PROJECTS)
        assert len(projects) == 1
        assert projects[0]["filename"] == "a.pdf"


class TestStatusChangeLogsEvent:
    def test_asset_status_change_logs_event(self, db: OpsDB) -> None:
        """Changing asset status always creates an ingest_event."""
        db.upsert_asset("x.pptx", "x.pptx", ".pptx", 100, "2026-01-01T00:00:00", WORKFLOWS)
        db.update_asset_status(
            "x.pptx",
            "routed",
            routed_to=f"{REFERENCE}/01_Product_Docs",
            routed_method="heuristic",
            routed_confidence=0.9,
            reasoning="Matched product doc pattern",
        )

        asset = db.get_asset("x.pptx")
        assert asset is not None
        assert asset["status"] == "routed"
        assert asset["routed_to"] == f"{REFERENCE}/01_Product_Docs"
        assert asset["routed_method"] == "heuristic"

        events = db.get_events_for_asset(asset["id"])
        assert len(events) == 1
        assert events[0]["action"] == "routed"
        assert events[0]["method"] == "heuristic"
        assert events[0]["reasoning"] == "Matched product doc pattern"

    def test_update_nonexistent_asset(self, db: OpsDB) -> None:
        """Updating non-existent asset does nothing (no crash)."""
        db.update_asset_status("nonexistent.pdf", "routed")
        # Should not raise


class TestUpdateAssetPath:
    def test_update_path_after_move(self, db: OpsDB) -> None:
        """Regression: update_asset_path changes the canonical path so
        subsequent lookups by new path succeed."""
        old = f"{INBOX}/report.pdf"
        new = f"{REFERENCE}/01_Product_Docs/report.pdf"
        db.upsert_asset(old, "report.pdf", ".pdf", 100, "2026-01-01T00:00:00", INBOX)

        ok = db.update_asset_path(old, new)
        assert ok is True

        # Old path no longer resolves
        assert db.get_asset(old) is None
        # New path does
        asset = db.get_asset(new)
        assert asset is not None
        assert asset["filename"] == "report.pdf"

    def test_update_path_then_status(self, db: OpsDB) -> None:
        """Regression: update_asset_status works after path is updated."""
        old = f"{INBOX}/deck.pptx"
        new = f"{REFERENCE}/02_Training/deck.pptx"
        db.upsert_asset(old, "deck.pptx", ".pptx", 500, "2026-01-01T00:00:00", INBOX)

        db.update_asset_path(old, new)
        db.update_asset_status(
            new,
            "routed",
            routed_to=new,
            routed_method="series",
            routed_confidence=0.95,
        )

        asset = db.get_asset(new)
        assert asset["status"] == "routed"
        assert asset["routed_to"] == new

    def test_update_path_nonexistent(self, db: OpsDB) -> None:
        """update_asset_path returns False for missing asset."""
        ok = db.update_asset_path("ghost.txt", "new_ghost.txt")
        assert ok is False

    def test_update_path_normalizes_backslashes(self, db: OpsDB) -> None:
        """Backslashes in paths are normalized to forward slashes."""
        db.upsert_asset(
            f"{INBOX}/file.txt", "file.txt", ".txt", 10, "2026-01-01T00:00:00", INBOX
        )
        ok = db.update_asset_path(
            f"{INBOX}\\file.txt",
            f"{PROJECTS}\\file.txt",
        )
        assert ok is True
        assert db.get_asset(f"{PROJECTS}/file.txt") is not None


class TestRevertEvent:
    def test_revert_event(self, db: OpsDB) -> None:
        """Reverting an event marks it as reverted."""
        db.upsert_asset("r.txt", "r.txt", ".txt", 50, "2026-01-01T00:00:00", INBOX)
        db.update_asset_status("r.txt", "routed", routed_to="somewhere")

        asset = db.get_asset("r.txt")
        events = db.get_events_for_asset(asset["id"])
        assert len(events) == 1

        ok = db.revert_event(events[0]["id"])
        assert ok is True

        events_after = db.get_events_for_asset(asset["id"])
        assert events_after[0]["reverted"] == 1

    def test_revert_nonexistent_event(self, db: OpsDB) -> None:
        """Reverting non-existent event returns False."""
        assert db.revert_event(9999) is False

    def test_revert_irreversible_event(self, db: OpsDB) -> None:
        """Reverting an irreversible event returns False."""
        eid = db.log_event("deleted", reversible=False)
        assert db.revert_event(eid) is False

    def test_revert_already_reverted(self, db: OpsDB) -> None:
        """Reverting an already-reverted event returns False."""
        eid = db.log_event("moved")
        db.revert_event(eid)
        assert db.revert_event(eid) is False


class TestPackages:
    def test_create_package(self, db: OpsDB) -> None:
        """Package creation with file count and size."""
        pid = db.create_package(
            folder_name="Cognitive_Friday_S12",
            source_path=f"{REFERENCE}/Cognitive_Friday_S12",
            file_count=5,
            total_size=1024000,
            inferred_topic="Cognitive Planning",
        )
        assert isinstance(pid, int)

        pkg = db.get_package(pid)
        assert pkg is not None
        assert pkg["folder_name"] == "Cognitive_Friday_S12"
        assert pkg["file_count"] == 5
        assert pkg["status"] == "pending"

    def test_update_package_status(self, db: OpsDB) -> None:
        """Package status updates correctly."""
        pid = db.create_package("test", "test/path", 2, 500)
        db.update_package_status(pid, "extracted", destination_path="vault/target")

        pkg = db.get_package(pid)
        assert pkg["status"] == "extracted"
        assert pkg["destination_path"] == "vault/target"
        assert pkg["completed_at"] is not None


class TestStats:
    def test_get_stats(self, db: OpsDB) -> None:
        """Stats returns counts by status."""
        db.upsert_asset("a.pdf", "a.pdf", ".pdf", 100, "2026-01-01T00:00:00", PROJECTS)
        db.upsert_asset("b.txt", "b.txt", ".txt", 200, "2026-01-01T00:00:00", INBOX)
        db.update_asset_status("b.txt", "routed")

        stats = db.get_stats()
        assert stats["total_assets"] == 2
        assert stats["by_status"]["discovered"] == 1
        assert stats["by_status"]["routed"] == 1
        assert PROJECTS in stats["by_folder"]
        assert ".pdf" in stats["top_extensions"]
        assert stats["total_events"] == 1  # one from update_asset_status


class TestForwardSlashPaths:
    def test_forward_slash_paths(self, db: OpsDB) -> None:
        """All paths stored with forward slashes, even on Windows."""
        db.upsert_asset(
            rf"{PROJECTS}\Lenzing\file.pdf",  # Windows-style input
            "file.pdf",
            ".pdf",
            100,
            "2026-01-01T00:00:00",
            PROJECTS,
        )
        asset = db.get_asset(f"{PROJECTS}/Lenzing/file.pdf")
        assert asset is not None
        assert "\\" not in asset["path"]

    def test_backslash_lookup(self, db: OpsDB) -> None:
        """Lookup with backslashes still finds the forward-slash asset."""
        db.upsert_asset("a/b/c.txt", "c.txt", ".txt", 10, "2026-01-01T00:00:00", "a")
        # Look up with backslashes
        asset = db.get_asset(r"a\b\c.txt")
        assert asset is not None


class TestSuggestions:
    def test_add_and_get_suggestions(self, db: OpsDB) -> None:
        """Registry suggestions can be added and retrieved."""
        sid = db.add_suggestion(
            pattern="Cognitive_Friday*",
            proposed_series="cognitive_friday",
            proposed_destination=f"{REFERENCE}/02_Training/CF",
            evidence='{"files": ["CF_S12.mp4", "CF_S13.mp4"], "count": 2}',
        )
        assert isinstance(sid, int)

        pending = db.get_pending_suggestions()
        assert len(pending) == 1
        assert pending[0]["proposed_series"] == "cognitive_friday"

    def test_update_suggestion_status(self, db: OpsDB) -> None:
        """Approving/rejecting a suggestion removes it from pending."""
        sid = db.add_suggestion("pat*", "series", "dest", '{"count": 1}')
        db.update_suggestion_status(sid, "approved")

        pending = db.get_pending_suggestions()
        assert len(pending) == 0


class TestIngestEvents:
    def test_log_event_standalone(self, db: OpsDB) -> None:
        """Events can be logged without an asset."""
        eid = db.log_event(
            "scanned",
            method="overnight",
            reasoning="Full MyWork scan",
        )
        assert isinstance(eid, int)

    def test_get_recent_events(self, db: OpsDB) -> None:
        """Recent events are returned in reverse chronological order."""
        db.log_event("scanned")
        db.log_event("routed")
        db.log_event("extracted")

        recent = db.get_recent_events(limit=2)
        assert len(recent) == 2
        assert recent[0]["action"] == "extracted"
        assert recent[1]["action"] == "routed"
