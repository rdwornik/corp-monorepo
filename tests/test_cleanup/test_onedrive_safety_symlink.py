"""Regression: every OneDrive guard must resolve paths before the substring check.

Failing-first tests for the Codex /review HIGH findings H-C1 and H-C2
(see docs/audits/2026-04-21-codex-hotfix-review.md).

The substring guard used at four sites —
  - cleanup/disk.py::_guard_onedrive
  - actions/_helpers.py::_guard_writable
  - cleanup/executor.py::_guard_onedrive
  - project/renderer.py::render_project (inline)
— is bypassable by a Windows junction or symlink whose text does not
contain "OneDrive - Blue Yonder" but whose ``.resolve()`` does. These
tests mock ``Path.resolve`` so no real symlink is created on CI.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from corp.actions._helpers import _guard_writable
from corp.cleanup.disk import _guard_onedrive as _disk_guard_onedrive
from corp.cleanup.errors import OneDriveSafetyError
from corp.cleanup.executor import _guard_onedrive as _executor_guard_onedrive
from corp.project.renderer import render_project

_RESOLVED_ONEDRIVE = Path(
    "C:/Users/1028120/OneDrive - Blue Yonder/MyWork_OneDrive/real/target.txt"
)


def _mock_resolve_returns(target: Path):
    """Return an autospec replacement for Path.resolve that returns ``target``."""

    def _fake_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
        return target

    return _fake_resolve


def test_disk_guard_catches_resolved_onedrive_via_symlink(tmp_path: Path) -> None:
    """disk.py ``_guard_onedrive`` must resolve before checking the substring."""
    fake = tmp_path / "looks_innocent_junction"
    fake.touch()

    with patch.object(Path, "resolve", _mock_resolve_returns(_RESOLVED_ONEDRIVE)):
        with pytest.raises(OneDriveSafetyError, match="synced|OneDrive"):
            _disk_guard_onedrive(fake)


def test_helpers_guard_writable_catches_resolved_onedrive(tmp_path: Path) -> None:
    """``_guard_writable(path, writable=True)`` must resolve before checking."""
    fake = tmp_path / "project_junction"
    fake.mkdir()

    with patch.object(Path, "resolve", _mock_resolve_returns(_RESOLVED_ONEDRIVE)):
        with pytest.raises(OneDriveSafetyError, match="synced|OneDrive"):
            _guard_writable(fake, writable=True)


def test_executor_guard_catches_resolved_onedrive(tmp_path: Path) -> None:
    """executor.py ``_guard_onedrive`` (pre-existing) must resolve before checking."""
    fake = tmp_path / "move_junction"
    fake.touch()

    with patch.object(Path, "resolve", _mock_resolve_returns(_RESOLVED_ONEDRIVE)):
        with pytest.raises(OneDriveSafetyError, match="synced|OneDrive|BLOCKED"):
            _executor_guard_onedrive(fake)


def test_renderer_guard_catches_resolved_onedrive(tmp_path: Path) -> None:
    """project/renderer.py inline guard must resolve before checking.

    renderer.render_project raises ValueError for backward compatibility
    with ``corp.project.cli`` which catches ``(FileNotFoundError, ValueError)``.
    After the fix the guard still raises ValueError, just for a resolved
    synced-tree path too.
    """
    fake = tmp_path / "innocent_project_junction"
    fake.mkdir()

    resolved_into_onedrive = Path(
        "C:/Users/1028120/OneDrive - Blue Yonder/MyWork_OneDrive/real_project"
    )

    with patch.object(Path, "resolve", _mock_resolve_returns(resolved_into_onedrive)):
        with pytest.raises(ValueError, match="synced|OneDrive"):
            render_project(fake)


# --- Fail-closed behavior when resolve() itself fails ---------------------


def test_disk_guard_fails_closed_on_resolve_oserror(tmp_path: Path) -> None:
    """If ``Path.resolve`` raises, guard must refuse (fail-closed)."""
    fake = tmp_path / "unresolvable"
    fake.touch()

    def _raising_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
        raise OSError("UNC path resolution failed")

    with patch.object(Path, "resolve", _raising_resolve):
        with pytest.raises(OneDriveSafetyError, match="resolve|verify"):
            _disk_guard_onedrive(fake)


def test_helpers_guard_writable_fails_closed_on_resolve_oserror(tmp_path: Path) -> None:
    fake = tmp_path / "unresolvable_project"
    fake.mkdir()

    def _raising_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
        raise OSError("junction cycle")

    with patch.object(Path, "resolve", _raising_resolve):
        with pytest.raises(OneDriveSafetyError, match="resolve|verify"):
            _guard_writable(fake, writable=True)
