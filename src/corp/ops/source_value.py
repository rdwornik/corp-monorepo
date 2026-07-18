"""FR-10 deterministic source-value scorer (intake-16 §2) — DAY-1, learning-free.

A **pure deterministic** function of registry-visible signals: identical inputs always
produce an identical score. No randomness, no learned parameter, no model, no I/O, and no
content hydration or OneDrive traversal — the caller supplies one frozen Graph-metadata
snapshot (this story makes ZERO Graph calls; seeds + the live resolver are #40/#36).

This module carries the eight components and their composition (§2.2) and the single-pass
neighbour prior (§2.3). Every score records its ``weights_version`` (intake-16 §8.1, ruling
F1 — a single field; the design body's "score_version" mentions denote the same concept and
are unified into ``weights_version``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

# --- v1 weight-set (intake-16 §2.2; equal yield weights, D5 pick) ------------
WEIGHTS_VERSION = "v1"

# v1 composition constants (§2.2 two-level mixing; recalibration bumps WEIGHTS_VERSION)
_I_YIELD, _I_CURATION, _I_OPERATOR = 0.60, 0.20, 0.20  # intrinsic mix
_FINAL_INTRINSIC, _FINAL_NEIGHBOUR = 0.85, 0.15  # final mix

_TYPE_WEIGHTS = {
    # recording / audio / video -> 1.00
    ".mp4": 1.00, ".mov": 1.00, ".avi": 1.00, ".mkv": 1.00, ".webm": 1.00,
    ".mp3": 1.00, ".wav": 1.00, ".m4a": 1.00, ".aac": 1.00,
    # slides -> 0.90
    ".pptx": 0.90, ".ppt": 0.90,
    # documents -> 0.70
    ".docx": 0.70, ".doc": 0.70, ".pdf": 0.70,
    # spreadsheets -> 0.40
    ".xlsx": 0.40, ".xls": 0.40,
}
_TYPE_OTHER = 0.20

_CURATION_VALUES = {"golden": 1.00, "ratified": 0.75, "candidate": 0.25}
_OPERATOR_PRIOR_VALUES = {
    "max": 1.00, "high": 0.75, "normal": 0.50, "low": 0.25, "exclude": 0.00,
}
_NEUTRAL = 0.50


@dataclass(frozen=True)
class ChildItem:
    """One directly-listed Graph child (metadata only — no content)."""

    name: str
    is_folder: bool = False
    extension: str = ""  # normalized lowercase incl. dot; "" for folders/unknown
    last_modified: datetime | None = None


@dataclass(frozen=True)
class MetadataSnapshot:
    """One frozen, direct-child metadata listing for a registered source (§2.2)."""

    location_name: str = ""
    children: tuple[ChildItem, ...] = ()


def _type_weight(extension: str) -> float:
    ext = extension.lower()
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    return _TYPE_WEIGHTS.get(ext, _TYPE_OTHER)


def component_density(docs: int, folders: int) -> float:
    """D — document density (§2.2): ``0`` for an empty listing."""
    if docs <= 0:
        return 0.0
    return (docs / (docs + folders)) * min(1.0, math.log(1 + docs) / math.log(64))


def component_recency(ages_days: list[float]) -> float:
    """R — recency (§2.2): mean of ``2^(-age/180)`` over docs; ``0`` when none."""
    if not ages_days:
        return 0.0
    return sum(2.0 ** (-age / 180.0) for age in ages_days) / len(ages_days)


def component_type_value(extensions: list[str]) -> float:
    """T — type value (§2.2): mean per-document type weight; ``0`` when no docs."""
    if not extensions:
        return 0.0
    return sum(_type_weight(e) for e in extensions) / len(extensions)


def component_match(tokens: list[str], haystack_names: list[str]) -> float:
    """M — dim/topic match (§2.2): matched fraction; neutral ``0.50`` with no terms."""
    if not tokens:
        return _NEUTRAL
    hay = " ".join(haystack_names).lower()
    found = sum(1 for t in tokens if t.lower() in hay)
    return found / len(tokens)


def component_uniqueness(duplicate_rate: float | None) -> float:
    """U — uniqueness (§2.2): ``1 - duplicate_rate``; neutral ``0.50`` until sampled."""
    if duplicate_rate is None:
        return _NEUTRAL
    return max(0.0, min(1.0, 1.0 - duplicate_rate))


def component_curation(curation_level: str) -> float:
    """C — curation (§2.2): golden 1.00 / ratified 0.75 / candidate 0.25."""
    return _CURATION_VALUES.get(curation_level, 0.25)


def component_operator_prior(operator_prior: str) -> float:
    """O — operator prior (§2.2): max 1.00 .. exclude 0.00."""
    return _OPERATOR_PRIOR_VALUES.get(operator_prior, _NEUTRAL)


def _match_tokens(dims: dict, topics: list) -> list[str]:
    """The normalized dim/topic token set (industry + software + topics)."""
    dims = dims or {}
    return [*dims.get("industry", []), *dims.get("software", []), *(topics or [])]


def compute_components(
    dims: dict,
    topics: list,
    curation_level: str,
    operator_prior: str,
    snapshot: MetadataSnapshot,
    *,
    score_as_of: datetime,
    duplicate_rate: float | None = None,
) -> dict[str, float]:
    """The seven yield/intrinsic components {D,R,T,M,U,C,O} for one record (§2.2).

    All values are in ``[0,1]``, computed from the frozen ``snapshot`` + registry state
    only — no hydration, no traversal. ``score_as_of`` is the snapshot instant used for
    the recency ages, so the result is a pure function of its inputs.
    """
    docs = [c for c in snapshot.children if not c.is_folder]
    folders = [c for c in snapshot.children if c.is_folder]
    ages = [
        max(0.0, (score_as_of - c.last_modified).total_seconds() / 86400.0)
        for c in docs
        if c.last_modified is not None
    ]
    haystack = [snapshot.location_name, *(c.name for c in snapshot.children)]
    return {
        "D": component_density(len(docs), len(folders)),
        "R": component_recency(ages),
        "T": component_type_value([c.extension for c in docs]),
        "M": component_match(_match_tokens(dims, topics), haystack),
        "U": component_uniqueness(duplicate_rate),
        "C": component_curation(curation_level),
        "O": component_operator_prior(operator_prior),
    }


@dataclass(frozen=True)
class ValueScore:
    """The deterministic §2.2 score struct — always explainable and reproducible.

    ``components`` carries the full breakdown ({D,R,T,M,U,C,O} + derived Y/I/N).
    ``weights_version`` is the SINGLE version field (ruling F1 — the design body's
    "score_version" is the same concept, unified here). ``score_as_of`` is the ISO
    snapshot instant the score was computed against.
    """

    score: int  # 0..100, round-half-up (ruling F2)
    components: dict
    weights_version: str
    score_as_of: str


def round_half_up(value: float) -> int:
    """Round to the nearest integer, halves UP (ruling F2 — NOT banker's rounding).

    Implemented via ``Decimal`` with ``ROUND_HALF_UP`` for reproducibility: Python's
    built-in ``round`` is round-half-to-even, so ``round(2.5) == 2`` — rejected here.
    ``Decimal(str(value))`` uses the float's deterministic shortest repr, so identical
    inputs always yield an identical integer (guards the seam-G golden vector).
    """
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compose_score(
    components: dict[str, float],
    neighbour: float,
    *,
    score_as_of: datetime,
) -> ValueScore:
    """Compose the two-level §2.2 score: yield -> intrinsic -> neighbour-adjusted final.

    ``Y = mean(D,R,T,M,U)`` (equal weights) -> ``I = 0.60Y + 0.20C + 0.20O`` ->
    ``value_score = round-half-up(100 * (0.85I + 0.15N))``. ``neighbour`` (N) is supplied
    by the single-pass neighbour pass (§2.3); a lone record uses the neutral ``0.50``.
    """
    yield_ = (
        components["D"] + components["R"] + components["T"]
        + components["M"] + components["U"]
    ) / 5.0
    intrinsic = _I_YIELD * yield_ + _I_CURATION * components["C"] + _I_OPERATOR * components["O"]
    final = 100.0 * (_FINAL_INTRINSIC * intrinsic + _FINAL_NEIGHBOUR * neighbour)
    breakdown = {**components, "Y": yield_, "I": intrinsic, "N": neighbour}
    return ValueScore(
        score=round_half_up(final),
        components=breakdown,
        weights_version=WEIGHTS_VERSION,
        score_as_of=score_as_of.isoformat(timespec="seconds"),
    )


def score_record(
    dims: dict,
    topics: list,
    curation_level: str,
    operator_prior: str,
    snapshot: MetadataSnapshot,
    *,
    score_as_of: datetime,
    neighbour: float = _NEUTRAL,
    duplicate_rate: float | None = None,
) -> ValueScore:
    """Pure end-to-end score for one record: components (§2.2) then composition.

    ``neighbour`` defaults to the neutral prior; the caller's single-pass neighbour
    computation (§2.3, ``rank``/neighbour helpers) overrides it. No I/O, no hydration.
    """
    components = compute_components(
        dims, topics, curation_level, operator_prior, snapshot,
        score_as_of=score_as_of, duplicate_rate=duplicate_rate,
    )
    return compose_score(components, neighbour, score_as_of=score_as_of)
