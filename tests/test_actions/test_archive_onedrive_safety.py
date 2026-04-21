"""Regression: archive_project must refuse OneDrive-resolved project paths.

Failing-first tests for P1-3 (see docs/audits/2026-04-21-p1-verification.md).
_resolve_project_path() returns ``ProjectSummary.onedrive_path`` directly;
archive_project() then calls shutil.move() on it. These tests assert the
write-intent guard at _resolve_project_path(..., writable=True).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from corp.actions._helpers import _resolve_project_path
from corp.actions.archive_actions import archive_project
from corp.cleanup.errors import OneDriveSafetyError


def test_archive_project_refuses_onedrive_resolved_path(
    app_config, tmp_path: Path
) -> None:
    """archive_project() fails closed when resolver returns a OneDrive path."""
    onedrive_project = (
        tmp_path / "OneDrive - Blue Yonder" / "MyWork" / "01_Projects" / "Lenzing"
    )
    onedrive_project.mkdir(parents=True)
    (onedrive_project / "marker.txt").write_text("synced", encoding="utf-8")

    class _Resolved:
        project_id = "lenzing"
        onedrive_path = onedrive_project
        vault_path = None

    with patch("corp.project_resolver.resolve_project", return_value=_Resolved()):
        with pytest.raises(OneDriveSafetyError, match="OneDrive"):
            archive_project({"project": "Lenzing", "reason": "test"})

    # Project dir must not be moved.
    assert onedrive_project.exists()
    assert (onedrive_project / "marker.txt").exists()


def test_resolve_project_path_writable_flag_blocks_onedrive(tmp_path: Path) -> None:
    """_resolve_project_path(..., writable=True) refuses OneDrive-backed resolutions."""
    onedrive_project = (
        tmp_path / "OneDrive - Blue Yonder" / "MyWork" / "01_Projects" / "Sample"
    )
    onedrive_project.mkdir(parents=True)

    class _Resolved:
        project_id = "sample"
        onedrive_path = onedrive_project
        vault_path = None

    with patch("corp.project_resolver.resolve_project", return_value=_Resolved()):
        with pytest.raises(OneDriveSafetyError, match="OneDrive"):
            _resolve_project_path("Sample", {}, writable=True)


def test_resolve_project_path_default_allows_onedrive_read(tmp_path: Path) -> None:
    """Default (writable=False) still returns OneDrive paths for read-only callers."""
    onedrive_project = (
        tmp_path / "OneDrive - Blue Yonder" / "MyWork" / "01_Projects" / "Sample"
    )
    onedrive_project.mkdir(parents=True)

    class _Resolved:
        project_id = "sample"
        onedrive_path = onedrive_project
        vault_path = None

    with patch("corp.project_resolver.resolve_project", return_value=_Resolved()):
        path = _resolve_project_path("Sample", {})
        assert path == onedrive_project
