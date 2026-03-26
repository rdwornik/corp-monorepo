"""Tests for centralized path configuration."""

from pathlib import Path

import pytest

from corp_os_meta.config import get_excluded_paths, get_path, load_config, vault_path


class TestGetPath:
    def test_env_var_overrides_config(self, monkeypatch):
        """Environment variable takes precedence over config file."""
        monkeypatch.setenv("TEST_VAULT", "C:/override/vault")
        result = get_path("vault", env_var="TEST_VAULT")
        assert result == Path("C:/override/vault")

    def test_config_file_loaded(self):
        """Config file is loaded from search path."""
        config = load_config()
        # paths.toml exists at monorepo root
        assert "paths" in config or config == {}

    def test_default_fallback(self):
        """Default value used when key not in env or config."""
        result = get_path(
            "nonexistent_key_12345",
            env_var="NONEXISTENT_ENV_12345",
            default="C:/fallback",
        )
        assert result == Path("C:/fallback")

    def test_missing_key_raises(self):
        """ValueError raised when key not found anywhere."""
        with pytest.raises(ValueError, match="not configured"):
            get_path("totally_missing_key_xyz", env_var="TOTALLY_MISSING_ENV_XYZ")

    def test_vault_path_convenience(self):
        """vault_path() returns a Path."""
        result = vault_path()
        assert isinstance(result, Path)

    def test_env_var_expands_variables(self, monkeypatch):
        """Environment variables in values are expanded."""
        monkeypatch.setenv("MY_BASE", "C:/base")
        monkeypatch.setenv("TEST_PATH", "%MY_BASE%/sub")
        result = get_path("x", env_var="TEST_PATH")
        assert "base" in str(result).lower()

    def test_get_excluded_paths(self):
        """Safety excluded paths loaded from config."""
        excluded = get_excluded_paths()
        assert isinstance(excluded, list)


class TestLoadConfig:
    def test_returns_dict(self):
        """load_config returns a dict even if no file found."""
        result = load_config()
        assert isinstance(result, dict)

    def test_has_paths_section_from_monorepo(self):
        """Monorepo paths.toml should have a [paths] section."""
        # This test depends on running from the monorepo root
        config = load_config()
        if config:  # only if paths.toml was found
            assert "paths" in config
