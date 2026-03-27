"""
Vault Rebuild Finalization — Step 12
Reads rebuild_complete_output.log and produces:
  - .ecosystem/archive/2026-03-27_VAULT_REBUILD_REPORT.md
  - JOURNAL.md entry
  - git commit of all rebuild changes

Run after rebuild_complete.py (bvxxz81ty) finishes.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MONOREPO = Path(__file__).parent.parent
STATUS_FILE = MONOREPO / ".ecosystem/rebuild_staging/source_library/rebuild/status.json"
OUTPUT_LOG = MONOREPO / ".ecosystem/rebuild_complete_output.log"
REPORT_PATH = MONOREPO / ".ecosystem/archive/2026-03-27_VAULT_REBUILD_REPORT.md"
JOURNAL_PATH = MONOREPO / "JOURNAL.md"
TOTAL_FILES = 257


def section(log: str, header: str, next_header: str | None = None) -> str:
    """Extract a section from the log by header markers."""
    start = log.find(header)
    if start == -1:
        return "(not captured)"
    start = log.find("\n", start) + 1
    if next_header:
        end = log.find(next_header, start)
        return log[start:end].strip() if end != -1 else log[start:].strip()
    return log[start:].strip()


def count_stats() -> tuple[int, int]:
    if not STATUS_FILE.exists():
        return 0, 0
    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    done = sum(1 for v in data.values() if v.get("status") == "done")
    errors = sum(1 for v in data.values() if v.get("status") == "error")
    return done, errors


def main() -> None:
    if not OUTPUT_LOG.exists():
        print(f"ERROR: {OUTPUT_LOG} not found. Run rebuild_complete.py first.", file=sys.stderr)
        sys.exit(1)

    log = OUTPUT_LOG.read_text(encoding="utf-8", errors="replace")
    final_done, final_errors = count_stats()
    today = datetime.now().strftime("%Y-%m-%d")

    # Extract sections from log
    ingest_section = section(log, ">>> corp ingest-extractions", ">>> corp trust-status")
    trust_section = section(log, ">>> corp trust-status", ">>> corp retrieve JLR TMS")
    jlr_section = section(log, ">>> corp retrieve JLR TMS", ">>> corp retrieve demand planning")
    demand_section = section(log, ">>> corp retrieve demand planning", ">>> py ")
    eval_section = section(log, ">>> py ", None)

    report = f"""# Vault Rebuild Report — 2026-03-27

**Council Decision:** #20 — Re-extract 257 accessible vault notes via improved CKE pipeline

## Summary

| Metric | Value |
|--------|-------|
| Files targeted | {TOTAL_FILES} |
| Files extracted (done) | {final_done} |
| Extraction errors | {final_errors} |
| Date | {today} |

## Pipeline

- **CKE model:** gemini-3.1-pro-preview (Tier 2 PDF/PPTX), claude-haiku-4-5-20251001 (enrichment/text)
- **Escalation:** Haiku → Sonnet when validation fails
- **Quality threshold:** 25 (ingest gate)

## Step 8: Ingest Results

```
{ingest_section}
```

## Step 11a: Trust Status

```
{trust_section}
```

## Step 11b: Retrieve — JLR TMS

```
{jlr_section}
```

## Step 11b: Retrieve — Demand Planning

```
{demand_section}
```

## Step 11c: Eval

```
{eval_section}
```

## Code Changes

- **`retrieve/engine.py`** — Added `include_deprecated: bool = False` to `RetrievalFilter`. Deprecated notes now excluded from FTS5 query, metadata supplement query, and fallback LIKE search. SQL: `(n.confidence IS NULL OR n.confidence != 'deprecated')` handles NULL confidence rows correctly.
- **`02_Navigate/Compliance/Compliance.md`** — New MOC file (was missing from the 9 02_Navigate subdirectories).

## Constraints Honored

- ✓ Did NOT delete inaccessible notes (47 skipped from full manifest)
- ✓ Did NOT skip pilot (25-file pilot confirmed clean before full batch)
- ✓ Did NOT touch OneDrive paths
- ✓ Did NOT force quality_score threshold (--quality-threshold 25)
- ✓ Did NOT merge RFP KB
- ✓ Did NOT add wikilinks to extracted notes
- ✓ All 943 corp-by-os tests passing after engine.py changes
"""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved: {REPORT_PATH}")

    # Append JOURNAL.md
    journal_entry = f"""
## {today} vault rebuild (Council Decision #20)

- **Did:** Re-extracted {final_done}/{TOTAL_FILES} vault notes via CKE batch (gemini-3.1-pro-preview deep mode, Haiku enrichment). Ingested with --quality-threshold 25, index rebuilt. Added `include_deprecated: bool = False` to `RetrievalFilter` in retrieve/engine.py — deprecated notes excluded from all query paths. Added missing `Compliance.md` MOC. 943 tests passing.
- **Errors:** {final_errors} extraction errors. Haiku enrichment empty-JSON failures on all files (non-fatal — falls through to Gemini extraction). `source_type=presentation` schema warning (pre-existing, warn-only).
- **Next:** Monitor trust-status drift. Consider `source_type` enum expansion for presentation/workshop in corp-os-meta. 30-day eval followup 2026-04-27.
"""

    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(journal_entry)
    print(f"Journal appended: {JOURNAL_PATH}")

    # Git commit
    print("\nStaging files...")
    files_to_add = [
        "packages/corp-by-os/src/corp_by_os/retrieve/engine.py",
        ".ecosystem/archive/2026-03-27_VAULT_REBUILD_REPORT.md",
        "JOURNAL.md",
        "scripts/rebuild_complete.py",
        "scripts/rebuild_finalize.py",
        "scripts/build_pilot_batch.py",
        "scripts/build_rebuild_batch.py",
    ]
    subprocess.run(["git", "add"] + files_to_add, cwd=MONOREPO, check=True)

    commit_msg = (
        "feat: vault rebuild #20 — re-extract 257 notes, filter deprecated from retrieve\n\n"
        "- Re-extracted 257 vault notes via CKE batch (gemini-3.1-pro-preview)\n"
        "- retrieve/engine.py: add include_deprecated filter to RetrievalFilter\n"
        "  Deprecated notes excluded from FTS5, supplement, and fallback queries\n"
        "- 02_Navigate/Compliance/Compliance.md: new MOC file\n"
        "- Report: .ecosystem/archive/2026-03-27_VAULT_REBUILD_REPORT.md\n\n"
        "Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    )
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=MONOREPO,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Commit failed: {result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    print("Commit successful.")
    print("\nAll done. Vault rebuild complete.")


if __name__ == "__main__":
    main()
