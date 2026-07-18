"""FR-10 source-observation repository — append-only derived state in ops.db.

The derived *observation* fields (liveness, recovery candidates, ``value_score``) live
here, joined to the hand-edited YAML *declaration* by ``source_id`` (intake-16 §1.3 / D1
split). The scout may only **append** observation rows; it never mutates a declaration.
Follows the ``EventRepository`` connection-injected, single-table pattern.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime

from corp.ops.source_value import ValueScore

logger = logging.getLogger(__name__)

LIVENESS = ("LIVE", "MOVED-candidate", "LOST", "STALE")


class SourceObservationRepository:
    """Append-only CRUD on the ``source_observations`` table (joined by ``source_id``)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def append(
        self,
        source_id: str,
        *,
        liveness: str,
        value_score: ValueScore | None = None,
        last_verified: str | None = None,
        recovery_candidates: list[str] | None = None,
    ) -> int:
        """Append one observation row for a source. Returns the observation id.

        Append-only: never updates a prior row. ``value_score`` is flattened into its
        struct fields; ``recovery_candidates`` is stored as a JSON list. ``liveness`` is
        validated against :data:`LIVENESS` (fail-closed).
        """
        if liveness not in LIVENESS:
            raise ValueError(f"liveness {liveness!r} not in {LIVENESS}")
        vs = value_score
        cur = self.conn.execute(
            """INSERT INTO source_observations
               (source_id, liveness, last_verified, recovery_candidates,
                score, components, weights_version, score_as_of, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                liveness,
                last_verified,
                json.dumps(recovery_candidates or []),
                vs.score if vs else None,
                json.dumps(vs.components) if vs else None,
                vs.weights_version if vs else None,
                vs.score_as_of if vs else None,
                self._now(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def latest(self, source_id: str) -> dict | None:
        """The most recent observation for a source (by append order), or ``None``."""
        row = self.conn.execute(
            """SELECT * FROM source_observations WHERE source_id = ?
               ORDER BY observation_id DESC LIMIT 1""",
            (source_id,),
        ).fetchone()
        return self._hydrate(row) if row else None

    def history(self, source_id: str) -> list[dict]:
        """All observations for a source, oldest first."""
        rows = self.conn.execute(
            "SELECT * FROM source_observations WHERE source_id = ? ORDER BY observation_id",
            (source_id,),
        ).fetchall()
        return [self._hydrate(r) for r in rows]

    @staticmethod
    def _hydrate(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["recovery_candidates"] = json.loads(d["recovery_candidates"]) if d["recovery_candidates"] else []
        d["components"] = json.loads(d["components"]) if d["components"] else None
        return d
