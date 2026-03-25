"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Global API keys (Documents/.secrets/.env)
_global_env = Path.home() / "Documents" / ".secrets" / ".env"
if _global_env.exists():
    load_dotenv(_global_env, override=False)

from corp_opportunity_manager.config import AppConfig


@pytest.fixture
def tmp_projects(tmp_path: Path) -> Path:
    """Temporary projects root directory."""
    d = tmp_path / "projects"
    d.mkdir()
    return d


@pytest.fixture
def tmp_templates(tmp_path: Path) -> Path:
    """Temporary templates root with a dummy deck template."""
    d = tmp_path / "templates"
    d.mkdir()
    # Create a dummy pptx file (just needs to exist for copy tests)
    (d / "BY_Discovery_Template.pptx").write_bytes(b"FAKE_PPTX_CONTENT")
    return d


@pytest.fixture
def app_config(tmp_projects: Path, tmp_templates: Path, tmp_path: Path) -> AppConfig:
    """AppConfig pointing at temp directories."""
    return AppConfig(
        projects_root=tmp_projects,
        archive_root=tmp_path / "archive",
        templates_root=tmp_templates,
        project_codes_excel=None,
        naming={
            "folder_pattern": "{client}_{product}",
            "pptx_pattern": "{client}_{date}_{topic}.pptx",
            "date_format": "%Y-%m-%d",
        },
        templates={"discovery_deck": "BY_Discovery_Template.pptx"},
        folder_structure={"create_dirs": ["_knowledge"]},
        stages=[
            "discovery",
            "qualification",
            "rfp",
            "proposal",
            "negotiation",
            "won",
            "lost",
            "archived",
        ],
        products=["Planning", "WMS", "TMS", "CatMan", "Network", "Platform"],
    )
