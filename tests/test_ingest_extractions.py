"""Tests for ingest/extractions.py — CKE output ingestion."""

from __future__ import annotations

from pathlib import Path

import yaml

from corp_by_os.ingest.extractions import (
    IngestResult,
    _find_cover_slide,
    _should_copy,
    ingest_extractions,
)


def _make_note(path: Path, title: str = "Test", trust_level: str = "extracted") -> None:
    """Helper: write a minimal markdown note with frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = {"title": title, "trust_level": trust_level}
    fm_str = yaml.dump(fm, default_flow_style=False)
    path.write_text(f"---\n{fm_str}---\nBody of {title}.\n", encoding="utf-8")


def _make_cke_package(
    output_dir: Path,
    pkg_name: str,
    notes: dict[str, str] | None = None,
    cover: bool = False,
    meta: dict | None = None,
) -> Path:
    """Create a fake CKE output package."""
    pkg = output_dir / pkg_name
    extract = pkg / "extract"
    extract.mkdir(parents=True, exist_ok=True)

    if notes:
        for filename, body in notes.items():
            _make_note(extract / filename, title=filename.replace(".md", ""))

    if cover:
        slides = pkg / "source" / "slides"
        slides.mkdir(parents=True, exist_ok=True)
        (slides / "slide_001.png").write_bytes(b"fake png")

    if meta:
        with open(pkg / "_meta.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta, f)

    return pkg


class TestShouldCopy:
    def test_md_file_in_extract(self):
        assert _should_copy(Path("extract/note.md")) is True

    def test_json_sidecar_skipped(self):
        assert _should_copy(Path("extract/note.json")) is False

    def test_transcript_skipped(self):
        assert _should_copy(Path("extract/audio_transcript.md")) is False

    def test_synthesis_skipped(self):
        assert _should_copy(Path("synthesis.md")) is False

    def test_index_skipped(self):
        assert _should_copy(Path("index.md")) is False

    def test_meta_skipped(self):
        assert _should_copy(Path("_meta.yaml")) is False

    def test_source_dir_skipped(self):
        assert _should_copy(Path("source/docs/readme.md")) is False

    def test_session_md_at_root(self):
        assert _should_copy(Path("session_001.md")) is True


class TestFindCoverSlide:
    def test_meta_cover_slide(self, tmp_path):
        pkg = tmp_path / "pkg"
        cover = pkg / "custom_cover.png"
        cover.parent.mkdir(parents=True)
        cover.write_bytes(b"png")
        result = _find_cover_slide(pkg, {"cover_slide": "custom_cover.png"})
        assert result == cover

    def test_fallback_slide_001(self, tmp_path):
        pkg = tmp_path / "pkg"
        fallback = pkg / "source" / "slides" / "slide_001.png"
        fallback.parent.mkdir(parents=True)
        fallback.write_bytes(b"png")
        result = _find_cover_slide(pkg, {})
        assert result == fallback

    def test_no_cover(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        result = _find_cover_slide(pkg, {})
        assert result is None


class TestIngestExtractions:
    def test_ingests_notes(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"
        _make_cke_package(output, "pkg-001", notes={"platform_overview.md": "content"})

        result = ingest_extractions(output, vault)

        assert result.notes_ingested == 1
        assert (vault / "knowledge" / "platform_overview.md").exists()

    def test_skips_verified_notes(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"

        # Pre-create a verified note in vault
        _make_note(
            vault / "knowledge" / "platform_overview.md",
            title="Original",
            trust_level="verified",
        )

        _make_cke_package(output, "pkg-001", notes={"platform_overview.md": "new content"})

        result = ingest_extractions(output, vault)

        assert result.notes_skipped_verified == 1
        assert result.notes_ingested == 0
        # Content unchanged
        content = (vault / "knowledge" / "platform_overview.md").read_text(encoding="utf-8")
        assert "Original" in content

    def test_force_overwrites_verified(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"

        _make_note(
            vault / "knowledge" / "platform_overview.md",
            title="Original",
            trust_level="verified",
        )

        _make_cke_package(output, "pkg-001", notes={"platform_overview.md": "replaced"})

        result = ingest_extractions(output, vault, force=True)

        assert result.notes_ingested == 1
        assert result.notes_skipped_verified == 0

    def test_copies_cover_slide(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"
        _make_cke_package(output, "pkg-001", notes={"note.md": "body"}, cover=True)

        result = ingest_extractions(output, vault)

        assert result.covers_copied == 1
        assert (vault / "knowledge" / "assets" / "pkg-001_cover.png").exists()

    def test_dry_run_no_writes(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"
        _make_cke_package(output, "pkg-001", notes={"note.md": "body"})

        result = ingest_extractions(output, vault, dry_run=True)

        assert result.notes_ingested == 1
        assert not (vault / "knowledge").exists()

    def test_empty_output(self, tmp_path):
        output = tmp_path / "cke_output"
        output.mkdir()
        vault = tmp_path / "vault"

        result = ingest_extractions(output, vault)

        assert result.notes_ingested == 0
        assert result.covers_copied == 0

    def test_not_a_directory(self, tmp_path):
        fake = tmp_path / "not_a_dir.txt"
        fake.write_text("nope")
        vault = tmp_path / "vault"

        result = ingest_extractions(fake, vault)

        assert len(result.errors) == 1

    def test_multiple_packages(self, tmp_path):
        output = tmp_path / "cke_output"
        vault = tmp_path / "vault"
        _make_cke_package(output, "pkg-001", notes={"note_a.md": "a"})
        _make_cke_package(output, "pkg-002", notes={"note_b.md": "b", "note_c.md": "c"})

        result = ingest_extractions(output, vault)

        assert result.notes_ingested == 3
