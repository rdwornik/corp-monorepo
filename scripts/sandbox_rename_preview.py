"""Sandbox rename preview — no file modifications.

For each file in the sandbox sample:
  1. light_scan  — extract title/headers/snippet
  2. classify_doc_type_hybrid — filename + content → doc_type
  3. get_type_code / get_client_alias / clean_description — build proposed name

Writes rename_preview.json to .sandbox/cleanup_pilot/.

Note: propose_name() in renamer.py requires a full Classification object.
We call the naming primitives directly — same logic, no Classification needed.
"""
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.WARNING)  # suppress debug noise

SANDBOX = Path(__file__).resolve().parents[1] / ".sandbox/cleanup_pilot"
MAX_NAME_LEN = 120  # matches renamer.py _MAX_NAME_LENGTH


def _build_proposed(
    f: Path,
    doc_type: str | None,
    client: str | None,
) -> str:
    """Build YYYY-MM_TYPE_CLIENT_Description.ext without a Classification object."""
    from corp_by_os.ingest.naming_config import (
        clean_description,
        get_client_alias,
        get_type_code,
    )

    try:
        date_str = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m")
    except OSError:
        date_str = datetime.now().strftime("%Y-%m")

    type_code = get_type_code(doc_type=doc_type, filename=f.name)
    client_code = get_client_alias(client)
    description = clean_description(f.stem)

    stem = f"{date_str}_{type_code}_{client_code}_{description}"
    max_stem = MAX_NAME_LEN - len(f.suffix)
    if len(stem) > max_stem:
        stem = stem[:max_stem].rstrip("_")

    return f"{stem}{f.suffix}"


def main() -> None:
    input_dir = SANDBOX / "input"
    if not input_dir.exists():
        raise SystemExit("Sandbox not found — run create_cleanup_sample.py first")

    from corp_by_os.ingest.light_scan import light_scan
    from corp_knowledge_extractor.doc_type_classifier import classify_doc_type_hybrid

    results: list[dict] = []

    for f in sorted(input_dir.rglob("*")):
        if not f.is_file() or f.name.startswith("."):
            continue

        # Project folder is the immediate child of input/
        try:
            project_folder = f.relative_to(input_dir).parts[0]
        except (ValueError, IndexError):
            project_folder = "root"

        # 1. Light scan
        scan = light_scan(f)

        # 2. Classify — pass content so hybrid TF-IDF can fire
        doc_type, confidence, method = classify_doc_type_hybrid(
            f.name, scan.content_text
        )

        # 3. Client from project folder name (most reliable signal)
        #    get_client_alias handles "Jaguar_Land_Rover_..." → "JLR" internally
        client = project_folder if project_folder != "root" else None

        # 4. Propose name
        proposed = _build_proposed(f, doc_type, client)
        name_changed = proposed != f.name

        results.append(
            {
                "original": f.name,
                "proposed": proposed,
                "changed": name_changed,
                "doc_type": doc_type,
                "confidence": round(confidence, 3),
                "method": method,
                "client_detected": client,
                "scan_title": (scan.title or "")[:60],
                "scan_tier": scan.scan_tier,
                "project_folder": project_folder,
                "extension": f.suffix.lower(),
                "size_kb": round(f.stat().st_size / 1024, 1),
            }
        )

    (SANDBOX / "rename_preview.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    # ── Summary ────────────────────────────────────────────────────────────────
    changed = [r for r in results if r["changed"]]
    unchanged = [r for r in results if not r["changed"]]
    no_type = [r for r in results if not r["doc_type"]]
    low_conf = [r for r in results if r["confidence"] < 0.5 and r["doc_type"]]

    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  Sandbox Rename Preview — {len(results)} files")
    print(sep)
    print(f"\n  Would rename : {len(changed)}/{len(results)}")
    print(f"  Already ok   : {len(unchanged)}/{len(results)}")

    types = Counter(r["doc_type"] or "NONE" for r in results)
    print("\n  Classification:")
    for t, n in types.most_common():
        print(f"    {n:>4}  {t}")

    methods = Counter(r["method"] for r in results)
    print("\n  Method:")
    for m, n in methods.most_common():
        print(f"    {n:>4}  {m}")

    print("\n  Example renames (first 10 changed):")
    for r in changed[:10]:
        print(f"    {r['original'][:50]}")
        print(f"    -> {r['proposed'][:50]}")
        print(f"      type={r['doc_type']}, conf={r['confidence']:.2f}, method={r['method']}")
        print()

    print(f"  WARNING no classification : {len(no_type)}")
    print(f"  WARNING low confidence    : {len(low_conf)}")
    print(f"\n  Output: {SANDBOX / 'rename_preview.json'}")


if __name__ == "__main__":
    main()
