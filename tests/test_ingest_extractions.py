"""Tests for ingest/extractions.py — CKE output_v2 ingestion."""

from __future__ import annotations

from pathlib import Path

import yaml

from corp_by_os.ingest.extractions import (
    IngestResult,
    _collect_packages,
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


def _make_output_v2(
    root: Path,
    scope: str,
    series_or_client: str,
    notes: dict[str, str] | None = None,
    cover: bool = False,
) -> Path:
    """Create a fake output_v2 package: {scope}/{series}/{series}/extract/*.md."""
    pkg = root / scope / series_or_client / series_or_client
    extract = pkg / "extract"
    extract.mkdir(parents=True, exist_ok=True)

    if notes:
        for filename, body in notes.items():
            _make_note(extract / filename, title=filename.replace(".md", ""))

    if cover:
        slides = pkg / "source" / "slides"
        slides.mkdir(parents=True, exist_ok=True)
        (slides / "slide_001.png").write_bytes(b"fake png")

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


class TestCollectPackages:
    def test_finds_all_scopes(self, tmp_path):
        out = tmp_path / "output_v2"
        _make_output_v2(out, "source_library", "Product_Docs", {"note.md": "x"})
        _make_output_v2(out, "templates", "Decks", {"note.md": "x"})
        _make_output_v2(out, "rfp", "RFP_Set", {"note.md": "x"})
        _make_output_v2(out, "projects", "Lenzing", {"note.md": "x"})

        pkgs = _collect_packages(out)
        scopes = [s for s, _, _ in pkgs]
        assert set(scopes) == {"source_library", "templates", "rfp", "projects"}

    def test_projects_have_client(self, tmp_path):
        out = tmp_path / "output_v2"
        _make_output_v2(out, "projects", "Lenzing", {"note.md": "x"})
        _make_output_v2(out, "projects", "SGDBF", {"note.md": "x"})

        pkgs = _collect_packages(out)
        clients = [c for _, c, _ in pkgs]
        assert "Lenzing" in clients
        assert "SGDBF" in clients

    def test_knowledge_scopes_have_no_client(self, tmp_path):
        out = tmp_path / "output_v2"
        _make_output_v2(out, "source_library", "Docs", {"note.md": "x"})

        pkgs = _collect_packages(out)
        assert pkgs[0][1] is None  # client is None


class TestRouting:
    def test_source_library_to_knowledge(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"platform.md": "x"})

        result = ingest_extractions(out, vault)

        assert result.notes_ingested == 1
        assert (vault / "01_knowledge" / "platform.md").exists()

    def test_templates_to_knowledge(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "templates", "Decks", {"deck.md": "x"})

        result = ingest_extractions(out, vault)

        assert (vault / "01_knowledge" / "deck.md").exists()

    def test_rfp_to_knowledge(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "rfp", "RFP_Set", {"rfp_q1.md": "x"})

        result = ingest_extractions(out, vault)

        assert (vault / "01_knowledge" / "rfp_q1.md").exists()

    def test_projects_to_client_folder(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "projects", "Lenzing", {"discovery.md": "x"})

        result = ingest_extractions(out, vault)

        assert (vault / "02_projects" / "Lenzing" / "discovery.md").exists()
        assert not (vault / "01_knowledge" / "discovery.md").exists()

    def test_multiple_clients(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "projects", "Lenzing", {"note_l.md": "x"})
        _make_output_v2(out, "projects", "SGDBF", {"note_s.md": "x"})

        result = ingest_extractions(out, vault)

        assert (vault / "02_projects" / "Lenzing" / "note_l.md").exists()
        assert (vault / "02_projects" / "SGDBF" / "note_s.md").exists()


class TestProtection:
    def test_skips_verified_notes(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        _make_note(
            vault / "01_knowledge" / "platform.md",
            title="Original",
            trust_level="verified",
        )
        _make_output_v2(out, "source_library", "Docs", {"platform.md": "new"})

        result = ingest_extractions(out, vault)

        assert result.notes_skipped_verified == 1
        assert result.notes_ingested == 0
        content = (vault / "01_knowledge" / "platform.md").read_text(encoding="utf-8")
        assert "Original" in content

    def test_force_overwrites_verified(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        _make_note(
            vault / "01_knowledge" / "platform.md",
            title="Original",
            trust_level="verified",
        )
        _make_output_v2(out, "source_library", "Docs", {"platform.md": "replaced"})

        result = ingest_extractions(out, vault, force=True)

        assert result.notes_ingested == 1


class TestCoverSlides:
    def test_cover_to_assets(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"note.md": "x"}, cover=True)

        result = ingest_extractions(out, vault)

        assert result.covers_copied == 1
        assert (vault / "_assets" / "Docs_cover.png").exists()


class TestDryRun:
    def test_dry_run_no_writes(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"note.md": "x"})

        result = ingest_extractions(out, vault, dry_run=True)

        assert result.notes_ingested == 1
        assert not (vault / "01_knowledge").exists()

    def test_dry_run_tracks_destinations(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"a.md": "x", "b.md": "x"})
        _make_output_v2(out, "projects", "Lenzing", {"c.md": "x"})

        result = ingest_extractions(out, vault, dry_run=True)

        assert result.notes_ingested == 3
        assert len(result.by_dest) == 2


class TestEdgeCases:
    def test_empty_output(self, tmp_path):
        out = tmp_path / "output_v2"
        out.mkdir()
        vault = tmp_path / "vault"

        result = ingest_extractions(out, vault)

        assert result.notes_ingested == 0

    def test_not_a_directory(self, tmp_path):
        fake = tmp_path / "not_a_dir.txt"
        fake.write_text("nope")
        vault = tmp_path / "vault"

        result = ingest_extractions(fake, vault)

        assert len(result.errors) == 1
