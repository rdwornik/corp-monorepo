"""Operational database for asset tracking and ingest audit trail.

ops.db is the system's memory of what files exist, where they went,
and why. Every state change is logged as an ingest_event for undo support.

DB location: {app_data_path}/ops.db (alongside index.db, NOT in OneDrive).

OpsDB is a facade that delegates to per-entity repositories:
- AssetRepository (asset_repo.py)
- PackageRepository (package_repo.py)
- EventRepository (event_repo.py)
- RoutingRepository (routing_repo.py)
- SuggestionRepository (suggestion_repo.py)
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from corp.ops.asset_repo import AssetRepository
from corp.ops.event_repo import EventRepository
from corp.ops.package_repo import PackageRepository
from corp.ops.routing_repo import RoutingRepository
from corp.ops.suggestion_repo import SuggestionRepository

logger = logging.getLogger(__name__)

_SCHEMA = """\
-- Assets: every known file in MyWork (populated by scans)
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime TEXT NOT NULL,
    content_hash TEXT,
    folder_l1 TEXT NOT NULL,
    folder_l2 TEXT,
    status TEXT NOT NULL DEFAULT 'discovered',
    package_id INTEGER,
    routed_to TEXT,
    routed_method TEXT,
    routed_confidence REAL,
    extracted_note_path TEXT,
    source_hash_at_extraction TEXT,
    first_seen TEXT NOT NULL,
    last_scanned TEXT NOT NULL,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

CREATE INDEX IF NOT EXISTS idx_assets_path ON assets(path);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_folder_l1 ON assets(folder_l1);
CREATE INDEX IF NOT EXISTS idx_assets_extension ON assets(extension);

-- Packages: folder-level groupings (for folder ingest)
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    destination_path TEXT,
    inferred_topic TEXT,
    inferred_products TEXT,
    inferred_domains TEXT,
    file_count INTEGER NOT NULL DEFAULT 0,
    total_size_bytes INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    completed_at TEXT
);

-- Ingest events: audit trail of every action taken on an asset
CREATE TABLE IF NOT EXISTS ingest_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    package_id INTEGER,
    action TEXT NOT NULL,
    source_path TEXT,
    destination_path TEXT,
    method TEXT,
    confidence REAL,
    reasoning TEXT,
    cost REAL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    reversible INTEGER NOT NULL DEFAULT 1,
    reverted INTEGER NOT NULL DEFAULT 0,
    vault_note_path TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

CREATE INDEX IF NOT EXISTS idx_events_asset ON ingest_events(asset_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON ingest_events(timestamp);

-- File registry: content-hash-based file identity (survives path changes)
CREATE TABLE IF NOT EXISTS files (
    file_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash  TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    current_path  TEXT,
    size_bytes    INTEGER,
    first_seen_at TEXT NOT NULL,
    last_seen_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(current_path);

-- Extraction history: tracks which models extracted which files
CREATE TABLE IF NOT EXISTS extractions (
    extraction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id        INTEGER NOT NULL REFERENCES files(file_id),
    model          TEXT NOT NULL,
    extracted_at   TEXT NOT NULL,
    vault_note_path TEXT,
    cost_cents     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_extractions_file ON extractions(file_id);

-- Routing feedback: every routing decision for manual review.
-- DECISION (Council 2026-03-25): Manual rules only. No automated learning.
-- Revisit when: loose files > 50/month AND override rate > 40% for 3 months.
CREATE TABLE IF NOT EXISTS routing_feedback (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    extension TEXT,
    file_size_bytes INTEGER,
    classifier_destination TEXT,
    classifier_confidence REAL DEFAULT NULL,
    final_destination TEXT NOT NULL,
    was_overridden BOOLEAN NOT NULL,
    routing_method TEXT NOT NULL,
    user_context TEXT,
    client TEXT,
    reviewed BOOLEAN NOT NULL DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_routing_feedback_reviewed ON routing_feedback(reviewed);
CREATE INDEX IF NOT EXISTS idx_routing_feedback_method ON routing_feedback(routing_method);

-- MinHash signatures for near-duplicate detection (ingest/dedup.py)
CREATE TABLE IF NOT EXISTS content_signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    hashvalues BLOB NOT NULL,
    num_perm INTEGER NOT NULL DEFAULT 128,
    computed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signatures_path ON content_signatures(file_path);

-- Registry suggestions: auto-discovered patterns from scans
CREATE TABLE IF NOT EXISTS registry_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    proposed_series TEXT NOT NULL,
    proposed_destination TEXT,
    evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
"""


def get_ops_db_path() -> Path:
    """Default ops.db path from config."""
    from corp.config import get_config

    return get_config().app_data_path / "ops.db"


class OpsDB:
    """Operational database facade — delegates to per-entity repositories.

    This is the system's memory of what files exist, where they went,
    and why. Every action is logged as an ingest_event for undo support.

    Repositories: AssetRepository, PackageRepository, EventRepository,
    RoutingRepository, SuggestionRepository (created lazily on first conn access).
    """

    def __init__(self, db_path: Path | None = None, config=None) -> None:
        # config: PipelineConfig | None — avoids top-level import cycle
        if db_path is None and config is not None:
            db_path = config.ops_db_path
        self.db_path = db_path or get_ops_db_path()
        self._conn: sqlite3.Connection | None = None
        # Repositories — created lazily when conn is first accessed
        self._asset_repo: AssetRepository | None = None
        self._package_repo: PackageRepository | None = None
        self._event_repo: EventRepository | None = None
        self._routing_repo: RoutingRepository | None = None
        self._suggestion_repo: SuggestionRepository | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._init_schema()
            # Initialize repositories
            self._asset_repo = AssetRepository(self._conn)
            self._package_repo = PackageRepository(self._conn)
            self._event_repo = EventRepository(self._conn)
            self._routing_repo = RoutingRepository(self._conn)
            self._suggestion_repo = SuggestionRepository(self._conn)
        return self._conn

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript(_SCHEMA)
        # Migrate: add vault_note_path if missing (pre-existing DBs)
        try:
            self.conn.execute("SELECT vault_note_path FROM ingest_events LIMIT 0")
        except sqlite3.OperationalError:
            self.conn.execute("ALTER TABLE ingest_events ADD COLUMN vault_note_path TEXT")
            self.conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._asset_repo = None
            self._package_repo = None
            self._event_repo = None
            self._routing_repo = None
            self._suggestion_repo = None

    # === Timestamp helper ===

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    # === Asset operations (delegated to AssetRepository) ===

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
        """Insert or update an asset record. Returns asset ID."""
        _ = self.conn  # ensure repos initialized
        return self._asset_repo.upsert_asset(
            path, filename, extension, size_bytes, mtime, folder_l1, folder_l2,
        )

    def get_asset(self, path: str) -> dict | None:
        """Get asset by relative path."""
        _ = self.conn
        return self._asset_repo.get_asset(path)

    def get_assets_by_status(self, status: str) -> list[dict]:
        """Get all assets with given status."""
        _ = self.conn
        return self._asset_repo.get_assets_by_status(status)

    def get_assets_by_folder(self, folder_l1: str) -> list[dict]:
        """Get all assets in a given L1 folder."""
        _ = self.conn
        return self._asset_repo.get_assets_by_folder(folder_l1)

    def update_asset_path(self, old_path: str, new_path: str) -> bool:
        """Update the canonical path of an asset after a file move."""
        _ = self.conn
        return self._asset_repo.update_asset_path(old_path, new_path)

    def update_asset_status(
        self,
        path: str,
        status: str,
        *,
        routed_to: str | None = None,
        routed_method: str | None = None,
        routed_confidence: float | None = None,
        extracted_note_path: str | None = None,
        source_hash_at_extraction: str | None = None,
        package_id: int | None = None,
        reasoning: str | None = None,
        cost: float = 0.0,
    ) -> None:
        """Update asset status and optional fields. Logs an ingest_event.

        Every state change goes through here to maintain the audit trail.
        This method stays on OpsDB because it coordinates asset + event repos.
        """
        path = path.replace("\\", "/")
        asset = self.get_asset(path)
        if asset is None:
            logger.warning("Cannot update status: asset not found: %s", path)
            return

        parts = ["status = ?"]
        params: list = [status]

        if routed_to is not None:
            parts.append("routed_to = ?")
            params.append(routed_to.replace("\\", "/"))
        if routed_method is not None:
            parts.append("routed_method = ?")
            params.append(routed_method)
        if routed_confidence is not None:
            parts.append("routed_confidence = ?")
            params.append(routed_confidence)
        if extracted_note_path is not None:
            parts.append("extracted_note_path = ?")
            params.append(extracted_note_path.replace("\\", "/"))
        if source_hash_at_extraction is not None:
            parts.append("source_hash_at_extraction = ?")
            params.append(source_hash_at_extraction)
        if package_id is not None:
            parts.append("package_id = ?")
            params.append(package_id)

        params.append(path)
        sql = f"UPDATE assets SET {', '.join(parts)} WHERE path = ?"
        self.conn.execute(sql, params)

        # Log the ingest event
        self.log_event(
            action=status,
            asset_id=asset["id"],
            source_path=path,
            destination_path=routed_to,
            method=routed_method,
            confidence=routed_confidence,
            reasoning=reasoning,
            cost=cost,
        )

        self.conn.commit()

    # === Package operations (delegated to PackageRepository) ===

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
        _ = self.conn
        return self._package_repo.create_package(
            folder_name, source_path, file_count, total_size,
            inferred_topic=inferred_topic, inferred_products=inferred_products,
            inferred_domains=inferred_domains,
        )

    def get_package(self, package_id: int) -> dict | None:
        """Get package by ID."""
        _ = self.conn
        return self._package_repo.get_package(package_id)

    def update_package_status(
        self,
        package_id: int,
        status: str,
        *,
        destination_path: str | None = None,
    ) -> None:
        """Update package status."""
        _ = self.conn
        self._package_repo.update_package_status(
            package_id, status, destination_path=destination_path,
        )

    # === Ingest event operations (delegated to EventRepository) ===

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
        """Log an ingest event. Returns event ID."""
        _ = self.conn
        return self._event_repo.log_event(
            action,
            asset_id=asset_id, package_id=package_id,
            source_path=source_path, destination_path=destination_path,
            method=method, confidence=confidence, reasoning=reasoning,
            cost=cost, reversible=reversible, vault_note_path=vault_note_path,
        )

    def revert_event(self, event_id: int) -> bool:
        """Mark an event as reverted."""
        _ = self.conn
        return self._event_repo.revert_event(event_id)

    def get_events_for_asset(self, asset_id: int) -> list[dict]:
        """Get full history for an asset, ordered chronologically."""
        _ = self.conn
        return self._event_repo.get_events_for_asset(asset_id)

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Get most recent ingest events."""
        _ = self.conn
        return self._event_repo.get_recent_events(limit)

    # === Registry suggestion operations (delegated to SuggestionRepository) ===

    def add_suggestion(
        self,
        pattern: str,
        proposed_series: str,
        proposed_destination: str,
        evidence: str,
    ) -> int:
        """Add a registry suggestion from auto-discovery."""
        _ = self.conn
        return self._suggestion_repo.add_suggestion(
            pattern, proposed_series, proposed_destination, evidence,
        )

    def get_pending_suggestions(self) -> list[dict]:
        """Get suggestions awaiting review."""
        _ = self.conn
        return self._suggestion_repo.get_pending_suggestions()

    def update_suggestion_status(
        self,
        suggestion_id: int,
        status: str,
    ) -> None:
        """Approve, reject, or expire a suggestion."""
        _ = self.conn
        self._suggestion_repo.update_suggestion_status(suggestion_id, status)

    # === Stats (cross-table — stays on OpsDB) ===

    def get_stats(self) -> dict:
        """Summary stats for corp status command."""
        total = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        by_status = self.conn.execute(
            """SELECT status, COUNT(*) AS cnt
               FROM assets GROUP BY status ORDER BY cnt DESC""",
        ).fetchall()
        by_folder = self.conn.execute(
            """SELECT folder_l1, COUNT(*) AS cnt
               FROM assets GROUP BY folder_l1 ORDER BY cnt DESC""",
        ).fetchall()
        by_ext = self.conn.execute(
            """SELECT extension, COUNT(*) AS cnt
               FROM assets GROUP BY extension ORDER BY cnt DESC LIMIT 10""",
        ).fetchall()
        total_events = self.conn.execute(
            "SELECT COUNT(*) FROM ingest_events",
        ).fetchone()[0]
        total_packages = self.conn.execute(
            "SELECT COUNT(*) FROM packages",
        ).fetchone()[0]
        pending_suggestions = self.conn.execute(
            "SELECT COUNT(*) FROM registry_suggestions WHERE status = 'pending'",
        ).fetchone()[0]

        return {
            "total_assets": total,
            "by_status": {row["status"]: row["cnt"] for row in by_status},
            "by_folder": {row["folder_l1"]: row["cnt"] for row in by_folder},
            "top_extensions": {row["extension"]: row["cnt"] for row in by_ext},
            "total_events": total_events,
            "total_packages": total_packages,
            "pending_suggestions": pending_suggestions,
        }

    # === Routing feedback (delegated to RoutingRepository) ===

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
        _ = self.conn
        self._routing_repo.log_routing_decision(
            filename=filename, extension=extension,
            file_size_bytes=file_size_bytes,
            classifier_destination=classifier_destination,
            classifier_confidence=classifier_confidence,
            final_destination=final_destination,
            was_overridden=was_overridden, routing_method=routing_method,
            user_context=user_context, client=client,
        )

    def check_review_trigger(self) -> str | None:
        """Check if routing review is needed. Returns message or None."""
        _ = self.conn
        return self._routing_repo.check_review_trigger()

    def get_routing_overrides(self, limit: int = 20) -> list[dict]:
        """Get unreviewed routing override patterns grouped by destination."""
        _ = self.conn
        return self._routing_repo.get_routing_overrides(limit)

    def get_routing_stats(self) -> dict:
        """Get routing feedback stats for unreviewed entries."""
        _ = self.conn
        return self._routing_repo.get_routing_stats()

    def mark_routing_reviewed(self) -> int:
        """Mark all unreviewed routing feedback as reviewed. Returns count."""
        _ = self.conn
        return self._routing_repo.mark_routing_reviewed()
