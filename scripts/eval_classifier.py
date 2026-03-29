"""One-time evaluation on locked held-out test set.

Run ONCE. Do NOT tune on test results.

Metrics:
- Test accuracy (hybrid vs regex vs filename-only)
- Confidence threshold analysis (where to set LLM fallback boundary)
- Content vs filename-only accuracy breakdown
- High-confidence errors (most dangerous failure mode)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report

MONOREPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MONOREPO / "packages/corp-knowledge-extractor/src"))

from corp.extractor.doc_type_classifier import (  # noqa: E402
    classify_from_filename,
)
from corp.extractor.hybrid_loader import (  # noqa: E402
    load_hybrid_classifier,
    predict_hybrid,
)

MODELS_DIR = MONOREPO / "models"
TEST_PATH = MODELS_DIR / "classifier_test.json"
MODEL_PATH = MODELS_DIR / "hybrid_classifier.json"


def main() -> None:
    test: list[dict] = json.loads(TEST_PATH.read_text(encoding="utf-8"))
    tfidf_fn, tfidf_ct, clf, meta = load_hybrid_classifier(MODEL_PATH)

    filenames = [d.get("filename_text", d["filename"]) for d in test]
    contents = [d.get("content_text", "") for d in test]
    labels = [d["doc_type"] for d in test]

    # -------------------------------------------------------------------------
    # Hybrid predictions
    # -------------------------------------------------------------------------

    predictions: list[str] = []
    confidences: list[float] = []
    for fn, ct in zip(filenames, contents):
        pred, conf = predict_hybrid(tfidf_fn, tfidf_ct, clf, fn, ct)
        predictions.append(pred)
        confidences.append(conf)

    hybrid_acc = accuracy_score(labels, predictions)
    print("=" * 60)
    print("HYBRID CLASSIFIER — TEST SET EVALUATION (ONE TIME)")
    print("=" * 60)
    print(f"\nTest size: {len(test)} examples")
    print(f"Test with content: {sum(1 for d in test if d.get('content_text'))}/{len(test)}")
    print(f"\nCV accuracy was: combined={meta.get('cv_accuracy_combined', '?'):.3f}, "
          f"filename-only={meta.get('cv_accuracy_filename_only', '?'):.3f}")
    print(f"Test accuracy (hybrid): {hybrid_acc:.3f} ({hybrid_acc*100:.1f}%)")
    print(f"\n{classification_report(labels, predictions)}")

    # -------------------------------------------------------------------------
    # Regex baseline
    # -------------------------------------------------------------------------

    regex_preds = [classify_from_filename(fn) or "general" for fn in filenames]
    regex_acc = accuracy_score(labels, regex_preds)
    print(f"Regex baseline accuracy: {regex_acc:.3f} ({regex_acc*100:.1f}%)")
    print(f"Hybrid vs regex:         {(hybrid_acc - regex_acc)*100:+.1f}pp")

    # -------------------------------------------------------------------------
    # Confidence threshold analysis
    # -------------------------------------------------------------------------

    print("\n=== Confidence Threshold Analysis ===")
    print(f"{'Threshold':>9}  {'Classified':>10}  {'Accuracy':>8}  {'LLM fallback':>12}")
    for t in [0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
        above = [(p, lbl) for p, lbl, c in zip(predictions, labels, confidences) if c >= t]
        n_below = len(test) - len(above)
        if above:
            acc = sum(1 for p, lbl in above if p == lbl) / len(above)
            print(f"  {t:.2f}     {len(above):>5}/{len(test)}  {acc*100:>7.1f}%  {n_below:>5} ({n_below/len(test)*100:.0f}%)")

    # -------------------------------------------------------------------------
    # Content vs filename-only breakdown
    # -------------------------------------------------------------------------

    with_content = [(p, lbl, c) for p, lbl, c, d in zip(predictions, labels, confidences, test) if d.get("content_text")]
    without = [(p, lbl, c) for p, lbl, c, d in zip(predictions, labels, confidences, test) if not d.get("content_text")]

    print("\n=== Content Impact ===")
    if with_content:
        acc_with = sum(1 for p, lbl, _ in with_content if p == lbl) / len(with_content)
        avg_conf_with = sum(c for _, _, c in with_content) / len(with_content)
        print(f"With content ({len(with_content)} files):    {acc_with*100:.1f}% acc, {avg_conf_with:.2f} avg confidence")
    if without:
        acc_without = sum(1 for p, lbl, _ in without if p == lbl) / len(without)
        avg_conf_without = sum(c for _, _, c in without) / len(without)
        print(f"Filename-only ({len(without)} files): {acc_without*100:.1f}% acc, {avg_conf_without:.2f} avg confidence")

    # -------------------------------------------------------------------------
    # High-confidence errors (most dangerous — model was certain but wrong)
    # -------------------------------------------------------------------------

    print("\n=== High-Confidence Errors (conf >= 0.7, wrong) ===")
    hce = [(fn, p, lbl, c) for fn, p, lbl, c in zip(filenames, predictions, labels, confidences) if p != lbl and c >= 0.7]
    if hce:
        for fn, p, lbl, c in sorted(hce, key=lambda x: -x[3]):
            print(f"  {fn[:55]:<55}  pred={p:<15} exp={lbl:<15} {c:.2f}")
    else:
        print("  None — no high-confidence errors.")

    # -------------------------------------------------------------------------
    # Save results
    # -------------------------------------------------------------------------

    result = {
        "test_size": len(test),
        "hybrid_accuracy": hybrid_acc,
        "regex_accuracy": regex_acc,
        "uplift_vs_regex": hybrid_acc - regex_acc,
        "cv_accuracy_combined": meta.get("cv_accuracy_combined"),
        "cv_accuracy_filename_only": meta.get("cv_accuracy_filename_only"),
        "n_with_content": sum(1 for d in test if d.get("content_text")),
        "high_confidence_errors": len(hce),
    }
    results_path = MODELS_DIR / "eval_results.json"
    results_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nResults saved: {results_path}")


if __name__ == "__main__":
    main()
