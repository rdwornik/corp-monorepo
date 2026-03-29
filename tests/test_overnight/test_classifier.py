"""Tests for overnight metadata-based classifier."""

from __future__ import annotations

from corp.overnight.classifier import (
    _clean_spaces,
    _propose_rename,
    _slugify,
    classify_batch,
    classify_from_metadata,
    generate_filename,
)
from corp.schema.folder_names import (
    INBOX,
    PROJECTS,
    RFP,
    SOURCE_LIBRARY,
    TEMPLATES,
)


def _make_scan_result(
    path: str = f"{SOURCE_LIBRARY}/doc.pptx",
    extension: str = ".pptx",
    title: str | None = "Platform Architecture Overview",
    text_preview: str = "Blue Yonder platform services architecture",
    slide_count: int | None = None,
    headings: list[str] | None = None,
    doc_type: str | None = None,
) -> dict:
    meta: dict = {}
    if title:
        meta["title"] = title
    if text_preview:
        meta["text_preview"] = text_preview
    if slide_count:
        meta["slide_count"] = slide_count
    if headings:
        meta["headings"] = headings
    if doc_type:
        meta["type"] = doc_type
    return {
        "path": path,
        "filename": path.split("/")[-1],
        "extension": extension,
        "size_bytes": 1024,
        "metadata": meta,
    }


ROUTING_MAP: dict = {
    "folders": {
        TEMPLATES: {"vault_target": "05_templates"},
        SOURCE_LIBRARY: {"vault_target": "04_evergreen"},
    },
}


# --- Test: Rename Actions ---


class TestProposeRename:
    def test_space_cleanup(self) -> None:
        action, name, conf = _propose_rename(
            "Budget Report Q2.xlsx",
            "Budget Report Q2",
            ".xlsx",
            {},
            f"{SOURCE_LIBRARY}/Budget Report Q2.xlsx",
        )
        assert action == "space_cleanup"
        assert name == "Budget_Report_Q2.xlsx"
        assert conf == 0.95

    def test_remove_copy_of_prefix(self) -> None:
        action, name, conf = _propose_rename(
            "Copy of Budget.xlsx",
            "Copy of Budget",
            ".xlsx",
            {},
            f"{INBOX}/Copy of Budget.xlsx",
        )
        assert action == "remove_copy"
        assert name == "Budget.xlsx"
        assert conf == 0.92

    def test_remove_copy_suffix(self) -> None:
        action, name, conf = _propose_rename(
            "Budget - Copy.xlsx",
            "Budget - Copy",
            ".xlsx",
            {},
            f"{INBOX}/Budget - Copy.xlsx",
        )
        assert action == "remove_copy"
        assert name == "Budget.xlsx"
        assert conf == 0.92

    def test_remove_numbered_copy(self) -> None:
        action, name, conf = _propose_rename(
            "Budget (1).xlsx",
            "Budget (1)",
            ".xlsx",
            {},
            f"{INBOX}/Budget (1).xlsx",
        )
        assert action == "remove_copy"
        assert name == "Budget.xlsx"
        assert conf == 0.92

    def test_enrich_generic_name(self) -> None:
        action, name, conf = _propose_rename(
            "Presentation.pptx",
            "Presentation",
            ".pptx",
            {},
            f"{PROJECTS}/Lenzing_Planning/Presentation.pptx",
        )
        assert action == "enrich_generic"
        assert "Lenzing_Planning" in name
        assert "Presentation" in name
        assert conf == 0.80

    def test_skip_good_name(self) -> None:
        action, name, conf = _propose_rename(
            "WMS_Best_Practices.pptx",
            "WMS_Best_Practices",
            ".pptx",
            {},
            f"{SOURCE_LIBRARY}/WMS_Best_Practices.pptx",
        )
        assert action == "skip"
        assert name is None
        assert conf == 0.0

    def test_skip_generic_no_context(self) -> None:
        """Generic name with no enrichable path context → skip."""
        action, name, conf = _propose_rename(
            "Document.docx",
            "Document",
            ".docx",
            {},
            "Document.docx",
        )
        assert action == "skip"
        assert name is None

    def test_does_not_replace_with_slide_title(self) -> None:
        """A descriptive filename should NOT be replaced by slide title."""
        action, name, conf = _propose_rename(
            "WMS_Architecture_Deck.pptx",
            "WMS_Architecture_Deck",
            ".pptx",
            {"title": "Something Completely Different"},
            f"{SOURCE_LIBRARY}/WMS_Architecture_Deck.pptx",
        )
        assert action == "skip"
        assert name is None


# --- Test: Pinned vs Movable Folders ---


class TestFolderRules:
    def test_pinned_project_files_never_move(self) -> None:
        sr = _make_scan_result(
            path=f"{PROJECTS}/Lenzing_Planning/demo.pptx",
            text_preview="training exercise lab hands-on",
        )
        result = classify_from_metadata(sr, ROUTING_MAP)
        assert result.proposed_folder is None

    def test_pinned_initiative_files_never_move(self) -> None:
        sr = _make_scan_result(
            path="20_Extra_Initiatives/side_project/notes.docx",  # Extra folder not in constants
            text_preview="rfp request for proposal",
        )
        result = classify_from_metadata(sr, ROUTING_MAP)
        assert result.proposed_folder is None

    def test_inbox_files_can_move(self) -> None:
        sr = _make_scan_result(
            path=f"{INBOX}/training doc.pptx",
            text_preview="training exercise lab hands-on workshop",
        )
        result = classify_from_metadata(sr, ROUTING_MAP)
        assert result.proposed_folder is not None
        assert "Training" in result.proposed_folder

    def test_inbox_rfp_routes_correctly(self) -> None:
        sr = _make_scan_result(
            path=f"{INBOX}/client_rfp.docx",
            text_preview="rfp request for proposal response template",
        )
        result = classify_from_metadata(sr, ROUTING_MAP)
        assert result.proposed_folder == RFP

    def test_non_inbox_non_pinned_no_move(self) -> None:
        """Files in SOURCE_LIBRARY etc. shouldn't be moved either."""
        sr = _make_scan_result(
            path=f"{SOURCE_LIBRARY}/doc.pptx",
            text_preview="training exercise lab hands-on workshop",
        )
        result = classify_from_metadata(sr, ROUTING_MAP)
        assert result.proposed_folder is None


# --- Test: classify_batch filters ---


class TestClassifyBatch:
    def test_batch_only_returns_actionable(self) -> None:
        """classify_batch should only return files that need action."""
        files = [
            _make_scan_result(path=f"{SOURCE_LIBRARY}/Good_Name.pptx"),
            _make_scan_result(path=f"{SOURCE_LIBRARY}/Also Fine.pptx"),
            _make_scan_result(path=f"{SOURCE_LIBRARY}/Another_Clean.pptx"),
        ]
        results = classify_batch(files, ROUTING_MAP)
        # "Also Fine.pptx" has a space → space_cleanup action
        # Others are clean → skip
        assert len(results) == 1
        assert results[0].proposed_name == "Also_Fine.pptx"

    def test_batch_empty_for_clean_files(self) -> None:
        files = [
            _make_scan_result(path=f"{SOURCE_LIBRARY}/Clean_Name.pptx"),
            _make_scan_result(path=f"{SOURCE_LIBRARY}/Another_Clean.pptx"),
        ]
        results = classify_batch(files, ROUTING_MAP)
        assert len(results) == 0

    def test_batch_includes_moves_from_inbox(self) -> None:
        files = [
            _make_scan_result(
                path=f"{INBOX}/demo script.pptx",
                text_preview="demo script demo scenario click path",
            ),
        ]
        results = classify_batch(files, ROUTING_MAP)
        assert len(results) == 1
        assert results[0].proposed_folder is not None
        assert results[0].proposed_name is not None  # space cleanup too


# --- Test: generate_filename ---


class TestGenerateFilename:
    def test_generate_with_client(self) -> None:
        meta = {"title": "Platform Architecture Overview"}
        name = generate_filename(meta, client="Lenzing", extension=".pptx")
        assert name == "Lenzing_Platform_Architecture_Overview.pptx"

    def test_generate_without_client(self) -> None:
        meta = {"title": "WMS Best Practices Guide"}
        name = generate_filename(meta, extension=".pdf")
        assert name == "WMS_Best_Practices_Guide.pdf"

    def test_generate_truncates_long_title(self) -> None:
        meta = {"title": "A" * 200}
        name = generate_filename(meta, extension=".pptx")
        stem = name.rsplit(".", 1)[0]
        assert len(stem) <= 80

    def test_generate_no_title(self) -> None:
        meta = {"title": ""}
        name = generate_filename(meta, extension=".pdf")
        assert name == ""

    def test_generate_special_chars(self) -> None:
        meta = {"title": "Q2/Q3 Planning: Next Steps (Draft)"}
        name = generate_filename(meta, extension=".pptx")
        assert "/" not in name
        assert ":" not in name
        assert "(" not in name


# --- Test: _slugify ---


class TestSlugify:
    def test_basic(self) -> None:
        assert _slugify("Hello World") == "Hello_World"

    def test_special_chars(self) -> None:
        assert _slugify("Q2/Q3: Planning") == "Q2_Q3_Planning"

    def test_collapse_underscores(self) -> None:
        assert _slugify("a   b---c") == "a_b_c"


# --- Test: _clean_spaces ---


class TestCleanSpaces:
    def test_replaces_spaces(self) -> None:
        assert _clean_spaces("hello world") == "hello_world"

    def test_multiple_spaces(self) -> None:
        assert _clean_spaces("a  b   c") == "a_b_c"

    def test_preserves_underscores(self) -> None:
        assert _clean_spaces("already_clean") == "already_clean"
