"""Tests for inbox file renamer (Decision #14 naming convention).

Pattern: YYYY-MM_TYPE_CLIENT_Description.ext
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from corp_by_os.ingest.classifier import classify
from corp_by_os.ingest.naming_config import (
    clean_description,
    get_client_alias,
    get_client_variants,
    get_type_code,
)
from corp_by_os.ingest.renamer import (
    _infer_client,
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


# -- sanitize --


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


# -- type code resolution --


class TestGetTypeCode:
    def test_rfi_from_filename(self) -> None:
        assert get_type_code(filename="Digital Property RFI - Transport.docx") == "RFI"

    def test_rfp_from_doc_type(self) -> None:
        assert get_type_code(doc_type="rfp_response") == "RFP"

    def test_rfi_beats_rfp_doc_type(self) -> None:
        """Filename hint for RFI overrides doc_type rfp_response."""
        assert get_type_code(doc_type="rfp_response", filename="RFI_Overview.docx") == "RFI"

    def test_va_from_filename(self) -> None:
        assert get_type_code(filename="VA_Questionnaire_WMS.xlsx") == "VA"

    def test_sow_from_filename(self) -> None:
        assert get_type_code(filename="SOW_Implementation_Phase1.docx") == "SOW"

    def test_training_from_source_category(self) -> None:
        assert get_type_code(source_category="training") == "TRAIN"

    def test_competitive_from_source_category(self) -> None:
        assert get_type_code(source_category="competitive") == "COMP"

    def test_architecture_from_doc_type(self) -> None:
        assert get_type_code(doc_type="architecture") == "ARCH"

    def test_presentation_from_doc_type(self) -> None:
        assert get_type_code(doc_type="presentation") == "PRES"

    def test_unknown_gets_misc(self) -> None:
        assert get_type_code() == "MISC"

    def test_unknown_file_gets_misc(self) -> None:
        assert get_type_code(filename="random_file.txt") == "MISC"

    def test_security_from_filename(self) -> None:
        assert get_type_code(filename="SOC_2_Report.pdf") == "SEC"

    def test_workshop_from_filename(self) -> None:
        assert get_type_code(filename="Ahold_Workshop_Agenda.pptx") == "WORK"

    def test_demo_from_doc_type(self) -> None:
        assert get_type_code(doc_type="demo") == "DEMO"

    def test_meeting_from_filename(self) -> None:
        assert get_type_code(filename="Weekly_Standup_Notes.docx") == "MEET"


class TestInferType:
    def test_training_from_metadata(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "TRAIN"

    def test_rfp_from_metadata(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "RFP_Database_WMS.xlsx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "RFP"

    def test_competitive_from_metadata(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "Competitive_Analysis.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "COMP"

    def test_misc_for_no_match(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "random_file.txt"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_type(c) == "MISC"


# -- client alias --


class TestGetClientAlias:
    def test_jaguar_land_rover(self) -> None:
        assert get_client_alias("Jaguar Land Rover") == "JLR"

    def test_lenzing(self) -> None:
        assert get_client_alias("Lenzing") == "LENZ"

    def test_pepsico(self) -> None:
        assert get_client_alias("PepsiCo") == "PEPSI"

    def test_saint_gobain(self) -> None:
        assert get_client_alias("Saint-Gobain") == "SGDBF"

    def test_none_gets_fallback(self) -> None:
        assert get_client_alias(None) == "GEN"

    def test_unknown_client_auto_alias(self) -> None:
        """Unknown clients get auto-generated 5-char alias."""
        result = get_client_alias("Volkswagen Group")
        assert result == "VOLKS"

    def test_case_insensitive(self) -> None:
        assert get_client_alias("lenzing") == "LENZ"
        assert get_client_alias("MICHELIN") == "MICH"


class TestInferClient:
    def test_client_from_classification(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "Lenzing_Discovery.docx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_client(c) == "LENZ"

    def test_no_client_gets_fallback(self, tmp_path: Path, registry: ContentRegistry) -> None:
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        assert _infer_client(c) == "GEN"


# -- description cleaning --


class TestCleanDescription:
    def test_strip_special_chars(self) -> None:
        result = clean_description("Report (2024)")
        assert result == "Report_2024"

    def test_noise_words_removed(self) -> None:
        result = clean_description("Copy of Final Draft v2")
        # "Copy", "of", "Final", "Draft", "v2" are all noise words
        assert "Copy" not in result
        assert "of" not in result.split("_")

    def test_truncation_at_word_boundary(self) -> None:
        long_name = "_".join(["Word"] * 20)
        result = clean_description(long_name)
        assert len(result) <= 50

    def test_empty_after_noise_removal(self) -> None:
        result = clean_description("Copy of Draft v2")
        # Should return "Untitled" if everything is noise
        assert result  # Non-empty

    def test_underscores_preserved(self) -> None:
        result = clean_description("Blue_Yonder_Overview")
        assert "Blue" in result
        assert "Yonder" in result
        assert "Overview" in result


# -- full propose_name --


class TestProposeName:
    def test_full_rename_series(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Series file gets proper convention name."""
        f = tmp_path / "Cognitive_Friday_S4E1_Tag_Changes.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)

        assert result.original_name == "Cognitive_Friday_S4E1_Tag_Changes.pptx"
        assert result.proposed_name.endswith(".pptx")
        assert "TRAIN" in result.proposed_name
        # Has YYYY-MM prefix
        assert result.proposed_name[:4].isdigit()
        assert result.proposed_name[4] == "-"

    def test_rename_with_client(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Client file includes client alias in name."""
        f = tmp_path / "Lenzing_Discovery_Workshop.docx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert "LENZ" in result.proposed_name

    def test_rename_ignores_user_context(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Proposed name uses original filename, not user context."""
        f = tmp_path / "slide_deck.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c, user_context="WMS warehouse architecture overview")
        # Context should NOT appear in the filename
        assert "warehouse" not in result.proposed_name.lower()
        assert "slide_deck" in result.proposed_name

    def test_long_name_truncated(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Long filename truncated to max length."""
        long_name = "A" * 200 + ".pptx"
        f = tmp_path / long_name
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert len(result.proposed_name) <= 125  # 120 stem + 5 ext

    def test_preserves_extension(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Original extension preserved in rename."""
        f = tmp_path / "test.xlsx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert result.proposed_name.endswith(".xlsx")

    def test_components_populated(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """RenameProposal components dict is populated."""
        f = tmp_path / "Cognitive_Friday_S4.pptx"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        assert "date" in result.components
        assert "type" in result.components
        assert "client" in result.components
        assert result.components["type"] == "TRAIN"

    def test_no_topic_in_pattern(self, tmp_path: Path, registry: ContentRegistry) -> None:
        """Decision #14 removes TOPIC from pattern (was GEN in 80% of cases)."""
        f = tmp_path / "random_file.txt"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        # Pattern is now DATE_TYPE_CLIENT_DESC, no TOPIC segment
        parts = result.proposed_name.split("_", 3)
        assert parts[1] == "MISC"  # type code
        assert parts[2] == "GEN"  # client (not topic)

    def test_filename_hint_overrides_source_category(
        self, tmp_path: Path, registry: ContentRegistry
    ) -> None:
        """Filename hint takes priority over source_category for type code."""
        f = tmp_path / "RFI_Security_Assessment.pdf"
        f.write_bytes(b"x" * 100)
        c = classify(f, registry)
        result = propose_name(f, c)
        # "RFI" in filename should give RFI type code
        assert "_RFI_" in result.proposed_name


class TestGetClientVariants:
    def test_alias_expands_to_full_names(self) -> None:
        """'JLR' returns all Jaguar Land Rover variants."""
        variants = get_client_variants("JLR")
        assert "Jaguar Land Rover" in variants
        assert "JLR" in variants

    def test_full_name_expands_to_alias(self) -> None:
        """'Jaguar Land Rover' returns the same group including 'JLR'."""
        variants = get_client_variants("Jaguar Land Rover")
        assert "JLR" in variants
        assert "Jaguar Land Rover" in variants

    def test_unknown_client_returns_itself(self) -> None:
        """Unknown client falls back to [client_name]."""
        variants = get_client_variants("SomeUnknownCorp")
        assert variants == ["SomeUnknownCorp"]

    def test_case_insensitive_lookup(self) -> None:
        """Lookup is case-insensitive."""
        variants = get_client_variants("jaguar land rover")
        assert "Jaguar Land Rover" in variants
