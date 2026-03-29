"""Tests for ingest/extractions.py — CKE output_v2 ingestion."""

from __future__ import annotations

from pathlib import Path

import yaml
from corp.ingest.extractions import (
    _collect_packages,
    _find_cover_slide,
    _quality_gate,
    _quarantine_note,
    _should_copy,
    _validate_note,
    ingest_extractions,
)


def _make_note(
    path: Path,
    title: str = "Test",
    trust_level: str = "extracted",
    quality_score: int | None = None,
) -> None:
    """Helper: write a minimal markdown note with frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm: dict = {"title": title, "trust_level": trust_level}
    if quality_score is not None:
        fm["quality_score"] = quality_score
    fm_str = yaml.dump(fm, default_flow_style=False)
    path.write_text(f"---\n{fm_str}---\nBody of {title}.\n", encoding="utf-8")


def _make_output_v2(
    root: Path,
    scope: str,
    series_or_client: str,
    notes: dict[str, str] | None = None,
    cover: bool = False,
    quality_score: int | None = None,
) -> Path:
    """Create a fake output_v2 package: {scope}/{series}/{series}/extract/*.md."""
    pkg = root / scope / series_or_client / series_or_client
    extract = pkg / "extract"
    extract.mkdir(parents=True, exist_ok=True)

    if notes:
        for filename, _body in notes.items():
            _make_note(
                extract / filename,
                title=filename.replace(".md", ""),
                quality_score=quality_score,
            )

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
        assert (vault / "01_Knowledge" / "platform.md").exists()

    def test_templates_to_knowledge(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "templates", "Decks", {"deck.md": "x"})

        ingest_extractions(out, vault)

        assert (vault / "01_Knowledge" / "deck.md").exists()

    def test_rfp_to_knowledge(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "rfp", "RFP_Set", {"rfp_q1.md": "x"})

        ingest_extractions(out, vault)

        assert (vault / "01_Knowledge" / "rfp_q1.md").exists()

    def test_projects_to_knowledge_flat(self, tmp_path):
        """Council Decision #7: project notes go to 01_Knowledge/ (flat), not 02_projects/."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "projects", "Lenzing", {"discovery.md": "x"})

        ingest_extractions(out, vault)

        assert (vault / "01_Knowledge" / "discovery.md").exists()
        assert not (vault / "02_projects").exists()

    def test_multiple_clients_flat(self, tmp_path):
        """All client notes land in same 01_Knowledge/ folder."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "projects", "Lenzing", {"note_l.md": "x"})
        _make_output_v2(out, "projects", "SGDBF", {"note_s.md": "x"})

        ingest_extractions(out, vault)

        assert (vault / "01_Knowledge" / "note_l.md").exists()
        assert (vault / "01_Knowledge" / "note_s.md").exists()


class TestProtection:
    def test_skips_verified_notes(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        _make_note(
            vault / "01_Knowledge" / "platform.md",
            title="Original",
            trust_level="verified",
        )
        _make_output_v2(out, "source_library", "Docs", {"platform.md": "new"})

        result = ingest_extractions(out, vault)

        assert result.notes_skipped_verified == 1
        assert result.notes_ingested == 0
        content = (vault / "01_Knowledge" / "platform.md").read_text(encoding="utf-8")
        assert "Original" in content

    def test_force_overwrites_verified(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        _make_note(
            vault / "01_Knowledge" / "platform.md",
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
        assert not (vault / "01_Knowledge").exists()

    def test_dry_run_tracks_destinations(self, tmp_path):
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"a.md": "x", "b.md": "x"})
        _make_output_v2(out, "projects", "Lenzing", {"c.md": "x"})

        result = ingest_extractions(out, vault, dry_run=True)

        assert result.notes_ingested == 3
        # All notes go to 01_Knowledge/ now (flat)
        assert len(result.by_dest) == 1
        assert "01_Knowledge" in result.by_dest


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


# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------


class TestQualityGate:
    def test_quality_gate_accepts_above_threshold(self):
        ok, _ = _quality_gate({"quality_score": 50}, threshold=25)
        assert ok

    def test_quality_gate_rejects_below_threshold(self):
        ok, reason = _quality_gate({"quality_score": 10}, threshold=25)
        assert not ok
        assert "10 < 25" in reason

    def test_quality_gate_accepts_missing_score(self):
        """Notes without quality_score pass by default."""
        ok, _ = _quality_gate({}, threshold=25)
        assert ok

    def test_quality_gate_accepts_zero_score(self):
        """Zero score passes (0 means 'not computed', not 'bad')."""
        ok, _ = _quality_gate({"quality_score": 0}, threshold=25)
        assert ok

    def test_quality_gate_quarantines_low_note(self, tmp_path):
        """Full pipeline: low quality note goes to _quarantine/."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"low.md": "x"}, quality_score=10)

        result = ingest_extractions(out, vault, quality_threshold=25)

        assert result.notes_quarantined == 1
        assert result.notes_ingested == 0
        assert (vault / "_quarantine" / "low.md").exists()

    def test_quality_gate_accepts_high_note(self, tmp_path):
        """High quality note passes gate."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"good.md": "x"}, quality_score=50)

        result = ingest_extractions(out, vault, quality_threshold=25)

        assert result.notes_ingested == 1
        assert result.notes_quarantined == 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_validate_note_missing_title(self):
        ok, reason = _validate_note({})
        assert not ok
        assert "Missing title" in reason

    def test_validate_note_with_title(self):
        ok, _ = _validate_note({"title": "Test"})
        assert ok

    def test_quarantine_on_missing_title(self, tmp_path):
        """Note without title in frontmatter gets quarantined."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        # Create note with empty frontmatter (no title)
        pkg = out / "source_library" / "Docs" / "Docs"
        extract = pkg / "extract"
        extract.mkdir(parents=True, exist_ok=True)
        (extract / "bad.md").write_text(
            "---\nquality_score: 50\n---\nNo title.\n", encoding="utf-8"
        )

        result = ingest_extractions(out, vault)

        assert result.notes_quarantined == 1
        assert (vault / "_quarantine" / "bad.md").exists()
        # Quarantine note has reason in frontmatter
        content = (vault / "_quarantine" / "bad.md").read_text(encoding="utf-8")
        assert "quarantine_reason" in content


# ---------------------------------------------------------------------------
# Trust level injection
# ---------------------------------------------------------------------------


class TestTrustLevelInjection:
    def test_trust_level_set_to_extracted(self, tmp_path):
        """New ingested notes get trust_level=extracted."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"
        _make_output_v2(out, "source_library", "Docs", {"note.md": "x"})

        ingest_extractions(out, vault)

        content = (vault / "01_Knowledge" / "note.md").read_text(encoding="utf-8")
        assert "trust_level" in content
        # Parse frontmatter to verify
        end = content.find("---", 3)
        fm = yaml.safe_load(content[3:end])
        assert fm.get("trust_level") == "extracted"

    def test_existing_trust_level_preserved(self, tmp_path):
        """If note already has trust_level, don't overwrite it."""
        out = tmp_path / "output_v2"
        vault = tmp_path / "vault"

        # Create note with trust_level=draft
        pkg = out / "source_library" / "Docs" / "Docs"
        extract = pkg / "extract"
        extract.mkdir(parents=True, exist_ok=True)
        fm = {"title": "Draft Note", "trust_level": "draft"}
        fm_str = yaml.dump(fm, default_flow_style=False)
        (extract / "draft.md").write_text(f"---\n{fm_str}---\nBody.\n", encoding="utf-8")

        ingest_extractions(out, vault)

        content = (vault / "01_Knowledge" / "draft.md").read_text(encoding="utf-8")
        end = content.find("---", 3)
        fm_out = yaml.safe_load(content[3:end])
        assert fm_out.get("trust_level") == "draft"


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------


class TestQuarantine:
    def test_quarantine_note_written(self, tmp_path):
        vault = tmp_path / "vault"
        md_file = tmp_path / "note.md"
        md_file.write_text("test")

        _quarantine_note(md_file, {"title": "Bad"}, "Body.\n", "test reason", vault)

        q_file = vault / "_quarantine" / "note.md"
        assert q_file.exists()
        content = q_file.read_text(encoding="utf-8")
        assert "quarantine_reason: test reason" in content

    def test_quarantine_has_draft_trust_level(self, tmp_path):
        vault = tmp_path / "vault"
        md_file = tmp_path / "note.md"
        md_file.write_text("test")

        _quarantine_note(md_file, {"title": "Bad"}, "Body.\n", "test reason", vault)

        content = (vault / "_quarantine" / "note.md").read_text(encoding="utf-8")
        assert "trust_level: draft" in content
