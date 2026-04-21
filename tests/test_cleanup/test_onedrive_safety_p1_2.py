"""Regression: moves.yaml must reject path-traversal and absolute paths.

Failing-first tests for P1-2 (see docs/audits/2026-04-21-p1-verification.md).
executor.py joins untrusted strings from moves.yaml onto mywork_root without
resolution; a ``../../`` source escapes the root. These tests exercise both
the runtime guard (caller-side) and the load-time schema validator.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from corp.cleanup.errors import PathTraversalError
from corp.cleanup.executor import execute_moves
from corp.schema.folder_names import INBOX


def _write_moves(path: Path, entries: list[dict]) -> None:
    path.write_text(
        yaml.dump({"version": "1.0", "moves": entries}),
        encoding="utf-8",
    )


# --- Runtime guard: source escapes mywork_root via ../ ---------------------


def test_execute_refuses_parent_traversal_in_source(tmp_path: Path) -> None:
    """An approved entry with ``..`` segments in source must fail closed."""
    mywork = tmp_path / "MyWork"
    (mywork / INBOX).mkdir(parents=True)

    # Create a file outside mywork that an attacker might target.
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("secret", encoding="utf-8")

    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": "../outside_secret.txt",
                "action": "delete",
                "destination": "DELETE",
                "proposed_name": "outside_secret.txt",
                "approved": True,
            },
        ],
    )

    # Schema layer (MoveEntry.from_dict) catches at load time — assert the
    # exact exception class so a broken runtime guard can't hide behind this.
    with pytest.raises(ValueError, match="traversal|\\.\\."):
        execute_moves(moves_file, mywork)

    assert outside.exists(), "File outside mywork_root must not be deleted"


def test_execute_refuses_absolute_source(tmp_path: Path) -> None:
    """Absolute path in source must be refused (even if it happens to be inside mywork)."""
    mywork = tmp_path / "MyWork"
    (mywork / INBOX).mkdir(parents=True)
    inside = mywork / INBOX / "victim.txt"
    inside.write_text("victim", encoding="utf-8")

    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": str(inside),  # absolute path — schema must reject
                "action": "delete",
                "destination": "DELETE",
                "proposed_name": "victim.txt",
                "approved": True,
            },
        ],
    )

    with pytest.raises(ValueError, match="absolute"):
        execute_moves(moves_file, mywork)


def test_execute_refuses_parent_traversal_in_destination(tmp_path: Path) -> None:
    """``..`` in destination must be rejected just like source."""
    mywork = tmp_path / "MyWork"
    (mywork / INBOX).mkdir(parents=True)
    (mywork / INBOX / "file.txt").write_text("x", encoding="utf-8")

    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/file.txt",
                "action": "move",
                "destination": "../escape_dir",
                "proposed_name": "file.txt",
                "approved": True,
            },
        ],
    )

    with pytest.raises(ValueError, match="traversal|\\.\\."):
        execute_moves(moves_file, mywork)


def test_execute_refuses_parent_traversal_in_proposed_name(tmp_path: Path) -> None:
    """``..`` inside proposed_name must be rejected."""
    mywork = tmp_path / "MyWork"
    (mywork / INBOX).mkdir(parents=True)
    (mywork / INBOX / "file.txt").write_text("x", encoding="utf-8")

    moves_file = tmp_path / "moves.yaml"
    _write_moves(
        moves_file,
        [
            {
                "source": f"{INBOX}/file.txt",
                "action": "move",
                "destination": "20_Extra_Initiatives",
                "proposed_name": "../escape.txt",
                "approved": True,
            },
        ],
    )

    with pytest.raises(ValueError, match="traversal|\\.\\."):
        execute_moves(moves_file, mywork)


# --- Schema-layer validation (unit) ----------------------------------------


def test_move_entry_schema_rejects_parent_traversal() -> None:
    """The MoveEntry schema/validator rejects ``..`` segments at load time."""
    from corp.cleanup.executor import MoveEntry  # schema lands in Step 3

    with pytest.raises(ValueError, match="traversal|\\.\\."):
        MoveEntry(
            source="../../etc/passwd",
            action="delete",
            destination="DELETE",
            proposed_name="passwd",
            approved=True,
        )


def test_move_entry_schema_rejects_absolute_source() -> None:
    from corp.cleanup.executor import MoveEntry

    with pytest.raises(ValueError, match="absolute"):
        MoveEntry(
            source="C:/Users/1028120/secret.txt",
            action="delete",
            destination="DELETE",
            proposed_name="secret.txt",
            approved=True,
        )


def test_move_entry_schema_accepts_clean_relative() -> None:
    from corp.cleanup.executor import MoveEntry

    entry = MoveEntry(
        source=f"{INBOX}/file.txt",
        action="move",
        destination="20_Extra_Initiatives",
        proposed_name="file.txt",
        approved=True,
    )
    assert entry.source == f"{INBOX}/file.txt"


# --- Runtime-guard-only validation (bypasses schema layer) -----------------


def test_assert_within_root_rejects_escape(tmp_path: Path) -> None:
    """Runtime guard catches an escape even when schema did not fire.

    Proves _assert_within_root() carries its own weight — simulates the case
    where a symlink/junction or a programmatic caller slipped a bypass past
    MoveEntry validation.
    """
    from corp.cleanup.executor import _assert_within_root

    mywork = tmp_path / "MyWork"
    mywork.mkdir()
    escaped = tmp_path / "outside" / "secret.txt"

    with pytest.raises(PathTraversalError, match="escapes mywork_root"):
        _assert_within_root(escaped, mywork, field="source")


def test_assert_within_root_accepts_path_inside_root(tmp_path: Path) -> None:
    """Runtime guard allows paths genuinely inside the root."""
    from corp.cleanup.executor import _assert_within_root

    mywork = tmp_path / "MyWork"
    mywork.mkdir()
    inside = mywork / INBOX / "file.txt"

    # Must not raise — file need not exist (strict=False).
    _assert_within_root(inside, mywork, field="source")
