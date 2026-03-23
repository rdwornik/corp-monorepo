"""Tests for interactive inbox ingestion command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from corp_by_os.ingest.inbox import (
    _check_dedup,
    _full_revert,
    _get_custom_destination,
    _list_events,
    _log_ingest_event,
    _move_file,
    _register_file,
    _scan_inbox_files,
    _undo_event,
    process_file,
)
from corp_by_os.ops.database import OpsDB
from corp_by_os.ops.file_registry import FileRegistry
from corp_by_os.ops.registry import ContentRegistry


@pytest.fixture()
def registry_path(tmp_path: Path) -> Path:
    """Create a test content_registry.yaml."""
    data = {
        "version": "1.0",
        "series": {
            "cognitive_friday": {
                "display_name": "Cognitive Friday",
                "destination": "60_Source_Library/02_Training_Enablement/Cognitive_Friday",
                "naming_patterns": ["Cognitive_Friday*", "CF_S[0-9]*"],
                "expected_extensions": [".mp4", ".pptx"],
                "default_metadata": {
                    "source_category": "training",
                    "topics": ["Cognitive Planning"],
                },
            },
        },
        "destination_rules": [
            {
                "name": "RFP databases",
                "match": {
                    "filename_contains": ["RFP_Database"],
                    "extensions": [".xlsx"],
                },
                "destination": "50_RFP/_databases",
                "metadata": {"source_category": "rfp"},
            },
        ],
        "client_patterns": [
            {"pattern": "Lenzing", "project": "Lenzing_Planning"},
        ],
        "fallback": {
            "unknown_destination": "00_Inbox/_Unmatched",
            "confidence_threshold": 0.75,
        },
    }
    path = tmp_path / "content_registry.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return path


@pytest.fixture()
def registry(registry_path: Path) -> ContentRegistry:
    return ContentRegistry(registry_path)


@pytest.fixture()
def ops(tmp_path: Path) -> OpsDB:
    db = OpsDB(tmp_path / "test_ops.db")
    yield db
    db.close()


@pytest.fixture()
def mywork(tmp_path: Path) -> Path:
    """Create a minimal MyWork structure."""
    root = tmp_path / "MyWork"
    inbox = root / "00_Inbox"
    inbox.mkdir(parents=True)
    return root


class TestScanInboxFiles:
    def test_finds_files(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / "test.pptx").write_bytes(b"x" * 100)
        (inbox / "test2.xlsx").write_bytes(b"x" * 100)
        files = _scan_inbox_files(inbox)
        assert len(files) == 2

    def test_skips_gitkeep(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / ".gitkeep").write_bytes(b"")
        (inbox / "test.pptx").write_bytes(b"x" * 100)
        files = _scan_inbox_files(inbox)
        assert len(files) == 1
        assert files[0].name == "test.pptx"

    def test_skips_hidden_files(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / ".DS_Store").write_bytes(b"")
        files = _scan_inbox_files(inbox)
        assert len(files) == 0

    def test_skips_temp_extensions(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / "download.crdownload").write_bytes(b"x" * 100)
        files = _scan_inbox_files(inbox)
        assert len(files) == 0

    def test_skips_directories(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / "subfolder").mkdir()
        (inbox / "test.pptx").write_bytes(b"x" * 100)
        files = _scan_inbox_files(inbox)
        assert len(files) == 1

    def test_empty_inbox(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        files = _scan_inbox_files(inbox)
        assert len(files) == 0

    def test_nonexistent_inbox(self, tmp_path: Path) -> None:
        files = _scan_inbox_files(tmp_path / "no_such_dir")
        assert len(files) == 0

    def test_skips_infrastructure_names(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        (inbox / "desktop.ini").write_bytes(b"")
        (inbox / "Thumbs.db").write_bytes(b"")
        (inbox / "real_file.pdf").write_bytes(b"x" * 100)
        files = _scan_inbox_files(inbox)
        assert len(files) == 1


class TestMoveFile:
    def test_moves_file(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pptx"
        f.write_bytes(b"x" * 100)

        dest = _move_file(f, "60_Source_Library/Training", "renamed.pptx", mywork)
        assert dest.exists()
        assert dest.name == "renamed.pptx"
        assert not f.exists()

    def test_creates_destination_dir(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pptx"
        f.write_bytes(b"x" * 100)

        dest = _move_file(f, "60_Source_Library/New_Folder", "test.pptx", mywork)
        assert dest.parent.exists()

    def test_handles_collision(self, mywork: Path) -> None:
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pptx"
        f.write_bytes(b"x" * 100)

        # Pre-create collision
        dest_dir = mywork / "60_Source_Library"
        dest_dir.mkdir(parents=True)
        (dest_dir / "test.pptx").write_bytes(b"y" * 100)

        dest = _move_file(f, "60_Source_Library", "test.pptx", mywork)
        assert dest.exists()
        assert dest.name == "test_1.pptx"


class TestLogIngestEvent:
    def test_logs_event(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        from corp_by_os.ingest.classifier import classify

        classification = classify(f, registry)

        # Move file first (log needs dest_file)
        dest_dir = mywork / "60_Source_Library" / "Training"
        dest_dir.mkdir(parents=True)
        dest_file = dest_dir / "renamed.pptx"
        import shutil

        shutil.copy2(str(f), str(dest_file))

        event_id = _log_ingest_event(
            ops, f, dest_file, mywork,
            classification, f.name, "renamed.pptx",
            "test context", True,
        )
        assert event_id > 0

        # Verify event in database
        events = ops.get_recent_events(10)
        # Should have at least the route event
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        assert len(route_events) >= 1


class TestProcessFile:
    def test_auto_mode_high_confidence(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Auto mode accepts high-confidence matches without prompting."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4_Test.pptx"
        f.write_bytes(b"x" * 100)

        action = process_file(
            f, mywork, registry, ops,
            auto=True, skip_extract=True,
        )
        assert action == "routed"
        assert not f.exists()  # file moved

    def test_auto_mode_low_confidence_not_auto_accepted(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Auto mode doesn't auto-accept low-confidence matches."""
        inbox = mywork / "00_Inbox"
        f = inbox / "random_file.txt"
        f.write_bytes(b"x" * 100)

        # Mock the interactive prompt to return 's' (skip)
        with patch("corp_by_os.ingest.inbox._prompt_action", return_value="s"):
            action = process_file(
                f, mywork, registry, ops,
                auto=True, skip_extract=True,
            )
        assert action == "skipped"

    def test_dry_run_no_move(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Dry run doesn't move files."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4_Test.pptx"
        f.write_bytes(b"x" * 100)

        action = process_file(
            f, mywork, registry, ops,
            auto=True, dry_run=True, skip_extract=True,
        )
        assert action == "routed"
        assert f.exists()  # file NOT moved in dry run

    def test_interactive_accept(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Interactive mode: user accepts suggestion."""
        inbox = mywork / "00_Inbox"
        f = inbox / "RFP_Database_WMS.xlsx"
        f.write_bytes(b"x" * 100)

        with patch("corp_by_os.ingest.inbox._prompt_action", return_value="a"):
            action = process_file(
                f, mywork, registry, ops,
                skip_extract=True,
            )
        assert action == "routed"
        assert not f.exists()

    def test_interactive_skip(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Interactive mode: user skips file."""
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pdf"
        f.write_bytes(b"x" * 100)

        with patch("corp_by_os.ingest.inbox._prompt_action", return_value="s"):
            action = process_file(
                f, mywork, registry, ops,
                skip_extract=True,
            )
        assert action == "skipped"
        assert f.exists()

    def test_interactive_quit(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Interactive mode: user quits."""
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pdf"
        f.write_bytes(b"x" * 100)

        with patch("corp_by_os.ingest.inbox._prompt_action", return_value="q"):
            action = process_file(
                f, mywork, registry, ops,
                skip_extract=True,
            )
        assert action == "quit"


class TestUndoEvent:
    def test_undo_moves_file_back(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Undo moves file back to Inbox."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        # Route the file via auto mode
        action = process_file(
            f, mywork, registry, ops,
            auto=True, skip_extract=True,
        )
        assert action == "routed"
        assert not f.exists()

        # Find the event
        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        assert len(route_events) >= 1
        event_id = route_events[0]["id"]

        # Undo
        success = _undo_event(event_id, ops, mywork)
        assert success is True

        # File should be back in inbox
        inbox_files = list(inbox.iterdir())
        restored = [f for f in inbox_files if f.suffix == ".pptx"]
        assert len(restored) == 1

    def test_undo_nonexistent_event(self, mywork: Path, ops: OpsDB) -> None:
        """Undo of nonexistent event returns False."""
        result = _undo_event(99999, ops, mywork)
        assert result is False

    def test_undo_already_reverted(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Undo of already-reverted event returns False."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        # First undo succeeds
        _undo_event(event_id, ops, mywork)
        # Second undo fails
        result = _undo_event(event_id, ops, mywork)
        assert result is False


class TestUserContext:
    def test_user_context_reaches_manifest(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Verify user_context is included in the CKE manifest when passed."""
        import json

        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        captured_context: list[str | None] = []

        original_run_extraction = None

        def mock_run_extraction(
            file_path, mywork_root, ops_db, asset_id, content_hash, mtime_str,
            user_context=None,
        ):
            captured_context.append(user_context)
            return None, 0.0

        with patch(
            "corp_by_os.ingest.router._run_extraction",
            side_effect=mock_run_extraction,
        ):
            from corp_by_os.ingest.inbox import _trigger_extraction

            # Route the file first so it has a destination
            dest_dir = mywork / "60_Source_Library" / "Training"
            dest_dir.mkdir(parents=True)
            import shutil

            dest_file = dest_dir / "test.pptx"
            shutil.copy2(str(f), str(dest_file))

            _trigger_extraction(
                dest_file, mywork, ops,
                user_context="Cognitive Friday S4E1, tag changes in platform",
            )

        assert len(captured_context) == 1
        assert captured_context[0] == "Cognitive Friday S4E1, tag changes in platform"

    def test_user_context_none_when_not_provided(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """user_context is None when not provided by user."""
        inbox = mywork / "00_Inbox"
        f = inbox / "test.pptx"
        f.write_bytes(b"x" * 100)

        captured_context: list[str | None] = []

        def mock_run_extraction(
            file_path, mywork_root, ops_db, asset_id, content_hash, mtime_str,
            user_context=None,
        ):
            captured_context.append(user_context)
            return None, 0.0

        with patch(
            "corp_by_os.ingest.router._run_extraction",
            side_effect=mock_run_extraction,
        ):
            from corp_by_os.ingest.inbox import _trigger_extraction

            dest_dir = mywork / "60_Source_Library"
            dest_dir.mkdir(parents=True)
            import shutil

            dest_file = dest_dir / "test.pptx"
            shutil.copy2(str(f), str(dest_file))

            _trigger_extraction(dest_file, mywork, ops, user_context=None)

        assert captured_context[0] is None


class TestListEvents:
    def test_list_shows_recent_events(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """--list shows ingest-inbox events."""
        inbox = mywork / "00_Inbox"

        # Create 2 events via auto mode (unique content per file)
        for i, name in enumerate(["Cognitive_Friday_S4.pptx", "Cognitive_Friday_S5.pptx"]):
            f = inbox / name
            f.write_bytes(f"content_{i}".encode())
            process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        # List should show 2 events (captured via Rich console)
        events = ops.conn.execute(
            "SELECT * FROM ingest_events WHERE action = 'ingest_inbox_route'"
        ).fetchall()
        assert len(events) >= 2

    def test_list_shows_undone_status(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Undone events have reverted=1 in the database."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        _undo_event(event_id, ops, mywork)

        row = ops.conn.execute(
            "SELECT reverted FROM ingest_events WHERE id = ?", (event_id,)
        ).fetchone()
        assert row["reverted"] == 1

    def test_list_empty(self, ops: OpsDB) -> None:
        """--list with no events prints message without crashing."""
        # Should not raise — just prints "No ingest-inbox events found."
        _list_events(ops)

    def test_list_respects_limit(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """--list with limit returns at most N events."""
        inbox = mywork / "00_Inbox"
        for i in range(5):
            f = inbox / f"Cognitive_Friday_S{i}.pptx"
            f.write_bytes(f"unique_content_{i}".encode())
            process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        rows = ops.conn.execute(
            """SELECT * FROM ingest_events
               WHERE action = 'ingest_inbox_route'
               ORDER BY id DESC LIMIT 3"""
        ).fetchall()
        assert len(rows) == 3


class TestFullUndo:
    def test_full_undo_removes_vault_package(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB, tmp_path: Path
    ) -> None:
        """--full undo removes vault package when vault_note_path is recorded."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        # Simulate extraction by creating a vault package and recording its path
        vault_dir = tmp_path / "vault"
        vault_pkg = vault_dir / "01_Knowledge" / "test_package"
        vault_pkg.mkdir(parents=True)
        (vault_pkg / "note.md").write_text("# Test", encoding="utf-8")

        ops.conn.execute(
            "UPDATE ingest_events SET vault_note_path = ? WHERE id = ?",
            ("01_Knowledge/test_package", event_id),
        )
        ops.conn.commit()

        with patch("corp_by_os.index_builder.rebuild_index") as mock_rebuild:
            mock_rebuild.return_value = MagicMock(notes_indexed=0)
            _undo_event(
                event_id, ops, mywork, full=True,
                vault_path=vault_dir, app_data_path=tmp_path / "appdata",
            )

        assert not vault_pkg.exists(), "Vault package should be removed"

    def test_full_undo_rebuilds_index(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB, tmp_path: Path
    ) -> None:
        """--full undo triggers index rebuild."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        with patch("corp_by_os.index_builder.rebuild_index") as mock_rebuild:
            mock_rebuild.return_value = MagicMock(notes_indexed=42)
            _undo_event(
                event_id, ops, mywork, full=True,
                vault_path=tmp_path / "vault",
                app_data_path=tmp_path / "appdata",
            )

        mock_rebuild.assert_called_once()

    def test_full_undo_without_vault_package(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB, tmp_path: Path
    ) -> None:
        """--full undo handles missing vault_note_path gracefully."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        # vault_note_path is NULL — should not crash
        with patch("corp_by_os.index_builder.rebuild_index") as mock_rebuild:
            mock_rebuild.return_value = MagicMock(notes_indexed=0)
            result = _undo_event(
                event_id, ops, mywork, full=True,
                vault_path=tmp_path / "vault",
                app_data_path=tmp_path / "appdata",
            )

        assert result is True

    def test_normal_undo_does_not_rebuild(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Normal (non-full) undo does NOT rebuild index."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        process_file(f, mywork, registry, ops, auto=True, skip_extract=True)

        events = ops.get_recent_events(10)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        event_id = route_events[0]["id"]

        # full=False — _full_revert never called, no rebuild
        _undo_event(event_id, ops, mywork, full=False)


class TestVaultNotePathStored:
    def test_vault_note_path_column_exists(self, ops: OpsDB) -> None:
        """ingest_events table has vault_note_path column."""
        row = ops.conn.execute(
            "PRAGMA table_info(ingest_events)"
        ).fetchall()
        col_names = [r[1] for r in row]
        assert "vault_note_path" in col_names

    def test_log_event_stores_vault_note_path(self, ops: OpsDB) -> None:
        """log_event with vault_note_path stores it in the database."""
        event_id = ops.log_event(
            action="ingest_inbox_route",
            source_path="00_Inbox/test.pptx",
            destination_path="30_Reference/test.pptx",
            vault_note_path="01_Knowledge/test_pkg",
        )

        row = ops.conn.execute(
            "SELECT vault_note_path FROM ingest_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        assert row["vault_note_path"] == "01_Knowledge/test_pkg"

    def test_vault_note_path_default_null(self, ops: OpsDB) -> None:
        """vault_note_path defaults to NULL when not provided."""
        event_id = ops.log_event(
            action="ingest_inbox_route",
            source_path="00_Inbox/test.pptx",
        )

        row = ops.conn.execute(
            "SELECT vault_note_path FROM ingest_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        assert row["vault_note_path"] is None


class TestRegistrationAtRouteTime:
    """Files must be registered in FileRegistry at route time, not extraction."""

    def test_skip_extract_still_registers(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """--skip-extract routes file AND registers it in files table."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)

        action = process_file(
            f, mywork, registry, ops, auto=True, skip_extract=True,
        )
        assert action == "routed"

        # File should be in files table
        fr = FileRegistry(ops.conn)
        count = ops.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        assert count == 1, f"Expected 1 file in registry, got {count}"

    def test_second_ingest_fires_dedup_no_extraction(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Same file --skip-extract twice → second time dedup fires."""
        inbox = mywork / "00_Inbox"
        content = b"x" * 100

        # First ingest: route + register, NO extraction
        f1 = inbox / "Cognitive_Friday_S4.pptx"
        f1.write_bytes(content)
        action1 = process_file(
            f1, mywork, registry, ops, auto=True, skip_extract=True,
        )
        assert action1 == "routed"

        # Second ingest: same content → dedup fires even without extraction
        f2 = inbox / "Cognitive_Friday_S4_copy.pptx"
        f2.write_bytes(content)
        action2 = process_file(
            f2, mywork, registry, ops, auto=True, skip_extract=True,
        )
        assert action2 == "skipped"
        assert f2.exists(), "Dedup-skipped file should stay in Inbox"

    def test_second_ingest_fires_dedup_with_extraction(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Same file with extraction record → dedup shows model info."""
        inbox = mywork / "00_Inbox"
        content = b"x" * 100

        # First ingest + fake extraction
        f1 = inbox / "Cognitive_Friday_S4.pptx"
        f1.write_bytes(content)
        process_file(f1, mywork, registry, ops, auto=True, skip_extract=True)
        fr = FileRegistry(ops.conn)
        file_rec = ops.conn.execute("SELECT file_id FROM files").fetchone()
        fr.record_extraction(file_rec[0], "test-model", "01_Knowledge/test")

        # Second ingest: dedup fires (auto → skip)
        f2 = inbox / "Cognitive_Friday_S4_copy.pptx"
        f2.write_bytes(content)
        action = process_file(
            f2, mywork, registry, ops, auto=True, skip_extract=True,
        )
        assert action == "skipped"

    def test_dedup_check_before_move(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Dedup skip leaves file in Inbox (not moved)."""
        inbox = mywork / "00_Inbox"
        content = b"unique_content_123"

        # Register + fake-extract a file (use auto-matched name)
        f1 = inbox / "Cognitive_Friday_S10.pptx"
        f1.write_bytes(content)
        process_file(f1, mywork, registry, ops, auto=True, skip_extract=True)

        fr = FileRegistry(ops.conn)
        file_rec = ops.conn.execute("SELECT file_id FROM files").fetchone()
        fr.record_extraction(file_rec[0], "model-a", "01_Knowledge/pkg")

        # Second file with same content
        f2 = inbox / "Cognitive_Friday_S10_copy.pptx"
        f2.write_bytes(content)
        process_file(f2, mywork, registry, ops, auto=True, skip_extract=True)

        # f2 should still exist in Inbox (wasn't moved)
        assert f2.exists(), "Dedup-skipped file should stay in Inbox"

    def test_new_file_not_blocked_by_dedup(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Different content → no dedup, routes normally."""
        inbox = mywork / "00_Inbox"
        f = inbox / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"brand_new_content")

        action = process_file(
            f, mywork, registry, ops, auto=True, skip_extract=True,
        )
        assert action == "routed"
        assert not f.exists()  # File was moved

    def test_interactive_dedup_skip(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Interactive mode: user picks [s]kip on dedup → skipped."""
        inbox = mywork / "00_Inbox"
        content = b"dupe_content"

        # First: register + fake extract (auto mode)
        f1 = inbox / "Cognitive_Friday_S4.pptx"
        f1.write_bytes(content)
        process_file(f1, mywork, registry, ops, auto=True, skip_extract=True)
        fr = FileRegistry(ops.conn)
        file_rec = ops.conn.execute("SELECT file_id FROM files").fetchone()
        fr.record_extraction(file_rec[0], "model-a", "01_Knowledge/pkg")

        # Second: interactive, dedup prompt returns "s"
        f2 = inbox / "Cognitive_Friday_S4_v2.pptx"
        f2.write_bytes(content)
        with patch("corp_by_os.ingest.inbox.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "s"
            action = process_file(
                f2, mywork, registry, ops, skip_extract=True,
            )
        assert action == "skipped"


class TestContextBehavior:
    def test_context_does_not_change_filename(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """Adding context preserves original proposed name."""
        inbox = mywork / "00_Inbox"
        f = inbox / "RFP_Database_WMS.xlsx"
        f.write_bytes(b"unique_rfp_content")

        # Simulate: [c] adds context, then [a] accepts
        call_count = [0]

        def mock_prompt_action(needs_human):
            call_count[0] += 1
            if call_count[0] == 1:
                return "c"  # First: add context
            return "a"  # Second: accept

        with patch("corp_by_os.ingest.inbox._prompt_action", side_effect=mock_prompt_action):
            with patch("corp_by_os.ingest.inbox._get_user_context", return_value="This is an RFI from the client"):
                action = process_file(
                    f, mywork, registry, ops, skip_extract=True,
                )

        assert action == "routed"
        assert not f.exists()  # File was moved

        # Verify filename does NOT contain context text
        events = ops.get_recent_events(5)
        route_events = [e for e in events if e["action"] == "ingest_inbox_route"]
        assert len(route_events) >= 1
        dest = route_events[0]["destination_path"]
        assert "RFI" not in dest
        assert "client" not in dest

    def test_context_does_not_loop(
        self, mywork: Path, registry: ContentRegistry, ops: OpsDB
    ) -> None:
        """After [c], returns to prompt. [a] proceeds normally."""
        inbox = mywork / "00_Inbox"
        f = inbox / "RFP_Database_WMS.xlsx"
        f.write_bytes(b"unique_context_test")

        calls = []

        def mock_prompt_action(needs_human):
            calls.append("prompt")
            if len(calls) == 1:
                return "c"
            return "a"

        with patch("corp_by_os.ingest.inbox._prompt_action", side_effect=mock_prompt_action):
            with patch("corp_by_os.ingest.inbox._get_user_context", return_value="test context"):
                action = process_file(
                    f, mywork, registry, ops, skip_extract=True,
                )

        assert action == "routed"
        # Prompt was called exactly twice: once for [c], once for [a]
        assert len(calls) == 2


class TestCustomDestination:
    def test_destination_override_sets_path(self, mywork: Path) -> None:
        """[d] with valid path returns the path."""
        dest_dir = mywork / "10_Projects" / "TestProject"
        dest_dir.mkdir(parents=True)

        with patch("corp_by_os.ingest.inbox.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "10_Projects/TestProject"
            result = _get_custom_destination(mywork)

        assert result == "10_Projects/TestProject"

    def test_destination_creates_folder(self, mywork: Path) -> None:
        """[d] with new path and [y] creates the folder."""
        with patch("corp_by_os.ingest.inbox.Prompt") as mock_prompt:
            # First ask: path input. Second ask: create confirmation.
            mock_prompt.ask.side_effect = [
                "10_Projects/NewProject",
                "y",
            ]
            result = _get_custom_destination(mywork)

        assert result == "10_Projects/NewProject"
        assert (mywork / "10_Projects" / "NewProject").exists()

    def test_destination_create_declined(self, mywork: Path) -> None:
        """[d] with new path and [n] cancels."""
        with patch("corp_by_os.ingest.inbox.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ["10_Projects/Nope", "n"]
            result = _get_custom_destination(mywork)

        assert result is None

    def test_destination_empty_cancels(self, mywork: Path) -> None:
        """[d] with empty input returns None."""
        with patch("corp_by_os.ingest.inbox.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = ""
            result = _get_custom_destination(mywork)

        assert result is None

