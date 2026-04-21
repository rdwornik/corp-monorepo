"""Regression: execute_plan() must refuse OneDrive-Blue-Yonder paths.

Failing-first test for P1-1 (see docs/audits/2026-04-21-p1-verification.md).
find_onedrive_overlap() populates CleanupItem.path with OneDrive absolute
paths; execute_plan() used to call target.unlink() on them. This test
asserts the execution site now fails closed with OneDriveSafetyError.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from corp.cleanup.disk import CleanupItem, CleanupPlan, execute_plan
from corp.cleanup.errors import OneDriveSafetyError


def _make_plan_with_onedrive_item(tmp_path: Path) -> tuple[CleanupPlan, Path]:
    """Stage a plan containing an item inside a fake OneDrive - Blue Yonder tree."""
    onedrive_root = tmp_path / "OneDrive - Blue Yonder" / "MyWork_OneDrive"
    onedrive_root.mkdir(parents=True)
    target = onedrive_root / "synced_file.docx"
    target.write_bytes(b"important synced content")

    plan = CleanupPlan()
    plan.add(
        CleanupItem(
            path=str(target),
            filename=target.name,
            size_bytes=target.stat().st_size,
            category="overlap",
            reason="test: simulated find_onedrive_overlap output",
            keep_path=str(tmp_path / "local" / target.name),
        )
    )
    return plan, target


def test_execute_plan_refuses_onedrive_path(tmp_path: Path) -> None:
    """Execution fails closed when any item resolves inside OneDrive - Blue Yonder."""
    plan, target = _make_plan_with_onedrive_item(tmp_path)
    log_path = tmp_path / "cleanup_log.jsonl"

    with pytest.raises(OneDriveSafetyError, match="OneDrive"):
        execute_plan(plan, log_path, dry_run=False)

    # File must still exist — the guard prevents deletion.
    assert target.exists(), "OneDrive file must not be deleted when guard fires"


def test_execute_plan_dry_run_allows_onedrive_listing(tmp_path: Path) -> None:
    """Dry run may list OneDrive items for reporting; only execution is blocked."""
    plan, target = _make_plan_with_onedrive_item(tmp_path)
    log_path = tmp_path / "cleanup_log.jsonl"

    deleted, failed = execute_plan(plan, log_path, dry_run=True)

    assert deleted == 0
    assert failed == 0
    assert target.exists()
