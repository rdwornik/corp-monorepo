"""Create a locked stratified train/test split from enriched classifier data.

Run once. Never re-run after training begins — test set must stay unseen.

Output:
    models/classifier_train.json  (80%)
    models/classifier_test.json   (20%)
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from sklearn.model_selection import train_test_split

MONOREPO = Path(__file__).resolve().parents[1]
FIXTURE = MONOREPO / "packages/corp-knowledge-extractor/tests/fixtures/classifier_training_enriched.json"
MODELS_DIR = MONOREPO / "models"


def main() -> None:
    data: list[dict] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    labels = [d["doc_type"] for d in data]

    train, test = train_test_split(data, test_size=0.2, random_state=42, stratify=labels)

    MODELS_DIR.mkdir(exist_ok=True)
    (MODELS_DIR / "classifier_train.json").write_text(
        json.dumps(train, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (MODELS_DIR / "classifier_test.json").write_text(
        json.dumps(test, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Train: {len(train)}, Test: {len(test)}")

    train_content = sum(1 for d in train if d.get("content_text"))
    test_content = sum(1 for d in test if d.get("content_text"))
    print(f"\nTrain with content: {train_content}/{len(train)} ({train_content/len(train)*100:.0f}%)")
    print(f"Test  with content: {test_content}/{len(test)} ({test_content/len(test)*100:.0f}%)")

    print("\nClass distribution (train):")
    for cls, n in Counter(d["doc_type"] for d in train).most_common():
        bar = "#" * n
        print(f"  {n:>4}  {cls:<20} {bar}")

    print(f"\nSplit written to {MODELS_DIR}/")
    print("IMPORTANT: Do NOT re-run after training — test set must stay unseen.")


if __name__ == "__main__":
    main()
