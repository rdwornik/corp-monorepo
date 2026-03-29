"""Shared pytest fixtures for corp-project-extractor tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a temporary directory resembling a project root."""
    (tmp_path / "_knowledge").mkdir()
    (tmp_path / "_extracted").mkdir()
    return tmp_path
