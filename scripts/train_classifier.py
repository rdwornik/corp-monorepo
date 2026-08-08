"""Train hybrid dual-vectorizer classifier.

Filename features (char n-grams) + content features (word n-grams)
combined via scipy.sparse.hstack → LogisticRegression.

Council Decision #19: separate feature spaces.
No pickle — model serialized as JSON.

Output: models/hybrid_classifier.json
        models/cv_report.txt
"""

from __future__ import annotations

import json
from pathlib import Path

from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score

MONOREPO = Path(__file__).resolve().parents[1]
MODELS_DIR = MONOREPO / "models"
TRAIN_PATH = MODELS_DIR / "classifier_train.json"


def main() -> None:
    train: list[dict] = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))

    filenames = [d.get("filename_text", d["filename"]) for d in train]
    contents = [d.get("content_text", "") for d in train]
    labels = [d["doc_type"] for d in train]

    n_with_content = sum(1 for c in contents if c.strip())
    print(f"Training set: {len(train)} examples, {n_with_content} with content ({n_with_content/len(train)*100:.0f}%)")

    # -------------------------------------------------------------------------
    # Two vectorizers — Council Decision #19 (separate feature spaces)
    # -------------------------------------------------------------------------

    # Filename: character n-grams work for short noisy strings (underscores, dates, etc.)
    tfidf_fn = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        max_features=3000,
        lowercase=True,
        strip_accents="unicode",
    )

    # Content: word n-grams work for English titles/headers/snippets
    # sublinear_tf dampens high-frequency words; min_df=2 removes hapax legomena
    tfidf_ct = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=5000,
        lowercase=True,
        strip_accents="unicode",
        sublinear_tf=True,
        min_df=2,
    )

    X_fn = tfidf_fn.fit_transform(filenames)
    X_ct = tfidf_ct.fit_transform(contents)
    X = hstack([X_fn, X_ct])

    print(f"\nFeature dims: filename={X_fn.shape[1]}, content={X_ct.shape[1]}, combined={X.shape[1]}")

    # -------------------------------------------------------------------------
    # Classifier — balanced weights compensate for training=48% of examples
    # -------------------------------------------------------------------------

    # multi_class removed in sklearn 1.7+ — lbfgs uses multinomial by default
    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        solver="lbfgs",
    )

    # -------------------------------------------------------------------------
    # Cross-validation (train data only — test set stays locked)
    # -------------------------------------------------------------------------

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Combined features
    scores = cross_val_score(clf, X, labels, cv=cv, scoring="accuracy")
    print(f"\nCV accuracy (combined): {scores.mean():.3f} ± {scores.std():.3f}")

    # Filename-only baseline (for uplift measurement)
    scores_fn = cross_val_score(clf, X_fn, labels, cv=cv, scoring="accuracy")
    print(f"CV accuracy (filename): {scores_fn.mean():.3f} ± {scores_fn.std():.3f}")
    print(f"Content uplift:         {(scores.mean() - scores_fn.mean()) * 100:+.1f}pp")

    # Per-class CV report
    cv_preds = cross_val_predict(clf, X, labels, cv=cv)
    report = classification_report(labels, cv_preds)
    print(f"\nPer-class CV report:\n{report}")

    # Save CV report for reference
    cv_report_path = MODELS_DIR / "cv_report.txt"
    cv_report_path.write_text(
        f"CV accuracy (combined):  {scores.mean():.3f} +/- {scores.std():.3f}\n"
        f"CV accuracy (filename):  {scores_fn.mean():.3f} +/- {scores_fn.std():.3f}\n"
        f"Content uplift:          {(scores.mean()-scores_fn.mean())*100:+.1f}pp\n\n"
        f"Per-class CV report:\n{report}",
        encoding="utf-8",
    )

    # -------------------------------------------------------------------------
    # Train final model on full training set
    # -------------------------------------------------------------------------

    clf.fit(X, labels)

    # -------------------------------------------------------------------------
    # Serialize as JSON — no pickle (Council + security)
    # -------------------------------------------------------------------------

    model_data = {
        "filename_vectorizer": {
            "vocabulary": {k: int(v) for k, v in tfidf_fn.vocabulary_.items()},
            "idf": tfidf_fn.idf_.tolist(),
            "params": {"analyzer": "char", "ngram_range": [3, 5], "max_features": 3000},
        },
        "content_vectorizer": {
            "vocabulary": {k: int(v) for k, v in tfidf_ct.vocabulary_.items()},
            "idf": tfidf_ct.idf_.tolist(),
            "params": {"analyzer": "word", "ngram_range": [1, 2], "max_features": 5000},
        },
        "classifier": {
            "coef": clf.coef_.tolist(),
            "intercept": clf.intercept_.tolist(),
            "classes": clf.classes_.tolist(),
        },
        "metadata": {
            "train_size": len(train),
            "n_classes": int(len(clf.classes_)),
            "classes": clf.classes_.tolist(),
            "cv_accuracy_combined": float(scores.mean()),
            "cv_accuracy_filename_only": float(scores_fn.mean()),
            "cv_std": float(scores.std()),
            "content_enriched_pct": float(n_with_content / len(train)),
            "feature_dims": {
                "filename": int(X_fn.shape[1]),
                "content": int(X_ct.shape[1]),
                "combined": int(X.shape[1]),
            },
        },
    }

    model_path = MODELS_DIR / "hybrid_classifier.json"
    model_path.write_text(json.dumps(model_data, indent=2), encoding="utf-8")
    size_kb = model_path.stat().st_size / 1024
    print(f"\nModel saved: {model_path} ({size_kb:.0f} KB)")
    print("Serialization: JSON (no pickle)")

    # Also copy to CKE data dir for packaging. The two copies are byte-identical BY DESIGN, not by
    # accident: models/ is the training artifact (scored by eval_classifier.py against the locked
    # held-out split), while this copy is shipped package data (pyproject.toml `corp.extractor` ->
    # data/*.json) and is what hybrid_loader._DEFAULT_MODEL_PATH loads at runtime -- models/ does not
    # exist inside an installed wheel. Do not "de-dup" these; see models/README.md.
    cke_data = MONOREPO / "src/corp/extractor/data"
    dest = cke_data / "hybrid_classifier.json"
    dest.write_text(json.dumps(model_data, indent=2), encoding="utf-8")
    print(f"Copied to CKE data: {dest}")


if __name__ == "__main__":
    main()
