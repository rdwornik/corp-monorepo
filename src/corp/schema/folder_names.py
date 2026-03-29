"""Canonical MyWork folder names — single source of truth.

Council #24 binding decision (2026-03-29).
Access-frequency principle: daily=1 click, weekly=2, monthly=deeper.
Folders = access state. Tags = knowledge dimensions.

Zero imports — safe to use from any module without circular import risk.
"""

# === Top-level MyWork folders (ordered by number prefix) ===
INBOX = "00_Inbox"
PROJECTS = "10_Projects"
WORKFLOWS = "20_Workflows"
REFERENCE = "30_Reference"
ADMIN = "70_Admin"
COMPLIANCE = "80_Compliance"
ARCHIVE = "90_Archive"

# === Hidden pipeline infrastructure ===
CORP_INFRA = ".corp"

# === Inbox sub-locations ===
STAGING = "_Staging"
UNMATCHED = "_Unmatched"
QUARANTINE = "_quarantine"

# === All canonical top-level folders ===
ALL_MYWORK_FOLDERS: tuple[str, ...] = (
    INBOX, PROJECTS, WORKFLOWS, REFERENCE, ADMIN, COMPLIANCE, ARCHIVE
)

# === Folders the scanner skips (non-ingestible) ===
SCAN_SKIP_FOLDERS: frozenset[str] = frozenset(
    {ARCHIVE, ADMIN, COMPLIANCE, CORP_INFRA,
     "__pycache__", ".git", ".venv", "node_modules", ".claude"}
)

# === Reference subfolders ===
REF_PRODUCTS = "Products"
REF_ARCHITECTURE = "Architecture"
REF_COMPETITION = "Competition"
REF_BRANDING = "Branding"
REF_RFP_LIBRARY = "RFP_Library"

# === Workflow subfolders ===
WF_MASTER_DECK = "Master_Deck"
WF_TECH_PRESENTATIONS = "Technical_Presentations"
WF_DEMO_SCRIPTS = "Demo_Scripts"
WF_WORKSHOP_KITS = "Workshop_Kits"
