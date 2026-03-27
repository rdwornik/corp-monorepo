"""Sandbox near-duplicate detection — no DB, in-memory only.

Uses corp_by_os.ingest.dedup.compute_minhash (word 3-grams, 128 perms)
to find near-duplicate pairs in the sandbox sample.

Writes dedup_preview.json to .sandbox/cleanup_pilot/.
"""
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

SANDBOX = Path(r"C:\Users\1028120\Documents\Scripts\corp-monorepo\.sandbox\cleanup_pilot")
THRESHOLD = 0.5  # lower than prod (0.6) to surface more candidates for review


def main() -> None:
    input_dir = SANDBOX / "input"
    if not input_dir.exists():
        raise SystemExit("Sandbox not found — run create_cleanup_sample.py first")

    from corp_by_os.ingest.dedup import compute_minhash
    from corp_by_os.ingest.light_scan import light_scan

    # Build content index
    index: dict[str, tuple[str, object]] = {}  # path → (filename, minhash)
    skipped = 0

    for f in sorted(input_dir.rglob("*")):
        if not f.is_file() or f.name.startswith("."):
            continue
        scan = light_scan(f)
        # Prefer content_text; fall back to filename so every file is indexed
        text = scan.content_text or scan.filename
        if not text.strip():
            skipped += 1
            continue
        index[str(f)] = (f.name, compute_minhash(text))

    print(f"Indexed: {len(index)} files  |  Skipped (no content): {skipped}")

    # Pairwise Jaccard — O(n²) is fine for n≈120
    paths = list(index.keys())
    pairs: list[dict] = []

    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            pa, pb = paths[i], paths[j]
            name_a, mh_a = index[pa]
            name_b, mh_b = index[pb]
            sim = mh_a.jaccard(mh_b)
            if sim >= THRESHOLD:
                proj_a = Path(pa).parent.name
                proj_b = Path(pb).parent.name
                pairs.append(
                    {
                        "file_a": name_a,
                        "file_b": name_b,
                        "similarity": round(sim, 3),
                        "same_project": proj_a == proj_b,
                        "project_a": proj_a,
                        "project_b": proj_b,
                    }
                )

    pairs.sort(key=lambda x: -x["similarity"])
    (SANDBOX / "dedup_preview.json").write_text(
        json.dumps(pairs, indent=2), encoding="utf-8"
    )

    # Summary
    high = [p for p in pairs if p["similarity"] > 0.8]
    mid = [p for p in pairs if 0.6 < p["similarity"] <= 0.8]
    low = [p for p in pairs if THRESHOLD <= p["similarity"] <= 0.6]

    print(f"\nNear-duplicate pairs (similarity >= {THRESHOLD}): {len(pairs)}")
    print(f"  HIGH  (>0.80): {len(high)}")
    print(f"  MED   (>0.60): {len(mid)}")
    print(f"  LOW   (>0.50): {len(low)}")

    print("\nTop 15 pairs:")
    for p in pairs[:15]:
        flag = "HIGH" if p["similarity"] > 0.8 else "MED " if p["similarity"] > 0.6 else "LOW "
        xp = "SAME-PROJ" if p["same_project"] else "DIFF-PROJ"
        print(f"  [{flag}] {p['similarity']:.3f}  {xp}")
        print(f"         {p['file_a'][:55]}")
        print(f"         {p['file_b'][:55]}")

    print(f"\n  Output: {SANDBOX / 'dedup_preview.json'}")


if __name__ == "__main__":
    main()
