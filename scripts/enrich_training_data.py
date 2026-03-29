"""Retroactively enrich classifier training examples with content features.

Reads ``classifier_training.json`` (310 labelled filenames), attempts to
locate each file on disk, runs ``light_scan`` if found, and writes
``classifier_training_enriched.json`` alongside the original.

Strategies (in order):
1. Locate file on disk under SEARCH_ROOT — full light_scan
2. Filename-only ScanResult — zero content features but struct intact

Output adds a ``scan_result`` dict (from ``ScanResult.to_feature_dict()``)
and ``scan_strategy`` (``"full"`` | ``"filename_only"``) to each entry.
"""

import json
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent.parent  # corp-monorepo/
FIXTURE_PATH = (
    REPO_ROOT
    / "packages/corp-knowledge-extractor/tests/fixtures/classifier_training.json"
)
OUTPUT_PATH = FIXTURE_PATH.parent / "classifier_training_enriched.json"

# Candidate roots to search for actual files (safe paths only)
SEARCH_ROOTS: list[Path] = [
    Path(os.environ.get("MYWORK_ROOT", r"C:\Users\1028120\Documents\MyWork")),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_file(filename: str) -> Path | None:
    """Search SEARCH_ROOTS for a file with the given name."""
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for match in root.rglob(filename):
            # Safety: never touch OneDrive - Blue Yonder
            if "OneDrive - Blue Yonder" in str(match):
                continue
            return match
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Import here so the script works from any CWD
    sys.path.insert(
        0,
        str(REPO_ROOT / "packages/corp-by-os/src"),
    )
    from corp.ingest.light_scan import ScanResult, light_scan  # noqa: PLC0415

    with FIXTURE_PATH.open(encoding="utf-8") as f:
        examples: list[dict] = json.load(f)

    enriched: list[dict] = []
    found_count = 0
    filename_only_count = 0

    for ex in examples:
        filename = ex["filename"]
        file_path = _find_file(filename)

        if file_path is not None:
            result = light_scan(file_path)
            strategy = "full"
            found_count += 1
            if result.errors:
                log.warning("scan errors for %s: %s", filename, result.errors)
        else:
            # Filename-only fallback — ScanResult with no content
            result = ScanResult(
                filename=filename,
                extension=ex.get("extension", Path(filename).suffix),
                scan_tier="filename_only",
            )
            strategy = "filename_only"
            filename_only_count += 1

        enriched.append(
            {
                **ex,
                "scan_strategy": strategy,
                "scan_result": result.to_feature_dict(),
                "content_text": result.content_text,
                "filename_text": result.filename_text,
            }
        )

    total = len(examples)
    log.info(
        "Enriched %d/%d with real scan (%d%%), %d filename-only",
        found_count,
        total,
        round(found_count / total * 100),
        filename_only_count,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    log.info("Written to: %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
