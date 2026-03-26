#!/usr/bin/env python3
"""Extraction quality eval against corpus fixtures.

Usage:
    python scripts/eval.py

Metrics:
    1. Classifier accuracy  -- classify_from_filename() vs labelled doc_type (310 files)
    2. Tag taxonomy coverage -- validate_tags() on golden tag vocabulary (200 tags)
    3. Product Jaccard      -- normalize_product_names() stability (64 products)
    4. People filter F1     -- filter_people() precision/recall (444 entries)

Results appended as JSONL to eval/eval_history.jsonl.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MONOREPO = Path(__file__).resolve().parents[1]

# Suppress noisy taxonomy "not in taxonomy" warnings during eval
import logging  # noqa: E402

logging.getLogger("corp_knowledge_extractor.post_process").setLevel(logging.ERROR)
FIXTURES = MONOREPO / "packages/corp-knowledge-extractor/tests/fixtures"
EVAL_DIR = MONOREPO / "eval"

sys.path.insert(0, str(MONOREPO / "packages/corp-knowledge-extractor/src"))
sys.path.insert(0, str(MONOREPO / "packages/corp-os-meta"))

from corp_knowledge_extractor.doc_type_classifier import (  # noqa: E402
    classify_from_filename,
)
from corp_knowledge_extractor.post_process import (  # noqa: E402
    filter_people,
    normalize_product_names,
    validate_tags,
)


def _jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


# ---------------------------------------------------------------------------
# 1. Classifier accuracy
# ---------------------------------------------------------------------------


def eval_classifier() -> dict:
    """classify_from_filename() accuracy against 310 labelled filenames."""
    data = json.loads((FIXTURES / "classifier_training.json").read_text(encoding="utf-8"))
    correct = 0
    errors: Counter = Counter()
    for item in data:
        predicted = classify_from_filename(item["filename"])
        expected = item["doc_type"]
        if predicted == expected:
            correct += 1
        else:
            errors[(str(predicted), expected)] += 1

    total = len(data)
    return {
        "accuracy": correct / total,
        "correct": correct,
        "total": total,
        "top_errors": errors.most_common(10),
    }


# ---------------------------------------------------------------------------
# 2. Tag taxonomy coverage (Jaccard-style: 1.0 validated, 0.5 kept, 0.0 rejected)
# ---------------------------------------------------------------------------


def eval_tag_coverage() -> dict:
    """Taxonomy recognition rate against 200 golden tags from real extractions.

    Fixture is a vocabulary list (not per-doc pairs), so Jaccard is approximated
    as a recognition score per tag: validated=1.0, kept-but-unknown=0.5, rejected=0.0.
    """
    data = json.loads((FIXTURES / "tag_golden_set.json").read_text(encoding="utf-8"))
    scores: list[float] = []
    worst: list[tuple[float, str]] = []

    for item in data:
        tag = item["tag"]
        result = validate_tags([tag])[0]
        if result["reason"] == "validated":
            score = 1.0
        elif result["valid"]:
            score = 0.5  # accepted but not confirmed in taxonomy
        else:
            score = 0.0
        scores.append(score)
        worst.append((score, tag))

    worst.sort()
    return {
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "worst10": worst[:10],
        "n": len(scores),
    }


# ---------------------------------------------------------------------------
# 3. Product normalizer Jaccard
# ---------------------------------------------------------------------------


def eval_product_jaccard() -> dict:
    """normalize_product_names() idempotency: normalize(normalize(x)) == normalize(x).

    Canonical is defined as the first-pass output. Idempotency score = 1.0 means
    the normaliser is stable -- aliases like "WMS" -> "Blue Yonder WMS" score 1.0
    because the second pass leaves the canonical form unchanged. Score < 1.0 means
    the normaliser is remapping its own output, which is a bug.
    """
    data = json.loads((FIXTURES / "product_normalization.json").read_text(encoding="utf-8"))
    scores: list[float] = []
    worst: list[tuple[float, str, list[str]]] = []

    for item in data:
        raw = item["product"]
        canonical = normalize_product_names([raw])
        stable = normalize_product_names(canonical) if canonical else []
        score = _jaccard({p.lower() for p in canonical}, {p.lower() for p in stable})
        scores.append(score)
        worst.append((score, raw, canonical))

    worst.sort()
    return {
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "worst10": worst[:10],
        "n": len(scores),
    }


# ---------------------------------------------------------------------------
# 4. People filter F1
# ---------------------------------------------------------------------------


def eval_people_f1() -> dict:
    """filter_people() precision/recall against 444 labelled entries."""
    data = json.loads((FIXTURES / "people_filter.json").read_text(encoding="utf-8"))
    tp = fp = fn = tn = 0

    for item in data:
        kept, _ = filter_people([item["input"]])
        predicted_keep = len(kept) > 0
        expected_keep = item["expected"] == "keep"

        if expected_keep and predicted_keep:
            tp += 1
        elif not expected_keep and not predicted_keep:
            tn += 1
        elif predicted_keep and not expected_keep:
            fp += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": len(data),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_report(clf: dict, tags: dict, prod: dict, ppl: dict) -> None:
    bar = "=" * 58
    print(f"\n{bar}")
    print("  Extraction Quality Eval")
    print(bar)

    print(f"\n[1] Classifier Accuracy  ({clf['total']} filenames)")
    print(f"    Accuracy : {clf['accuracy']:.1%}  ({clf['correct']}/{clf['total']})")
    print("    Note: filename-only patterns. LLM classifier not evaluated.")
    if clf["top_errors"]:
        print("    Top confusion pairs  (predicted -> expected  count):")
        for (pred, exp), n in clf["top_errors"]:
            print(f"      {pred:>20} -> {exp:<20} {n}x")

    print(f"\n[2] Tag Taxonomy Coverage  ({tags['n']} golden tags)")
    print(f"    Mean : {tags['mean']:.3f}   Median : {tags['median']:.1f}")
    low = [(s, t) for s, t in tags["worst10"] if s < 1.0]
    if low:
        print("    Worst (unrecognised / partial):")
        for score, tag in low:
            label = "unrecognised" if score == 0.0 else "partial"
            print(f"      {score:.1f}  {tag}  [{label}]")
    else:
        print("    All 200 golden tags fully recognised.")

    print(f"\n[3] Product Normalizer Idempotency  ({prod['n']} products)")
    print(f"    Mean : {prod['mean']:.3f}   Median : {prod['median']:.1f}")
    unstable = [(s, r, n) for s, r, n in prod["worst10"] if s < 1.0]
    if unstable:
        print("    Unstable (normalizer remaps its own output -- bug):")
        for score, raw, norm in unstable:
            print(f"      {score:.1f}  {raw!r:35} -> {norm}")
    else:
        print("    All products normalise stably (idempotent).")

    print(f"\n[4] People Filter F1  ({ppl['total']} entries)")
    print(f"    Precision : {ppl['precision']:.3f}   Recall : {ppl['recall']:.3f}   F1 : {ppl['f1']:.3f}")
    print(f"    TP={ppl['tp']}  TN={ppl['tn']}  FP={ppl['fp']}  FN={ppl['fn']}")

    print(f"\n{bar}\n")


def main() -> None:
    clf = eval_classifier()
    tags = eval_tag_coverage()
    prod = eval_product_jaccard()
    ppl = eval_people_f1()

    _print_report(clf, tags, prod, ppl)

    EVAL_DIR.mkdir(exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classifier": {"accuracy": clf["accuracy"], "correct": clf["correct"], "total": clf["total"]},
        "tag_coverage": {"mean": tags["mean"], "median": tags["median"], "n": tags["n"]},
        "product_jaccard": {"mean": prod["mean"], "median": prod["median"], "n": prod["n"]},
        "people_f1": {"precision": ppl["precision"], "recall": ppl["recall"], "f1": ppl["f1"]},
    }
    history = EVAL_DIR / "eval_history.jsonl"
    with open(history, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    print(f"Results appended -> {history.relative_to(MONOREPO)}")


if __name__ == "__main__":
    main()
