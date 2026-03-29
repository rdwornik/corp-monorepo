"""Shared fixtures for cleanup tests."""

from __future__ import annotations

import pytest
from corp.schema.folder_names import INBOX, RFP, SOURCE_LIBRARY


@pytest.fixture()
def mywork_cleanup(tmp_path):
    """Create a MyWork-like structure with problematic files."""
    mywork = tmp_path / "MyWork"

    # INBOX with triageable files
    inbox = mywork / INBOX
    inbox.mkdir(parents=True)
    (inbox / "Sprint Planning.pptx").write_bytes(b"fake-pptx")
    (inbox / "MeetingNotes_Q4_Review.txt").write_text("notes", encoding="utf-8")
    (inbox / "RFP_Response_Final.txt").write_text("rfp response", encoding="utf-8")
    # Infrastructure files (should be skipped)
    (inbox / "folder_manifest.yaml").write_text("purpose: Inbox", encoding="utf-8")
    (inbox / "_triage_log.jsonl").write_text("", encoding="utf-8")
    (inbox / "_triage_schema.yaml").write_text("fields: {}", encoding="utf-8")

    # SOURCE_LIBRARY with junk files
    source_lib = mywork / SOURCE_LIBRARY / "02_Training_Enablement"
    source_lib.mkdir(parents=True)
    (source_lib / "training.pptx").write_bytes(b"pptx")
    (source_lib / "bookmark.url").write_text(
        "[InternetShortcut]\nURL=https://example.com", encoding="utf-8"
    )
    (source_lib / "debug.log").write_text("log line", encoding="utf-8")

    # RFP with loose files
    rfp = mywork / RFP
    rfp.mkdir(parents=True)
    (rfp / "RFP_Database_Master.xlsx").write_bytes(b"xlsx")
    (rfp / "RFP_Database_Planning.xlsx").write_bytes(b"xlsx")
    (rfp / "folder_manifest.yaml").write_text("purpose: RFP", encoding="utf-8")
    # Subfolder (should not be scanned as loose)
    (rfp / "Certificate").mkdir()
    (rfp / "Certificate" / "cert.pdf").write_bytes(b"pdf")

    return mywork
