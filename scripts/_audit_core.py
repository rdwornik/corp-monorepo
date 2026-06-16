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
import hashlib
import heapq
import json
import logging
import os
import re
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
    "HashedFile",
    "build_duplication",
    "build_inventory",
    "build_naming_metrics",
    "build_path_inventory",
    "build_sot_violations",
    "collect_files",
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
class HashedFile:
    """One file in the dedup/source-of-truth index. ``sha256`` is None when the
    file was not hashed (cloud-only, over the size cap, or empty)."""

    path: str
    name: str
    size_bytes: int
    sha256: str | None
    cloud_only: bool
    is_onedrive: bool


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
        inv.naming.append(
            build_naming_metrics(root, config, allow_onedrive=allow)
        )
    files = collect_files(config, include_onedrive=include_onedrive)
    inv.duplication = build_duplication(
        files, config, include_onedrive=include_onedrive
    )
    inv.sot_violations = build_sot_violations(files)
    return inv


# --------------------------------------------------------------------------- #
# Naming-entropy metrics (Step 3).
# --------------------------------------------------------------------------- #

# Clean recognized schemes (a stem matching any of these is "conventional").
_SNAKE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CAMEL_RE = re.compile(r"^[a-z]+(?:[A-Z][a-z0-9]*)+$")
_DATED_PREFIX_RE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?[ _-]")

# Signal patterns (a file may exhibit several at once).
_DATE_RE = re.compile(r"(?:\d{4}[-_]\d{2}[-_]\d{2})|(?:\b\d{8}\b)|(?:\d{4}[-_]\d{2}\b)")
_VERSION_RE = re.compile(
    r"(?i)(?:_v\d+|[ _-](?:final|copy|draft|backup|bak|old|new)\b|\(\d+\)|"
    r"final[ _-]?final)"
)

_NAMING_SIGNALS = (
    "spaces",
    "underscore",
    "hyphen",
    "camelCase",
    "embedded_date",
    "version_suffix",
)


def _classify_name(stem: str, full_name: str) -> dict[str, bool]:
    """Return naming signals + a ``no_convention`` flag for one filename."""
    is_camel = bool(_CAMEL_RE.match(stem))
    conventional = bool(
        _SNAKE_RE.match(stem)
        or _KEBAB_RE.match(stem)
        or is_camel
        or _DATED_PREFIX_RE.match(full_name)
    )
    return {
        "spaces": " " in stem,
        "underscore": "_" in stem,
        "hyphen": "-" in stem,
        "camelCase": is_camel,
        "embedded_date": bool(_DATE_RE.search(full_name)),
        "version_suffix": bool(_VERSION_RE.search(stem)),
        "no_convention": not conventional,
    }


def build_naming_metrics(
    root: Path,
    config: AuditConfig,
    *,
    allow_onedrive: bool = False,
) -> NamingMetrics:
    """Naming-entropy metrics for one root: coexisting conventions + junk drawers."""
    nm = NamingMetrics(scan_path=_norm(root))
    if not root.exists():
        return nm
    signals = {key: 0 for key in _NAMING_SIGNALS}
    loose_counts: dict[str, int] = {}
    generic: list[str] = []
    generic_fragments = [frag.lower() for frag in config.generic_dir_names]
    for entry, _depth, is_dir in walk_tree(
        root, config.exclude_dirs, allow_onedrive=allow_onedrive
    ):
        if is_dir:
            low = entry.name.lower()
            if any(frag in low for frag in generic_fragments):
                generic.append(_norm(entry.path))
            continue
        parent = _norm(os.path.dirname(entry.path))
        loose_counts[parent] = loose_counts.get(parent, 0) + 1
        flags = _classify_name(Path(entry.name).stem, entry.name)
        for key in _NAMING_SIGNALS:
            if flags[key]:
                signals[key] += 1
        if flags["no_convention"]:
            nm.no_convention_count += 1
    nm.convention_counts = {key: val for key, val in signals.items() if val}
    nm.coexisting_convention_count = len(nm.convention_counts)
    threshold = config.junk_drawer_loose_file_threshold
    nm.junk_dirs = sorted(d for d, c in loose_counts.items() if c > threshold)
    nm.generic_named = sorted(generic)
    return nm


# --------------------------------------------------------------------------- #
# Content hashing, duplication, OneDrive overlap (Step 4).
# --------------------------------------------------------------------------- #


def _sha256(path: str, chunk: int = 8192) -> str:
    """Streaming SHA-256 (mirrors corp.extraction.vault_writer._file_hash)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_files(
    config: AuditConfig,
    *,
    include_onedrive: bool = False,
) -> list[HashedFile]:
    """Index every file across all roots, hashing ONLY eligible local files.

    A file is hashed only when it is not a cloud placeholder and its size is in
    ``(0, hashable_size_cap_bytes]`` — cloud-only files are never opened (no
    hydration), and over-cap/empty files are left with ``sha256 = None``.
    """
    roots: list[tuple[Path, bool]] = [(Path(p), False) for p in config.scan_paths]
    if include_onedrive and config.onedrive_path:
        roots.append((Path(config.onedrive_path), True))
    cap = config.hashable_size_cap_bytes
    out: list[HashedFile] = []
    for root, is_onedrive in roots:
        if not root.exists():
            continue
        for entry, _depth, is_dir in walk_tree(
            root, config.exclude_dirs, allow_onedrive=is_onedrive
        ):
            if is_dir:
                continue
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            size = st.st_size
            cloud = is_cloud_placeholder(st)
            digest: str | None = None
            if not cloud and 0 < size <= cap:
                try:
                    digest = _sha256(_long_path(entry.path))
                except OSError as exc:
                    log.warning("hash failed %s: %s", entry.path, exc)
            out.append(
                HashedFile(
                    path=_norm(entry.path),
                    name=entry.name,
                    size_bytes=size,
                    sha256=digest,
                    cloud_only=cloud,
                    is_onedrive=is_onedrive,
                )
            )
    return out


def build_duplication(
    files: list[HashedFile],
    config: AuditConfig,
    *,
    include_onedrive: bool = False,
) -> DuplicationReport:
    """Exact-duplicate clusters (by content hash) + OneDrive overlap summary."""
    report = DuplicationReport()
    by_hash: dict[str, list[HashedFile]] = {}
    for f in files:
        if f.sha256 is not None:
            by_hash.setdefault(f.sha256, []).append(f)

    for digest, group in by_hash.items():
        if len(group) < 2:
            continue
        size = group[0].size_bytes
        report.clusters.append(
            DupCluster(
                sha256=digest,
                size_bytes=size,
                paths=tuple(sorted(f.path for f in group)),
                wasted_bytes=(len(group) - 1) * size,
            )
        )
    report.clusters.sort(key=lambda c: (-c.wasted_bytes, c.sha256))
    report.total_wasted_bytes = sum(c.wasted_bytes for c in report.clusters)
    cap = config.hashable_size_cap_bytes
    report.skipped_cloud_only = sum(1 for f in files if f.cloud_only)
    report.skipped_over_cap = sum(
        1 for f in files if not f.cloud_only and f.size_bytes > cap
    )
    report.onedrive_overlap = _overlap_summary(files, include_onedrive)
    return report


def _overlap_summary(files: list[HashedFile], include_onedrive: bool) -> str:
    if not include_onedrive:
        return (
            "OneDrive mirror not scanned (run --include-onedrive); see "
            "corp.cleanup.disk.find_onedrive_overlap for the local<->synced map."
        )
    od_hashes = {f.sha256 for f in files if f.is_onedrive and f.sha256}
    local_hashes = {f.sha256 for f in files if not f.is_onedrive and f.sha256}
    shared_hashes = od_hashes & local_hashes
    size_by_hash = {f.sha256: f.size_bytes for f in files if f.sha256}
    dup_bytes = sum(size_by_hash.get(h, 0) for h in shared_hashes)
    od_names = {f.name for f in files if f.is_onedrive}
    local_names = {f.name for f in files if not f.is_onedrive}
    shared_names = od_names & local_names
    return (
        f"onedrive_scanned=True; by_hash={len(shared_hashes)} files "
        f"(~{dup_bytes} B duplicated across trees); "
        f"by_name={len(shared_names)} shared filenames"
    )


# --------------------------------------------------------------------------- #
# Source-of-truth violations (Step 5).
# --------------------------------------------------------------------------- #

# Filenames that legitimately recur across directories (not SoT violations).
_SOT_NAME_IGNORE: frozenset[str] = frozenset(
    {
        "__init__.py",
        "__main__.py",
        "conftest.py",
        "setup.py",
        "py.typed",
        "readme.md",
        "readme.txt",
        "index.md",
        "license",
        "license.md",
        "changelog.md",
        "makefile",
        "dockerfile",
        ".gitignore",
        ".gitkeep",
        ".gitattributes",
        ".ds_store",
        "thumbs.db",
    }
)


def build_sot_violations(files: list[HashedFile]) -> list[SourceOfTruthViolation]:
    """Flag files that look authoritative in more than one location.

    ``by_hash``: identical content (same SHA-256) in >= 2 distinct directories.
    ``by_name``: same filename in >= 2 distinct directories (content may differ),
    excluding ubiquitous framework filenames.
    """
    violations: list[SourceOfTruthViolation] = []

    hash_paths: dict[str, set[str]] = {}
    for f in files:
        if f.sha256 is not None:
            hash_paths.setdefault(f.sha256, set()).add(f.path)
    for digest, paths in hash_paths.items():
        if len({os.path.dirname(p) for p in paths}) >= 2:
            violations.append(
                SourceOfTruthViolation(
                    key=digest, kind="by_hash", locations=tuple(sorted(paths))
                )
            )

    name_paths: dict[str, set[str]] = {}
    for f in files:
        if f.name.lower() in _SOT_NAME_IGNORE:
            continue
        name_paths.setdefault(f.name, set()).add(f.path)
    for name, paths in name_paths.items():
        if len({os.path.dirname(p) for p in paths}) >= 2:
            violations.append(
                SourceOfTruthViolation(
                    key=name, kind="by_name", locations=tuple(sorted(paths))
                )
            )

    violations.sort(key=lambda v: (v.kind, -len(v.locations), v.key))
    return violations


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
