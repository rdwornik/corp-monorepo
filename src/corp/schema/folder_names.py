"""Canonical MyWork folder names — single source of truth.

Zero imports — safe to use from any module without circular import risk.
Renaming a folder means changing one constant here; all usages follow.
"""

# Top-level MyWork folders
INBOX = "00_Inbox"
PROJECTS = "10_Projects"
TEMPLATES = "30_Templates"
RFP = "50_RFP"
SOURCE_LIBRARY = "60_Source_Library"
ADMIN = "70_Admin"
ARCHIVE = "80_Archive"
SYSTEM = "90_System"

# Internal sub-folder names (appear inside any top-level folder)
STAGING = "_Staging"
UNMATCHED = "_Unmatched"
QUARANTINE = "_quarantine"

# All top-level MyWork folders in canonical order
ALL_MYWORK_FOLDERS: tuple[str, ...] = (
    INBOX,
    PROJECTS,
    TEMPLATES,
    RFP,
    SOURCE_LIBRARY,
    ADMIN,
    ARCHIVE,
    SYSTEM,
)

# Folders the overnight scanner and audit skip (they are not ingestible content)
SCAN_SKIP_FOLDERS: frozenset[str] = frozenset(
    {ARCHIVE, SYSTEM, ".corp", "__pycache__", ".git", ".venv", "node_modules"}
)
