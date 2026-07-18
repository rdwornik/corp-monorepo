"""FR-10 source-observation repository tests — append-only derived state (§1.3 / D1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.ops.database import OpsDB
from corp.ops.source_observation_repo import SourceObservationRepository
from corp.ops.source_value import ValueScore


@pytest.fixture()
def repo(tmp_path: Path) -> SourceObservationRepository:
    ops = OpsDB(db_path=tmp_path / "test_ops.db")
    yield SourceObservationRepository(ops.conn)
    ops.close()


def _vs() -> ValueScore:
    return ValueScore(
        score=76,
        components={"D": 0.17, "Y": 0.67, "I": 0.80, "N": 0.50},
        weights_version="v1",
        score_as_of="2026-07-01T12:00:00",
    )


class TestAppend:
    def test_append_returns_id_and_latest_hydrates(self, repo) -> None:
        oid = repo.append(
            "by-platform",
            liveness="LIVE",
            value_score=_vs(),
            last_verified="2026-07-01T12:00:00",
            recovery_candidates=["/moved/here"],
        )
        assert oid >= 1
        latest = repo.latest("by-platform")
        assert latest["liveness"] == "LIVE"
        assert latest["score"] == 76
        assert latest["weights_version"] == "v1"
        assert latest["components"]["Y"] == 0.67
        assert latest["recovery_candidates"] == ["/moved/here"]

    def test_append_only_keeps_history(self, repo) -> None:
        repo.append("s", liveness="LIVE", value_score=_vs())
        repo.append("s", liveness="STALE")
        repo.append("s", liveness="MOVED-candidate", recovery_candidates=["/x"])
        history = repo.history("s")
        assert [h["liveness"] for h in history] == ["LIVE", "STALE", "MOVED-candidate"]
        # latest is the most recent append
        assert repo.latest("s")["liveness"] == "MOVED-candidate"

    def test_observation_without_score(self, repo) -> None:
        repo.append("s", liveness="LOST")
        latest = repo.latest("s")
        assert latest["score"] is None
        assert latest["components"] is None
        assert latest["recovery_candidates"] == []

    def test_invalid_liveness_fails_closed(self, repo) -> None:
        with pytest.raises(ValueError, match="liveness"):
            repo.append("s", liveness="ALIVE")

    def test_latest_unknown_source_is_none(self, repo) -> None:
        assert repo.latest("nope") is None

    def test_observations_isolated_by_source_id(self, repo) -> None:
        repo.append("a", liveness="LIVE")
        repo.append("b", liveness="STALE")
        assert repo.latest("a")["liveness"] == "LIVE"
        assert len(repo.history("a")) == 1

    def test_gate_status_survives_round_trip(self, repo) -> None:
        # terra P1: a hard-gated (exclude) zero must not hydrate as a permitted zero.
        gated = ValueScore(
            score=0, components={}, weights_version="v1", score_as_of="t", gated=True
        )
        repo.append("excluded", liveness="LIVE", value_score=gated)
        repo.append("permitted", liveness="LIVE", value_score=_vs())
        assert repo.latest("excluded")["gated"] is True
        assert repo.latest("permitted")["gated"] is False

    def test_scoreless_observation_is_not_gated(self, repo) -> None:
        repo.append("s", liveness="LOST")
        assert repo.latest("s")["gated"] is False

    def test_recovery_candidate_paths_normalized_to_forward_slash(self, repo) -> None:
        # terra P1 (CLAUDE.md §5 rule 12): stored paths use forward slashes only.
        repo.append(
            "s",
            liveness="MOVED-candidate",
            recovery_candidates=[r"Sites\Platform\General", "Sites/Products/Docs"],
        )
        assert repo.latest("s")["recovery_candidates"] == [
            "Sites/Platform/General",
            "Sites/Products/Docs",
        ]
