"""Ingest CKE extraction output into the vault.

Reads CKE output packages, copies extracted notes and cover slides
to the vault knowledge folder, and logs actions to ops.db.

What gets copied:
- extract/{filename}.md -> vault/knowledge/{filename}.md
- session_*.md -> vault/knowledge/session_{id}.md
- Cover slide (from _meta.yaml or fallback slide_001.png)
  -> vault/knowledge/assets/{filename}_cover.png

What stays in CKE output (NOT copied):
- extract/{filename}.json (sidecar metadata)
- Non-cover slide PNGs
- source/frames/, source/docs/, source/video/
- *_transcript.md
- synthesis.md, index.md, _meta.yaml
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from corp_by_os.vault_io import read_frontmatter, write_note

logger = logging.getLogger(__name__)

# Files that should NOT be copied to vault
_SKIP_PATTERNS = [
    re.compile(r".*\.json$"),
    re.compile(r".*_transcript\.md$"),
    re.compile(r"^synthesis\.md$"),
    re.compile(r"^index\.md$"),
    re.compile(r"^_meta\.yaml$"),
]

_SKIP_DIRS = {"source", "frames", "docs", "video"}


@dataclass
class IngestResult:
    """Result of ingesting CKE extractions."""

    notes_ingested: int = 0
    notes_skipped_verified: int = 0
    covers_copied: int = 0
    errors: list[str] = field(default_factory=list)


def _read_meta(pkg_dir: Path) -> dict:
    """Read _meta.yaml from a CKE package."""
    meta_path = pkg_dir / "_meta.yaml"
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _find_cover_slide(pkg_dir: Path, meta: dict) -> Path | None:
    """Find cover slide: prefer _meta.yaml cover_slide, fallback to slide_001.png."""
    cover = meta.get("cover_slide")
    if cover:
        cover_path = pkg_dir / cover
        if cover_path.exists():
            return cover_path

    fallback = pkg_dir / "source" / "slides" / "slide_001.png"
    if fallback.exists():
        return fallback

    return None


def _should_copy(rel_path: Path) -> bool:
    """Check if a file should be copied to vault."""
    name = rel_path.name

    # Skip files in excluded directories
    for part in rel_path.parts[:-1]:
        if part in _SKIP_DIRS:
            return False

    # Skip matching patterns
    for pattern in _SKIP_PATTERNS:
        if pattern.match(name):
            return False

    # Only copy .md files
    return rel_path.suffix == ".md"


def _match_by_source_path(
    source_path: str,
    vault_knowledge: Path,
) -> Path | None:
    """Find existing vault note with matching source_path in frontmatter."""
    if not source_path or not vault_knowledge.exists():
        return None

    normalized = source_path.replace("\\", "/")
    for md_file in vault_knowledge.glob("*.md"):
        fm = read_frontmatter(md_file)
        existing_sp = fm.get("source_path", "")
        if existing_sp and str(existing_sp).replace("\\", "/") == normalized:
            return md_file
    return None


def ingest_extractions(
    cke_output_path: Path,
    vault_root: Path,
    dry_run: bool = False,
    force: bool = False,
    ops_db: object | None = None,
) -> IngestResult:
    """Ingest CKE extraction output into vault/knowledge/.

    Args:
        cke_output_path: Path to CKE output directory (contains package dirs).
        vault_root: Path to vault root.
        dry_run: If True, report what would happen without writing.
        force: If True, overwrite even trust_level=verified notes.
        ops_db: Optional OpsDB instance for logging ingest events.

    Returns:
        IngestResult with counts of actions taken.
    """
    result = IngestResult()
    vault_knowledge = vault_root / "knowledge"
    vault_assets = vault_knowledge / "assets"

    if not cke_output_path.is_dir():
        result.errors.append(f"Not a directory: {cke_output_path}")
        return result

    # Process each package directory
    for pkg_dir in sorted(cke_output_path.iterdir()):
        if not pkg_dir.is_dir():
            continue

        meta = _read_meta(pkg_dir)

        # Find and copy extractable .md files
        extract_dir = pkg_dir / "extract"
        md_files = list(extract_dir.glob("*.md")) if extract_dir.exists() else []

        # Also check for session_*.md at package level
        md_files.extend(pkg_dir.glob("session_*.md"))

        for md_file in md_files:
            rel = md_file.relative_to(pkg_dir)
            if not _should_copy(rel):
                continue

            # Read frontmatter to check source_path for matching
            fm = read_frontmatter(md_file) if md_file.exists() else {}
            source_path = fm.get("source_path", "")

            # Determine destination: match by source_path or use filename
            existing = _match_by_source_path(source_path, vault_knowledge)
            if existing:
                dest = existing
            else:
                dest = vault_knowledge / md_file.name

            # Check trust_level protection
            if dest.exists() and not force:
                existing_fm = read_frontmatter(dest)
                if existing_fm.get("trust_level") == "verified":
                    logger.info("SKIP verified: %s", dest.name)
                    result.notes_skipped_verified += 1
                    continue

            if dry_run:
                action = "would replace" if dest.exists() else "would create"
                logger.info("%s: %s", action, dest.name)
                result.notes_ingested += 1
                continue

            # Read source content and write to vault
            try:
                content = md_file.read_text(encoding="utf-8")
                # Parse frontmatter and body
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end != -1:
                        fm_text = content[3:end]
                        body = content[end + 4:]
                        note_fm = yaml.safe_load(fm_text) or {}
                    else:
                        note_fm, body = {}, content
                else:
                    note_fm, body = {}, content

                dest.parent.mkdir(parents=True, exist_ok=True)
                write_note(dest, note_fm, body, mode="upsert", force=force)
                result.notes_ingested += 1

                # Log to ops.db
                if ops_db is not None:
                    _log_ingest_event(
                        ops_db,
                        source_path=str(md_file).replace("\\", "/"),
                        destination_path=str(dest).replace("\\", "/"),
                        action="ingested",
                    )

            except Exception as e:
                result.errors.append(f"{md_file.name}: {e}")

        # Copy cover slide
        cover = _find_cover_slide(pkg_dir, meta)
        if cover:
            stem = pkg_dir.name
            cover_dest = vault_assets / f"{stem}_cover.png"

            if dry_run:
                logger.info("would copy cover: %s", cover_dest.name)
                result.covers_copied += 1
            else:
                try:
                    cover_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(cover), str(cover_dest))
                    result.covers_copied += 1

                    # Rewrite image paths in ingested notes for this package
                    _rewrite_cover_paths(
                        vault_knowledge, stem, cover_dest, vault_knowledge,
                    )
                except Exception as e:
                    result.errors.append(f"cover {cover.name}: {e}")

    return result


def _rewrite_cover_paths(
    vault_knowledge: Path,
    pkg_stem: str,
    cover_dest: Path,
    vault_base: Path,
) -> None:
    """Rewrite image paths in notes to point to vault-relative asset path."""
    vault_rel = cover_dest.relative_to(vault_base)
    vault_rel_str = str(vault_rel).replace("\\", "/")

    for md_file in vault_knowledge.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            # Replace references to source slide paths
            patterns = [
                "source/slides/slide_001.png",
                "slides/slide_001.png",
            ]
            changed = False
            for pat in patterns:
                if pat in content:
                    content = content.replace(pat, vault_rel_str)
                    changed = True
            if changed:
                md_file.write_text(content, encoding="utf-8")
        except Exception:
            pass


def _log_ingest_event(
    ops_db: object,
    source_path: str,
    destination_path: str,
    action: str,
) -> None:
    """Log an ingest event to ops.db."""
    try:
        ops_db.log_event(  # type: ignore[attr-defined]
            action=action,
            source_path=source_path,
            destination_path=destination_path,
            method="ingest-extractions",
            confidence=1.0,
            reasoning="CKE extraction output ingestion",
        )
    except Exception as e:
        logger.debug("Failed to log ingest event: %s", e)
