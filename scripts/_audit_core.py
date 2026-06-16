"""Core logic for the read-only current-state architecture audit.

Pure, testable functions + dataclasses for ``scripts/current_state_audit.py``.
This module is **read-only by construction**: it reads filesystem metadata via
``os.scandir``/``os.stat`` and (in later steps) streams file content for hashing.
Its ONLY write is :func:`write_inventory` — the single guarded write sink, which
is whitelisted by ``tests/safety/test_audit_readonly_invariant.py``.

Safety reuse (single source of truth — imported, not copied, to prevent drift):
  * ``corp.cleanup.disk._guard_onedrive`` — fail-closed synced-tree write guard.
  * ``corp.cleanup.errors.OneDriveSafetyError`` — raised by the guard.

Placeholder detection (:func:`is_cloud_placeholder`) checks the Windows file
attributes ``FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`` (0x00400000) and
``FILE_ATTRIBUTE_OFFLINE`` (0x1000); precedent: ``corp.cleanup.disk._is_real_file``
(disk.py:179). Reading ``st_file_attributes`` does NOT hydrate a cloud-only file.
"""

from __future__ import annotations

import dataclasses
import heapq
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

from corp.cleanup.disk import _guard_onedrive
from corp.cleanup.errors import OneDriveSafetyError

log = logging.getLogger("current_state_audit")

# OneDriveSafetyError is re-exported so the CLI can catch it without importing
# from corp directly (keeps corp's import surface in one place).
__all__ = [
    "AuditConfig",
    "AuditInventory",
    "DupCluster",
    "DuplicationReport",
    "FileEntry",
    "NamingMetrics",
    "OneDriveSafetyError",
    "PathInventory",
    "RepoAutomation",
    "SourceOfTruthViolation",
    "WriteLedger",
    "build_inventory",
    "build_path_inventory",
    "is_cloud_placeholder",
    "iter_entries",
    "load_config",
    "to_serializable",
    "walk_tree",
    "write_inventory",
]

# Substring that marks the protected synced tree (mirrors disk.py:24).
ONEDRIVE_MARKER = "OneDrive - Blue Yonder"

# Windows file attributes signalling a cloud-only placeholder (no local content).
FILE_ATTRIBUTE_OFFLINE = 0x00001000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
_CLOUD_ONLY_MASK = FILE_ATTRIBUTE_OFFLINE | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS


# --------------------------------------------------------------------------- #
# Dataclasses — the inventory schema (serialized to JSON for the gap report).
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FileEntry:
    """A single inventoried file. ``sha256`` is set only for hashed local files."""

    path: str
    name: str
    ext: str
    size_bytes: int
    mtime: float
    depth: int
    cloud_only: bool
    sha256: str | None = None


@dataclass
class PathInventory:
    """Aggregate inventory for one scanned root (Step 2)."""

    scan_path: str
    exists: bool = True
    file_count: int = 0
    dir_count: int = 0
    total_bytes: int = 0
    cloud_only_count: int = 0
    cloud_only_bytes: int = 0
    hashed_count: int = 0
    depth_histogram: dict[int, int] = field(default_factory=dict)
    ext_histogram: dict[str, int] = field(default_factory=dict)
    mtime_buckets: dict[str, int] = field(default_factory=dict)
    largest_files: list[FileEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class NamingMetrics:
    """Naming-entropy metrics for one scanned root (Step 3)."""

    scan_path: str
    convention_counts: dict[str, int] = field(default_factory=dict)
    no_convention_count: int = 0
    coexisting_convention_count: int = 0
    junk_dirs: list[str] = field(default_factory=list)
    generic_named: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DupCluster:
    """A set of byte-identical files (Step 4)."""

    sha256: str
    size_bytes: int
    paths: tuple[str, ...]
    wasted_bytes: int


@dataclass
class DuplicationReport:
    """Exact-duplicate clusters + OneDrive overlap (Step 4)."""

    clusters: list[DupCluster] = field(default_factory=list)
    total_wasted_bytes: int = 0
    onedrive_overlap: str = ""
    skipped_cloud_only: int = 0
    skipped_over_cap: int = 0


@dataclass(frozen=True)
class SourceOfTruthViolation:
    """Same file authoritative in more than one location (Step 5)."""

    key: str
    kind: str  # "by_hash" | "by_name"
    locations: tuple[str, ...]


@dataclass
class RepoAutomation:
    """Automation inventory for one sibling repo (Step 6)."""

    repo: str
    entry_points: list[str] = field(default_factory=list)
    write_targets: list[str] = field(default_factory=list)
    schedulers: list[str] = field(default_factory=list)
    model_routing: list[str] = field(default_factory=list)
    layer_candidates: list[str] = field(default_factory=list)


@dataclass
class AuditInventory:
    """Top-level deterministic inventory — serialized to the JSON artifact."""

    generated_at: str
    scan_paths: list[str] = field(default_factory=list)
    onedrive_included: bool = False
    inventories: list[PathInventory] = field(default_factory=list)
    naming: list[NamingMetrics] = field(default_factory=list)
    duplication: DuplicationReport | None = None
    sot_violations: list[SourceOfTruthViolation] = field(default_factory=list)
    automation: list[RepoAutomation] = field(default_factory=list)
    write_ledger: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class AuditConfig:
    """Parsed ``config/audit.yaml``."""

    scan_paths: list[str]
    onedrive_path: str
    exclude_dirs: list[str]
    hashable_size_cap_bytes: int
    junk_drawer_loose_file_threshold: int
    generic_dir_names: list[str]
    largest_files_top_n: int
    output_dir: str
    dev_root: str


# --------------------------------------------------------------------------- #
# Config loading.
# --------------------------------------------------------------------------- #


def load_config(config_path: Path) -> AuditConfig:
    """Load and validate ``audit.yaml``.

    Fail-closed: any always-on ``scan_paths`` entry containing the OneDrive
    marker is rejected (the only synced path the tool may read is the explicit
    ``onedrive_path``, and only under ``--include-onedrive``).
    """
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    scan_paths = [str(p) for p in data.get("scan_paths", [])]
    for p in scan_paths:
        if ONEDRIVE_MARKER in p:
            raise SystemExit(
                f"audit.yaml: scan_paths entry must not be a synced tree: {p!r}"
            )
    return AuditConfig(
        scan_paths=scan_paths,
        onedrive_path=str(data.get("onedrive_path", "")),
        exclude_dirs=[str(d) for d in data.get("exclude_dirs", [])],
        hashable_size_cap_bytes=int(data.get("hashable_size_cap_bytes", 52428800)),
        junk_drawer_loose_file_threshold=int(
            data.get("junk_drawer_loose_file_threshold", 40)
        ),
        generic_dir_names=[str(n) for n in data.get("generic_dir_names", [])],
        largest_files_top_n=int(data.get("largest_files_top_n", 20)),
        output_dir=str(data.get("output_dir", "docs/audits")),
        dev_root=str(data.get("dev_root", "")),
    )


# --------------------------------------------------------------------------- #
# Read-only traversal + placeholder detection.
# --------------------------------------------------------------------------- #


def _long_path(path_str: str) -> str:
    """Return a Windows extended-length path for deep trees, else unchanged."""
    if os.name != "nt":
        return path_str
    abs_path = os.path.abspath(path_str)
    if len(abs_path) < 240 or abs_path.startswith("\\\\?\\"):
        return abs_path
    if abs_path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + abs_path[2:]
    return "\\\\?\\" + abs_path


def is_cloud_placeholder(st: os.stat_result) -> bool:
    """True if ``st`` describes a cloud-only placeholder (no local content).

    Size-independent (unlike ``disk.py::_is_real_file``, which also rejects
    empty files). Reading the attribute does not hydrate the file.
    """
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & _CLOUD_ONLY_MASK)


def walk_tree(
    root: Path,
    exclude_dirs: list[str],
    *,
    allow_onedrive: bool = False,
) -> Iterator[tuple[os.DirEntry, int, bool]]:
    """Yield ``(DirEntry, depth, is_dir)`` for every entry under ``root``.

    The single read-only, hydration-safe traversal used by all metrics:
      * ``follow_symlinks=False`` — junctions/symlinks are never traversed.
      * Directories whose path contains the OneDrive marker are pruned unless
        ``allow_onedrive`` (set only for the explicit OneDrive root scan).
      * Every ``OSError``/``PermissionError`` is swallowed (partial inventory).

    Reads metadata only; never opens file content (no hydration).
    """
    excluded = {d.lower() for d in exclude_dirs}
    stack: list[tuple[str, int]] = [(str(root), 0)]
    while stack:
        current, depth = stack.pop()
        try:
            with os.scandir(_long_path(current)) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name.lower() in excluded:
                                continue
                            if not allow_onedrive and ONEDRIVE_MARKER in entry.path:
                                continue
                            yield entry, depth + 1, True
                            stack.append((entry.path, depth + 1))
                        elif entry.is_file(follow_symlinks=False):
                            yield entry, depth + 1, False
                    except OSError:
                        continue
        except (OSError, PermissionError) as exc:
            log.warning("scandir skipped %s: %s", current, exc)


def iter_entries(
    root: Path,
    exclude_dirs: list[str],
    *,
    allow_onedrive: bool = False,
) -> Iterator[tuple[os.DirEntry, int]]:
    """Yield ``(DirEntry, depth)`` for files only (thin wrapper over walk_tree)."""
    for entry, depth, is_dir in walk_tree(
        root, exclude_dirs, allow_onedrive=allow_onedrive
    ):
        if not is_dir:
            yield entry, depth


# --------------------------------------------------------------------------- #
# Per-root filesystem inventory (Step 2). Metadata only — no hashing here.
# --------------------------------------------------------------------------- #

_SECONDS_PER_DAY = 86400.0


def _ext_of(name: str) -> str:
    """Lowercased file extension, or ``<none>`` for extensionless files."""
    suffix = Path(name).suffix.lower()
    return suffix if suffix else "<none>"


def _mtime_bucket(mtime: float, now_ts: float) -> str:
    """Bucket a file's age (days since last modification)."""
    age_days = (now_ts - mtime) / _SECONDS_PER_DAY
    if age_days <= 30:
        return "<=30d"
    if age_days <= 180:
        return "31-180d"
    if age_days <= 365:
        return "181-365d"
    return ">365d"


def build_path_inventory(
    root: Path,
    config: AuditConfig,
    now_ts: float,
    *,
    allow_onedrive: bool = False,
) -> PathInventory:
    """Full inventory for one root: counts, histograms, largest files.

    Cloud-only placeholders are tagged via :func:`is_cloud_placeholder` and
    counted, but never hashed/opened (hashing arrives in Step 4). Reads metadata
    only — no hydration.
    """
    inv = PathInventory(scan_path=_norm(root))
    if not root.exists():
        inv.exists = False
        return inv
    top_n = config.largest_files_top_n
    heap: list[tuple[int, int, FileEntry]] = []
    idx = 0
    for entry, depth, is_dir in walk_tree(
        root, config.exclude_dirs, allow_onedrive=allow_onedrive
    ):
        if is_dir:
            inv.dir_count += 1
            continue
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError as exc:
            inv.errors.append(f"stat failed: {_norm(entry.path)}: {exc}")
            continue
        size = st.st_size
        cloud = is_cloud_placeholder(st)
        ext = _ext_of(entry.name)
        inv.file_count += 1
        inv.total_bytes += size
        inv.depth_histogram[depth] = inv.depth_histogram.get(depth, 0) + 1
        inv.ext_histogram[ext] = inv.ext_histogram.get(ext, 0) + 1
        bucket = _mtime_bucket(st.st_mtime, now_ts)
        inv.mtime_buckets[bucket] = inv.mtime_buckets.get(bucket, 0) + 1
        if cloud:
            inv.cloud_only_count += 1
            inv.cloud_only_bytes += size
        if top_n > 0:
            fe = FileEntry(
                path=_norm(entry.path),
                name=entry.name,
                ext=ext,
                size_bytes=size,
                mtime=st.st_mtime,
                depth=depth,
                cloud_only=cloud,
            )
            if len(heap) < top_n:
                heapq.heappush(heap, (size, idx, fe))
                idx += 1
            elif size > heap[0][0]:
                heapq.heapreplace(heap, (size, idx, fe))
                idx += 1
    inv.largest_files = [fe for _, _, fe in sorted(heap, key=lambda t: (-t[0], t[1]))]
    return inv


def build_inventory(
    config: AuditConfig,
    generated_at: str,
    now_ts: float,
    *,
    include_onedrive: bool = False,
) -> AuditInventory:
    """Assemble the full inventory across all scanned roots."""
    roots: list[tuple[Path, bool]] = [(Path(p), False) for p in config.scan_paths]
    if include_onedrive and config.onedrive_path:
        roots.append((Path(config.onedrive_path), True))
    inv = AuditInventory(
        generated_at=generated_at,
        scan_paths=[_norm(p) for p, _ in roots],
        onedrive_included=include_onedrive,
    )
    for root, allow in roots:
        inv.inventories.append(
            build_path_inventory(root, config, now_ts, allow_onedrive=allow)
        )
    return inv


# --------------------------------------------------------------------------- #
# The single write sink — the ONLY mutation in this tool.
# --------------------------------------------------------------------------- #


@dataclass
class WriteLedger:
    """Records every path written, so the run can assert it wrote only the JSON."""

    writes: list[str] = field(default_factory=list)

    def record(self, path: Path | str) -> None:
        self.writes.append(_norm(path))


def write_inventory(
    inventory: AuditInventory,
    out_path: Path,
    ledger: WriteLedger,
    *,
    force: bool = False,
) -> Path:
    """Serialize ``inventory`` to ``out_path`` (JSON). The tool's sole write.

    Guards: OneDrive-synced destinations are refused (fail-closed); the parent
    dir must already exist (the tool never creates folders); an existing file is
    not overwritten unless ``force``.
    """
    resolved = out_path.resolve(strict=False)
    _guard_onedrive(resolved)
    if not resolved.parent.is_dir():
        raise SystemExit(
            f"Output dir must already exist (tool never creates folders): "
            f"{resolved.parent}"
        )
    if resolved.exists() and not force:
        raise SystemExit(
            f"Refusing to overwrite existing inventory (pass --force): {resolved}"
        )
    ledger.record(resolved)
    inventory.write_ledger = list(ledger.writes)
    payload = json.dumps(to_serializable(inventory), indent=2, ensure_ascii=False)
    resolved.write_text(payload, encoding="utf-8")
    return resolved


def to_serializable(inventory: AuditInventory) -> dict:
    """Convert the inventory dataclass tree to JSON-ready primitives."""
    return dataclasses.asdict(inventory)


def _norm(path: Path | str) -> str:
    """Forward-slash normalized string form (repo convention: forward slashes)."""
    return str(path).replace("\\", "/")
