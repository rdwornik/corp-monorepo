"""FR-10 deterministic scorer tests (intake-16 §2).

Step 2 covers the eight components {D,R,T,M,U,C,O} in isolation (§2.2). Composition
(seam G golden vector) and the single-pass neighbour prior (seam H) are added alongside.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from corp.ops.source_value import (
    ChildItem,
    MetadataSnapshot,
    component_curation,
    component_density,
    component_match,
    component_operator_prior,
    component_recency,
    component_type_value,
    component_uniqueness,
    compute_components,
)

_AS_OF = datetime(2026, 7, 1, 12, 0, 0)


class TestComponentDensity:
    def test_empty_listing_is_zero(self) -> None:
        assert component_density(0, 0) == 0.0
        assert component_density(0, 5) == 0.0

    def test_saturates_at_64_docs(self) -> None:
        assert component_density(63, 0) == pytest.approx(1.0)

    def test_single_doc(self) -> None:
        assert component_density(1, 0) == pytest.approx(math.log(2) / math.log(64))

    def test_folders_dilute_density(self) -> None:
        assert component_density(2, 2) == pytest.approx(0.5 * math.log(3) / math.log(64))


class TestComponentRecency:
    def test_no_docs_is_zero(self) -> None:
        assert component_recency([]) == 0.0

    def test_brand_new_is_one(self) -> None:
        assert component_recency([0.0]) == pytest.approx(1.0)

    def test_half_life_is_180_days(self) -> None:
        assert component_recency([180.0]) == pytest.approx(0.5)

    def test_mean_over_docs(self) -> None:
        assert component_recency([0.0, 180.0]) == pytest.approx(0.75)


class TestComponentTypeValue:
    def test_no_docs_is_zero(self) -> None:
        assert component_type_value([]) == 0.0

    @pytest.mark.parametrize(
        ("ext", "weight"),
        [(".mp4", 1.0), (".pptx", 0.90), (".pdf", 0.70), (".xlsx", 0.40), (".txt", 0.20)],
    )
    def test_single_extension_weight(self, ext: str, weight: float) -> None:
        assert component_type_value([ext]) == pytest.approx(weight)

    def test_extension_without_dot_and_case(self) -> None:
        assert component_type_value(["PPTX"]) == pytest.approx(0.90)

    def test_mean_of_mixed_types(self) -> None:
        assert component_type_value([".pptx", ".pdf"]) == pytest.approx(0.80)


class TestComponentMatch:
    def test_no_tokens_is_neutral(self) -> None:
        assert component_match([], ["anything"]) == 0.50

    def test_all_tokens_found(self) -> None:
        assert component_match(["retail", "luminate"], ["Retail Luminate deck"]) == 1.0

    def test_partial_match_fraction(self) -> None:
        assert component_match(["retail", "wms"], ["retail overview"]) == pytest.approx(0.5)


class TestComponentUniqueness:
    def test_unsampled_is_neutral(self) -> None:
        assert component_uniqueness(None) == 0.50

    def test_inverse_of_duplicate_rate(self) -> None:
        assert component_uniqueness(0.25) == pytest.approx(0.75)

    @pytest.mark.parametrize(("rate", "expected"), [(2.0, 0.0), (-1.0, 1.0)])
    def test_clamped_to_unit_interval(self, rate: float, expected: float) -> None:
        assert component_uniqueness(rate) == expected


class TestComponentCuration:
    @pytest.mark.parametrize(
        ("level", "value"),
        [("golden", 1.0), ("ratified", 0.75), ("candidate", 0.25), ("unknown", 0.25)],
    )
    def test_values(self, level: str, value: float) -> None:
        assert component_curation(level) == value


class TestComponentOperatorPrior:
    @pytest.mark.parametrize(
        ("prior", "value"),
        [("max", 1.0), ("high", 0.75), ("normal", 0.50), ("low", 0.25), ("exclude", 0.0)],
    )
    def test_values(self, prior: str, value: float) -> None:
        assert component_operator_prior(prior) == value

    def test_unknown_is_neutral(self) -> None:
        assert component_operator_prior("???") == 0.50


class TestComputeComponents:
    def test_full_vector_from_snapshot(self) -> None:
        snapshot = MetadataSnapshot(
            location_name="Retail Luminate",
            children=(
                ChildItem("deck.pptx", extension=".pptx", last_modified=_AS_OF),
                ChildItem(
                    "spec.pdf",
                    extension=".pdf",
                    last_modified=_AS_OF - timedelta(days=180),
                ),
                ChildItem("archive", is_folder=True),
            ),
        )
        comps = compute_components(
            dims={"industry": ["retail"], "software": ["luminate"]},
            topics=["planning"],
            curation_level="golden",
            operator_prior="max",
            snapshot=snapshot,
            score_as_of=_AS_OF,
        )
        assert comps["D"] == pytest.approx((2 / 3) * math.log(3) / math.log(64))
        assert comps["R"] == pytest.approx(0.75)
        assert comps["T"] == pytest.approx(0.80)
        assert comps["M"] == pytest.approx(2 / 3)  # retail+luminate in name, planning not
        assert comps["U"] == 0.50
        assert comps["C"] == 1.0
        assert comps["O"] == 1.0

    def test_deterministic_repeat(self) -> None:
        snapshot = MetadataSnapshot(
            "loc", (ChildItem("a.pdf", extension=".pdf", last_modified=_AS_OF),)
        )
        kw = dict(
            dims={}, topics=[], curation_level="candidate", operator_prior="normal",
            snapshot=snapshot, score_as_of=_AS_OF,
        )
        assert compute_components(**kw) == compute_components(**kw)
