"""CLI-level safety regression tests for ``cpe render`` (ADR-27 Decision 1).

Covers the ``corp.project.cli.render`` command's exception handling for the
centralized OneDrive/path-containment guards, as distinct from the
lower-level guard unit tests in ``tests/safety/test_onedrive_guard.py`` and
the ``render_project`` guard test in ``tests/test_cleanup/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from corp.project.cli import cli


def _create_extraction(project_path: Path, file_id: str = "file-1") -> None:
    """Minimal CKE output fixture so render_project produces an index.md.

    Mirrors ``tests/project/test_renderer.py::_create_extraction``, trimmed
    to the fields ``render_project`` actually reads.
    """
    extract_dir = project_path / "_knowledge" / "_cke_output" / file_id / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "id": file_id,
        "source_file": f"C:/fake/{file_id}.pdf",
        "doc_type": "document",
        "project": "test_project",
        "title": "Test Doc",
        "summary": "A summary long enough to be included as a fact entry for this fixture.",
        "topics": ["SLA"],
        "products": ["Blue Yonder Platform"],
        "people": [],
        "key_points": ["A detailed key point long enough to pass the length filter."],
        "slides_count": 0,
        "links_line": "",
        "validation_result": "valid",
        "unknown_terms": [],
        "processed_at": "2026-03-06T12:00:00",
    }
    with open(extract_dir / "extract.json", "w", encoding="utf-8") as f:
        json.dump(data, f)


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


class TestCopyToVaultGuards:
    """D6 close: ``cpe render --copy-to-vault`` guards its destination.

    ``VAULT_PATH`` is monkeypatched in every case (even where the OneDrive
    guard fires before ``PipelineConfig.production()`` is ever evaluated) so
    none of these tests can fall through to a real, ambient vault path.
    """

    def test_onedrive_destination_raises_onedrive_safety_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault_root"))
        project = tmp_path / "myproj_onedrive_dest"
        project.mkdir()
        _create_extraction(project)

        dest = tmp_path / "OneDrive - Blue Yonder" / "vault_landing"

        runner = CliRunner()
        result = runner.invoke(cli, ["render", str(project), "--copy-to-vault", str(dest)])

        assert result.exit_code != 0, result.output
        assert "OneDrive" in result.output or "synced" in result.output, result.output
        # Nothing was written to the refused destination.
        assert not dest.exists()

    def test_destination_outside_vault_root_raises_path_traversal_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vault_root = tmp_path / "vault_root"
        monkeypatch.setenv("VAULT_PATH", str(vault_root))
        project = tmp_path / "myproj_outside_root"
        project.mkdir()
        _create_extraction(project)

        # A sibling of vault_root, not inside it.
        outside_dest = tmp_path / "outside_dest"

        runner = CliRunner()
        result = runner.invoke(cli, ["render", str(project), "--copy-to-vault", str(outside_dest)])

        assert result.exit_code != 0, result.output
        assert "root" in result.output or "escapes" in result.output, result.output
        assert not outside_dest.exists()

    def test_destination_inside_vault_root_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Control: a legitimate destination inside the configured vault root
        must still work — the guards must not break normal use."""
        vault_root = tmp_path / "vault_root"
        monkeypatch.setenv("VAULT_PATH", str(vault_root))
        project = tmp_path / "myproj_inside_root"
        project.mkdir()
        _create_extraction(project)

        inside_dest = vault_root / "landing"

        runner = CliRunner()
        result = runner.invoke(cli, ["render", str(project), "--copy-to-vault", str(inside_dest)])

        assert result.exit_code == 0, result.output
        copied = inside_dest / project.name / "index.md"
        assert copied.exists()

    def test_existing_destination_symlink_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A pre-existing symlink at the destination is refused no-follow —
        ``shutil.copy2`` would otherwise follow it out of the vault or into
        OneDrive even when the link's own path text looks safe (Codex
        2026-07-17). Real symlink creation needs privileges on Windows, so we
        make the production guard's ``Path.is_symlink()`` report the dest dir
        as a link (the same simulate-resolution technique as
        ``tests/test_cleanup/test_onedrive_safety_symlink.py``)."""
        vault_root = tmp_path / "vault_root"
        monkeypatch.setenv("VAULT_PATH", str(vault_root))
        project = tmp_path / "myproj_symlink"
        project.mkdir()
        _create_extraction(project)
        dest = vault_root / "landing"

        def fake_is_symlink(self: Path) -> bool:
            # Only the copy-to-vault dest dir (name == project.name, under dest)
            # reports as a symlink; nothing else in the tree is touched.
            return self.name == project.name and str(self).startswith(str(dest))

        monkeypatch.setattr(Path, "is_symlink", fake_is_symlink, raising=True)

        runner = CliRunner()
        result = runner.invoke(cli, ["render", str(project), "--copy-to-vault", str(dest)])

        assert result.exit_code != 0, result.output
        assert "symlink" in result.output.lower(), result.output
        assert not (dest / project.name / "index.md").exists()


def test_render_personal_onedrive_path_still_refused_broad(tmp_path: Path) -> None:
    """Centralization must not narrow the renderer's protection (Codex
    2026-07-17): a personal ``OneDrive`` path (no ``"- Blue Yonder"``) is still
    refused, because ``render_project`` guards with ``strict=False``. A
    ``strict=True`` guard would let this write through."""
    # 'OneDrive' but NOT the canonical 'OneDrive - Blue Yonder' zone.
    personal = tmp_path / "OneDrive" / "personal_proj"
    personal.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(personal)])

    assert result.exit_code == 1, result.output
    assert "OneDrive" in result.output or "synced" in result.output, result.output
