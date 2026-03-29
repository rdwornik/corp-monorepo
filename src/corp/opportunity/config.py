"""Configuration loader — YAML config + .env environment variables."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_DEFAULT_CONFIG = _CONFIG_DIR / "default.yaml"


@dataclass
class AppConfig:
    """Resolved application configuration combining YAML defaults and env vars."""

    projects_root: Path
    archive_root: Path
    templates_root: Path
    project_codes_excel: Path | None
    naming: dict
    templates: dict
    folder_structure: dict
    stages: list[str]
    products: list[str]


def load_config(config_path: Path | None = None, env_file: Path | None = None) -> AppConfig:
    """Load configuration from YAML + .env files.

    Args:
        config_path: Path to YAML config. Defaults to config/default.yaml.
        env_file: Path to .env file. Defaults to project root .env.
    """
    # Global API keys (Documents/.secrets/.env)
    _global_env = Path.home() / "Documents" / ".secrets" / ".env"
    if _global_env.exists():
        load_dotenv(_global_env, override=False)
        logger.debug("Loaded global .env from %s", _global_env)

    # Local .env (project-specific vars only)
    project_root = Path(__file__).resolve().parent.parent.parent
    if env_file is None:
        env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
        logger.debug("Loaded local .env from %s", env_file)

    # Load YAML
    if config_path is None:
        config_path = _DEFAULT_CONFIG
    with open(config_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    logger.debug("Loaded config from %s", config_path)

    # Resolve paths from env vars (with fallbacks)
    projects_root = Path(os.environ.get("PROJECTS_ROOT", str(project_root / "test_projects")))
    archive_root = Path(os.environ.get("ARCHIVE_ROOT", str(project_root / "test_archive")))
    templates_root = Path(os.environ.get("TEMPLATES_ROOT", str(project_root / "test_templates")))

    excel_path_str = os.environ.get("PROJECT_CODES_EXCEL", "")
    project_codes_excel = Path(excel_path_str) if excel_path_str else None

    return AppConfig(
        projects_root=projects_root,
        archive_root=archive_root,
        templates_root=templates_root,
        project_codes_excel=project_codes_excel,
        naming=yaml_config.get("naming", {}),
        templates=yaml_config.get("templates", {}),
        folder_structure=yaml_config.get("folder_structure", {}),
        stages=yaml_config.get("stages", []),
        products=yaml_config.get("products", []),
    )
