#!/usr/bin/env python3
"""Update MASTER_HANDOFF.md with latest ecosystem stats.

Run at end of each session:
    python scripts/update_handoff.py

Updates:
  - Last updated timestamp
  - Eval scores from eval/eval_history.jsonl (latest entry)
  - Vault note count from index.db
  - Test count from JOURNAL.md (latest "N passed" mention)
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HANDOFF_PATH = REPO_ROOT / ".ecosystem" / "MASTER_HANDOFF.md"
EVAL_HISTORY = REPO_ROOT / "eval" / "eval_history.jsonl"
JOURNAL_PATH = REPO_ROOT / "JOURNAL.md"
INDEX_DB = Path(os.environ.get("LOCALAPPDATA", "")) / "corp-by-os" / "index.db"


def get_latest_eval() -> dict:
    if not EVAL_HISTORY.exists():
        return {}
    last_line = ""
    with EVAL_HISTORY.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if not last_line:
        return {}
    return json.loads(last_line)


def get_vault_note_count() -> int | None:
    if not INDEX_DB.exists():
        return None
    try:
        conn = sqlite3.connect(INDEX_DB)
        cur = conn.execute("SELECT COUNT(*) FROM notes")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None


def get_test_count_from_journal() -> str | None:
    """Return latest 'N passed' count from JOURNAL.md (first match = most recent entry)."""
    if not JOURNAL_PATH.exists():
        return None
    text = JOURNAL_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"(\d[\d,]*)\s+passed", text)
    if not matches:
        return None
    return matches[0].replace(",", "")


def update_table_row(content: str, label: str, value: str) -> str:
    """Replace the value column in a markdown table row matching `label`."""
    pattern = r"(\|\s*" + re.escape(label) + r"\s*\|\s*)([^|\n]+?)(\s*\|)"
    replacement = r"\g<1>" + value + r" \3"
    new_content, n = re.subn(pattern, replacement, content)
    if n == 0:
        print(f"  WARN: table row '{label}' not found — skipped")
    return new_content


def update_last_updated(content: str, ts: str) -> str:
    return re.sub(r"(Last updated:\s*)\S+", r"\g<1>" + ts, content)


def main() -> None:
    if not HANDOFF_PATH.exists():
        print(f"ERROR: {HANDOFF_PATH} not found.")
        print("Create .ecosystem/MASTER_HANDOFF.md first.")
        raise SystemExit(1)

    content = HANDOFF_PATH.read_text(encoding="utf-8")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Timestamp ---
    content = update_last_updated(content, ts)
    print(f"  Timestamp: {ts}")

    # --- Eval scores ---
    eval_data = get_latest_eval()
    if eval_data:
        hybrid = eval_data.get("hybrid_classifier", {})
        if acc := hybrid.get("overall_classified_accuracy"):
            content = update_table_row(content, "Hybrid classifier accuracy", f"{acc:.1%}")
            print(f"  Hybrid accuracy: {acc:.1%}")

        tag = eval_data.get("tag_coverage", {})
        if mean := tag.get("mean"):
            content = update_table_row(content, "Tag coverage (mean)", f"{mean:.1%}")
            print(f"  Tag coverage: {mean:.1%}")

        people = eval_data.get("people_f1", {})
        if f1 := people.get("f1"):
            content = update_table_row(content, "People NER F1", f"{f1:.1%}")
            print(f"  People F1: {f1:.1%}")

        eval_ts = (eval_data.get("timestamp") or "")[:10]
        if eval_ts:
            content = update_table_row(content, "Eval timestamp", eval_ts)
            print(f"  Eval timestamp: {eval_ts}")
    else:
        print("  Eval: no data (eval_history.jsonl empty or missing)")

    # --- Vault note count ---
    note_count = get_vault_note_count()
    if note_count is not None:
        content = update_table_row(content, "Vault notes (indexed)", str(note_count))
        print(f"  Vault notes: {note_count}")
    else:
        print(f"  Vault notes: n/a (index.db not found at {INDEX_DB})")

    # --- Test count ---
    test_count = get_test_count_from_journal()
    if test_count:
        content = update_table_row(content, "Tests passing", test_count)
        print(f"  Tests passing: {test_count}")
    else:
        print("  Tests passing: n/a (no 'N passed' found in JOURNAL.md)")

    HANDOFF_PATH.write_text(content, encoding="utf-8")
    print(f"\nUpdated: {HANDOFF_PATH}")


if __name__ == "__main__":
    main()
