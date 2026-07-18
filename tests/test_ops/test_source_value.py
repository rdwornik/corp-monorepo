"""FR-10 deterministic scorer tests (intake-16 §2).

Step 2 covers the eight components {D,R,T,M,U,C,O} in isolation (§2.2). Composition
(seam G golden vector) and the single-pass neighbour prior (seam H) are added alongside.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from corp.ops.source_value import (
    WEIGHTS_VERSION,
    ChildItem,
    MetadataSnapshot,
    NeighbourNode,
    ValueScore,
    component_curation,
    component_density,
    component_match,
    component_operator_prior,
    component_recency,
    component_type_value,
    component_uniqueness,
    compose_score,
    compute_components,
    neighbour_priors,
    round_half_up,
    score_record,
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


class TestRoundHalfUp:
    """Ruling F2 — round-half-UP, never banker's (round-half-to-even)."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0.5, 1), (1.5, 2), (2.5, 3), (42.5, 43), (99.5, 100), (42.4, 42), (42.49, 42)],
    )
    def test_halves_round_up(self, value: float, expected: int) -> None:
        assert round_half_up(value) == expected

    def test_differs_from_bankers_rounding(self) -> None:
        # round(2.5) == 2 and round(0.5) == 0 under banker's; F2 must give 3 and 1.
        assert round_half_up(2.5) == 3 != round(2.5)
        assert round_half_up(0.5) == 1 != round(0.5)


def _golden_snapshot() -> MetadataSnapshot:
    return MetadataSnapshot(
        location_name="Retail Luminate Planning",
        children=(
            ChildItem("session.mp4", extension=".mp4", last_modified=_AS_OF),
            ChildItem("deck.pptx", extension=".pptx", last_modified=_AS_OF - timedelta(days=180)),
            ChildItem("old", is_folder=True),
        ),
    )


_GOLDEN_KW = dict(
    dims={"industry": ["retail"], "software": ["luminate"]},
    topics=["planning"],
    curation_level="golden",
    operator_prior="max",
    score_as_of=_AS_OF,
)


class TestComposeAndScore:
    def test_golden_vector(self) -> None:
        """Seam G — frozen record + fixture -> exact integer score + component vector."""
        vs = score_record(snapshot=_golden_snapshot(), **_GOLDEN_KW)
        assert isinstance(vs, ValueScore)
        assert vs.score == 76  # 100 * (0.85*I + 0.15*0.50), round-half-up
        assert vs.weights_version == WEIGHTS_VERSION == "v1"
        assert vs.score_as_of == "2026-07-01T12:00:00"
        c = vs.components
        # exactly-representable components
        assert (c["U"], c["C"], c["O"], c["N"]) == (0.50, 1.0, 1.0, 0.50)
        # components carrying a non-exact float (0.9 -> T) via approx
        assert c["R"] == pytest.approx(0.75)
        assert c["T"] == pytest.approx(0.95)
        assert c["M"] == pytest.approx(1.0)
        assert c["D"] == pytest.approx(0.1761069, abs=1e-6)
        # internal consistency of the two-level composition
        assert c["Y"] == pytest.approx((c["D"] + c["R"] + c["T"] + c["M"] + c["U"]) / 5)
        assert c["I"] == pytest.approx(0.60 * c["Y"] + 0.20 * c["C"] + 0.20 * c["O"])

    def test_score_is_reproducible(self) -> None:
        assert score_record(snapshot=_golden_snapshot(), **_GOLDEN_KW) == score_record(
            snapshot=_golden_snapshot(), **_GOLDEN_KW
        )

    def test_exclude_operator_prior_lowers_score(self) -> None:
        base = score_record(snapshot=_golden_snapshot(), **_GOLDEN_KW)
        excluded = score_record(
            snapshot=_golden_snapshot(), **{**_GOLDEN_KW, "operator_prior": "exclude"}
        )
        assert excluded.score < base.score
        assert excluded.components["O"] == 0.0

    def test_neighbour_shifts_final(self) -> None:
        comps = compute_components(snapshot=_golden_snapshot(), **_GOLDEN_KW)
        low = compose_score(comps, 0.0, score_as_of=_AS_OF).score
        high = compose_score(comps, 1.0, score_as_of=_AS_OF).score
        assert high > low


class TestNeighbourPriorIsSinglePass:
    """Seam H — one-hop N from intrinsic I, single snapshot / single pass (§2.3)."""

    def test_child_uses_parent_and_top3_siblings(self) -> None:
        nodes = [
            NeighbourNode("p", 0.8, drive_id="d"),
            NeighbourNode("c1", 0.6, parent_id="p", drive_id="d"),
            NeighbourNode("c2", 0.4, parent_id="p", drive_id="d"),
            NeighbourNode("c3", 0.2, parent_id="p", drive_id="d"),
        ]
        n = neighbour_priors(nodes)
        # N(c1) = 0.70*I(p) + 0.30*mean(top-3 siblings {c2,c3})
        assert n["c1"] == pytest.approx(0.70 * 0.8 + 0.30 * ((0.4 + 0.2) / 2))
        # N(root p) = mean(top-3 children)
        assert n["p"] == pytest.approx((0.6 + 0.4 + 0.2) / 3)

    def test_top3_siblings_only(self) -> None:
        nodes = [NeighbourNode("p", 0.5, drive_id="d")] + [
            NeighbourNode(f"c{i}", v, parent_id="p", drive_id="d")
            for i, v in enumerate([0.9, 0.7, 0.5, 0.3, 0.1])
        ]
        n = neighbour_priors(nodes)
        # root uses only the top-3 children by I
        assert n["p"] == pytest.approx((0.9 + 0.7 + 0.5) / 3)

    def test_lone_node_is_neutral(self) -> None:
        assert neighbour_priors([NeighbourNode("solo", 0.9, drive_id="d")]) == {"solo": 0.50}

    def test_child_without_siblings_gets_neutral_sibling_term(self) -> None:
        nodes = [
            NeighbourNode("p", 0.8, drive_id="d"),
            NeighbourNode("c", 0.3, parent_id="p", drive_id="d"),
        ]
        n = neighbour_priors(nodes)
        assert n["c"] == pytest.approx(0.70 * 0.8 + 0.30 * 0.50)

    def test_cross_drive_parent_link_ignored(self) -> None:
        nodes = [
            NeighbourNode("p", 0.8, drive_id="drive-A"),
            NeighbourNode("c", 0.3, parent_id="p", drive_id="drive-B"),
        ]
        # parent is in a different drive -> not a neighbour -> c is a childless root -> neutral
        assert neighbour_priors(nodes)["c"] == 0.50

    def test_single_pass_is_idempotent(self) -> None:
        nodes = [
            NeighbourNode("p", 0.8, drive_id="d"),
            NeighbourNode("c", 0.6, parent_id="p", drive_id="d"),
        ]
        assert neighbour_priors(nodes) == neighbour_priors(nodes)

    def test_n_reads_intrinsic_not_final(self) -> None:
        """A final score offered as a neighbourhood input would change N — it must not.

        The node carries only ``intrinsic``; N tracks it exactly. Shifting intrinsic
        shifts N proportionally, proving N is computed from I (never a final score).
        """
        base = neighbour_priors(
            [NeighbourNode("p", 0.8, drive_id="d"), NeighbourNode("c", 0.5, parent_id="p", drive_id="d")]
        )["c"]
        shifted = neighbour_priors(
            [NeighbourNode("p", 0.4, drive_id="d"), NeighbourNode("c", 0.5, parent_id="p", drive_id="d")]
        )["c"]
        assert base - shifted == pytest.approx(0.70 * (0.8 - 0.4))
