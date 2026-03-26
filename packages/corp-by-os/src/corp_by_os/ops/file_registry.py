"""File registry — content-hash-based file identity and extraction tracking.

File identity = SHA256 content hash. Paths are metadata that change
when folders restructure. The registry survives index rebuilds and
tracks extraction history per model for conscious re-extraction.

Lives in ops.db alongside other operational data.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileRecord:
    """A known file identified by content hash."""

    file_id: int
    content_hash: str
    original_name: str
    current_path: str | None
    size_bytes: int | None
    first_seen_at: str
    last_seen_at: str


@dataclass(frozen=True)
class ExtractionRecord:
    """A single extraction event for a file."""

    extraction_id: int
    file_id: int
    model: str
    extracted_at: str
    vault_note_path: str | None
    cost_cents: int | None


class FileRegistry:
    """Centralized file identity and extraction tracking.

    Uses content_hash (SHA256) as file identity — survives path changes.
    Thin wrapper over SQL in ops.db.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def register_file(
        self,
        content_hash: str,
        filename: str,
        path: str,
        size_bytes: int,
    ) -> FileRecord:
        """Register a file or update its path if already known.

        If content_hash exists: update current_path + last_seen_at.
        If new: insert with first_seen_at = now.
        """
        path = path.replace("\\", "/")
        now = self._now()

        existing = self.get_by_hash(content_hash)
        if existing:
            self.conn.execute(
                "UPDATE files SET current_path = ?, last_seen_at = ? WHERE file_id = ?",
                (path, now, existing.file_id),
            )
            self.conn.commit()
            return FileRecord(
                file_id=existing.file_id,
                content_hash=content_hash,
                original_name=existing.original_name,
                current_path=path,
                size_bytes=existing.size_bytes,
                first_seen_at=existing.first_seen_at,
                last_seen_at=now,
            )

        cur = self.conn.execute(
            """INSERT INTO files
               (content_hash, original_name, current_path, size_bytes,
                first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (content_hash, filename, path, size_bytes, now, now),
        )
        self.conn.commit()
        return FileRecord(
            file_id=cur.lastrowid,
            content_hash=content_hash,
            original_name=filename,
            current_path=path,
            size_bytes=size_bytes,
            first_seen_at=now,
            last_seen_at=now,
        )

    def get_by_hash(self, content_hash: str) -> FileRecord | None:
        """Look up a file by content hash."""
        row = self.conn.execute(
            "SELECT * FROM files WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_file(row)

    def get_extractions(self, file_id: int) -> list[ExtractionRecord]:
        """Get all extractions for a file, newest first."""
        rows = self.conn.execute(
            "SELECT * FROM extractions WHERE file_id = ? ORDER BY extraction_id DESC",
            (file_id,),
        ).fetchall()
        return [self._row_to_extraction(r) for r in rows]

    def latest_extraction(self, file_id: int) -> ExtractionRecord | None:
        """Get most recent extraction for a file."""
        row = self.conn.execute(
            "SELECT * FROM extractions WHERE file_id = ? ORDER BY extraction_id DESC LIMIT 1",
            (file_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_extraction(row)

    def record_extraction(
        self,
        file_id: int,
        model: str,
        vault_note_path: str | None,
        cost_cents: int | None = None,
    ) -> ExtractionRecord:
        """Record that a file was extracted."""
        now = self._now()
        if vault_note_path:
            vault_note_path = vault_note_path.replace("\\", "/")
        cur = self.conn.execute(
            """INSERT INTO extractions
               (file_id, model, extracted_at, vault_note_path, cost_cents)
               VALUES (?, ?, ?, ?, ?)""",
            (file_id, model, now, vault_note_path, cost_cents),
        )
        self.conn.commit()
        return ExtractionRecord(
            extraction_id=cur.lastrowid,
            file_id=file_id,
            model=model,
            extracted_at=now,
            vault_note_path=vault_note_path,
            cost_cents=cost_cents,
        )

    def update_path(self, content_hash: str, new_path: str) -> None:
        """Update current_path when a file moves."""
        new_path = new_path.replace("\\", "/")
        self.conn.execute(
            "UPDATE files SET current_path = ?, last_seen_at = ? WHERE content_hash = ?",
            (new_path, self._now(), content_hash),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_file(row: sqlite3.Row) -> FileRecord:
        return FileRecord(
            file_id=row["file_id"],
            content_hash=row["content_hash"],
            original_name=row["original_name"],
            current_path=row["current_path"],
            size_bytes=row["size_bytes"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
        )

    @staticmethod
    def _row_to_extraction(row: sqlite3.Row) -> ExtractionRecord:
        return ExtractionRecord(
            extraction_id=row["extraction_id"],
            file_id=row["file_id"],
            model=row["model"],
            extracted_at=row["extracted_at"],
            vault_note_path=row["vault_note_path"],
            cost_cents=row["cost_cents"],
        )
