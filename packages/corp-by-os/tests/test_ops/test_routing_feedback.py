"""Tests for routing feedback table and review workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp_by_os.ops.database import OpsDB


@pytest.fixture()
def db(tmp_path: Path) -> OpsDB:
    ops = OpsDB(db_path=tmp_path / "test_ops.db")
    _ = ops.conn  # trigger schema init
    yield ops
    ops.close()


def _log(db: OpsDB, **kwargs) -> None:
    """Helper to log a routing decision with defaults."""
    defaults = {
        "filename": "test.pdf",
        "extension": ".pdf",
        "file_size_bytes": 1024,
        "classifier_destination": "50_RFP",
        "classifier_confidence": 0.85,
        "final_destination": "50_RFP",
        "was_overridden": False,
        "routing_method": "classifier_auto",
        "user_context": None,
        "client": None,
    }
    defaults.update(kwargs)
    db.log_routing_decision(**defaults)


class TestLogRoutingDecision:
    def test_stores_decision(self, db: OpsDB) -> None:
        """Routing decision stored in ops.db."""
        _log(db)
        row = db.conn.execute("SELECT * FROM routing_feedback").fetchone()
        assert row is not None
        assert row["filename"] == "test.pdf"
        assert row["routing_method"] == "classifier_auto"

    def test_fail_open(self, tmp_path: Path) -> None:
        """Bad DB connection doesn't block routing."""
        ops = OpsDB(db_path=tmp_path / "test_ops.db")
        _ = ops.conn
        ops.close()
        # Connection closed — write should warn but not raise
        ops.log_routing_decision(
            filename="test.pdf",
            extension=".pdf",
            file_size_bytes=1024,
            classifier_destination=None,
            classifier_confidence=None,
            final_destination="50_RFP",
            was_overridden=False,
            routing_method="classifier_auto",
        )
        # No exception raised — fail-open works

    def test_batch_flag_method(self, db: OpsDB) -> None:
        """--destination flag logged as batch_flag."""
        _log(db, routing_method="batch_flag")
        row = db.conn.execute("SELECT routing_method FROM routing_feedback").fetchone()
        assert row["routing_method"] == "batch_flag"

    def test_classifier_auto_method(self, db: OpsDB) -> None:
        """Classifier accepted logged as classifier_auto."""
        _log(db, routing_method="classifier_auto")
        row = db.conn.execute("SELECT routing_method FROM routing_feedback").fetchone()
        assert row["routing_method"] == "classifier_auto"

    def test_manual_override_method(self, db: OpsDB) -> None:
        """User [d] override logged as manual_override."""
        _log(db, routing_method="manual_override", was_overridden=True)
        row = db.conn.execute("SELECT routing_method, was_overridden FROM routing_feedback").fetchone()
        assert row["routing_method"] == "manual_override"
        assert row["was_overridden"]

    def test_stores_user_context(self, db: OpsDB) -> None:
        """User context stored alongside decision."""
        _log(db, user_context="This is JLR RFI response", client="JLR")
        row = db.conn.execute("SELECT user_context, client FROM routing_feedback").fetchone()
        assert row["user_context"] == "This is JLR RFI response"
        assert row["client"] == "JLR"


class TestReviewTrigger:
    def test_trigger_fires_at_15(self, db: OpsDB) -> None:
        """Trigger fires when 15+ unreviewed overrides."""
        for i in range(15):
            _log(db, filename=f"file_{i}.pdf", routing_method="manual_override", was_overridden=True)
        msg = db.check_review_trigger()
        assert msg is not None
        assert "15" in msg

    def test_trigger_silent_below_15(self, db: OpsDB) -> None:
        """No trigger with fewer than 15 overrides."""
        for i in range(10):
            _log(db, filename=f"file_{i}.pdf", routing_method="manual_override", was_overridden=True)
        assert db.check_review_trigger() is None

    def test_trigger_ignores_batch(self, db: OpsDB) -> None:
        """Batch-flagged routes don't count toward trigger."""
        for i in range(20):
            _log(db, filename=f"file_{i}.pdf", routing_method="batch_flag")
        assert db.check_review_trigger() is None

    def test_trigger_ignores_reviewed(self, db: OpsDB) -> None:
        """Already-reviewed overrides don't trigger."""
        for i in range(20):
            _log(db, filename=f"file_{i}.pdf", routing_method="manual_override", was_overridden=True)
        db.mark_routing_reviewed()
        assert db.check_review_trigger() is None


class TestRoutingStats:
    def test_stats_count_by_method(self, db: OpsDB) -> None:
        """Stats correctly count by routing method."""
        _log(db, filename="a.pdf", routing_method="classifier_auto")
        _log(db, filename="b.pdf", routing_method="manual_override", was_overridden=True)
        _log(db, filename="c.pdf", routing_method="batch_flag")
        _log(db, filename="d.pdf", routing_method="classifier_auto")

        stats = db.get_routing_stats()
        assert stats["auto"] == 2
        assert stats["manual"] == 1
        assert stats["batch"] == 1
        assert stats["total"] == 4

    def test_overrides_grouped_by_destination(self, db: OpsDB) -> None:
        """Override report groups by final destination."""
        _log(db, filename="a.pdf", final_destination="50_RFP", routing_method="manual_override", was_overridden=True)
        _log(db, filename="b.pdf", final_destination="50_RFP", routing_method="manual_override", was_overridden=True)
        _log(db, filename="c.pdf", final_destination="10_Projects/JLR", routing_method="manual_override", was_overridden=True)

        overrides = db.get_routing_overrides()
        assert len(overrides) == 2
        # 50_RFP has 2, should be first
        assert overrides[0]["cnt"] == 2


class TestMarkReviewed:
    def test_mark_reviewed_clears_flag(self, db: OpsDB) -> None:
        """Mark-reviewed sets reviewed=1 on all entries."""
        for i in range(5):
            _log(db, filename=f"file_{i}.pdf")

        count = db.mark_routing_reviewed()
        assert count == 5

        unreviewed = db.conn.execute(
            "SELECT COUNT(*) FROM routing_feedback WHERE reviewed = 0"
        ).fetchone()[0]
        assert unreviewed == 0

    def test_mark_reviewed_returns_count(self, db: OpsDB) -> None:
        """Returns number of entries marked."""
        _log(db, filename="a.pdf")
        _log(db, filename="b.pdf")
        assert db.mark_routing_reviewed() == 2
        # Second call returns 0
        assert db.mark_routing_reviewed() == 0


class TestSchemaCreation:
    def test_routing_feedback_table_exists(self, db: OpsDB) -> None:
        """Schema includes routing_feedback table."""
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "routing_feedback" in table_names
