"""FR-10 source registry — declaration records + fail-closed schema validator.

The FR-10 *source* registry is a logical map of where valuable knowledge lives
across the SharePoint/OneDrive terrain — distinct from the routing
``ContentRegistry`` (``registry.py``, FR-3). One YAML file is the operator-hand-edited
source of truth (``config/source_registry.yaml`` — intake-16 §8.1 / D1). Every record
is anchored on the Graph **site (A1)** + **drive (A2)** identities and validated
**fail-closed**: a record missing an A1/A2 anchor or carrying an out-of-enum value is
rejected, never silently defaulted (seam F, intake-16 §4). This contrasts with the
routing registry's no-crash floor — the FR-10 registry must never admit an invalid
record.

The declaration fields here (the YAML source of truth) are disjoint from the derived
*observation* fields (``source_observation_repo.py``, ops.db, joined by ``id``) — the
intake-16 §1.3 declaration/observation split. This module performs **no I/O beyond
reading the YAML source** and never hydrates or traverses the synced OneDrive tree
(``local_hint`` is display-only; core-invariant #1).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# --- controlled vocabularies (intake-16 §1.3 / §2.2 enums) -------------------
OPERATOR_PRIORS = ("max", "high", "normal", "low", "exclude")
PHASES = ("RAW", "REGISTERED", "ESSENCE", "ARCHIVED")  # S0..S3 lifecycle (FR-12)
CURATION_LEVELS = ("golden", "ratified", "candidate")
ADDED_BY = ("operator", "scout-promotion")


class SourceRegistryError(ValueError):
    """A declaration record failed fail-closed schema validation (seam F)."""


@dataclass(frozen=True)
class SourceDeclaration:
    """One registered source — the hand-edited YAML declaration (intake-16 §1.3).

    ``site_id`` (A1) and ``drive_id`` (A2) are the hard Graph anchors; ``path_hint``
    (A3) is a soft, drift-expected hint. ``local_hint`` is a DISPLAY-ONLY OneDrive
    sync path — it is never opened or traversed (core-invariant #1).
    """

    id: str  # stable slug, permanent join key
    name: str  # human, stable
    site_id: str  # A1 — hard key
    drive_id: str  # A2 — hard key
    path_hint: str = ""  # A3 — soft, drift-expected
    web_url: str = ""  # display/convenience, regenerable from IDs
    local_hint: str = ""  # OneDrive sync path — DISPLAY-ONLY, never traversed
    what_it_holds: str = ""
    owner_team: str = ""
    dims: dict = field(default_factory=dict)  # {"industry": [...], "software": [...]}
    topics: list = field(default_factory=list)
    phase: str = "REGISTERED"
    curation_level: str = "candidate"
    operator_prior: str = "normal"
    archive_pointer: str | None = None  # S3 tombstone; NEVER a SharePoint delete
    added_by: str = "operator"


_REQUIRED = ("id", "name", "site_id", "drive_id")
_ENUMS = {
    "operator_prior": OPERATOR_PRIORS,
    "phase": PHASES,
    "curation_level": CURATION_LEVELS,
    "added_by": ADDED_BY,
}
_KNOWN_FIELDS = frozenset(f.name for f in fields(SourceDeclaration))
_STR_FIELDS = ("path_hint", "web_url", "local_hint", "what_it_holds", "owner_team")
_ALLOWED_ROOT = frozenset({"sources", "version"})
_DIMS_KEYS = frozenset({"industry", "software"})  # the two T1-bridge business dimensions


def _is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _check_field_types(rid: str, raw: dict) -> None:
    """Enforce structured/optional field types — dataclasses do NOT at runtime, so a
    ``dims: []`` or ``topics: 42`` would otherwise pass and later corrupt scoring (seam F).
    """
    for key in _STR_FIELDS:
        if key in raw and not isinstance(raw[key], str):
            raise SourceRegistryError(f"record {rid!r}: {key} must be a string")
    ap = raw.get("archive_pointer")
    if "archive_pointer" in raw and ap is not None and not isinstance(ap, str):
        raise SourceRegistryError(f"record {rid!r}: archive_pointer must be a string or null")
    if "topics" in raw and not _is_str_list(raw["topics"]):
        raise SourceRegistryError(f"record {rid!r}: topics must be a list of strings")
    if "dims" in raw:
        dims = raw["dims"]
        if not isinstance(dims, dict):
            raise SourceRegistryError(f"record {rid!r}: dims must be a mapping")
        unknown_dims = set(dims) - _DIMS_KEYS
        if unknown_dims:
            # a typo like `industy:` would be silently dropped by the scorer (mis-rank) —
            # reject it so the fail-closed contract holds for dims too.
            raise SourceRegistryError(
                f"record {rid!r}: unknown dims key(s) {sorted(unknown_dims)}; expected {sorted(_DIMS_KEYS)}"
            )
        for dk in _DIMS_KEYS:
            if dk in dims and not _is_str_list(dims[dk]):
                raise SourceRegistryError(f"record {rid!r}: dims.{dk} must be a list of strings")


def validate_declaration(raw: dict) -> SourceDeclaration:
    """Validate one raw record and return a :class:`SourceDeclaration`, fail-closed.

    Raises :class:`SourceRegistryError` when a hard anchor is missing (A1 ``site_id``
    or A2 ``drive_id``, or ``id``/``name``), an enum field is out of its vocabulary, or
    an unknown field is present. Nothing is silently defaulted for these — the record is
    rejected (seam F). Optional fields fall back to their declared defaults.
    """
    if not isinstance(raw, dict):
        raise SourceRegistryError(f"record must be a mapping, got {type(raw).__name__}")
    rid = raw.get("id", "<no-id>")
    for key in _REQUIRED:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SourceRegistryError(f"record {rid!r}: missing/empty required field {key!r}")
    for key, allowed in _ENUMS.items():
        if key in raw and raw[key] not in allowed:
            raise SourceRegistryError(f"record {rid!r}: {key}={raw[key]!r} not in {allowed}")
    unknown = set(raw) - _KNOWN_FIELDS
    if unknown:
        raise SourceRegistryError(f"record {rid!r}: unknown field(s) {sorted(unknown)}")
    _check_field_types(rid, raw)
    return SourceDeclaration(**raw)


def to_dict(decl: SourceDeclaration) -> dict:
    """Canonical dict serialization (stable field order) — the round-trip for seam F."""
    return {f.name: getattr(decl, f.name) for f in fields(SourceDeclaration)}


def load_source_registry(path: Path) -> list[SourceDeclaration]:
    """Load + validate every declaration from the YAML source of truth (fail-closed).

    A missing file yields an empty list (no sources registered yet). A malformed YAML
    root, a bad record, or a duplicate ``id`` raises :class:`SourceRegistryError` — the
    FR-10 registry never silently drops an invalid record the way the routing floor does.
    """
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SourceRegistryError("source registry root must be a mapping with a 'sources' list")
    unknown_root = set(data) - _ALLOWED_ROOT
    if unknown_root:
        # a misspelled `source:` must NOT silently load an empty registry (fail-closed)
        raise SourceRegistryError(f"unknown registry root key(s) {sorted(unknown_root)}; expected 'sources'")
    if data and "sources" not in data:
        raise SourceRegistryError("a non-empty registry must define a 'sources' list")
    raw_sources = data.get("sources", [])
    if not isinstance(raw_sources, list):
        raise SourceRegistryError("'sources' must be a list")
    records = [validate_declaration(r) for r in raw_sources]
    ids = [r.id for r in records]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SourceRegistryError(f"duplicate source id(s): {dupes}")
    return records


def get_source_registry_path() -> Path:
    """Default ``config/source_registry.yaml`` path (intake-16 §8.1 / D1)."""
    from corp.config import get_config

    return get_config().repo_path / "config" / "source_registry.yaml"
