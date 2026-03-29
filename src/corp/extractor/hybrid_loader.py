"""Load hybrid dual-vectorizer classifier from safe JSON format.

No pickle deserialization risk — model stored as plain JSON arrays.

Usage:
    tfidf_fn, tfidf_ct, clf, meta = load_hybrid_classifier()
    doc_type, confidence = predict_hybrid(tfidf_fn, tfidf_ct, clf, filename, content)

Council Decision #19: separate feature spaces.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_PATH = Path(__file__).parent / "data" / "hybrid_classifier.json"


def load_hybrid_classifier(
    model_path: Path | None = None,
) -> tuple[TfidfVectorizer, TfidfVectorizer, LogisticRegression, dict]:
    """Load dual-vectorizer classifier from JSON. Zero deserialization risk.

    Returns (tfidf_fn, tfidf_ct, clf, metadata).
    Raises FileNotFoundError if model not found.
    """
    import json

    path = Path(model_path) if model_path else _DEFAULT_MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"Hybrid classifier model not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    # -------------------------------------------------------------------------
    # Reconstruct filename vectorizer (char n-grams)
    # -------------------------------------------------------------------------
    fn_p = data["filename_vectorizer"]
    tfidf_fn = TfidfVectorizer(
        analyzer=fn_p["params"]["analyzer"],
        ngram_range=tuple(fn_p["params"]["ngram_range"]),
        max_features=fn_p["params"]["max_features"],
        lowercase=True,
    )
    tfidf_fn.vocabulary_ = {k: int(v) for k, v in fn_p["vocabulary"].items()}
    tfidf_fn.idf_ = np.array(fn_p["idf"], dtype=np.float64)
    # Required by sklearn internals for transform()
    tfidf_fn._tfidf._idf_diag = _build_idf_diag(tfidf_fn.idf_)

    # -------------------------------------------------------------------------
    # Reconstruct content vectorizer (word n-grams)
    # -------------------------------------------------------------------------
    ct_p = data["content_vectorizer"]
    tfidf_ct = TfidfVectorizer(
        analyzer=ct_p["params"]["analyzer"],
        ngram_range=tuple(ct_p["params"]["ngram_range"]),
        max_features=ct_p["params"]["max_features"],
        lowercase=True,
    )
    tfidf_ct.vocabulary_ = {k: int(v) for k, v in ct_p["vocabulary"].items()}
    tfidf_ct.idf_ = np.array(ct_p["idf"], dtype=np.float64)
    tfidf_ct._tfidf._idf_diag = _build_idf_diag(tfidf_ct.idf_)

    # -------------------------------------------------------------------------
    # Reconstruct logistic regression classifier
    # -------------------------------------------------------------------------
    clf = LogisticRegression()
    clf.coef_ = np.array(data["classifier"]["coef"], dtype=np.float64)
    clf.intercept_ = np.array(data["classifier"]["intercept"], dtype=np.float64)
    clf.classes_ = np.array(data["classifier"]["classes"])

    meta = data.get("metadata", {})
    logger.debug(
        "Hybrid classifier loaded: %d classes, cv_acc=%.3f",
        len(clf.classes_),
        meta.get("cv_accuracy_combined", 0),
    )
    return tfidf_fn, tfidf_ct, clf, meta


def _build_idf_diag(idf: np.ndarray):
    """Build the sparse diagonal IDF matrix sklearn needs internally."""
    from scipy.sparse import diags

    return diags(idf, offsets=0, format="csr")


def predict_hybrid(
    tfidf_fn: TfidfVectorizer,
    tfidf_ct: TfidfVectorizer,
    clf: LogisticRegression,
    filename: str,
    content: str = "",
) -> tuple[str, float]:
    """Predict doc_type using dual feature spaces.

    Returns (doc_type, confidence).
    confidence is the max softmax probability across classes.
    """
    X_fn = tfidf_fn.transform([filename])
    X_ct = tfidf_ct.transform([content])
    X = hstack([X_fn, X_ct])

    prediction: str = clf.predict(X)[0]
    confidence = float(clf.predict_proba(X)[0].max())
    return prediction, confidence


@lru_cache(maxsize=1)
def _cached_hybrid_model(
    model_path_str: str,
) -> tuple[TfidfVectorizer, TfidfVectorizer, LogisticRegression, dict]:
    """Module-level cache so we load once per process, not once per call."""
    return load_hybrid_classifier(Path(model_path_str))


def get_cached_model(
    model_path: Path | None = None,
) -> tuple[TfidfVectorizer, TfidfVectorizer, LogisticRegression, dict]:
    """Get the cached model instance (loads on first call, reuses after)."""
    path = model_path or _DEFAULT_MODEL_PATH
    return _cached_hybrid_model(str(path))
