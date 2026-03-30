"""Asset repository — CRUD for the assets table.

Connection-injected, single-table focus. Follows FileRegistry pattern.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class AssetRepository:
    """CRUD operations on the assets table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def upsert_asset(
        self,
        path: str,
        filename: str,
        extension: str,
        size_bytes: int,
        mtime: str,
        folder_l1: str,
        folder_l2: str | None = None,
    ) -> int:
        """Insert or update an asset record. Returns asset ID.

        Path must use forward slashes, relative to mywork_root.
        """
        path = path.replace("\\", "/")
        now = self._now()

        existing = self.conn.execute(
            "SELECT id FROM assets WHERE path = ?",
            (path,),
        ).fetchone()

        if existing:
            self.conn.execute(
                """UPDATE assets SET
                     filename = ?, extension = ?, size_bytes = ?,
                     mtime = ?, folder_l1 = ?, folder_l2 = ?,
                     last_scanned = ?
                   WHERE path = ?""",
                (filename, extension, size_bytes, mtime, folder_l1, folder_l2, now, path),
            )
            self.conn.commit()
            return existing["id"]

        cur = self.conn.execute(
            """INSERT INTO assets
               (path, filename, extension, size_bytes, mtime,
                folder_l1, folder_l2, first_seen, last_scanned)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (path, filename, extension, size_bytes, mtime, folder_l1, folder_l2, now, now),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_asset(self, path: str) -> dict | None:
        """Get asset by relative path."""
        path = path.replace("\\", "/")
        row = self.conn.execute(
            "SELECT * FROM assets WHERE path = ?",
            (path,),
        ).fetchone()
        return dict(row) if row else None

    def get_assets_by_status(self, status: str) -> list[dict]:
        """Get all assets with given status."""
        rows = self.conn.execute(
            "SELECT * FROM assets WHERE status = ?",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_assets_by_folder(self, folder_l1: str) -> list[dict]:
        """Get all assets in a given L1 folder."""
        rows = self.conn.execute(
            "SELECT * FROM assets WHERE folder_l1 = ?",
            (folder_l1,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_asset_path(self, old_path: str, new_path: str) -> bool:
        """Update the canonical path of an asset after a file move.

        Must be called BEFORE update_asset_status when the lookup path
        needs to reflect the file's new location. Returns True if a row
        was updated.
        """
        old_path = old_path.replace("\\", "/")
        new_path = new_path.replace("\\", "/")
        cur = self.conn.execute(
            "UPDATE assets SET path = ? WHERE path = ?",
            (new_path, old_path),
        )
        self.conn.commit()
        if cur.rowcount == 0:
            logger.warning(
                "update_asset_path: no asset found at old path: %s",
                old_path,
            )
            return False
        return True
