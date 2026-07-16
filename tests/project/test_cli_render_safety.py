"""CLI-level safety regression tests for ``cpe render`` (ADR-27 Decision 1).

Covers the ``corp.project.cli.render`` command's exception handling for the
centralized OneDrive/path-containment guards, as distinct from the
lower-level guard unit tests in ``tests/safety/test_onedrive_guard.py`` and
the ``render_project`` guard test in ``tests/test_cleanup/``.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from corp.project.cli import cli


def test_render_onedrive_target_exits_nonzero_not_traceback(tmp_path: Path) -> None:
    """``cpe render`` on a OneDrive-Blue-Yonder project path must exit 1 with
    a clean message, not an uncaught traceback.

    ``render_project`` raises ``OneDriveSafetyError`` natively (ADR-27
    Decision 1); the CLI must catch it alongside ``(FileNotFoundError,
    ValueError)``. The guard fires before any CKE-output check, so no
    fixture extraction data is needed here.
    """
    onedrive_project = tmp_path / "OneDrive - Blue Yonder" / "someproj"
    onedrive_project.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(onedrive_project)])

    assert result.exit_code == 1, (
        f"expected clean exit 1, got {result.exit_code}: {result.output}"
    )
    assert result.exception is None or isinstance(result.exception, SystemExit), (
        f"expected the CLI to catch the guard error, not propagate a "
        f"traceback: {result.exception!r}"
    )
    assert "OneDrive" in result.output or "synced" in result.output, (
        f"expected a clean OneDrive-safety message in CLI output: {result.output!r}"
    )
