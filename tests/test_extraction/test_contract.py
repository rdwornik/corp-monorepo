"""Tests for extraction/contract.py — manifest validation against CKE schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from corp.extraction.contract import ManifestValidationError, validate_manifest


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _valid_manifest(tmp_path: Path) -> dict:
    """Minimal valid manifest with one file entry."""
    test_file = tmp_path / "test.pdf"
    test_file.write_text("fake pdf", encoding="utf-8")
    return {
        "schema_version": 1,
        "output_dir": str(tmp_path),
        "files": [
            {
                "id": "test-entry",
                "path": str(test_file),
                "doc_type": "document",
                "content_origin": "mywork",
                "source_category": "product_docs",
                "source_locator": "10_Projects/test.pdf",
                "routing_confidence": 0.95,
            }
        ],
    }


class TestValidManifest:
    def test_valid_manifest_passes(self, tmp_path):
        data = _valid_manifest(tmp_path)
        path = _write_manifest(tmp_path, data)
        assert validate_manifest(path) is True

    def test_valid_manifest_skip_file_check(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["path"] = "/nonexistent/file.pdf"
        path = _write_manifest(tmp_path, data)
        assert validate_manifest(path, check_files_exist=False) is True


class TestInvalidJSON:
    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{broken json", encoding="utf-8")
        with pytest.raises(ManifestValidationError, match="Invalid JSON"):
            validate_manifest(p)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ManifestValidationError, match="not found"):
            validate_manifest(tmp_path / "missing.json")


class TestSchemaVersion:
    def test_wrong_schema_version(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["schema_version"] = 2
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="schema_version must be 1"):
            validate_manifest(path, check_files_exist=False)

    def test_missing_schema_version(self, tmp_path):
        data = _valid_manifest(tmp_path)
        del data["schema_version"]
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="schema_version"):
            validate_manifest(path, check_files_exist=False)


class TestRequiredFields:
    def test_missing_top_level_fields(self, tmp_path):
        data = {"schema_version": 1}  # Missing output_dir and files
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing top-level"):
            validate_manifest(path, check_files_exist=False)

    def test_missing_entry_id(self, tmp_path):
        data = _valid_manifest(tmp_path)
        del data["files"][0]["id"]
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="missing required field 'id'"):
            validate_manifest(path, check_files_exist=False)

    def test_missing_entry_path(self, tmp_path):
        data = _valid_manifest(tmp_path)
        del data["files"][0]["path"]
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="missing required field 'path'"):
            validate_manifest(path, check_files_exist=False)


class TestV21Fields:
    def test_missing_v21_fields(self, tmp_path):
        data = _valid_manifest(tmp_path)
        del data["files"][0]["content_origin"]
        del data["files"][0]["source_category"]
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="missing v2.1 fields"):
            validate_manifest(path, check_files_exist=False)


class TestDocType:
    def test_invalid_doc_type(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["doc_type"] = "unknown_type"
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="unknown doc_type"):
            validate_manifest(path, check_files_exist=False)

    def test_all_valid_doc_types(self, tmp_path):
        valid_types = ["video", "audio", "document", "presentation", "slides",
                       "spreadsheet", "note", "transcript"]
        for dt in valid_types:
            data = _valid_manifest(tmp_path)
            data["files"][0]["doc_type"] = dt
            path = _write_manifest(tmp_path, data)
            assert validate_manifest(path) is True


class TestSourceLocator:
    def test_backslashes_rejected(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["source_locator"] = "10_Projects\\test.pdf"
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="backslashes"):
            validate_manifest(path, check_files_exist=False)


class TestRoutingConfidence:
    def test_confidence_above_one(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["routing_confidence"] = 1.5
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="routing_confidence must be 0.0-1.0"):
            validate_manifest(path, check_files_exist=False)

    def test_negative_confidence(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["routing_confidence"] = -0.1
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="routing_confidence must be 0.0-1.0"):
            validate_manifest(path, check_files_exist=False)

    def test_confidence_boundary_zero(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["routing_confidence"] = 0.0
        path = _write_manifest(tmp_path, data)
        assert validate_manifest(path) is True

    def test_confidence_boundary_one(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["routing_confidence"] = 1.0
        path = _write_manifest(tmp_path, data)
        assert validate_manifest(path) is True


class TestDuplicateIds:
    def test_duplicate_entry_ids(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"].append(data["files"][0].copy())
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="duplicate id"):
            validate_manifest(path, check_files_exist=False)


class TestEmptyManifest:
    def test_empty_files_list_passes(self, tmp_path):
        data = {"schema_version": 1, "output_dir": str(tmp_path), "files": []}
        path = _write_manifest(tmp_path, data)
        assert validate_manifest(path) is True

    def test_files_not_list(self, tmp_path):
        data = {"schema_version": 1, "output_dir": str(tmp_path), "files": "not a list"}
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="must be a list"):
            validate_manifest(path, check_files_exist=False)


class TestFileExistence:
    def test_missing_file_detected(self, tmp_path):
        data = _valid_manifest(tmp_path)
        data["files"][0]["path"] = str(tmp_path / "gone.pdf")
        path = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="file not found"):
            validate_manifest(path, check_files_exist=True)
