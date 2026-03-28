"""
Step 2: Tag inaccessible/missing source notes as deprecated.

Reads the vault manifest and updates frontmatter in-place for:
- source_accessible == "inaccessible" → trust_level: deprecated, rebuild_status: source_inaccessible
- source_accessible == "missing"      → trust_level: deprecated, rebuild_status: source_missing

Does NOT delete any notes.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_MONOREPO_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = _MONOREPO_ROOT / ".ecosystem/archive/2026-03-26_VAULT_MANIFEST.json"
VAULT_ROOT = Path(os.environ["USERPROFILE"]) / "Documents" / "ObsidianVault" / "01_Knowledge"


def _update_frontmatter(text: str, updates: dict[str, str]) -> str:
    """Update YAML frontmatter fields in a markdown file's text."""
    fm_pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
    match = fm_pattern.match(text)
    if not match:
        # No frontmatter — prepend minimal block
        fm_lines = "\n".join(f"{k}: {v}" for k, v in updates.items())
        return f"---\n{fm_lines}\n---\n{text}"

    fm_text = match.group(1)
    for key, value in updates.items():
        # Replace existing field or append
        field_pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
        if field_pattern.search(fm_text):
            fm_text = field_pattern.sub(f"{key}: {value}", fm_text)
        else:
            fm_text = fm_text.rstrip("\n") + f"\n{key}: {value}"

    return text[: match.start()] + f"---\n{fm_text}\n---" + text[match.end() :]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    notes = manifest["notes"]  # root key is "notes"

    to_tag = [
        n
        for n in notes
        if n["source_accessible"] in ("inaccessible", "missing")
    ]

    print(f"Notes to tag as deprecated: {len(to_tag)}")
    tagged = 0
    skipped = 0

    for note in to_tag:
        note_path = VAULT_ROOT / note["filename"]
        if not note_path.exists():
            print(f"  SKIP (not found in vault): {note['filename']}", file=sys.stderr)
            skipped += 1
            continue

        rebuild_status = (
            "source_inaccessible"
            if note["source_accessible"] == "inaccessible"
            else "source_missing"
        )

        text = note_path.read_text(encoding="utf-8")
        updated = _update_frontmatter(
            text,
            {
                "trust_level": "deprecated",
                "rebuild_status": rebuild_status,
            },
        )

        if updated == text:
            skipped += 1
            continue

        note_path.write_text(updated, encoding="utf-8")
        tagged += 1

    print(f"Tagged: {tagged}  |  Skipped: {skipped}")


if __name__ == "__main__":
    main()
