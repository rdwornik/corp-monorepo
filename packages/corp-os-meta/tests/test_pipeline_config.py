"""Tests for PipelineConfig — portable path bundle."""

from pathlib import Path

import pytest

from corp_os_meta.pipeline_config import PipelineConfig


class TestSandbox:
    def test_all_paths_under_tmp(self, tmp_path):
        """sandbox() puts every path under tmp_root."""
        cfg = PipelineConfig.sandbox(tmp_path)
        for attr in (
            "vault_path",
            "mywork_root",
            "projects_root",
            "templates_root",
            "archive_root",
            "app_data_path",
            "inbox_path",
            "index_db_path",
            "ops_db_path",
            "state_db_path",
        ):
            p = getattr(cfg, attr)
            assert str(p).startswith(str(tmp_path)), f"{attr}={p!r} is not under tmp_root={tmp_path!r}"

    def test_inbox_is_derived_from_mywork(self, tmp_path):
        """inbox_path == mywork_root / '00_Inbox'."""
        cfg = PipelineConfig.sandbox(tmp_path)
        assert cfg.inbox_path == cfg.mywork_root / "00_Inbox"

    def test_db_paths_derived_from_app_data(self, tmp_path):
        """All DB paths live under app_data_path."""
        cfg = PipelineConfig.sandbox(tmp_path)
        assert cfg.index_db_path == cfg.app_data_path / "index.db"
        assert cfg.ops_db_path == cfg.app_data_path / "ops.db"
        assert cfg.state_db_path == cfg.app_data_path / "overnight_state.db"

    def test_two_sandboxes_are_independent(self, tmp_path):
        """Different tmp roots produce independent configs."""
        root_a = tmp_path / "a"
        root_b = tmp_path / "b"
        cfg_a = PipelineConfig.sandbox(root_a)
        cfg_b = PipelineConfig.sandbox(root_b)
        assert cfg_a.vault_path != cfg_b.vault_path
        assert cfg_a.app_data_path != cfg_b.app_data_path


class TestProduction:
    def test_env_var_overrides_vault_path(self, monkeypatch, tmp_path):
        """VAULT_PATH env var takes precedence over default."""
        override = str(tmp_path / "custom_vault")
        monkeypatch.setenv("VAULT_PATH", override)
        cfg = PipelineConfig.production()
        assert cfg.vault_path == Path(override)

    def test_env_var_overrides_mywork_root(self, monkeypatch, tmp_path):
        """MYWORK_ROOT env var takes precedence over default."""
        override = str(tmp_path / "custom_mywork")
        monkeypatch.setenv("MYWORK_ROOT", override)
        cfg = PipelineConfig.production()
        assert cfg.mywork_root == Path(override)

    def test_env_var_overrides_app_data_path(self, monkeypatch, tmp_path):
        """APP_DATA_PATH env var takes precedence over default."""
        override = str(tmp_path / "custom_appdata")
        monkeypatch.setenv("APP_DATA_PATH", override)
        cfg = PipelineConfig.production()
        assert cfg.app_data_path == Path(override)

    def test_production_derived_paths_consistent(self, monkeypatch, tmp_path):
        """Derived paths are consistent with base paths in production mode."""
        monkeypatch.setenv("MYWORK_ROOT", str(tmp_path / "mw"))
        monkeypatch.setenv("APP_DATA_PATH", str(tmp_path / "ad"))
        cfg = PipelineConfig.production()
        assert cfg.inbox_path == cfg.mywork_root / "00_Inbox"
        assert cfg.index_db_path == cfg.app_data_path / "index.db"


class TestFrozen:
    def test_is_frozen(self, tmp_path):
        """PipelineConfig cannot be mutated after creation."""
        cfg = PipelineConfig.sandbox(tmp_path)
        with pytest.raises((AttributeError, TypeError)):
            cfg.vault_path = tmp_path / "other"  # type: ignore[misc]

    def test_derived_fields_frozen(self, tmp_path):
        """Derived fields are also immutable."""
        cfg = PipelineConfig.sandbox(tmp_path)
        with pytest.raises((AttributeError, TypeError)):
            cfg.inbox_path = tmp_path / "other"  # type: ignore[misc]
