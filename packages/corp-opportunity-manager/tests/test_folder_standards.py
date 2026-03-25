"""Tests for folder structure standards — audit, subfolder creation, naming."""

from datetime import date
from pathlib import Path

import pytest

from corp_opportunity_manager.folder_standards import (
    check_structure,
    create_subfolder,
    list_project_files,
    suggest_rename,
)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a sample project folder."""
    d = tmp_path / "Lenzing_Planning"
    d.mkdir()
    (d / "_knowledge").mkdir()
    (d / "_knowledge" / "project-info.yaml").write_text("client: Lenzing\n")
    (d / "_knowledge" / "notes.md").write_text("# Notes\n")
    (d / "Lenzing_2026-03-05_Discovery.pptx").write_bytes(b"FAKE")
    return d


def test_check_structure_clean(project_dir: Path):
    issues = check_structure(project_dir)
    assert issues == []


def test_check_structure_missing_knowledge(tmp_path: Path):
    d = tmp_path / "Test_WMS"
    d.mkdir()
    issues = check_structure(d)
    types = [i.issue_type for i in issues]
    assert "missing_folder" in types


def test_check_structure_missing_project_info(tmp_path: Path):
    d = tmp_path / "Test_WMS"
    d.mkdir()
    (d / "_knowledge").mkdir()
    issues = check_structure(d)
    types = [i.issue_type for i in issues]
    assert "missing_file" in types


def test_check_structure_non_standard_pptx_name(project_dir: Path):
    (project_dir / "prezka v3 FINAL.pptx").write_bytes(b"FAKE")
    issues = check_structure(project_dir)
    non_std = [i for i in issues if i.issue_type == "non_standard_name"]
    assert len(non_std) == 1
    assert "Rename to:" in non_std[0].suggestion


def test_check_structure_nonexistent_path(tmp_path: Path):
    issues = check_structure(tmp_path / "nonexistent")
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_folder"


def test_create_subfolder_rfp(project_dir: Path):
    created = create_subfolder(project_dir, "rfp")
    assert len(created) == 4  # RFP/ + Original/ + WIP/ + Submission/
    assert (project_dir / "RFP").exists()
    assert (project_dir / "RFP" / "Original").exists()
    assert (project_dir / "RFP" / "WIP").exists()
    assert (project_dir / "RFP" / "Submission").exists()


def test_create_subfolder_meetings(project_dir: Path):
    created = create_subfolder(project_dir, "meetings")
    assert len(created) == 1
    assert (project_dir / "Meetings").exists()


def test_create_subfolder_implementation(project_dir: Path):
    create_subfolder(project_dir, "implementation")
    assert (project_dir / "Implementation Services").exists()


def test_create_subfolder_unknown(project_dir: Path):
    with pytest.raises(ValueError, match="Unknown folder type"):
        create_subfolder(project_dir, "nonexistent")


def test_create_subfolder_idempotent(project_dir: Path):
    create_subfolder(project_dir, "rfp")
    create_subfolder(project_dir, "rfp")  # Should not raise
    assert (project_dir / "RFP" / "Original").exists()


def test_suggest_rename_non_standard():
    result = suggest_rename("prezka v3 FINAL.pptx", "Lenzing", date(2026, 3, 5), "Proposal")
    assert result == "Lenzing_2026-03-05_Proposal.pptx"


def test_suggest_rename_already_standard():
    result = suggest_rename("Lenzing_2026-03-05_Discovery.pptx", "Lenzing")
    assert result is None


def test_suggest_rename_non_pptx():
    result = suggest_rename("document.pdf", "Lenzing")
    assert result is None


def test_suggest_rename_auto_topic():
    result = suggest_rename("Technical Overview.pptx", "Honda", date(2026, 4, 1))
    assert result is not None
    assert result.startswith("Honda_2026-04-01_")
    assert result.endswith(".pptx")


def test_list_project_files(project_dir: Path):
    files = list_project_files(project_dir)
    assert len(files) >= 3
    paths = [f["path"] for f in files]
    assert any("project-info.yaml" in p for p in paths)


def test_list_project_files_empty(tmp_path: Path):
    d = tmp_path / "Empty_Project"
    d.mkdir()
    files = list_project_files(d)
    assert files == []


def test_list_project_files_nonexistent(tmp_path: Path):
    files = list_project_files(tmp_path / "nope")
    assert files == []
