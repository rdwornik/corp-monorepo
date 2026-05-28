"""Shared fixtures for cleanup tests."""

from __future__ import annotations

import pytest

from corp.schema.folder_names import INBOX, REF_RFP_LIBRARY, REFERENCE


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

    # REFERENCE with junk files
    ref_training = mywork / REFERENCE / "02_Training_Enablement"
    ref_training.mkdir(parents=True)
    (ref_training / "training.pptx").write_bytes(b"pptx")
    (ref_training / "bookmark.url").write_text(
        "[InternetShortcut]\nURL=https://example.com", encoding="utf-8"
    )
    (ref_training / "debug.log").write_text("log line", encoding="utf-8")

    # RFP_Library with loose files
    rfp_lib = mywork / REFERENCE / REF_RFP_LIBRARY
    rfp_lib.mkdir(parents=True)
    (rfp_lib / "RFP_Database_Master.xlsx").write_bytes(b"xlsx")
    (rfp_lib / "RFP_Database_Planning.xlsx").write_bytes(b"xlsx")
    (rfp_lib / "folder_manifest.yaml").write_text("purpose: RFP_Library", encoding="utf-8")
    # Subfolder (should not be scanned as loose)
    (rfp_lib / "Certificate").mkdir()
    (rfp_lib / "Certificate" / "cert.pdf").write_bytes(b"pdf")

    return mywork
