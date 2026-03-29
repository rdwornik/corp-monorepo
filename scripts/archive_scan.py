"""Archive scan — local metadata only, no API calls."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

if __name__ == "__main__":
    archive = Path(r"C:\Users\1028120\Documents\MyWork\80_Archive")
    output = Path(r"C:\Users\1028120\Documents\MyWork\90_System\archive_scan.json")

    results = []
    errors = []

    for f in sorted(archive.rglob("*")):
        if not f.is_file():
            continue
        try:
            stat = f.stat()
        except Exception as e:
            errors.append(f"Cannot stat: {f} -- {e}")
            continue

        rel = f.relative_to(archive)
        parts = rel.parts

        entry = {
            "path": str(rel).replace("\\", "/"),
            "name": f.name,
            "ext": f.suffix.lower(),
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "folder_l1": parts[0] if parts else "",
            "folder_l2": parts[1] if len(parts) > 1 else "",
        }
        results.append(entry)

        if len(results) % 500 == 0:
            print(f"Scanned {len(results)} files...")

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "files": results,
                "errors": errors,
                "total": len(results),
                "scan_date": datetime.now().isoformat(),
            },
            fh,
            indent=2,
            ensure_ascii=False,
        )

    exts = Counter(r["ext"] for r in results)
    folders = Counter(r["folder_l1"] for r in results)
    total_gb = round(sum(r["size_mb"] for r in results) / 1024, 1)

    print(f"\nArchive scan complete: {len(results)} files, {total_gb} GB")
    print(f"Errors: {len(errors)}")
    print(f"Top extensions: {exts.most_common(10)}")
    print(f"Top L1 folders: {folders.most_common(10)}")
    print(f"Output: {output}")
