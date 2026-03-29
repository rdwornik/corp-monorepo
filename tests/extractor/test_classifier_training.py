"""Test filename-based doc_type classification against real extraction data.

Fixtures generated from 690 CKE extraction outputs. Tests classifier behavior
against filenames with classifiable keywords and tracks agreement rate.
"""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "classifier_training.json"

if FIXTURES_PATH.exists():
    ALL_FIXTURES = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
else:
    ALL_FIXTURES = []


def test_classifier_fixtures_exist() -> None:
    """Verify fixture file exists and has data."""
    assert FIXTURES_PATH.exists(), "classifier_training.json not found"
    assert len(ALL_FIXTURES) > 100, f"Expected 100+ fixtures, got {len(ALL_FIXTURES)}"


def test_doc_type_coverage() -> None:
    """Training data covers all major doc_types."""
    doc_types = {f["doc_type"] for f in ALL_FIXTURES}
    expected = {"training", "product_doc", "meeting", "security", "rfp_response", "architecture"}
    missing = expected - doc_types
    assert not missing, f"Missing doc_types in training data: {missing}"


def test_classify_from_filename_no_crashes() -> None:
    """classify_from_filename handles all real filenames without error."""
    from corp_knowledge_extractor.doc_type_classifier import classify_from_filename

    for fixture in ALL_FIXTURES:
        # Should not raise
        classify_from_filename(fixture["filename"])


def test_classifier_agreement_rate() -> None:
    """Filename classifier agrees with extraction doc_type at a reasonable rate.

    We expect some disagreement because extraction uses folder paths and
    content analysis in addition to filename patterns. This test tracks the
    agreement rate as a quality metric.
    """
    from corp_knowledge_extractor.doc_type_classifier import classify_from_filename

    agreed = 0
    disagreed = 0
    no_match = 0

    for fixture in ALL_FIXTURES:
        result = classify_from_filename(fixture["filename"])
        if result is None:
            no_match += 1
        elif result == fixture["doc_type"]:
            agreed += 1
        else:
            disagreed += 1

    total_classified = agreed + disagreed
    if total_classified > 0:
        agreement_rate = agreed / total_classified
        # Expect at least 50% agreement when the classifier fires
        assert agreement_rate >= 0.50, (
            f"Classifier agreement rate too low: {agreement_rate:.1%} "
            f"({agreed}/{total_classified} agreed, {disagreed} disagreed)"
        )


def test_rfp_keywords_classified_correctly() -> None:
    """Files with explicit RFP/RFI keywords should classify as rfp_response."""
    from corp_knowledge_extractor.doc_type_classifier import classify_from_filename

    rfp_fixtures = [
        f
        for f in ALL_FIXTURES
        if f["doc_type"] == "rfp_response" and any(kw in f["filename"].lower() for kw in ["rfp", "rfi", "request for"])
    ]

    for fixture in rfp_fixtures:
        result = classify_from_filename(fixture["filename"])
        assert result == "rfp_response", f"RFP file misclassified: {fixture['filename']!r} → {result}"


def test_training_keywords_classified() -> None:
    """Files with explicit training keywords should classify as training."""
    from corp_knowledge_extractor.doc_type_classifier import classify_from_filename

    training_fixtures = [
        f
        for f in ALL_FIXTURES
        if f["doc_type"] == "training"
        and any(kw in f["filename"].lower() for kw in ["training", "enablement", "course"])
    ]

    for fixture in training_fixtures:
        result = classify_from_filename(fixture["filename"])
        assert result == "training", f"Training file misclassified: {fixture['filename']!r} → {result}"


def test_security_assessment_keywords_classified() -> None:
    """Files with security assessment keywords classify correctly."""
    from corp_knowledge_extractor.doc_type_classifier import classify_from_filename

    # classify_from_filename only detects "security assessment" for
    # vendor_assessment. Other security keywords are handled by
    # classify_doc_type's filename rules (not tested here).
    security_fixtures = [
        f
        for f in ALL_FIXTURES
        if f["doc_type"] == "security"
        and any(
            kw in f["filename"].lower()
            for kw in [
                "security assessment",
                "security questionnaire",
            ]
        )
    ]

    for fixture in security_fixtures:
        result = classify_from_filename(fixture["filename"])
        assert result is not None, f"Security assessment file not classified: {fixture['filename']!r}"
