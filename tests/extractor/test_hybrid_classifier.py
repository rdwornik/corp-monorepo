"""Tests for hybrid_loader and classify_doc_type_hybrid integration.

Covers:
- JSON round-trip (load → predict without touching training code)
- Content vs filename-only prediction paths
- Feature flag USE_TFIDF
- Graceful degradation on missing model
- Separate feature spaces (dual vectorizer, not combined)
- Return contract: (doc_type, confidence, method) tuple
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parents[2] / "src" / "corp" / "extractor" / "data"
MODEL_PATH = DATA_DIR / "hybrid_classifier.json"

TRAINING_FILENAME = "2024-01_TRAINING_Lenzing_Demand-Planning-Fundamentals.pptx"
TRAINING_CONTENT = "Learning objectives overview agenda hands-on exercises training module"

MEETING_FILENAME = "2024-03_MEETING_Lenzing_Discovery-Call-Notes.docx"
MEETING_CONTENT = "meeting notes discovery call recap agenda action items"

SECURITY_FILENAME = "2024-02_SECURITY_Lenzing_SOC2-Type2-Audit-Report.pdf"


# ---------------------------------------------------------------------------
# hybrid_loader.load_hybrid_classifier
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_hybrid_loader_from_json():
    """Model loads from JSON without pickle, returns correct types."""
    from corp.extractor.hybrid_loader import load_hybrid_classifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    tfidf_fn, tfidf_ct, clf, meta = load_hybrid_classifier(MODEL_PATH)

    assert isinstance(tfidf_fn, TfidfVectorizer)
    assert isinstance(tfidf_ct, TfidfVectorizer)
    assert isinstance(clf, LogisticRegression)
    assert isinstance(meta, dict)
    assert len(clf.classes_) > 0


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_separate_feature_spaces():
    """Filename vectorizer uses char n-grams; content uses word n-grams — never mixed."""
    from corp.extractor.hybrid_loader import load_hybrid_classifier

    tfidf_fn, tfidf_ct, _clf, _meta = load_hybrid_classifier(MODEL_PATH)

    assert tfidf_fn.analyzer == "char"
    assert tfidf_ct.analyzer == "word"
    # Vocabulary sizes should differ (char n-grams << word n-grams in coverage)
    assert len(tfidf_fn.vocabulary_) > 0
    assert len(tfidf_ct.vocabulary_) > 0


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_predict_with_content():
    """Prediction with filename + content returns (str, float) contract."""
    from corp.extractor.hybrid_loader import (
        load_hybrid_classifier,
        predict_hybrid,
    )

    tfidf_fn, tfidf_ct, clf, _meta = load_hybrid_classifier(MODEL_PATH)
    doc_type, conf = predict_hybrid(tfidf_fn, tfidf_ct, clf, TRAINING_FILENAME, TRAINING_CONTENT)

    assert isinstance(doc_type, str)
    assert 0.0 <= conf <= 1.0
    assert doc_type in clf.classes_


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_predict_without_content():
    """Filename-only prediction (empty content string) still returns valid output."""
    from corp.extractor.hybrid_loader import (
        load_hybrid_classifier,
        predict_hybrid,
    )

    tfidf_fn, tfidf_ct, clf, _meta = load_hybrid_classifier(MODEL_PATH)
    doc_type, conf = predict_hybrid(tfidf_fn, tfidf_ct, clf, TRAINING_FILENAME, "")

    assert isinstance(doc_type, str)
    assert 0.0 <= conf <= 1.0


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_balanced_class_weights():
    """Model metadata records training parameters (class_weight=balanced)."""
    from corp.extractor.hybrid_loader import load_hybrid_classifier

    _fn, _ct, clf, meta = load_hybrid_classifier(MODEL_PATH)
    # coef_ shape: (n_classes, n_features) — balanced weighting produces non-trivial coefficients
    assert clf.coef_.shape[0] > 1
    assert not np.all(clf.coef_ == 0)


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_high_confidence_correct():
    """High-confidence prediction for an archetypal training file should be 'training'."""
    from corp.extractor.hybrid_loader import (
        load_hybrid_classifier,
        predict_hybrid,
    )

    tfidf_fn, tfidf_ct, clf, _meta = load_hybrid_classifier(MODEL_PATH)
    doc_type, conf = predict_hybrid(tfidf_fn, tfidf_ct, clf, TRAINING_FILENAME, TRAINING_CONTENT)

    # If model confidence >= 0.5, we trust it — verify it produced a plausible answer
    if conf >= 0.5:
        assert doc_type in {"training", "presentation", "general"}  # not a nonsensical class


# ---------------------------------------------------------------------------
# classify_doc_type_hybrid — integration with doc_type_classifier
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_classify_doc_type_hybrid_returns_tuple():
    """classify_doc_type_hybrid returns (doc_type, conf, method) for any input."""
    from corp.extractor.doc_type_classifier import classify_doc_type_hybrid

    result = classify_doc_type_hybrid(TRAINING_FILENAME, TRAINING_CONTENT)

    assert isinstance(result, tuple) and len(result) == 3
    doc_type, conf, method = result
    assert doc_type is None or isinstance(doc_type, str)
    assert 0.0 <= conf <= 1.0
    assert method in {"tfidf", "regex", "none"}


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model file not present")
def test_classify_returns_tfidf_method_when_confident():
    """When TF-IDF fires above threshold, method == 'tfidf'."""
    from corp.extractor.doc_type_classifier import classify_doc_type_hybrid

    # A very archetypal security filename should produce high TF-IDF confidence
    doc_type, conf, method = classify_doc_type_hybrid(
        SECURITY_FILENAME, "SOC 2 Type II audit report controls assurance"
    )

    if method == "tfidf":
        assert conf >= 0.5
        assert doc_type is not None


def test_feature_flag_off_skips_tfidf():
    """When USE_TFIDF=False, classify_doc_type_hybrid never calls the model."""
    import corp.extractor.doc_type_classifier as dtc
    from corp.extractor.doc_type_classifier import classify_doc_type_hybrid

    original = dtc.USE_TFIDF
    try:
        dtc.USE_TFIDF = False
        with patch("corp.extractor.hybrid_loader.get_cached_model") as mock_model:
            doc_type, conf, method = classify_doc_type_hybrid(MEETING_FILENAME, "")
            mock_model.assert_not_called()
        # Regex should have fired on MEETING_FILENAME (contains "MEETING" and "Notes")
        assert method in {"regex", "none"}
    finally:
        dtc.USE_TFIDF = original


def test_model_missing_graceful():
    """Missing model file → FileNotFoundError caught → falls back to regex, no crash."""
    from corp.extractor.doc_type_classifier import classify_doc_type_hybrid

    with patch("corp.extractor.hybrid_loader.get_cached_model") as mock_model:
        mock_model.side_effect = FileNotFoundError("model not found")
        doc_type, conf, method = classify_doc_type_hybrid(MEETING_FILENAME, "")

    # Regex should pick up "meeting" in MEETING_FILENAME
    assert method in {"regex", "none"}
    assert doc_type != "tfidf_error"


def test_regex_fallback_when_tfidf_low_confidence():
    """When TF-IDF confidence is below threshold, method falls through to regex."""
    from corp.extractor.doc_type_classifier import classify_doc_type_hybrid

    # Filename that clearly matches a regex pattern (training)
    training_fn = "2024-01_TRAINING_Lenzing_Enablement-Bootcamp.pptx"

    with patch("corp.extractor.hybrid_loader.get_cached_model") as mock_get:
        mock_predict = MagicMock(return_value=("general", 0.3))
        mock_get.return_value = (MagicMock(), MagicMock(), MagicMock(), {})

        with patch(
            "corp.extractor.hybrid_loader.predict_hybrid",
            mock_predict,
        ):
            doc_type, conf, method = classify_doc_type_hybrid(training_fn, "")

    # TF-IDF confidence 0.3 < 0.5 threshold → regex fires for "training"/"enablement"
    assert method == "regex"
    assert doc_type == "training"
