"""
Step 3: Move fragment-quality notes to _quarantine/.

Reads vault manifest, moves all quality=fragment notes from 01_Knowledge/
to _quarantine/. Updates frontmatter with quarantine_reason.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

_MONOREPO_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = _MONOREPO_ROOT / ".ecosystem/archive/2026-03-26_VAULT_MANIFEST.json"
VAULT_ROOT = Path(os.environ["USERPROFILE"]) / "Documents" / "ObsidianVault"
KNOWLEDGE_DIR = VAULT_ROOT / "01_Knowledge"
QUARANTINE_DIR = VAULT_ROOT / "_quarantine"


def _update_frontmatter_field(text: str, key: str, value: str) -> str:
    fm_pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
    match = fm_pattern.match(text)
    if not match:
        return f"---\n{key}: {value}\n---\n{text}"
    fm_text = match.group(1)
    field_pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if field_pattern.search(fm_text):
        fm_text = field_pattern.sub(f"{key}: {value}", fm_text)
    else:
        fm_text = fm_text.rstrip("\n") + f"\n{key}: {value}"
    return text[: match.start()] + f"---\n{fm_text}\n---" + text[match.end() :]


def main() -> None:
    QUARANTINE_DIR.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fragments = [n for n in manifest["notes"] if n.get("quality") == "fragment"]

    print(f"Fragment notes to quarantine: {len(fragments)}")
    moved = 0
    skipped = 0

    for note in fragments:
        src = KNOWLEDGE_DIR / note["filename"]
        dst = QUARANTINE_DIR / note["filename"]

        if not src.exists():
            print(f"  SKIP (already gone): {note['filename']}", file=sys.stderr)
            skipped += 1
            continue

        if dst.exists():
            print(f"  SKIP (already in quarantine): {note['filename']}", file=sys.stderr)
            skipped += 1
            continue

        # Update frontmatter before moving
        text = src.read_text(encoding="utf-8")
        text = _update_frontmatter_field(text, "quarantine_reason", "quality_fragment")
        src.write_text(text, encoding="utf-8")

        shutil.move(str(src), str(dst))
        moved += 1
        print(f"  Moved: {note['filename']}")

    print(f"\nMoved: {moved}  |  Skipped: {skipped}")


if __name__ == "__main__":
    main()
