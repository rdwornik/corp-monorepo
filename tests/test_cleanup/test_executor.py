"""Tests for cleanup executor."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from corp.cleanup.executor import _guard_onedrive, execute_moves
from corp.schema.folder_names import ADMIN, INBOX, REF_RFP_LIBRARY, REFERENCE


def _write_moves(path, entries):
    """Helper to write a moves.yaml file."""
    data = {"version": "1.0", "moves": entries}
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_execute_approved_only(mywork_cleanup, tmp_path):
    """Only moves with approved: true are executed."""
    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/Sprint Planning.pptx",
                "action": "move",
                "destination": "20_Extra_Initiatives",
                "proposed_name": "Sprint Planning.pptx",
                "approved": True,
            },
            {
                "source": f"{INBOX}/MeetingNotes_Q4_Review.txt",
                "action": "move",
                "destination": "20_Extra_Initiatives",
                "proposed_name": "MeetingNotes_Q4_Review.txt",
                "approved": False,
            },
            {
                "source": f"{INBOX}/RFP_Response_Final.txt",
                "action": "move",
                "destination": f"{REFERENCE}/{REF_RFP_LIBRARY}",
                "proposed_name": "RFP_Response_Final.txt",
                "approved": None,
            },
        ],
    )

    result = execute_moves(moves_file, mywork_cleanup)

    assert result.moved == 1
    assert result.skipped == 2
    # Approved file was moved
    assert (mywork_cleanup / "20_Extra_Initiatives" / "Sprint Planning.pptx").exists()
    # Non-approved files stay
    assert (mywork_cleanup / INBOX / "MeetingNotes_Q4_Review.txt").exists()
    assert (mywork_cleanup / INBOX / "RFP_Response_Final.txt").exists()


def test_execute_dry_run(mywork_cleanup, tmp_path):
    """Dry run doesn't move anything."""
    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/Sprint Planning.pptx",
                "action": "move",
                "destination": "20_Extra_Initiatives",
                "proposed_name": "Sprint Planning.pptx",
                "approved": True,
            },
        ],
    )

    result = execute_moves(moves_file, mywork_cleanup, dry_run=True)

    assert result.moved == 1  # counted but not actually moved
    # File still in original location
    assert (mywork_cleanup / INBOX / "Sprint Planning.pptx").exists()
    assert not (mywork_cleanup / "20_Extra_Initiatives" / "Sprint Planning.pptx").exists()


def test_execute_creates_destination(mywork_cleanup, tmp_path):
    """Creates destination folder if it doesn't exist."""
    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/Sprint Planning.pptx",
                "action": "move",
                "destination": "20_Extra_Initiatives/Sprint_Planning_2026",
                "proposed_name": "Sprint Planning.pptx",
                "approved": True,
            },
        ],
    )

    result = execute_moves(moves_file, mywork_cleanup)

    assert result.moved == 1
    dest = mywork_cleanup / "20_Extra_Initiatives" / "Sprint_Planning_2026" / "Sprint Planning.pptx"
    assert dest.exists()


def test_execute_delete_action(mywork_cleanup, tmp_path):
    """Delete action removes the file."""
    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{REFERENCE}/02_Training_Enablement/bookmark.url",
                "action": "delete",
                "destination": "DELETE",
                "proposed_name": "bookmark.url",
                "approved": True,
            },
        ],
    )

    result = execute_moves(moves_file, mywork_cleanup)

    assert result.deleted == 1
    assert not (
        mywork_cleanup / REFERENCE / "02_Training_Enablement" / "bookmark.url"
    ).exists()


def test_execute_missing_source(mywork_cleanup, tmp_path):
    """Missing source file counts as failed."""
    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/nonexistent.txt",
                "action": "move",
                "destination": ADMIN,
                "proposed_name": "nonexistent.txt",
                "approved": True,
            },
        ],
    )

    result = execute_moves(moves_file, mywork_cleanup)
    assert result.failed == 1


# --- OneDrive safety guard ---


def test_guard_onedrive_blocks_onedrive_path():
    """OneDrive paths are blocked by safety guard."""
    with pytest.raises(RuntimeError, match="BLOCKED"):
        _guard_onedrive(Path("C:/Users/rob/OneDrive - Blue Yonder/MyWork/file.txt"))


def test_guard_onedrive_allows_local_path():
    """Local paths pass the guard without error."""
    _guard_onedrive(Path("C:/Users/rob/Documents/MyWork/file.txt"))


def test_execute_blocks_onedrive_source(tmp_path):
    """Execute refuses to act on OneDrive source paths."""
    # Create a fake mywork root that contains "OneDrive - Blue Yonder"
    onedrive_root = tmp_path / "OneDrive - Blue Yonder" / "MyWork"
    inbox = onedrive_root / INBOX
    inbox.mkdir(parents=True)
    (inbox / "test.txt").write_text("test", encoding="utf-8")

    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/test.txt",
                "action": "delete",
                "destination": "DELETE",
                "proposed_name": "test.txt",
                "approved": True,
            },
        ],
    )

    with pytest.raises(RuntimeError, match="BLOCKED"):
        execute_moves(moves_file, onedrive_root)
