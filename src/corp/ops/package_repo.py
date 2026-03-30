"""Package repository — CRUD for the packages table.

Connection-injected, single-table focus. Follows FileRegistry pattern.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime


class PackageRepository:
    """CRUD operations on the packages table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def create_package(
        self,
        folder_name: str,
        source_path: str,
        file_count: int,
        total_size: int,
        *,
        inferred_topic: str | None = None,
        inferred_products: str | None = None,
        inferred_domains: str | None = None,
    ) -> int:
        """Create a new package record. Returns package ID."""
        source_path = source_path.replace("\\", "/")
        cur = self.conn.execute(
            """INSERT INTO packages
               (folder_name, source_path, file_count, total_size_bytes,
                inferred_topic, inferred_products, inferred_domains, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                folder_name,
                source_path,
                file_count,
                total_size,
                inferred_topic,
                inferred_products,
                inferred_domains,
                self._now(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_package(self, package_id: int) -> dict | None:
        """Get package by ID."""
        row = self.conn.execute(
            "SELECT * FROM packages WHERE id = ?",
            (package_id,),
        ).fetchone()
        return dict(row) if row else None

    def update_package_status(
        self,
        package_id: int,
        status: str,
        *,
        destination_path: str | None = None,
    ) -> None:
        """Update package status."""
        parts = ["status = ?"]
        params: list = [status]

        if destination_path is not None:
            parts.append("destination_path = ?")
            params.append(destination_path.replace("\\", "/"))
        if status in ("extracted", "archived"):
            parts.append("completed_at = ?")
            params.append(self._now())

        params.append(package_id)
        sql = f"UPDATE packages SET {', '.join(parts)} WHERE id = ?"
        self.conn.execute(sql, params)
        self.conn.commit()
