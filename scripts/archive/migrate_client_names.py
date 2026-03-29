"""Migrate vault note client fields to canonical names.

Reads every .md file in the Obsidian vault, checks the `client:` frontmatter
field, and normalises it via CKE's client_aliases.yaml.  Supports dry-run mode
(default) and apply mode (--apply).

Usage:
    python scripts/migrate_client_names.py            # dry-run: show what would change
    python scripts/migrate_client_names.py --apply    # patch files in-place
    python scripts/migrate_client_names.py --apply --rebuild-index  # patch + rebuild index
"""

from __future__ import annotations

import argparse
import io
import logging
import subprocess
import sys
from pathlib import Path

import yaml

# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CKE_ALIASES_PATH = (
    REPO_ROOT
    / "packages"
    / "corp-knowledge-extractor"
    / "src"
    / "corp.extractor"
    / "data"
    / "client_aliases.yaml"
)
FRONTMATTER_SEP = "---"


# ---------------------------------------------------------------------------
# Alias loading
# ---------------------------------------------------------------------------


def _load_aliases() -> dict[str, str]:
    """Return alias→canonical mapping from CKE client_aliases.yaml."""
    with open(CKE_ALIASES_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("aliases", {})


def _normalize(client: str, aliases: dict[str, str]) -> str:
    """Return canonical client name, or original if not in alias map."""
    return aliases.get(client, client)


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------


def _split_frontmatter(content: str) -> tuple[str, str, str]:
    """Split a note into (pre, frontmatter_block, body).

    If no YAML frontmatter found, returns ('', '', content).
    pre always equals '' — kept for symmetry with _join_frontmatter.
    """
    if not content.startswith(FRONTMATTER_SEP + "\n"):
        return "", "", content
    end = content.find("\n" + FRONTMATTER_SEP, len(FRONTMATTER_SEP))
    if end == -1:
        return "", "", content
    fm_block = content[len(FRONTMATTER_SEP) + 1 : end]
    body = content[end + len(FRONTMATTER_SEP) + 1 :]
    return "", fm_block, body


def _parse_and_patch(content: str, aliases: dict[str, str]) -> tuple[str | None, str, str]:
    """Parse frontmatter client field, normalise, return (old, new, patched_content).

    Returns (None, '', original_content) if no change needed.
    """
    _, fm_block, body = _split_frontmatter(content)
    if not fm_block:
        return None, "", content

    try:
        fm = yaml.safe_load(fm_block)
    except yaml.YAMLError:
        return None, "", content

    if not isinstance(fm, dict):
        return None, "", content

    original_client = fm.get("client")
    if not original_client or not isinstance(original_client, str):
        return None, "", content

    normalised = _normalize(original_client, aliases)
    if normalised == original_client:
        return None, "", content

    # Patch only the client line — safer than full YAML round-trip (preserves
    # field order, comments, and avoids yaml.dump altering other values)
    new_line = f"client: {normalised}"

    # Handle quoted variants yaml.safe_load strips quotes on load
    fm_patched = None
    for quote in ("", "'", '"'):
        candidate = f"client: {quote}{original_client}{quote}"
        if candidate in fm_block:
            fm_patched = fm_block.replace(candidate, new_line, 1)
            break

    if fm_patched is None:
        # Fallback: full YAML round-trip (may reorder fields)
        log.warning("Could not find exact client line for '%s', using yaml round-trip", original_client)
        fm["client"] = normalised
        fm_patched = yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()
        patched = f"{FRONTMATTER_SEP}\n{fm_patched}\n{FRONTMATTER_SEP}\n{body}"
        return original_client, normalised, patched

    patched = f"{FRONTMATTER_SEP}\n{fm_patched}\n{FRONTMATTER_SEP}\n{body}"
    return original_client, normalised, patched


# ---------------------------------------------------------------------------
# Vault discovery
# ---------------------------------------------------------------------------


def _find_vault_notes(vault_path: Path) -> list[Path]:
    return sorted(vault_path.rglob("*.md"))


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


def run_migration(vault_path: Path, dry_run: bool) -> dict[str, list[tuple[Path, str, str]]]:
    """Scan vault notes, return changes dict keyed by canonical name.

    changes[canonical] = [(path, old_client, canonical), ...]
    """
    aliases = _load_aliases()
    notes = _find_vault_notes(vault_path)
    log.info("Scanning %d notes in %s", len(notes), vault_path)

    changes: dict[str, list[tuple[Path, str, str]]] = {}
    errors: list[tuple[Path, str]] = []

    for note in notes:
        try:
            content = note.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append((note, str(exc)))
            continue

        old_client, new_client, patched = _parse_and_patch(content, aliases)
        if old_client is None:
            continue

        changes.setdefault(new_client, []).append((note, old_client, new_client))

        if not dry_run:
            try:
                note.write_text(patched, encoding="utf-8")
            except Exception as exc:
                errors.append((note, str(exc)))

    if errors:
        log.warning("%d files could not be processed:", len(errors))
        for path, err in errors:
            log.warning("  %s — %s", path, err)

    return changes


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_report(changes: dict[str, list[tuple[Path, str, str]]], dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "APPLIED"
    total = sum(len(v) for v in changes.values())

    print(f"\n[{mode}] Client name migration — {total} notes to update\n")
    if not changes:
        print("  Nothing to do.")
        return

    for canonical, entries in sorted(changes.items()):
        old_names = sorted({old for _, old, _ in entries})
        print(f"  {canonical} ({len(entries)} notes) — from: {', '.join(old_names)}")
        for path, old, _ in sorted(entries):
            print(f"    {path.name}  [{old}]")

    print()


# ---------------------------------------------------------------------------
# Index rebuild
# ---------------------------------------------------------------------------


def _rebuild_index() -> None:
    log.info("Rebuilding corp-by-os index…")
    result = subprocess.run(
        ["corp", "index", "rebuild"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        log.info("Index rebuilt successfully.")
        if result.stdout:
            print(result.stdout)
    else:
        log.error("Index rebuild failed (exit %d):", result.returncode)
        if result.stderr:
            print(result.stderr, file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _get_vault_path() -> Path:
    """Resolve vault path via corp-by-os AppConfig."""
    try:
        from corp.config import get_config

        return get_config().vault_path
    except Exception as exc:
        log.error("Could not load corp-by-os config: %s", exc)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate vault client field to canonical names.")
    parser.add_argument("--apply", action="store_true", help="Patch files in-place (default: dry-run)")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild corp-by-os index after apply")
    parser.add_argument("--vault", type=Path, help="Override vault path")
    args = parser.parse_args()

    dry_run = not args.apply
    vault_path = args.vault or _get_vault_path()

    if not vault_path.exists():
        log.error("Vault path does not exist: %s", vault_path)
        sys.exit(1)

    changes = run_migration(vault_path, dry_run=dry_run)
    _print_report(changes, dry_run=dry_run)

    if not dry_run and args.rebuild_index:
        _rebuild_index()

    if dry_run and changes:
        total = sum(len(v) for v in changes.values())
        print(f"Re-run with --apply to patch {total} notes.")


if __name__ == "__main__":
    main()
