"""Ingest CKE extraction output into the vault.

Reads output_v2 structure and routes ALL notes to vault 01_Knowledge/ (flat).
Client dimension is handled by tags (client/sgdbf), not by folder.

  source_library/*/extract/*.md    -> vault 01_Knowledge/
  templates/*/extract/*.md         -> vault 01_Knowledge/
  rfp/*/extract/*.md               -> vault 01_Knowledge/
  projects/{client}/*/extract/*.md -> vault 01_Knowledge/

Skip: synthesis.md, index.md, *.json, *_transcript.md, _meta.yaml
Cover slides -> vault _assets/
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
    by_dest: dict[str, int] = field(default_factory=dict)


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


def _resolve_dest(
    scope: str,
    client: str | None,
    md_file: Path,
    vault_root: Path,
) -> Path:
    """Resolve vault destination — ALL notes go to 01_Knowledge/ (flat).

    Per Council Decision #7, client dimension is handled by tags, not folders.
    """
    return vault_root / "01_Knowledge" / md_file.name


def _collect_packages(cke_output_path: Path) -> list[tuple[str, str | None, Path]]:
    """Walk output_v2 and yield (scope, client_or_none, pkg_dir) tuples.

    output_v2 structure:
      source_library/{series}/{series}/extract/*.md
      templates/{series}/{series}/extract/*.md
      rfp/{series}/{series}/extract/*.md
      projects/{client}/{client}/extract/*.md
    """
    packages: list[tuple[str, str | None, Path]] = []

    for scope_dir in sorted(cke_output_path.iterdir()):
        if not scope_dir.is_dir():
            continue
        scope = scope_dir.name

        for client_or_series in sorted(scope_dir.iterdir()):
            if not client_or_series.is_dir():
                continue

            client = client_or_series.name if scope == "projects" else None

            # The actual package dir may be nested one more level
            # (e.g., projects/Lenzing_Planning/Lenzing_Planning/extract/)
            # or directly contain extract/
            extract_dir = client_or_series / "extract"
            if extract_dir.exists():
                packages.append((scope, client, client_or_series))
            else:
                # Check one level deeper
                for pkg_dir in sorted(client_or_series.iterdir()):
                    if pkg_dir.is_dir():
                        packages.append((scope, client, pkg_dir))

    return packages


def ingest_extractions(
    cke_output_path: Path,
    vault_root: Path,
    dry_run: bool = False,
    force: bool = False,
    ops_db: object | None = None,
) -> IngestResult:
    """Ingest CKE extraction output into the vault.

    All notes route to 01_Knowledge/ (flat). Client dimension via tags.

    Args:
        cke_output_path: Path to CKE output_v2 directory.
        vault_root: Path to vault root.
        dry_run: If True, report what would happen without writing.
        force: If True, overwrite even trust_level=verified notes.
        ops_db: Optional OpsDB instance for logging ingest events.

    Returns:
        IngestResult with counts of actions taken.
    """
    result = IngestResult()
    vault_assets = vault_root / "_assets"

    if not cke_output_path.is_dir():
        result.errors.append(f"Not a directory: {cke_output_path}")
        return result

    packages = _collect_packages(cke_output_path)
    logger.info("Found %d packages in %s", len(packages), cke_output_path)

    for scope, client, pkg_dir in packages:
        meta = _read_meta(pkg_dir)

        # Find extractable .md files
        extract_dir = pkg_dir / "extract"
        md_files = list(extract_dir.glob("*.md")) if extract_dir.exists() else []
        md_files.extend(pkg_dir.glob("session_*.md"))

        for md_file in md_files:
            rel = md_file.relative_to(pkg_dir)
            if not _should_copy(rel):
                continue

            dest = _resolve_dest(scope, client, md_file, vault_root)

            # Check trust_level protection
            if dest.exists() and not force:
                existing_fm = read_frontmatter(dest)
                if existing_fm.get("trust_level") == "verified":
                    logger.info("SKIP verified: %s", dest.name)
                    result.notes_skipped_verified += 1
                    continue

            if dry_run:
                action = "would replace" if dest.exists() else "would create"
                logger.info("%s: %s -> %s", action, md_file.name, dest)
                result.notes_ingested += 1
                dest_folder = str(dest.parent.relative_to(vault_root))
                result.by_dest[dest_folder] = result.by_dest.get(dest_folder, 0) + 1
                continue

            # Read source content and write to vault
            try:
                content = md_file.read_text(encoding="utf-8")
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

                dest_folder = str(dest.parent.relative_to(vault_root)).replace("\\", "/")
                result.by_dest[dest_folder] = result.by_dest.get(dest_folder, 0) + 1

                if ops_db is not None:
                    _log_ingest_event(
                        ops_db,
                        source_path=str(md_file).replace("\\", "/"),
                        destination_path=str(dest).replace("\\", "/"),
                        action="ingested",
                    )

            except Exception as e:
                result.errors.append(f"{md_file.name}: {e}")

        # Copy cover slide to _assets/
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
                except Exception as e:
                    result.errors.append(f"cover {cover.name}: {e}")

    return result


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
