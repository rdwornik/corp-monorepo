"""Suggestion repository — CRUD for the registry_suggestions table.

Connection-injected, single-table focus. Follows FileRegistry pattern.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime


class SuggestionRepository:
    """CRUD operations on the registry_suggestions table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def add_suggestion(
        self,
        pattern: str,
        proposed_series: str,
        proposed_destination: str,
        evidence: str,
    ) -> int:
        """Add a registry suggestion from auto-discovery."""
        cur = self.conn.execute(
            """INSERT INTO registry_suggestions
               (pattern, proposed_series, proposed_destination, evidence, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (pattern, proposed_series, proposed_destination, evidence, self._now()),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_pending_suggestions(self) -> list[dict]:
        """Get suggestions awaiting review."""
        rows = self.conn.execute(
            "SELECT * FROM registry_suggestions WHERE status = 'pending' ORDER BY created_at",
        ).fetchall()
        return [dict(r) for r in rows]

    def update_suggestion_status(
        self,
        suggestion_id: int,
        status: str,
    ) -> None:
        """Approve, reject, or expire a suggestion."""
        self.conn.execute(
            "UPDATE registry_suggestions SET status = ?, reviewed_at = ? WHERE id = ?",
            (status, self._now(), suggestion_id),
        )
        self.conn.commit()
