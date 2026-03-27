"""
Step 5a: Build CKE pilot manifest — 25 diverse files.

Selects 25 files from the full rebuild batch covering all doc_types.
Writes to .ecosystem/archive/rebuild_pilot_manifest.json.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

FULL_MANIFEST_PATH = Path(
    "C:/Users/1028120/Documents/Scripts/corp-monorepo"
    "/.ecosystem/archive/rebuild_batch_manifest.json"
)
PILOT_MANIFEST_PATH = Path(
    "C:/Users/1028120/Documents/Scripts/corp-monorepo"
    "/.ecosystem/archive/rebuild_pilot_manifest.json"
)
STAGING_ROOT = Path(
    "C:/Users/1028120/Documents/Scripts/corp-monorepo/.ecosystem/rebuild_staging"
)
PILOT_OUTPUT_DIR = str(STAGING_ROOT / "source_library" / "rebuild_pilot")


def main() -> None:
    full = json.loads(FULL_MANIFEST_PATH.read_text(encoding="utf-8"))
    files = full["files"]

    by_type: dict[str, list] = defaultdict(list)
    for f in files:
        by_type[f["doc_type"] or "None"].append(f)

    # Diverse sample: proportional to doc_type distribution, max 25
    targets = {
        "general": 8,
        "meeting": 5,
        "rfp_response": 4,
        "architecture": 4,
        "security": 3,
        "commercial": 1,
    }

    pilot_files = []
    for dt, n in targets.items():
        pilot_files.extend(by_type.get(dt, [])[:n])

    pilot_files = pilot_files[:25]

    pilot_manifest = {
        "schema_version": 1,
        "project": "vault_rebuild_pilot",
        "output_dir": PILOT_OUTPUT_DIR,
        "files": pilot_files,
    }

    PILOT_MANIFEST_PATH.write_text(
        json.dumps(pilot_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Size summary
    total_mb = 0.0
    print(f"Pilot files: {len(pilot_files)}")
    for f in pilot_files:
        p = Path(f["path"])
        size_kb = p.stat().st_size // 1024 if p.exists() else 0
        total_mb += size_kb / 1024
        print(f"  [{f['doc_type'] or 'None':15s}] {f['name'][:50]:50s}  {size_kb}KB")

    print(f"\nTotal input size: {total_mb:.1f} MB")
    print(f"Pilot manifest: {PILOT_MANIFEST_PATH}")
    print(f"Output dir: {PILOT_OUTPUT_DIR}")
    print("\nEstimated cost: ~$0.50–1.00 (Gemini Flash)")
    print("Run: cke process-manifest .ecosystem/archive/rebuild_pilot_manifest.json")


if __name__ == "__main__":
    main()
