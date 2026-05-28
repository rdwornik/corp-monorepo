"""Tests for extraction/scanner.py — file discovery with path-jailing."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.extraction.scanner import ScanResult, scan_folder


class TestScanFolder:
    def test_finds_allowed_extensions(self, tmp_path):
        (tmp_path / "doc.pdf").write_text("pdf", encoding="utf-8")
        (tmp_path / "note.txt").write_text("txt", encoding="utf-8")
        (tmp_path / "image.png").write_bytes(b"png")

        results = scan_folder(tmp_path, allow_extensions=[".pdf", ".txt"])
        assert len(results) == 2
        names = {r.absolute_path.name for r in results}
        assert names == {"doc.pdf", "note.txt"}

    def test_empty_folder_returns_empty(self, tmp_path):
        results = scan_folder(tmp_path, allow_extensions=[".pdf"])
        assert results == []

    def test_nonexistent_folder_returns_empty(self, tmp_path):
        results = scan_folder(tmp_path / "missing", allow_extensions=[".pdf"])
        assert results == []

    def test_skips_hidden_files(self, tmp_path):
        (tmp_path / ".hidden.pdf").write_text("h", encoding="utf-8")
        (tmp_path / "_meta.yaml").write_text("m", encoding="utf-8")
        (tmp_path / "visible.pdf").write_text("v", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf", ".yaml"])
        assert len(results) == 1
        assert results[0].absolute_path.name == "visible.pdf"

    def test_skips_hidden_directories(self, tmp_path):
        hidden = tmp_path / ".git"
        hidden.mkdir()
        (hidden / "file.pdf").write_text("g", encoding="utf-8")
        underscore = tmp_path / "_knowledge"
        underscore.mkdir()
        (underscore / "file.pdf").write_text("k", encoding="utf-8")
        (tmp_path / "file.pdf").write_text("ok", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"])
        assert len(results) == 1
        assert results[0].absolute_path.name == "file.pdf"

    def test_recursive_scan(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.pdf").write_text("t", encoding="utf-8")
        (sub / "nested.pdf").write_text("n", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"], recursive=True)
        assert len(results) == 2

    def test_non_recursive_scan(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.pdf").write_text("t", encoding="utf-8")
        (sub / "nested.pdf").write_text("n", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"], recursive=False)
        assert len(results) == 1
        assert results[0].absolute_path.name == "top.pdf"

    def test_results_sorted_by_relative_path(self, tmp_path):
        (tmp_path / "zz.pdf").write_text("z", encoding="utf-8")
        (tmp_path / "aa.pdf").write_text("a", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"])
        assert results[0].relative_path < results[1].relative_path

    def test_scan_result_fields(self, tmp_path):
        (tmp_path / "test.pdf").write_text("hello", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"])
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ScanResult)
        assert r.absolute_path.is_absolute()
        assert "/" in r.relative_path or r.relative_path == "test.pdf"
        assert "\\" not in r.relative_path  # forward slashes only
        assert r.extension == ".pdf"
        assert r.size_bytes == 5

    def test_extension_normalization(self, tmp_path):
        (tmp_path / "doc.PDF").write_text("pdf", encoding="utf-8")

        # Pass extension without dot
        results = scan_folder(tmp_path, allow_extensions=["pdf"])
        assert len(results) == 1

    def test_extension_case_insensitive(self, tmp_path):
        (tmp_path / "doc.PDF").write_text("pdf", encoding="utf-8")
        (tmp_path / "doc2.Pdf").write_text("pdf2", encoding="utf-8")

        results = scan_folder(tmp_path, allow_extensions=[".pdf"])
        assert len(results) == 2


class TestPathJailing:
    def test_is_inside_jail(self):
        from corp.extraction.scanner import _is_inside_jail

        jail = Path("/tmp/scan")
        assert _is_inside_jail(Path("/tmp/scan/file.txt"), jail) is True
        assert _is_inside_jail(Path("/tmp/scan/sub/file.txt"), jail) is True

    def test_should_skip_dir(self):
        from corp.extraction.scanner import _should_skip_dir

        assert _should_skip_dir(".git") is True
        assert _should_skip_dir("_knowledge") is True
        assert _should_skip_dir("normal") is False
        assert _should_skip_dir("10_Projects") is False
