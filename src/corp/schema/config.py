"""Centralized path configuration for Corporate OS ecosystem.

Resolution order: ENV_VAR > config/paths.toml > defaults.

Usage:
    from corp.schema.config import vault_path, mywork_path, get_path
    vault = vault_path()
    custom = get_path("rfp_kb", env_var="RFP_KB_PATH")
"""

import os
from functools import lru_cache
from pathlib import Path

import tomllib

_CONFIG_SEARCH = [
    Path.cwd() / "config" / "paths.toml",
    Path(__file__).parents[3] / "config" / "paths.toml",  # monorepo root
    Path.home() / ".corp" / "paths.toml",
]


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Load paths.toml from first found search location."""
    for p in _CONFIG_SEARCH:
        if p.exists():
            return tomllib.loads(p.read_text(encoding="utf-8"))
    return {}


def get_path(key: str, env_var: str | None = None, default: str | None = None) -> Path:
    """Get a path with resolution: env var > config > default.

    Args:
        key: Key in [paths] section of paths.toml (e.g., "vault", "mywork").
        env_var: Environment variable name to check first.
        default: Fallback if neither env var nor config has the key.

    Returns:
        Resolved Path.

    Raises:
        ValueError: If key not found in any source and no default provided.
    """
    if env_var:
        env_val = os.environ.get(env_var)
        if env_val:
            return Path(os.path.expandvars(env_val))

    config = load_config()
    paths = config.get("paths", {})
    val = paths.get(key)
    if val:
        return Path(os.path.expandvars(str(val)))

    if default:
        return Path(os.path.expandvars(default))

    raise ValueError(f"Path '{key}' not configured. Set {env_var} or add to config/paths.toml")


def get_excluded_paths() -> list[str]:
    """Get paths that must never be touched by cleanup operations."""
    config = load_config()
    return config.get("safety", {}).get("excluded_paths", [])


# Convenience accessors


def vault_path() -> Path:
    """Obsidian vault root."""
    return get_path("vault", "VAULT_PATH", "~/Documents/ObsidianVault")


def mywork_path() -> Path:
    """MyWork root (OneDrive project files)."""
    return get_path("mywork", "MYWORK_PATH", "~/Documents/MyWork")


def secrets_path() -> Path:
    """Global secrets .env file."""
    return get_path("secrets", "SECRETS_PATH", "~/Documents/.secrets/.env")


def rfp_kb_path() -> Path:
    """RFP knowledge base directory."""
    return get_path("rfp_kb", "RFP_KB_PATH", "~/Documents/corp_data/rfp_kb")
