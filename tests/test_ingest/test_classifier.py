"""Tests for inbox file classifier."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from corp_by_os.ingest.classifier import (
    _human_size,
    classify,
    detect_file_info,
)
from corp_by_os.ops.registry import ContentRegistry


@pytest.fixture()
def registry_path(tmp_path: Path) -> Path:
    """Create a test content_registry.yaml."""
    data = {
        "version": "1.0",
        "series": {
            "cognitive_friday": {
                "display_name": "Cognitive Friday",
                "destination": "60_Source_Library/02_Training_Enablement/Cognitive_Friday",
                "naming_patterns": [
                    "Cognitive_Friday*",
                    "Cognitive_Fridays*",
                    "CF_S[0-9]*",
                ],
                "expected_extensions": [".mp4", ".pptx"],
                "default_metadata": {
                    "source_category": "training",
                    "topics": ["Cognitive Planning", "AI/ML"],
                },
            },
            "lighthouse_program": {
                "display_name": "Lighthouse Program",
                "destination": "60_Source_Library/02_Training_Enablement/Lighthouse",
                "naming_patterns": ["Lighthouse*"],
                "default_metadata": {
                    "source_category": "training",
                },
            },
        },
        "destination_rules": [
            {
                "name": "RFP databases",
                "match": {
                    "filename_contains": ["RFP_Database"],
                    "extensions": [".xlsx", ".csv"],
                },
                "destination": "50_RFP/_databases",
                "metadata": {"source_category": "rfp"},
            },
            {
                "name": "Security compliance docs",
                "match": {
                    "filename_contains": ["ISO_27001", "SOC_2"],
                    "extensions": [".pdf"],
                },
                "destination": "50_RFP/Certificate",
                "metadata": {"source_category": "security_compliance"},
            },
        ],
        "client_patterns": [
            {"pattern": "Lenzing", "project": "Lenzing_Planning"},
            {"pattern": "SGDBF|Saint.Gobain", "project": "SGDBF_Retail"},
        ],
        "fallback": {
            "unknown_destination": "00_Inbox/_Unmatched",
            "confidence_threshold": 0.75,
            "llm_escalation_threshold": 0.50,
        },
    }
    path = tmp_path / "content_registry.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return path


@pytest.fixture()
def registry(registry_path: Path) -> ContentRegistry:
    return ContentRegistry(registry_path)


class TestHumanSize:
    def test_bytes(self) -> None:
        assert _human_size(500) == "500 B"

    def test_kilobytes(self) -> None:
        assert _human_size(2048) == "2.0 KB"

    def test_megabytes(self) -> None:
        result = _human_size(12_582_912)
        assert "12.0 MB" == result

    def test_gigabytes(self) -> None:
        result = _human_size(2_147_483_648)
        assert "2.0 GB" == result


class TestDetectFileInfo:
    def test_basic_detection(self, tmp_path: Path) -> None:
        f = tmp_path / "test.pptx"
        f.write_bytes(b"x" * 1024)
        info = detect_file_info(f)
        assert info.filename == "test.pptx"
        assert info.extension == ".pptx"
        assert info.size_bytes == 1024
        assert info.size_human == "1.0 KB"
        assert info.path == f

    def test_uppercase_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "test.PPTX"
        f.write_bytes(b"x" * 100)
        info = detect_file_info(f)
        assert info.extension == ".pptx"


class TestClassify:
    def test_series_match_high_confidence(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Cognitive Friday file classified with high confidence."""
        f = tmp_path / "Cognitive_Friday_S4E1_Tag_Changes.pptx"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.best_match is not None
        assert result.best_match.series_id == "cognitive_friday"
        assert result.best_match.confidence >= 0.90
        assert result.needs_human is False

    def test_series_match_returns_destination(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Lighthouse_Session_5.mp4"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.best_match is not None
        assert result.best_match.destination == (
            "60_Source_Library/02_Training_Enablement/Lighthouse"
        )

    def test_client_detected(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Client name detected from filename."""
        f = tmp_path / "Lenzing_Discovery_Notes.docx"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.detected_client == "Lenzing_Planning"

    def test_client_detected_alongside_series(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Client detected even when series match wins."""
        # Both Cognitive Friday and Lenzing in name — series wins, but client detected
        f = tmp_path / "Cognitive_Friday_Lenzing.mp4"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.best_match is not None
        assert result.best_match.method == "series"
        assert result.detected_client == "Lenzing_Planning"

    def test_rule_match(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Destination rule match."""
        f = tmp_path / "WMS_RFP_Database_v3.xlsx"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.best_match is not None
        assert result.best_match.rule_name == "RFP databases"
        assert result.best_match.destination == "50_RFP/_databases"

    def test_no_match_needs_human(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Unknown file needs human review."""
        f = tmp_path / "random_notes_v2.txt"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        assert result.best_match is None
        assert result.needs_human is True

    def test_low_confidence_needs_human(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Low-confidence rule match still needs human."""
        # SOC_2 doc as .docx won't match (rule requires .pdf)
        f = tmp_path / "SOC_2_Report.docx"
        f.write_bytes(b"x" * 1024)
        result = classify(f, registry)
        # No rule match for .docx — should need human
        assert result.needs_human is True

    def test_file_info_populated(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Classification includes file info."""
        f = tmp_path / "test.pdf"
        f.write_bytes(b"x" * 2048)
        result = classify(f, registry)
        assert result.file_info.filename == "test.pdf"
        assert result.file_info.size_bytes == 2048

    def test_custom_threshold(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Custom confidence threshold changes needs_human."""
        f = tmp_path / "ISO_27001_Certificate_BY.pdf"
        f.write_bytes(b"x" * 1024)
        # With default threshold (0.75), rule match at 0.85 = OK
        result_default = classify(f, registry, confidence_threshold=0.75)
        assert result_default.needs_human is False
        # With high threshold (0.95), same match = needs human
        result_high = classify(f, registry, confidence_threshold=0.95)
        assert result_high.needs_human is True
