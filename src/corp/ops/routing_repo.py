"""Routing feedback repository — CRUD for the routing_feedback table.

Connection-injected, single-table focus. Follows FileRegistry pattern.
"""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)


class RoutingRepository:
    """CRUD operations on the routing_feedback table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def log_routing_decision(
        self,
        *,
        filename: str,
        extension: str,
        file_size_bytes: int,
        classifier_destination: str | None,
        classifier_confidence: float | None,
        final_destination: str,
        was_overridden: bool,
        routing_method: str,
        user_context: str | None = None,
        client: str | None = None,
    ) -> None:
        """Log a routing decision. Fail-open — never blocks routing."""
        try:
            self.conn.execute(
                """INSERT INTO routing_feedback
                   (filename, extension, file_size_bytes, classifier_destination,
                    classifier_confidence, final_destination, was_overridden,
                    routing_method, user_context, client)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    filename,
                    extension,
                    file_size_bytes,
                    classifier_destination,
                    classifier_confidence,
                    final_destination,
                    was_overridden,
                    routing_method,
                    user_context,
                    client,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.warning("Failed to log routing decision: %s", e)

    def check_review_trigger(self) -> str | None:
        """Check if routing review is needed. Returns message or None."""
        try:
            row = self.conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN was_overridden AND routing_method = 'manual_override'
                              THEN 1 ELSE 0 END) as overrides
                   FROM routing_feedback
                   WHERE reviewed = 0 AND routing_method != 'batch_flag'""",
            ).fetchone()
            if row and row[1] and row[1] >= 15:
                return f"You have {row[1]} unreviewed routing overrides. Run: corp routing-review"
        except sqlite3.Error:
            pass
        return None

    def get_routing_overrides(self, limit: int = 20) -> list[dict]:
        """Get unreviewed routing override patterns grouped by destination."""
        try:
            rows = self.conn.execute(
                """SELECT final_destination, COUNT(*) as cnt,
                          GROUP_CONCAT(DISTINCT filename) as examples
                   FROM routing_feedback
                   WHERE was_overridden = 1 AND reviewed = 0
                   GROUP BY final_destination
                   ORDER BY cnt DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    def get_routing_stats(self) -> dict:
        """Get routing feedback stats for unreviewed entries."""
        try:
            row = self.conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN routing_method = 'classifier_auto'
                              THEN 1 ELSE 0 END) as auto,
                          SUM(CASE WHEN routing_method = 'manual_override'
                              THEN 1 ELSE 0 END) as manual,
                          SUM(CASE WHEN routing_method = 'batch_flag' THEN 1 ELSE 0 END) as batch
                   FROM routing_feedback WHERE reviewed = 0""",
            ).fetchone()
            return {
                "total": row[0] or 0,
                "auto": row[1] or 0,
                "manual": row[2] or 0,
                "batch": row[3] or 0,
            }
        except sqlite3.Error:
            return {"total": 0, "auto": 0, "manual": 0, "batch": 0}

    def mark_routing_reviewed(self) -> int:
        """Mark all unreviewed routing feedback as reviewed. Returns count."""
        cur = self.conn.execute("UPDATE routing_feedback SET reviewed = 1 WHERE reviewed = 0")
        self.conn.commit()
        return cur.rowcount
