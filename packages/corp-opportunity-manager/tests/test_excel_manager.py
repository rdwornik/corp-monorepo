"""Tests for Excel project codes management."""

from pathlib import Path

import pytest
from openpyxl import Workbook

from corp_opportunity_manager.excel_manager import (
    find_row_by_client,
    list_projects,
    update_folder_link,
)


@pytest.fixture
def sample_excel(tmp_path: Path) -> Path:
    """Create a sample Project_Codes spreadsheet matching real layout.

    Columns: A=Empty, B=Name, C=Account Name, D=Opportunity Name,
             E=Link to SF, F=Booking Amount, G=JDA Industry, H=Stage,
             I=Close Date, J=JDA OpptyID2, K=Date Added, L=Next Step, M=Folder Link
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Main"
    ws.append(
        [
            "Empty",
            "Name",
            "Account Name",
            "Opportunity Name",
            "Link to SF",
            "Booking Amount",
            "JDA Industry",
            "Stage",
            "Close Date",
            "JDA OpptyID2",
            "Date Added",
            "Next Step",
            "Folder Link",
        ]
    )
    ws.append(
        [
            None,
            "Robert Dwornik",
            "Lenzing AG",
            "Lenzing - Planning",
            "",
            500000,
            "Manufacturing",
            "Prove Value",
            None,
            "OP-001",
            None,
            "Discovery call",
            "",
        ]
    )
    ws.append(
        [
            None,
            "Robert Dwornik",
            "Honda Motor Co",
            "Honda - WMS",
            "",
            750000,
            "Manufacturing",
            "Negotiate",
            None,
            "OP-002",
            None,
            "POC next week",
            "",
        ]
    )
    ws.append(
        [
            None,
            "Robert Dwornik",
            "BMW Group",
            "BMW - TMS",
            "",
            300000,
            "Automotive",
            "Disqualified",
            None,
            "OP-003",
            None,
            "",
            "C:\\projects\\BMW_TMS",
        ]
    )

    path = tmp_path / "Project_Codes.xlsm"
    wb.save(path)
    wb.close()
    return path


def test_find_row_by_client(sample_excel: Path):
    row = find_row_by_client(sample_excel, "Lenzing")
    assert row is not None
    assert row.account_name == "Lenzing AG"
    assert row.opportunity_name == "Lenzing - Planning"
    assert row.row_number == 2


def test_find_row_by_client_case_insensitive(sample_excel: Path):
    row = find_row_by_client(sample_excel, "honda")
    assert row is not None
    assert row.account_name == "Honda Motor Co"


def test_find_row_by_client_substring_match(sample_excel: Path):
    row = find_row_by_client(sample_excel, "BMW")
    assert row is not None
    assert row.account_name == "BMW Group"


def test_find_row_by_client_not_found(sample_excel: Path):
    row = find_row_by_client(sample_excel, "Nonexistent")
    assert row is None


def test_find_row_missing_file(tmp_path: Path):
    row = find_row_by_client(tmp_path / "nope.xlsx", "Test")
    assert row is None


def test_update_folder_link(sample_excel: Path):
    success = update_folder_link(sample_excel, 2, "C:\\projects\\Lenzing_Planning")
    assert success

    row = find_row_by_client(sample_excel, "Lenzing")
    assert row is not None
    assert row.folder_link == "C:\\projects\\Lenzing_Planning"


def test_list_projects(sample_excel: Path):
    rows = list_projects(sample_excel)
    assert len(rows) == 3
    accounts = {r.account_name for r in rows}
    assert accounts == {"Lenzing AG", "Honda Motor Co", "BMW Group"}


def test_list_projects_missing_file(tmp_path: Path):
    rows = list_projects(tmp_path / "nope.xlsx")
    assert rows == []
