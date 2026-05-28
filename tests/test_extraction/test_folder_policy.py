"""Tests for extraction/folder_policy.py — extraction policy from folder_manifest.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.extraction.folder_policy import (
    ExtractionPolicy,
    PolicyError,
    load_policy,
)


def _write_manifest(folder: Path, data: dict) -> Path:
    import yaml

    manifest = folder / "folder_manifest.yaml"
    manifest.write_text(yaml.dump(data), encoding="utf-8")
    return manifest


class TestLoadPolicy:
    def test_basic_manifest(self, tmp_path):
        _write_manifest(tmp_path, {
            "extraction": {
                "enabled": True,
                "scope": "client_project",
                "extract_on_change": True,
                "settle_minutes": 15,
            },
            "allow_extensions": [".pdf", ".pptx"],
            "privacy": "confidential",
        })

        policy = load_policy(tmp_path)
        assert isinstance(policy, ExtractionPolicy)
        assert policy.enabled is True
        assert policy.scope == "client_project"
        assert policy.extract_on_change is True
        assert policy.settle_minutes == 15
        assert ".pdf" in policy.allow_extensions
        assert policy.privacy == "confidential"

    def test_defaults_when_fields_missing(self, tmp_path):
        _write_manifest(tmp_path, {"extraction": {"enabled": False}})

        policy = load_policy(tmp_path)
        assert policy.enabled is False
        assert policy.scope == ""
        assert policy.extract_on_change is False
        assert policy.settle_minutes == 30
        assert policy.allow_extensions == []
        assert policy.privacy == "internal"
        assert policy.credential_scrubbing is False

    def test_inherits_from_parent(self, tmp_path):
        _write_manifest(tmp_path, {
            "extraction": {"enabled": True, "scope": "parent_scope"},
            "allow_extensions": [".pdf"],
        })
        child = tmp_path / "subfolder"
        child.mkdir()
        # No manifest in child — should inherit from parent

        policy = load_policy(child)
        assert policy.enabled is True
        assert policy.scope == "parent_scope"

    def test_no_manifest_anywhere_raises(self, tmp_path):
        folder = tmp_path / "empty"
        folder.mkdir()

        with pytest.raises(PolicyError, match="No folder_manifest.yaml found"):
            load_policy(folder)

    def test_credential_scrubbing_from_parent_subfolders(self, tmp_path):
        _write_manifest(tmp_path, {
            "extraction": {"enabled": True, "scope": "parent"},
            "subfolders": {
                "sensitive": {"credential_scrubbing": True},
            },
        })
        child = tmp_path / "sensitive"
        child.mkdir()

        policy = load_policy(child)
        assert policy.credential_scrubbing is True

    def test_own_manifest_overrides_parent(self, tmp_path):
        _write_manifest(tmp_path, {
            "extraction": {"enabled": True, "scope": "parent"},
            "allow_extensions": [".pdf"],
        })
        child = tmp_path / "sub"
        child.mkdir()
        _write_manifest(child, {
            "extraction": {"enabled": False, "scope": "child_override"},
        })

        policy = load_policy(child)
        assert policy.enabled is False
        assert policy.scope == "child_override"
        # Extensions inherited from parent when child has none
        assert ".pdf" in policy.allow_extensions

    def test_empty_manifest_uses_defaults(self, tmp_path):
        _write_manifest(tmp_path, {})

        policy = load_policy(tmp_path)
        assert policy.enabled is False
        assert policy.scope == ""
