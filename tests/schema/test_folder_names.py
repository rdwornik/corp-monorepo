"""Tests for canonical folder name constants."""

import pytest

from corp.schema.folder_names import (
    ADMIN,
    ALL_MYWORK_FOLDERS,
    ARCHIVE,
    COMPLIANCE,
    INBOX,
    PROJECTS,
    QUARANTINE,
    REF_RFP_LIBRARY,
    REFERENCE,
    SCAN_SKIP_FOLDERS,
    STAGING,
    UNMATCHED,
    WORKFLOWS,
)


def test_folder_name_values():
    """Each constant has the expected string value."""
    assert INBOX == "00_Inbox"
    assert PROJECTS == "10_Projects"
    assert WORKFLOWS == "20_Workflows"
    assert REFERENCE == "30_Reference"
    assert ADMIN == "70_Admin"
    assert COMPLIANCE == "80_Compliance"
    assert ARCHIVE == "90_Archive"


def test_internal_folder_name_values():
    assert STAGING == "_Staging"
    assert UNMATCHED == "_Unmatched"
    assert QUARANTINE == "_quarantine"


def test_all_mywork_folders_ordered():
    """ALL_MYWORK_FOLDERS contains every top-level folder in numeric order."""
    assert ALL_MYWORK_FOLDERS == (
        INBOX,
        PROJECTS,
        WORKFLOWS,
        REFERENCE,
        ADMIN,
        COMPLIANCE,
        ARCHIVE,
    )


def test_all_mywork_folders_no_duplicates():
    assert len(ALL_MYWORK_FOLDERS) == len(set(ALL_MYWORK_FOLDERS))


def test_scan_skip_contains_archive_compliance():
    assert ARCHIVE in SCAN_SKIP_FOLDERS
    assert COMPLIANCE in SCAN_SKIP_FOLDERS


def test_scan_skip_does_not_contain_ingestible_folders():
    """Inbox, Projects, etc. must NOT be in SCAN_SKIP — they contain real content."""
    ingestible = {INBOX, PROJECTS, WORKFLOWS, REFERENCE}
    assert ingestible.isdisjoint(SCAN_SKIP_FOLDERS)


def test_scan_skip_is_frozenset():
    assert isinstance(SCAN_SKIP_FOLDERS, frozenset)


def test_no_imports_in_module():
    """folder_names must have zero internal imports (circular-import safety)."""
    import inspect

    import corp.schema.folder_names as mod

    src = inspect.getsource(mod)
    # No import statements other than the module docstring lines
    import_lines = [
        line.strip()
        for line in src.splitlines()
        if line.strip().startswith(("import ", "from ")) and "inspect" not in line
    ]
    assert import_lines == [], f"folder_names.py must have no imports, found: {import_lines}"
