"""Tests for inbox file renamer (Decision #10 naming convention)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from corp_by_os.ingest.classifier import classify
from corp_by_os.ingest.renamer import (
    RenameProposal,
    _infer_client,
    _infer_topic,
    _infer_type,
    _sanitize,
    propose_name,
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
                "naming_patterns": ["Cognitive_Friday*", "CF_S[0-9]*"],
                "expected_extensions": [".mp4", ".pptx"],
                "default_metadata": {
                    "source_category": "training",
                    "topics": ["Cognitive Planning", "AI/ML"],
                    "products": ["Cognitive Demand Planning"],
                },
            },
        },
        "destination_rules": [
            {
                "name": "RFP databases",
                "match": {
                    "filename_contains": ["RFP_Database"],
                    "extensions": [".xlsx"],
                },
                "destination": "50_RFP/_databases",
                "metadata": {"source_category": "rfp"},
            },
            {
                "name": "Competitive materials",
                "match": {
                    "filename_contains": ["Differentiation", "Competitive"],
                    "extensions": [".pdf", ".pptx"],
                },
                "destination": "60_Source_Library/03_Competitive",
                "metadata": {"source_category": "competitive"},
            },
        ],
        "client_patterns": [
            {"pattern": "Lenzing", "project": "Lenzing_Planning"},
            {"pattern": "SGDBF|Saint.Gobain", "project": "SGDBF_Retail"},
        ],
        "fallback": {
            "unknown_destination": "00_Inbox/_Unmatched",
            "confidence_threshold": 0.75,
        },
    }
    path = tmp_path / "content_registry.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return path


@pytest.fixture()
def registry(registry_path: Path) -> ContentRegistry:
    return ContentRegistry(registry_path)


class TestSanitize:
    def test_spaces_to_underscores(self) -> None:
        assert _sanitize("hello world") == "hello_world"

    def test_special_chars_removed(self) -> None:
        assert _sanitize("file@name#v2") == "file_name_v2"

    def test_collapse_underscores(self) -> None:
        assert _sanitize("hello___world") == "hello_world"

    def test_strip_leading_trailing(self) -> None:
        assert _sanitize("_hello_") == "hello"

    def test_preserve_hyphens(self) -> None:
        assert _sanitize("pre-sales-training") == "pre-sales-training"

    def test_preserve_dots(self) -> None:
        assert _sanitize("v2.1") == "v2.1"


class TestInferType:
    def test_training_from_metadata(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "TRAINING"

    def test_rfp_from_metadata(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "RFP_Database_WMS.xlsx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "RFP"

    def test_competitive_from_metadata(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Competitive_Analysis.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "COMPETITIVE"

    def test_misc_for_no_match(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "random_file.txt"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "MISC"


class TestInferTopic:
    def test_platform_from_series_topics(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_topic(c) == "PLATFORM"

    def test_user_context_ignored_for_topic(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """user_context is extraction hint, not naming source."""
        f = tmp_path / "some_file.pdf"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        # Context mentions WMS but should NOT influence topic code
        assert _infer_topic(c, "This is about WMS warehouse management") == "GEN"

    def test_metadata_determines_topic(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Topic comes from classification metadata, not user context."""
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        # Metadata says Cognitive Planning → PLATFORM, context is ignored
        assert _infer_topic(c, "WMS implementation details") == "PLATFORM"

    def test_gen_fallback(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "random_file.txt"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_topic(c) == "GEN"


class TestInferClient:
    def test_client_from_classification(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Lenzing_Discovery.docx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_client(c) == "LENZING"

    def test_no_client(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_client(c) is None


class TestProposeName:
    def test_full_rename_series(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Series file gets proper convention name."""
        f = tmp_path / "Cognitive_Friday_S4E1_Tag_Changes.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)

        assert result.original_name == "Cognitive_Friday_S4E1_Tag_Changes.pptx"
        assert result.proposed_name.endswith(".pptx")
        assert "TRAINING" in result.proposed_name
        assert "PLATFORM" in result.proposed_name
        # Has YYYY-MM prefix
        assert result.proposed_name[:4].isdigit()
        assert result.proposed_name[4] == "-"

    def test_rename_with_client(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Client file includes client code in name."""
        f = tmp_path / "Lenzing_Discovery_Workshop.docx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert "LENZING" in result.proposed_name

    def test_rename_ignores_user_context(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Proposed name uses original filename, not user context."""
        f = tmp_path / "slide_deck.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c, user_context="WMS warehouse architecture overview")
        # Context should NOT appear in the filename
        assert "warehouse" not in result.proposed_name.lower()
        assert "slide_deck" in result.proposed_name

    def test_long_name_truncated(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Long filename truncated to max length."""
        long_name = "A" * 200 + ".pptx"
        f = tmp_path / long_name
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert len(result.proposed_name) <= 125  # 120 stem + 5 ext

    def test_preserves_extension(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Original extension preserved in rename."""
        f = tmp_path / "test.xlsx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert result.proposed_name.endswith(".xlsx")

    def test_components_populated(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """RenameProposal components dict is populated."""
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert "date" in result.components
        assert "type" in result.components
        assert "topic" in result.components
        assert result.components["type"] == "TRAINING"
