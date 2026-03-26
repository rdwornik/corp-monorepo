"""Configuration — loads from .env + agents.yaml.

Single frozen AppConfig dataclass. Cached via lru_cache.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Application configuration — immutable after creation."""

    vault_path: Path
    mywork_root: Path
    projects_root: Path
    templates_root: Path
    archive_root: Path
    app_data_path: Path
    repo_path: Path
    agents: dict[str, Any] = field(default_factory=dict)
    index_extra_roots: tuple[Path, ...] = ()


def _expand_path(raw: str) -> Path:
    """Expand env vars and resolve path."""
    return Path(os.path.expandvars(raw)).resolve()


def _load_agents(repo_path: Path) -> dict[str, Any]:
    """Load agent registry from config/agents.yaml."""
    agents_file = repo_path / "config" / "agents.yaml"
    if agents_file.exists():
        try:
            with open(agents_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("agents", {})
        except yaml.YAMLError as e:
            import logging

            logging.getLogger(__name__).warning("Failed to parse agents.yaml: %s", e)
            return {}
    return {}


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache application config.

    Reads from .env file in repo root, falls back to environment variables.
    """
    repo_path = Path(__file__).resolve().parent.parent.parent

    # Global API keys (Documents/.secrets/.env)
    _global_env = Path.home() / "Documents" / ".secrets" / ".env"
    if _global_env.exists():
        load_dotenv(_global_env, override=False)

    # Local .env (project-specific vars only)
    load_dotenv(repo_path / ".env", override=False)

    _local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    _home_docs = Path.home() / "Documents"
    vault_path = os.environ.get(
        "VAULT_PATH",
        str(_home_docs / "ObsidianVault"),
    )
    projects_root = os.environ.get(
        "PROJECTS_ROOT",
        str(_home_docs / "MyWork" / "10_Projects"),
    )
    templates_root = os.environ.get(
        "TEMPLATES_ROOT",
        str(_home_docs / "MyWork" / "30_Templates"),
    )
    archive_root = os.environ.get(
        "ARCHIVE_ROOT",
        str(_home_docs / "MyWork" / "80_Archive"),
    )
    app_data_path = os.environ.get(
        "APP_DATA_PATH",
        str(Path(_local_appdata) / "corp-by-os"),
    )
    mywork_root = os.environ.get(
        "MYWORK_ROOT",
        str(_home_docs / "MyWork"),
    )

    # Extra index roots (e.g. rfp_kb) — semicolon-separated paths
    extra_roots_raw = os.environ.get("INDEX_EXTRA_ROOTS", "")
    extra_roots = tuple(_expand_path(p.strip()) for p in extra_roots_raw.split(";") if p.strip())

    return AppConfig(
        vault_path=_expand_path(vault_path),
        mywork_root=_expand_path(mywork_root),
        projects_root=_expand_path(projects_root),
        templates_root=_expand_path(templates_root),
        archive_root=_expand_path(archive_root),
        app_data_path=_expand_path(app_data_path),
        repo_path=repo_path,
        agents=_load_agents(repo_path),
        index_extra_roots=extra_roots,
    )
