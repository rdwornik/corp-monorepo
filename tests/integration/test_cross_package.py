"""Cross-package integration tests for monorepo."""

import importlib


def test_cke_imports_meta():
    """CKE can import from corp-os-meta."""
    from corp.schema.models import NoteFrontmatter

    assert NoteFrontmatter is not None


def test_corp_by_os_imports_meta():
    """Corp-by-os can import from corp-os-meta."""
    from corp.schema.models import NoteFrontmatter

    assert NoteFrontmatter is not None


def test_cke_namespace():
    """CKE uses correct namespace."""
    from corp.extractor._paths import REPO_ROOT

    assert (REPO_ROOT / "pyproject.toml").exists()


def test_cke_paths_resolve():
    """CKE _paths.py resolves to package root, not monorepo root."""
    from corp.extractor._paths import CONFIG_DIR, REPO_ROOT

    assert (REPO_ROOT / "pyproject.toml").exists()
    assert CONFIG_DIR.exists()
    # Should NOT be the monorepo root
    assert REPO_ROOT.name == "corp-knowledge-extractor"


def test_all_clis_importable():
    """All CLI entry points are importable."""
    importlib.import_module("corp.schema.cli")
    importlib.import_module("corp.cli")
    importlib.import_module("corp.project.cli")


def test_corp_by_os_config_loads():
    """Corp-by-os config module is importable."""
    from corp.config import AppConfig

    assert AppConfig is not None


def test_rfp_agent_importable():
    """RFP agent uses new namespace."""
    from corp.rfp.llm_router import LLMRouter

    assert LLMRouter is not None


def test_rfp_agent_paths_resolve():
    """RFP agent _paths.py resolves to package root."""
    from corp.rfp._paths import REPO_ROOT

    assert (REPO_ROOT / "pyproject.toml").exists()
    assert REPO_ROOT.name == "corp-rfp-agent"


def test_com_importable():
    """Opportunity manager is importable."""
    from corp.opportunity.cli import cli

    assert cli is not None
