"""Vault restructure — Council Decision #4: flat semantic folders.

Moves notes from numbered folders to semantic folders.
Logs every action. Skips conflicts. Does NOT delete old folders.

Usage:
    py scripts/vault_restructure.py              # dry run
    py scripts/vault_restructure.py --execute    # real migration
"""

from __future__ import annotations

import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

VAULT = Path(r"C:\Users\1028120\Documents\ObsidianVault")

# Files to skip when flattening CKE output into knowledge/
SKIP_NAMES = {"synthesis.md", "index.md", "_meta.yaml"}
SKIP_SUFFIXES = {"_transcript.md"}

# New folder structure
NEW_FOLDERS = ["knowledge", "projects", "guides", "dashboards", "templates", "system"]

# Migration tombstone text
TOMBSTONE = """# This folder has been migrated

Notes moved to `/{new_folder}/` on 2026-03-21.
This folder will be deleted after 2026-04-21.
"""


def should_skip_file(path: Path) -> bool:
    """Check if a file should be skipped (CKE artifacts, non-.md)."""
    if path.suffix != ".md":
        return True
    if path.name in SKIP_NAMES:
        return True
    for suffix in SKIP_SUFFIXES:
        if path.name.endswith(suffix):
            return True
    return False


def collect_moves(vault: Path) -> list[tuple[Path, Path, str]]:
    """Plan all moves. Returns list of (source, destination, category)."""
    moves: list[tuple[Path, Path, str]] = []
    dest_names: Counter[str] = Counter()

    # Helper to track name collisions for knowledge/ flattening
    knowledge_names: dict[str, Path] = {}  # name -> first source

    def add_knowledge(src: Path, tag: str) -> None:
        name = src.name
        if name in knowledge_names:
            # Collision — rename this one
            stem = src.stem
            new_name = f"{stem}_{tag}{src.suffix}"
            dest = vault / "knowledge" / new_name
            moves.append((src, dest, f"knowledge (renamed from {name})"))
        else:
            knowledge_names[name] = src
            dest = vault / "knowledge" / name
            moves.append((src, dest, "knowledge"))

    # 02_sources -> knowledge/ (flatten)
    sources_dir = vault / "02_sources"
    if sources_dir.exists():
        for md in sorted(sources_dir.rglob("*.md")):
            if should_skip_file(md):
                continue
            # Tag with parent folder for collision resolution
            rel = md.relative_to(sources_dir)
            tag = rel.parts[0] if len(rel.parts) > 1 else "sources"
            add_knowledge(md, tag)

    # 04_evergreen -> knowledge/ (flatten)
    evergreen_dir = vault / "04_evergreen"
    if evergreen_dir.exists():
        for md in sorted(evergreen_dir.rglob("*.md")):
            if should_skip_file(md):
                continue
            rel = md.relative_to(evergreen_dir)
            tag = rel.parts[0] if len(rel.parts) > 1 else "evergreen"
            add_knowledge(md, tag)

    # 70_Extracts -> knowledge/ (flatten, skip CKE artifacts)
    extracts_dir = vault / "70_Extracts"
    if extracts_dir.exists():
        for md in sorted(extracts_dir.rglob("*.md")):
            if should_skip_file(md):
                continue
            add_knowledge(md, "extracts")

    # 99_CKE -> knowledge/ (flatten, skip CKE artifacts)
    cke_dir = vault / "99_CKE"
    if cke_dir.exists():
        for md in sorted(cke_dir.rglob("*.md")):
            if should_skip_file(md):
                continue
            add_knowledge(md, "cke")

    # Root-level .md -> knowledge/
    for md in sorted(vault.glob("*.md")):
        if md.name.startswith("."):
            continue
        add_knowledge(md, "root")

    # 01_projects -> projects/ (keep client subfolders)
    projects_dir = vault / "01_projects"
    if projects_dir.exists():
        for md in sorted(projects_dir.rglob("*.md")):
            rel = md.relative_to(projects_dir)
            dest = vault / "projects" / rel
            moves.append((md, dest, "projects"))

        # Also move non-.md files (yaml, etc.) in projects
        for f in sorted(projects_dir.rglob("*")):
            if f.is_file() and f.suffix != ".md":
                rel = f.relative_to(projects_dir)
                dest = vault / "projects" / rel
                moves.append((f, dest, "projects (non-md)"))

    # 03_playbooks -> guides/ (flatten)
    playbooks_dir = vault / "03_playbooks"
    if playbooks_dir.exists():
        for md in sorted(playbooks_dir.rglob("*.md")):
            dest = vault / "guides" / md.name
            moves.append((md, dest, "guides"))

    # 00_dashboards -> dashboards/ (flatten)
    dashboards_dir = vault / "00_dashboards"
    if dashboards_dir.exists():
        for md in sorted(dashboards_dir.rglob("*.md")):
            dest = vault / "dashboards" / md.name
            moves.append((md, dest, "dashboards"))

    # 05_templates -> templates/ (flatten)
    templates_dir = vault / "05_templates"
    if templates_dir.exists():
        for md in sorted(templates_dir.rglob("*.md")):
            dest = vault / "templates" / md.name
            moves.append((md, dest, "templates"))

    # 90_System -> system/
    system_dir = vault / "90_System"
    if system_dir.exists():
        for f in sorted(system_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(system_dir)
                dest = vault / "system" / rel
                moves.append((f, dest, "system"))

    return moves


def execute_migration(
    vault: Path,
    moves: list[tuple[Path, Path, str]],
    dry_run: bool = True,
) -> dict:
    """Execute the migration. Returns stats dict."""
    stats = {
        "moved": 0,
        "skipped_conflict": 0,
        "skipped_missing": 0,
        "errors": 0,
        "collisions_renamed": 0,
    }
    log_lines: list[str] = []
    log_lines.append(f"# Vault Restructure Log — {datetime.now().isoformat()}")
    log_lines.append(f"# Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    log_lines.append(f"# Total planned moves: {len(moves)}")
    log_lines.append("")

    # Create new folders
    if not dry_run:
        for folder in NEW_FOLDERS:
            (vault / folder).mkdir(exist_ok=True)

    for src, dest, category in moves:
        if not src.exists():
            log_lines.append(f"SKIP (missing): {src} -> {dest}")
            stats["skipped_missing"] += 1
            continue

        if dest.exists():
            log_lines.append(f"SKIP (conflict): {src} -> {dest}")
            stats["skipped_conflict"] += 1
            continue

        if "renamed" in category:
            stats["collisions_renamed"] += 1

        if dry_run:
            log_lines.append(f"WOULD MOVE [{category}]: {src} -> {dest}")
            stats["moved"] += 1
        else:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                log_lines.append(f"MOVED [{category}]: {src} -> {dest}")
                stats["moved"] += 1
            except Exception as e:
                log_lines.append(f"ERROR: {src} -> {dest}: {e}")
                stats["errors"] += 1

    # Write log
    log_path = vault / "system" if not dry_run else vault / "90_System"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "vault_restructure_log.md"
    log_file.write_text("\n".join(log_lines), encoding="utf-8")

    # Add tombstones to old folders
    if not dry_run:
        old_to_new = {
            "00_dashboards": "dashboards",
            "01_projects": "projects",
            "02_sources": "knowledge",
            "03_playbooks": "guides",
            "04_evergreen": "knowledge",
            "05_templates": "templates",
        }
        for old, new in old_to_new.items():
            old_dir = vault / old
            if old_dir.exists():
                readme = old_dir / "README.md"
                readme.write_text(
                    TOMBSTONE.replace("{new_folder}", new),
                    encoding="utf-8",
                )

    return stats


def main() -> None:
    execute = "--execute" in sys.argv

    print(f"Vault: {VAULT}")
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print()

    # Pre-migration count
    pre_count = sum(1 for _ in VAULT.rglob("*.md") if ".obsidian" not in str(_))
    print(f"Pre-migration note count: {pre_count}")

    moves = collect_moves(VAULT)
    print(f"Planned moves: {len(moves)}")

    # Category breakdown
    categories: Counter[str] = Counter()
    for _, _, cat in moves:
        base = cat.split(" (")[0]
        categories[base] += 1
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")
    print()

    stats = execute_migration(VAULT, moves, dry_run=not execute)

    print(f"Moved: {stats['moved']}")
    print(f"Skipped (conflict): {stats['skipped_conflict']}")
    print(f"Skipped (missing): {stats['skipped_missing']}")
    print(f"Collisions renamed: {stats['collisions_renamed']}")
    print(f"Errors: {stats['errors']}")

    if execute:
        post_count = sum(1 for _ in VAULT.rglob("*.md") if ".obsidian" not in str(_))
        # Post count includes tombstone READMEs (+6) and the log file (+1)
        print(f"\nPost-migration note count: {post_count}")
        print(f"  (includes {post_count - pre_count + stats['moved'] - stats['skipped_conflict']} tombstone/log files)")
    else:
        print("\nThis was a dry run. Run with --execute to perform migration.")

    log_loc = "system" if execute else "90_System"
    print(f"Log: {VAULT / log_loc / 'vault_restructure_log.md'}")


if __name__ == "__main__":
    main()
