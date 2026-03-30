"""Tests for extraction/manifest_emitter.py — CKE-compatible manifest builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from corp.extraction.folder_policy import ExtractionPolicy
from corp.extraction.manifest_emitter import (
    _make_entry_id,
    _resolve_doc_type,
    build_manifest,
    write_manifest,
)
from corp.extraction.routing import RouteInfo
from corp.extraction.scanner import ScanResult


def _route_info():
    return RouteInfo(
        vault_target="01_Knowledge",
        provenance_scope="internal",
        content_origin="mywork",
        source_category="projects",
        routing_confidence=0.95,
    )


def _policy():
    return ExtractionPolicy(
        enabled=True,
        scope="test",
        privacy="internal",
        credential_scrubbing=False,
    )


def _scan_result(tmp_path: Path, name: str = "test.pdf") -> ScanResult:
    f = tmp_path / name
    f.write_text("content", encoding="utf-8")
    return ScanResult(
        absolute_path=f.resolve(),
        relative_path=name,
        extension=f.suffix.lower(),
        size_bytes=7,
    )


class TestMakeEntryId:
    def test_simple_filename(self):
        assert _make_entry_id("doc.pdf") == "doc--pdf"

    def test_path_with_spaces(self):
        result = _make_entry_id("01_Decks/Platform Overview.pptx")
        assert "--" in result  # path separator
        assert " " not in result
        assert result.islower()

    def test_nested_path(self):
        result = _make_entry_id("a/b/c.txt")
        assert "a--b--c" in result

    def test_special_characters_stripped(self):
        result = _make_entry_id("file (copy).pdf")
        assert "(" not in result
        assert ")" not in result


class TestResolveDocType:
    def test_known_extensions(self):
        assert _resolve_doc_type(".pptx") == "presentation"
        assert _resolve_doc_type(".pdf") == "document"
        assert _resolve_doc_type(".xlsx") == "spreadsheet"
        assert _resolve_doc_type(".mp4") == "video"
        assert _resolve_doc_type(".mp3") == "audio"
        assert _resolve_doc_type(".md") == "note"
        assert _resolve_doc_type(".csv") == "spreadsheet"

    def test_unknown_extension_defaults_to_document(self):
        assert _resolve_doc_type(".xyz") == "document"
        assert _resolve_doc_type(".zzz") == "document"

    def test_case_insensitive(self):
        assert _resolve_doc_type(".PDF") == "document"
        assert _resolve_doc_type(".PPTX") == "presentation"


class TestBuildManifest:
    def test_structure(self, tmp_path):
        scan = _scan_result(tmp_path)
        output_dir = tmp_path / "output"

        manifest = build_manifest(
            [scan], _route_info(), _policy(), output_dir,
        )

        assert manifest["schema_version"] == 1
        assert manifest["output_dir"] == str(output_dir)
        assert len(manifest["files"]) == 1
        assert manifest["config"]["vault_target"] == "01_Knowledge"
        assert manifest["config"]["privacy"] == "internal"

    def test_file_entry_fields(self, tmp_path):
        scan = _scan_result(tmp_path)
        output_dir = tmp_path / "output"

        manifest = build_manifest(
            [scan], _route_info(), _policy(), output_dir,
        )

        entry = manifest["files"][0]
        assert "id" in entry
        assert "path" in entry
        assert entry["doc_type"] == "document"  # .pdf → document
        assert entry["content_origin"] == "mywork"
        assert entry["source_category"] == "projects"
        assert entry["routing_confidence"] == 0.95
        assert "\\" not in entry["source_locator"]

    def test_project_name_override(self, tmp_path):
        scan = _scan_result(tmp_path)
        manifest = build_manifest(
            [scan], _route_info(), _policy(), tmp_path,
            project_name="custom_project",
        )
        assert manifest["project"] == "custom_project"

    def test_project_defaults_to_source_category(self, tmp_path):
        scan = _scan_result(tmp_path)
        manifest = build_manifest(
            [scan], _route_info(), _policy(), tmp_path,
        )
        assert manifest["project"] == "projects"

    def test_empty_scan_results(self, tmp_path):
        manifest = build_manifest(
            [], _route_info(), _policy(), tmp_path,
        )
        assert manifest["files"] == []

    def test_multiple_files(self, tmp_path):
        s1 = _scan_result(tmp_path, "a.pdf")
        s2 = _scan_result(tmp_path, "b.pptx")

        manifest = build_manifest(
            [s1, s2], _route_info(), _policy(), tmp_path,
        )
        assert len(manifest["files"]) == 2
        doc_types = {e["doc_type"] for e in manifest["files"]}
        assert "document" in doc_types
        assert "presentation" in doc_types

    def test_source_locator_with_mywork_root(self, tmp_path):
        mywork = tmp_path / "MyWork"
        project = mywork / "10_Projects"
        project.mkdir(parents=True)
        f = project / "test.pdf"
        f.write_text("x", encoding="utf-8")

        scan = ScanResult(
            absolute_path=f.resolve(),
            relative_path="test.pdf",
            extension=".pdf",
            size_bytes=1,
        )

        manifest = build_manifest(
            [scan], _route_info(), _policy(), tmp_path,
            mywork_root=mywork,
        )
        locator = manifest["files"][0]["source_locator"]
        assert "\\" not in locator
        assert "10_Projects" in locator

    def test_credential_scrubbing_in_config(self, tmp_path):
        policy = ExtractionPolicy(
            enabled=True, scope="test",
            credential_scrubbing=True,
        )
        manifest = build_manifest(
            [], _route_info(), policy, tmp_path,
        )
        assert manifest["config"]["credential_scrubbing"] is True


class TestWriteManifest:
    def test_writes_valid_json(self, tmp_path):
        manifest = {"schema_version": 1, "output_dir": ".", "files": []}
        path = write_manifest(manifest, tmp_path / "out" / "manifest.json")

        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == 1

    def test_creates_parent_dirs(self, tmp_path):
        manifest = {"schema_version": 1, "output_dir": ".", "files": []}
        path = tmp_path / "deep" / "nested" / "manifest.json"
        write_manifest(manifest, path)
        assert path.exists()
