"""Folder structure standards — audit, subfolder creation, naming conventions."""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

from corp_opportunity_manager.models import StructureIssue

logger = logging.getLogger(__name__)

# Standard subfolder definitions
SUBFOLDER_DEFS: dict[str, dict] = {
    "rfp": {
        "path": "RFP",
        "children": ["Original", "WIP", "Submission"],
    },
    "meetings": {
        "path": "Meetings",
        "children": [],
    },
    "implementation": {
        "path": "Implementation Services",
        "children": [],
    },
}

# Regex for standard naming convention: Client_YYYY-MM-DD_Topic.pptx
_STANDARD_PPTX_RE = re.compile(r"^[A-Za-z0-9_-]+_\d{4}-\d{2}-\d{2}_[A-Za-z0-9_ -]+\.pptx$")

# Regex for meeting folder: YYYY.MM.DD - topic
_MEETING_FOLDER_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2} - .+$")


def check_structure(project_path: Path) -> list[StructureIssue]:
    """Audit a project folder against standards.

    Returns a list of issues found (missing folders, non-standard names, etc.).
    """
    issues: list[StructureIssue] = []

    if not project_path.exists():
        return [
            StructureIssue("missing_folder", str(project_path), "Project folder does not exist")
        ]

    # Check _knowledge/ exists
    knowledge = project_path / "_knowledge"
    if not knowledge.exists():
        issues.append(
            StructureIssue(
                "missing_folder",
                str(knowledge),
                "Create _knowledge/ for project metadata",
            )
        )
    else:
        if not (knowledge / "project-info.yaml").exists():
            issues.append(
                StructureIssue(
                    "missing_file",
                    str(knowledge / "project-info.yaml"),
                    "Create project-info.yaml with project metadata",
                )
            )

    # Check for non-standard pptx names in root
    for f in project_path.iterdir():
        if f.is_file() and f.suffix.lower() == ".pptx":
            if not _STANDARD_PPTX_RE.match(f.name):
                # Try to suggest a standard name
                client = project_path.name.split("_")[0] if "_" in project_path.name else "Client"
                suggestion = f"{client}_{date.today().isoformat()}_{f.stem}.pptx"
                issues.append(
                    StructureIssue(
                        "non_standard_name",
                        str(f),
                        f"Rename to: {suggestion}",
                    )
                )

    # Check for meeting-like files in root that should be in Meetings/
    meetings_dir = project_path / "Meetings"
    for f in project_path.iterdir():
        if f.is_file() and "meeting" in f.name.lower():
            if not meetings_dir.exists():
                issues.append(
                    StructureIssue(
                        "misplaced_file",
                        str(f),
                        "Move to Meetings/ subfolder",
                    )
                )

    return issues


def create_subfolder(project_path: Path, folder_type: str) -> list[Path]:
    """Create a standard subfolder structure within a project.

    Args:
        project_path: The project root directory.
        folder_type: One of 'rfp', 'meetings', 'implementation'.

    Returns:
        List of paths created.

    Raises:
        ValueError: If folder_type is unknown.
    """
    folder_type = folder_type.lower()
    if folder_type not in SUBFOLDER_DEFS:
        raise ValueError(
            f"Unknown folder type '{folder_type}'. Valid: {', '.join(SUBFOLDER_DEFS.keys())}"
        )

    defn = SUBFOLDER_DEFS[folder_type]
    created: list[Path] = []

    base = project_path / defn["path"]
    base.mkdir(parents=True, exist_ok=True)
    created.append(base)
    logger.info("Created: %s", base)

    for child in defn.get("children", []):
        child_path = base / child
        child_path.mkdir(parents=True, exist_ok=True)
        created.append(child_path)
        logger.info("Created: %s", child_path)

    return created


def suggest_rename(
    filename: str,
    client: str,
    dt: date | None = None,
    topic: str | None = None,
) -> str | None:
    """Suggest a standard name for a file, or None if it already conforms.

    Only handles .pptx files for now.
    """
    if not filename.lower().endswith(".pptx"):
        return None

    if _STANDARD_PPTX_RE.match(filename):
        return None  # Already standard

    if dt is None:
        dt = date.today()
    if topic is None:
        # Extract topic from existing filename (strip extension, known prefixes)
        topic = Path(filename).stem
        # Remove common prefixes/suffixes
        for strip in [client, "FINAL", "final", "v2", "v3", "copy", "Copy", "-", "_"]:
            topic = topic.replace(strip, "")
        topic = topic.strip(" _-")
        if not topic:
            topic = "Presentation"

    return f"{client}_{dt.isoformat()}_{topic}.pptx"


def list_project_files(project_path: Path) -> list[dict[str, str]]:
    """List files in a project folder with size info, for display."""
    if not project_path.exists():
        return []

    entries: list[dict[str, str]] = []
    for item in sorted(project_path.rglob("*")):
        if item.is_file():
            rel = item.relative_to(project_path)
            size = item.stat().st_size
            if size > 1_000_000:
                size_str = f"{size / 1_000_000:.0f}MB"
            elif size > 1_000:
                size_str = f"{size / 1_000:.0f}KB"
            else:
                size_str = f"{size}B"
            entries.append({"path": str(rel), "size": size_str})

    return entries
