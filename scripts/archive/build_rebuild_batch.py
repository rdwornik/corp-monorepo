"""
Step 4: Build CKE manifest for vault rebuild.

Generates a CKE-format manifest (schema_version: 1) for the 257 accessible
source files. Output saved to docs/archive/rebuild_batch_manifest.json.

CKE manifest schema:
{
  "schema_version": 1,
  "project": "vault_rebuild",
  "output_dir": "<rebuild staging dir>",
  "files": [
    {
      "id": "<unique id>",
      "path": "<absolute source path>",
      "doc_type": "<from frontmatter or null>",
      "name": "<filename stem>",
      "client": "<from frontmatter or null>",
      "project": "vault_rebuild"
    }
  ]
}

Output dir structure for corp ingest-extractions:
  <staging_root>/source_library/rebuild/<pkg_id>/extract/<filename>.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MONOREPO_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = _MONOREPO_ROOT / "docs/archive/2026-03-26_VAULT_MANIFEST.json"
OUTPUT_PATH = _MONOREPO_ROOT / "docs/archive/rebuild_batch_manifest.json"

# CKE output dir — temp staging area for re-extracted notes
# Structure: scope/series/pkg/extract/*.md
# ingest-extractions expects: source_library/rebuild/<pkg>/extract/
STAGING_ROOT = _MONOREPO_ROOT / ".ecosystem/rebuild_staging"
OUTPUT_DIR = str(STAGING_ROOT / "source_library" / "rebuild")


def _normalize_source_path(raw: str | None) -> str | None:
    """Normalize path separators and verify the path looks valid."""
    if not raw:
        return None
    # Convert to forward slashes (CKE expects these)
    return raw.replace("\\", "/")


def main() -> None:
    vault_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    accessible = [
        n for n in vault_manifest["notes"] if n["source_accessible"] == "accessible"
    ]

    print(f"Accessible notes to rebuild: {len(accessible)}")

    files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for note in accessible:
        raw_path = note.get("source_path")
        path = _normalize_source_path(raw_path)
        if not path:
            continue

        # Deduplicate by source path
        if path in seen_paths:
            continue
        seen_paths.add(path)

        # Derive a safe unique ID from the filename stem
        filename = note["filename"]
        file_id = Path(filename).stem

        files.append(
            {
                "id": file_id,
                "path": path,
                "doc_type": note.get("doc_type"),
                "name": Path(filename).stem,
                "client": note.get("client"),
                "project": "vault_rebuild",
                "user_context": f"Re-extraction for vault rebuild. Original note: {filename}",
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "project": "vault_rebuild",
        "output_dir": OUTPUT_DIR,
        "files": files,
    }

    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest written to: {OUTPUT_PATH}")
    print(f"Files in manifest: {len(files)}")
    print(f"Output dir (CKE target): {OUTPUT_DIR}")

    # Summarize by doc_type
    from collections import Counter
    by_type = Counter(f["doc_type"] for f in files)
    print("\nBy doc_type:")
    for dt, count in by_type.most_common(10):
        print(f"  {dt or 'None':25s} {count}")


if __name__ == "__main__":
    main()
