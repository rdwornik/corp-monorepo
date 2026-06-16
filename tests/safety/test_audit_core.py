"""Unit tests for the current-state audit core metric functions.

All tests use ``tmp_path`` fixtures — never real corporate data. The OneDrive
guard/prune tests use a FAKE ``OneDrive - Blue Yonder`` segment created under
``tmp_path`` (never a real synced path).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _audit_core as core

NOW = 2_000_000_000.0
DAY = 86400.0


def _config(**over) -> core.AuditConfig:
    base = dict(
        scan_paths=[],
        onedrive_path="",
        exclude_dirs=["__pycache__", ".git"],
        hashable_size_cap_bytes=50_000_000,
        junk_drawer_loose_file_threshold=40,
        generic_dir_names=[],
        largest_files_top_n=5,
        output_dir="docs/audits",
        dev_root="",
    )
    base.update(over)
    return core.AuditConfig(**base)


def _mk(path: Path, size: int, mtime: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


# ------------------------------- inventory -------------------------------- #


def test_inventory_counts_histograms_and_largest(tmp_path: Path) -> None:
    _mk(tmp_path / "a.txt", 10, NOW - 10 * DAY)
    _mk(tmp_path / "b.md", 20, NOW - 10 * DAY)
    _mk(tmp_path / "noext", 5, NOW - 10 * DAY)
    _mk(tmp_path / "sub" / "c.txt", 30, NOW - 100 * DAY)
    _mk(tmp_path / "sub" / "deep" / "d.log", 40, NOW - 400 * DAY)

    inv = core.build_path_inventory(tmp_path, _config(), NOW)

    assert inv.exists is True
    assert inv.file_count == 5
    assert inv.dir_count == 2  # sub, sub/deep
    assert inv.total_bytes == 105
    assert inv.depth_histogram == {1: 3, 2: 1, 3: 1}
    assert inv.ext_histogram == {".txt": 2, ".md": 1, ".log": 1, "<none>": 1}
    assert inv.mtime_buckets == {"<=30d": 3, "31-180d": 1, ">365d": 1}
    assert [f.size_bytes for f in inv.largest_files] == [40, 30, 20, 10, 5]
    assert inv.largest_files[0].name == "d.log"
    # Step 2 never hashes — every largest-file entry must have sha256 unset.
    assert all(f.sha256 is None for f in inv.largest_files)


def test_largest_files_respects_top_n(tmp_path: Path) -> None:
    for i, size in enumerate((1, 2, 3, 4)):
        _mk(tmp_path / f"f{i}.bin", size, NOW - DAY)
    inv = core.build_path_inventory(tmp_path, _config(largest_files_top_n=2), NOW)
    assert [f.size_bytes for f in inv.largest_files] == [4, 3]


def test_missing_root_marks_not_exists(tmp_path: Path) -> None:
    inv = core.build_path_inventory(tmp_path / "does-not-exist", _config(), NOW)
    assert inv.exists is False
    assert inv.file_count == 0


def test_excluded_dirs_are_pruned(tmp_path: Path) -> None:
    _mk(tmp_path / "keep.txt", 3, NOW - DAY)
    _mk(tmp_path / "__pycache__" / "junk.pyc", 9, NOW - DAY)
    inv = core.build_path_inventory(tmp_path, _config(), NOW)
    assert inv.file_count == 1
    assert inv.dir_count == 0  # __pycache__ pruned before being yielded/counted


# --------------------------- placeholder logic ---------------------------- #


def test_is_cloud_placeholder_attribute_logic() -> None:
    assert core.is_cloud_placeholder(SimpleNamespace(st_file_attributes=0x00400000))
    assert core.is_cloud_placeholder(SimpleNamespace(st_file_attributes=0x00001000))
    assert core.is_cloud_placeholder(
        SimpleNamespace(st_file_attributes=0x00400000 | 0x00001000)
    )
    assert not core.is_cloud_placeholder(SimpleNamespace(st_file_attributes=0))
    assert not core.is_cloud_placeholder(SimpleNamespace(st_file_attributes=0x20))
    # Non-Windows stat_result has no st_file_attributes → treated as local.
    assert not core.is_cloud_placeholder(SimpleNamespace())


def test_inventory_tags_cloud_only_without_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cloud-only files are counted by metadata only; never hashed/opened."""
    _mk(tmp_path / "local.txt", 10, NOW - DAY)
    _mk(tmp_path / "ghost.cloud", 50, NOW - DAY)

    # Simulate a cloud-only placeholder by size, without a real OneDrive
    # placeholder on disk (the real attribute check is unit-tested above).
    monkeypatch.setattr(
        core,
        "is_cloud_placeholder",
        lambda st: getattr(st, "st_size", 0) == 50,
    )

    inv = core.build_path_inventory(tmp_path, _config(), NOW)
    assert inv.file_count == 2
    assert inv.total_bytes == 60
    assert inv.cloud_only_count == 1
    assert inv.cloud_only_bytes == 50
    ghost = next(f for f in inv.largest_files if f.name == "ghost.cloud")
    assert ghost.cloud_only is True
    assert ghost.sha256 is None  # never hashed


# --------------------------- naming entropy ------------------------------- #


def test_naming_conventions_counted(tmp_path: Path) -> None:
    for name in (
        "My Report.docx",        # spaces, no_convention
        "my_report.txt",         # snake (underscore)
        "myReport.md",           # camelCase
        "2026-06-16_notes.md",   # dated (underscore + hyphen + embedded_date)
        "deck_v2_final_FINAL.pptx",  # version_suffix, no_convention (uppercase)
        "kebab-case-name.txt",   # kebab (hyphen)
        "plain.txt",             # plain lowercase = snake
    ):
        _mk(tmp_path / name, 3, NOW - DAY)

    nm = core.build_naming_metrics(tmp_path, _config())

    assert nm.convention_counts == {
        "spaces": 1,
        "underscore": 3,
        "hyphen": 2,
        "camelCase": 1,
        "embedded_date": 1,
        "version_suffix": 1,
    }
    assert nm.coexisting_convention_count == 6
    assert nm.no_convention_count == 2  # "My Report" and "deck_v2_final_FINAL"


def test_junk_drawers_and_generic_dirs(tmp_path: Path) -> None:
    cfg = _config(
        junk_drawer_loose_file_threshold=3,
        generic_dir_names=["new folder", "copy of", "untitled"],
    )
    for i in range(4):  # 4 > threshold of 3 -> junk drawer
        _mk(tmp_path / "loose" / f"f{i}.txt", 2, NOW - DAY)
    _mk(tmp_path / "tidy" / "only.txt", 2, NOW - DAY)
    (tmp_path / "New folder").mkdir()
    (tmp_path / "Copy of stuff").mkdir()
    (tmp_path / "Untitled").mkdir()

    nm = core.build_naming_metrics(tmp_path, cfg)

    assert any(d.endswith("/loose") for d in nm.junk_dirs)
    assert not any(d.endswith("/tidy") for d in nm.junk_dirs)
    assert sorted(Path(d).name for d in nm.generic_named) == [
        "Copy of stuff",
        "New folder",
        "Untitled",
    ]


# ---------------------------- duplication --------------------------------- #


def test_duplication_clusters_and_skips(tmp_path: Path) -> None:
    cfg = _config(scan_paths=[str(tmp_path)], hashable_size_cap_bytes=100)
    _mk(tmp_path / "a.txt", 20, NOW - DAY)
    _mk(tmp_path / "copy.txt", 20, NOW - DAY)  # byte-identical to a.txt
    _mk(tmp_path / "unique.txt", 7, NOW - DAY)
    _mk(tmp_path / "big.bin", 200, NOW - DAY)  # over cap -> not hashed
    _mk(tmp_path / "empty.txt", 0, NOW - DAY)  # empty -> not hashed

    files = core.collect_files(cfg)
    dup = core.build_duplication(files, cfg)

    assert len(dup.clusters) == 1
    cluster = dup.clusters[0]
    assert cluster.size_bytes == 20
    assert cluster.wasted_bytes == 20
    assert dup.total_wasted_bytes == 20
    assert {Path(p).name for p in cluster.paths} == {"a.txt", "copy.txt"}
    assert dup.skipped_over_cap == 1
    assert dup.skipped_cloud_only == 0


def test_collect_files_hashes_only_eligible(tmp_path: Path) -> None:
    cfg = _config(scan_paths=[str(tmp_path)], hashable_size_cap_bytes=100)
    _mk(tmp_path / "small.txt", 10, NOW - DAY)
    _mk(tmp_path / "big.bin", 200, NOW - DAY)
    _mk(tmp_path / "empty.txt", 0, NOW - DAY)
    by_name = {f.name: f for f in core.collect_files(cfg)}
    assert by_name["small.txt"].sha256 is not None
    assert by_name["big.bin"].sha256 is None
    assert by_name["empty.txt"].sha256 is None


def test_cloud_only_never_hashed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = _config(scan_paths=[str(tmp_path)])
    _mk(tmp_path / "local.txt", 10, NOW - DAY)
    _mk(tmp_path / "ghost.cloud", 50, NOW - DAY)

    calls: list[str] = []
    real = core._sha256
    monkeypatch.setattr(core, "_sha256", lambda p: calls.append(p) or real(p))
    monkeypatch.setattr(
        core, "is_cloud_placeholder", lambda st: getattr(st, "st_size", 0) == 50
    )

    files = core.collect_files(cfg)
    assert not any("ghost.cloud" in c.replace("\\", "/") for c in calls)
    ghost = next(f for f in files if f.name == "ghost.cloud")
    assert ghost.cloud_only is True and ghost.sha256 is None
    assert core.build_duplication(files, cfg).skipped_cloud_only == 1


def test_onedrive_overlap_summary(tmp_path: Path) -> None:
    cfg = _config(
        scan_paths=[str(tmp_path / "local")],
        onedrive_path=str(tmp_path / "od"),
    )
    _mk(tmp_path / "local" / "shared.txt", 30, NOW - DAY)
    _mk(tmp_path / "od" / "shared.txt", 30, NOW - DAY)  # identical content + name
    _mk(tmp_path / "od" / "onlyod.txt", 11, NOW - DAY)

    files = core.collect_files(cfg, include_onedrive=True)
    dup = core.build_duplication(files, cfg, include_onedrive=True)
    assert "onedrive_scanned=True" in dup.onedrive_overlap
    assert "by_hash=1" in dup.onedrive_overlap
    assert "by_name=1" in dup.onedrive_overlap

    not_scanned = core.build_duplication(files, cfg, include_onedrive=False)
    assert "not scanned" in not_scanned.onedrive_overlap


# --------------------------- OneDrive guard ------------------------------- #


def test_onedrive_marker_pruned_in_local_walk(tmp_path: Path) -> None:
    _mk(tmp_path / "normal.txt", 4, NOW - DAY)
    _mk(tmp_path / "OneDrive - Blue Yonder" / "secret.txt", 4, NOW - DAY)

    pruned = core.build_path_inventory(tmp_path, _config(), NOW, allow_onedrive=False)
    assert pruned.file_count == 1  # secret.txt under the marker dir is pruned
    assert pruned.dir_count == 0

    allowed = core.build_path_inventory(tmp_path, _config(), NOW, allow_onedrive=True)
    assert allowed.file_count == 2  # opt-in descends the marker dir
    assert allowed.dir_count == 1


def test_write_inventory_refuses_onedrive_destination(tmp_path: Path) -> None:
    inv = core.AuditInventory(generated_at="2026-06-16")
    ledger = core.WriteLedger()
    out = tmp_path / "OneDrive - Blue Yonder" / "x.json"
    with pytest.raises(core.OneDriveSafetyError):
        core.write_inventory(inv, out, ledger)
    assert ledger.writes == []


def test_write_inventory_refuses_overwrite_and_missing_dir(tmp_path: Path) -> None:
    inv = core.AuditInventory(generated_at="2026-06-16")
    ledger = core.WriteLedger()

    # Parent dir must already exist (tool never creates folders).
    with pytest.raises(SystemExit):
        core.write_inventory(inv, tmp_path / "nope" / "x.json", ledger)

    out = tmp_path / "x.json"
    written = core.write_inventory(inv, out, ledger)
    assert ledger.writes == [str(written).replace("\\", "/")]
    assert out.exists()

    # Second write without --force is refused; with force it succeeds.
    with pytest.raises(SystemExit):
        core.write_inventory(inv, out, core.WriteLedger())
    core.write_inventory(inv, out, core.WriteLedger(), force=True)


def test_load_config_rejects_onedrive_scan_path(tmp_path: Path) -> None:
    cfg = tmp_path / "audit.yaml"
    cfg.write_text(
        'scan_paths:\n  - "C:/Users/x/OneDrive - Blue Yonder/MyWork"\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        core.load_config(cfg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
