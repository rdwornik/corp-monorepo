"""Tests for the 20-priority rule classifier.

Each priority rule gets at least one test case. Uses pure Path construction —
classify_file never checks file existence, so no tmp_path needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.project.classifier import classify_file

ROOT = Path("/fake/project")


def path(rel: str) -> Path:
    """Return an absolute Path under ROOT. Forward slashes are fine on all platforms."""
    return ROOT / rel


# ---------------------------------------------------------------------------
# Rule 1 — Junk
# ---------------------------------------------------------------------------


def test_rule1_junk_temp_lock():
    r = classify_file(path("~$temp_lock.docx"), ROOT)
    assert r.category == "Junk"
    assert r.is_junk
    assert r.confidence == 1.0


def test_rule1_junk_do_not_use():
    r = classify_file(path("Old Archive DO NOT USE.xlsx"), ROOT)
    assert r.category == "Junk"
    assert r.is_junk


def test_rule1_junk_old_bang():
    r = classify_file(path("draft_old!!.docx"), ROOT)
    assert r.category == "Junk"
    assert r.is_junk


def test_rule1_junk_template_pptx():
    r = classify_file(path("Slide Template.pptx"), ROOT)
    assert r.category == "Junk"
    assert r.is_junk


def test_rule1_junk_template_docx():
    r = classify_file(path("Blank Template.docx"), ROOT)
    assert r.category == "Junk"
    assert r.is_junk


def test_rule1_template_with_content_keyword_not_junk():
    # Template containing "rfp" should NOT be classified Junk (exemption in rule 1)
    r = classify_file(path("RFP_Template.docx"), ROOT)
    assert r.category != "Junk"


# ---------------------------------------------------------------------------
# Rule 2 — Security
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "SOC2 Report 2024.pdf",
        "SOC 2 Audit.pdf",
        "SOC1_Report.pdf",
        "soc 1 report.pdf",
    ],
)
def test_rule2_security_soc(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Security"


def test_rule2_security_iso27001():
    r = classify_file(path("ISO 27001 Certificate.pdf"), ROOT)
    assert r.category == "Security"


@pytest.mark.parametrize(
    "filename",
    [
        "Security Whitepaper.pdf",
        "whitepaper_network.pdf",
    ],
)
def test_rule2_security_whitepaper(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Security"


def test_rule2_security_cloud_services():
    r = classify_file(path("Cloud Services Standards.docx"), ROOT)
    assert r.category == "Security"


def test_rule2_security_reference_architecture():
    r = classify_file(path("General Reference Architecture.pdf"), ROOT)
    assert r.category == "Security"


@pytest.mark.parametrize(
    "filename",
    [
        "DPA Agreement.pdf",
        "data processing agreement.pdf",
        "Data Processing Addendum.docx",
    ],
)
def test_rule2_security_dpa(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Security"


# ---------------------------------------------------------------------------
# Rule 3 — RFP_QA (filename)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "Q&A Document.docx",
        "Q & A Session.docx",
        "Q and A.docx",
        "Questionnaire.xlsx",
        "Offer Questions Round 2.docx",
    ],
)
def test_rule3_rfp_qa_filename(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "RFP_QA"
    assert r.confidence == 1.0


# ---------------------------------------------------------------------------
# Rule 4 — WIP path
# ---------------------------------------------------------------------------


def test_rule4_wip_path():
    r = classify_file(path("WIP/answer_draft.docx"), ROOT)
    assert r.category == "RFP_WIP"
    assert r.confidence == 1.0


def test_rule4_wip_nested():
    r = classify_file(path("RFP/WIP/draft_v3.pptx"), ROOT)
    assert r.category == "RFP_WIP"


# ---------------------------------------------------------------------------
# Rule 5 — Submission / Official Response path
# ---------------------------------------------------------------------------


def test_rule5_official_response_path():
    r = classify_file(path("Official Response/final_answer.docx"), ROOT)
    assert r.category == "RFP_Response"
    assert r.confidence == 1.0


def test_rule5_submission_path():
    r = classify_file(path("Submission/BYR_complete.docx"), ROOT)
    assert r.category == "RFP_Response"


# ---------------------------------------------------------------------------
# Rule 6 — RFP_Response filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "Blue Yonder Responses v2.docx",
        "Blue Yonder Response.docx",
        "BY Responses.docx",
    ],
)
def test_rule6_rfp_response_filename(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "RFP_Response"
    assert r.confidence == 1.0


# ---------------------------------------------------------------------------
# Rule 7 — Data
# ---------------------------------------------------------------------------


def test_rule7_data_csv_extension():
    r = classify_file(path("export.csv"), ROOT)
    assert r.category == "Data"
    assert r.confidence == 1.0


def test_rule7_data_payload():
    # \bpayload\b requires word boundary — use space-separated name
    r = classify_file(path("inbound payload.xlsx"), ROOT)
    assert r.category == "Data"


def test_rule7_data_for_forecast():
    r = classify_file(path("Data for Forecast Q3.xlsx"), ROOT)
    assert r.category == "Data"


def test_rule7_data_forecast_exercise():
    r = classify_file(path("Forecast Exercise 2024.xlsx"), ROOT)
    assert r.category == "Data"


# ---------------------------------------------------------------------------
# Rule 8 — Original path within RFP subtree
# ---------------------------------------------------------------------------


def test_rule8_rfp_original_path():
    r = classify_file(path("RFP/Original/client_rfp.docx"), ROOT)
    assert r.category == "RFP_Original"
    assert r.confidence == 1.0


def test_rule8_original_without_rfp_ancestor_not_triggered():
    # "original" in path but no "rfp" ancestor → should NOT trigger rule 8
    r = classify_file(path("Original/misc.docx"), ROOT)
    assert r.category != "RFP_Original"


# ---------------------------------------------------------------------------
# Rule 9 — Commercial filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,expected_confidence",
    [
        ("PS Estimator v2.xlsx", 1.0),
        ("Effort Estimation Tool.xlsx", 1.0),
        ("Deal Alignment Summary.docx", 1.0),
        ("T&M Pricing Model.xlsx", 0.7),
        ("Time and Material Estimate.xlsx", 0.7),
    ],
)
def test_rule9_commercial_filename(filename, expected_confidence):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Commercial"
    assert r.confidence == expected_confidence


# ---------------------------------------------------------------------------
# Rule 10 — Implementation Services path
# ---------------------------------------------------------------------------


def test_rule10_implementation_services_path():
    r = classify_file(path("Implementation Services/scope_doc.pptx"), ROOT)
    assert r.category == "Commercial"
    assert r.confidence == 1.0


# ---------------------------------------------------------------------------
# Rule 11 — Proposal Presentation path
# ---------------------------------------------------------------------------


def test_rule11_proposal_presentation_path():
    r = classify_file(path("Proposal Presentation/deck.pptx"), ROOT)
    assert r.category == "Proposal"
    assert r.confidence == 1.0


# ---------------------------------------------------------------------------
# Rule 12 — Dated folder / meeting folder
# ---------------------------------------------------------------------------


def test_rule12_dated_folder():
    r = classify_file(path("2024.03.15/agenda.docx"), ROOT)
    assert r.category == "Meeting"
    assert r.confidence == 1.0


def test_rule12_meeting_folder():
    r = classify_file(path("Meeting/notes.docx"), ROOT)
    assert r.category == "Meeting"


def test_rule12_prep_meeting_folder():
    r = classify_file(path("Prep Meeting/slide.pptx"), ROOT)
    assert r.category == "Meeting"


# ---------------------------------------------------------------------------
# Rule 13 — Demo folder
# ---------------------------------------------------------------------------


def test_rule13_demo_folder():
    r = classify_file(path("demo/walkthrough.pptx"), ROOT)
    assert r.category == "Demo"
    assert r.confidence == 1.0


def test_rule13_demo_nested():
    r = classify_file(path("Acme/demo/script.docx"), ROOT)
    assert r.category == "Demo"


# ---------------------------------------------------------------------------
# Rule 14 — Transformation Journey / Workshop folder
# ---------------------------------------------------------------------------


def test_rule14_transformation_journey_folder():
    r = classify_file(path("Transformation Journey/plan.pptx"), ROOT)
    assert r.category == "Strategy"
    assert r.confidence == 1.0


def test_rule14_workshop_folder():
    r = classify_file(path("Workshop/agenda.pptx"), ROOT)
    assert r.category == "Strategy"


# ---------------------------------------------------------------------------
# Rule 15 — RFP folder catch-all (4 sub-cases)
# ---------------------------------------------------------------------------


def test_rule15_rfp_folder_qa_filename():
    r = classify_file(path("RFP/Q&A Round 1.docx"), ROOT)
    assert r.category == "RFP_QA"


def test_rule15_rfp_folder_old_suffix():
    r = classify_file(path("RFP/draft_old.docx"), ROOT)
    assert r.category == "RFP_WIP"


def test_rule15_rfp_folder_strategy_filename():
    # \bstrategy\b requires a word boundary; underscore is \w so use a space-separated stem
    r = classify_file(path("RFP/acme strategy.pptx"), ROOT)
    assert r.category == "Strategy"


def test_rule15_rfp_folder_catch_all():
    r = classify_file(path("RFP/misc_document.docx"), ROOT)
    assert r.category == "RFP_WIP"


# ---------------------------------------------------------------------------
# Rule 16 — Strategy filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "Briefing Book Q4.pptx",
        "Supply Chain Roadmap.pptx",
        "Transformation Journey Plan.docx",
        "Digital Strategy 2025.pptx",
    ],
)
def test_rule16_strategy_filename(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Strategy"


# ---------------------------------------------------------------------------
# Rule 17 — Meeting filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "Meeting Notes.docx",
        "Meeting Note.docx",
        "Notes 1.docx",
        "Notes 42.docx",
    ],
)
def test_rule17_meeting_filename(filename):
    r = classify_file(path(filename), ROOT)
    assert r.category == "Meeting"


# ---------------------------------------------------------------------------
# Rule 18 — Proposal filename
# ---------------------------------------------------------------------------


def test_rule18_proposal_filename():
    r = classify_file(path("Proposal Presentation Final.pptx"), ROOT)
    assert r.category == "Proposal"


# ---------------------------------------------------------------------------
# Rule 19 — Extension fallbacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,expected_category",
    [
        ("unknown_deck.pptx", "Presentation"),
        ("unknown_doc.pdf", "Document"),
        ("unknown_doc.docx", "Document"),
        ("unknown_doc.doc", "Document"),
        ("unknown_sheet.xlsx", "Spreadsheet"),
        ("unknown_sheet.xls", "Spreadsheet"),
    ],
)
def test_rule19_extension_fallbacks(filename, expected_category):
    r = classify_file(path(filename), ROOT)
    assert r.category == expected_category
    assert r.confidence == 0.4  # LOW


# ---------------------------------------------------------------------------
# Rule 20 — Unknown
# ---------------------------------------------------------------------------


def test_rule20_unknown_extension():
    r = classify_file(path("mystery.xyz"), ROOT)
    assert r.category == "Unknown"
    assert r.confidence == 0.4


def test_rule20_no_extension():
    r = classify_file(path("README"), ROOT)
    assert r.category == "Unknown"


# ---------------------------------------------------------------------------
# Classification fields contract
# ---------------------------------------------------------------------------


def test_classification_has_all_fields():
    """Every classification result has the 5 required fields."""
    r = classify_file(path("some_file.docx"), ROOT)
    assert r.category
    assert r.doc_role in ("source_of_truth", "supporting", "obsolete")
    assert 0.0 <= r.confidence <= 1.0
    assert r.reason
    assert isinstance(r.is_junk, bool)


def test_junk_sets_is_junk_flag():
    r = classify_file(path("~$lock.xlsx"), ROOT)
    assert r.is_junk is True
    assert r.doc_role == "obsolete"


def test_non_junk_clears_is_junk_flag():
    r = classify_file(path("Meeting Notes.docx"), ROOT)
    assert r.is_junk is False


# ---------------------------------------------------------------------------
# Priority ordering — higher rule wins over lower rule
# ---------------------------------------------------------------------------


def test_security_wins_over_submission_path():
    # SOC2 report inside an Official Response folder → Security beats path rule 5
    r = classify_file(path("Official Response/SOC2 Report.pdf"), ROOT)
    assert r.category == "Security"


def test_junk_wins_over_rfp_path():
    # ~$ temp file inside RFP folder → Junk beats RFP catch-all (rule 15)
    r = classify_file(path("RFP/~$temp.docx"), ROOT)
    assert r.category == "Junk"


def test_wip_path_wins_over_commercial_filename():
    # PS Estimator inside WIP/ → rule 4 (WIP path) beats rule 9 (Commercial filename)
    r = classify_file(path("WIP/PS Estimator v2.xlsx"), ROOT)
    assert r.category == "RFP_WIP"


def test_rfp_qa_filename_wins_over_wip_path():
    # Q&A doc inside WIP/ — filename rule 3 fires first, before path rule 4
    # Actually rule 3 is checked before rule 4, so Q&A should win
    r = classify_file(path("WIP/Q&A Document.docx"), ROOT)
    assert r.category == "RFP_QA"


def test_file_outside_project_root_still_classifies():
    # File not under ROOT — relative_to raises ValueError, should fall back to name-only
    outside = Path("/completely/different/location/SOC2_Report.pdf")
    r = classify_file(outside, ROOT)
    assert r.category == "Security"
