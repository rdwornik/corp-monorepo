"""Event repository — CRUD for the ingest_events table.

Connection-injected, single-table focus. Follows FileRegistry pattern.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class EventRepository:
    """CRUD operations on the ingest_events table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def log_event(
        self,
        action: str,
        *,
        asset_id: int | None = None,
        package_id: int | None = None,
        source_path: str | None = None,
        destination_path: str | None = None,
        method: str | None = None,
        confidence: float | None = None,
        reasoning: str | None = None,
        cost: float = 0.0,
        reversible: bool = True,
        vault_note_path: str | None = None,
    ) -> int:
        """Log an ingest event. Returns event ID.

        EVERY state change must go through this method to maintain
        the audit trail and enable undo.
        """
        if source_path:
            source_path = source_path.replace("\\", "/")
        if destination_path:
            destination_path = destination_path.replace("\\", "/")
        if vault_note_path:
            vault_note_path = vault_note_path.replace("\\", "/")

        cur = self.conn.execute(
            """INSERT INTO ingest_events
               (asset_id, package_id, action, source_path, destination_path,
                method, confidence, reasoning, cost, timestamp, reversible,
                vault_note_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                asset_id,
                package_id,
                action,
                source_path,
                destination_path,
                method,
                confidence,
                reasoning,
                cost,
                self._now(),
                1 if reversible else 0,
                vault_note_path,
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def revert_event(self, event_id: int) -> bool:
        """Mark an event as reverted.

        Does NOT undo the filesystem change — that's the caller's
        responsibility. This just marks the record.
        """
        row = self.conn.execute(
            "SELECT reversible, reverted FROM ingest_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return False
        if not row["reversible"]:
            logger.warning("Event %d is not reversible", event_id)
            return False
        if row["reverted"]:
            logger.warning("Event %d already reverted", event_id)
            return False

        self.conn.execute(
            "UPDATE ingest_events SET reverted = 1 WHERE id = ?",
            (event_id,),
        )
        self.conn.commit()
        return True

    def get_events_for_asset(self, asset_id: int) -> list[dict]:
        """Get full history for an asset, ordered chronologically."""
        rows = self.conn.execute(
            "SELECT * FROM ingest_events WHERE asset_id = ? ORDER BY timestamp",
            (asset_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Get most recent ingest events."""
        rows = self.conn.execute(
            "SELECT * FROM ingest_events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
