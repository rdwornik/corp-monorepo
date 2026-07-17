"""Cross-project SQLite index.

Aggregates project-info.yaml + facts.yaml from all projects into a single
queryable database. Lives in %LOCALAPPDATA%/corp-by-os/index.db.

NOT in OneDrive — rebuilds are frequent, SQLite + OneDrive sync = corruption.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import yaml

from corp.config import get_config
from corp.models import IndexStats
from corp.schema.pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    client TEXT NOT NULL,
    status TEXT,
    products TEXT,
    topics TEXT,
    domains TEXT,
    people TEXT,
    region TEXT,
    industry TEXT,
    files_processed INTEGER DEFAULT 0,
    facts_count INTEGER DEFAULT 0,
    last_extracted TEXT,
    onedrive_path TEXT,
    vault_path TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- ============================================================
-- NOTES TABLE — DO NOT REMOVE
-- This indexes 1,972+ CKE-generated notes from the vault.
-- Without this, corp query returns 0 results for note content.
-- Added: 2026-03-12. If you see 0 notes after rebuild,
-- this code was accidentally deleted.
-- ============================================================
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    client TEXT,
    title TEXT NOT NULL,
    type TEXT,
    source_type TEXT,
    layer TEXT,
    source TEXT,
    topics TEXT,
    products TEXT,
    domains TEXT,
    people TEXT,
    confidentiality TEXT,
    quality TEXT,
    language TEXT,
    date TEXT,
    valid_to TEXT,
    model TEXT,
    tokens_used INTEGER,
    content_origin TEXT,
    source_category TEXT,
    source_locator TEXT,
    routing_confidence REAL,
    confidence TEXT,
    note_path TEXT NOT NULL,
    extraction_version INTEGER,
    depth TEXT,
    doc_type TEXT,
    source_path TEXT,
    source_hash TEXT,
    extracted_at TEXT,
    rfp_visible INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, topics, products, domains, people, client, project_id, doc_type,
    content=notes, content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(
        rowid, title, topics, products, domains, people, client, project_id, doc_type)
    VALUES (
        new.id, new.title, new.topics, new.products, new.domains,
        new.people, new.client, new.project_id, new.doc_type);
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(
        notes_fts, rowid, title, topics, products, domains,
        people, client, project_id, doc_type)
    VALUES (
        'delete', old.id, old.title, old.topics, old.products,
        old.domains, old.people, old.client, old.project_id, old.doc_type);
END;
"""


def get_index_path() -> Path:
    """Returns %LOCALAPPDATA%/corp-by-os/index.db."""
    cfg = get_config()
    return cfg.app_data_path / "index.db"


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open (or create) the index database."""
    if db_path is None:
        db_path = get_index_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript(_SCHEMA)


def rebuild_index(db_path: Path | None = None, config: PipelineConfig | None = None) -> IndexStats:
    """Full rebuild: scan vault + OneDrive, aggregate into SQLite."""
    start = time.time()
    if config is None:
        config = PipelineConfig.production()
    conn = _connect(db_path or config.index_db_path)

    try:
        # Drop all content tables so schema changes (e.g. new columns)
        # are picked up cleanly.  The meta table is preserved across rebuilds.
        conn.executescript("""\
            DROP TABLE IF EXISTS notes_fts;
            DROP TRIGGER IF EXISTS notes_ai;
            DROP TRIGGER IF EXISTS notes_ad;
            DROP TABLE IF EXISTS notes;
            DROP TABLE IF EXISTS facts_fts;
            DROP TRIGGER IF EXISTS facts_ai;
            DROP TRIGGER IF EXISTS facts_ad;
            DROP TABLE IF EXISTS facts;
            DROP TABLE IF EXISTS projects;
        """)

        _ensure_schema(conn)

        projects_count = 0
        facts_count = 0

        # Collect all project folders from OneDrive + vault
        project_dirs = _collect_project_dirs(config)

        for pid, info in project_dirs.items():
            _insert_project(conn, pid, info)
            projects_count += 1

        # Index CKE-generated notes from vault
        notes_count = _index_cke_notes(conn, config.vault_path)

        # Index extra roots (e.g. rfp_kb)
        for extra_root in config.index_extra_roots:
            if extra_root.exists():
                extra_count = _index_cke_notes(conn, extra_root)
                notes_count += extra_count
                logger.info("Indexed %d extra notes from %s", extra_count, extra_root)
            else:
                logger.warning("Extra index root not found: %s", extra_root)

        # Dedup notes by content hash (after all roots indexed)
        deduped = _dedup_notes_by_hash(conn)
        notes_count -= deduped

        # Rebuild FTS for notes
        conn.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild')")

        # Update meta
        now = datetime.now().isoformat(timespec="seconds")
        duration = time.time() - start
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('last_rebuild', ?)",
            (now,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('total_projects', ?)",
            (str(projects_count),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('total_facts', ?)",
            (str(facts_count),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('total_notes', ?)",
            (str(notes_count),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('rebuild_duration_seconds', ?)",
            (f"{duration:.2f}",),
        )
        conn.commit()

        path = db_path or config.index_db_path
        logger.info(
            "Index rebuilt: %d projects, %d facts, %d notes in %.1fs -> %s",
            projects_count,
            facts_count,
            notes_count,
            duration,
            path,
        )

        return IndexStats(
            projects_indexed=projects_count,
            facts_indexed=facts_count,
            notes_indexed=notes_count,
            rebuild_duration=duration,
            index_path=str(path).replace("\\", "/"),
        )
    finally:
        conn.close()


def update_project(
    project_id: str, db_path: Path | None = None, config: PipelineConfig | None = None
) -> bool:
    """Update a single project in the index."""
    if config is None:
        config = PipelineConfig.production()
    conn = _connect(db_path or config.index_db_path)

    try:
        _ensure_schema(conn)

        # Remove old data for this project
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))

        project_dirs = _collect_project_dirs(config)
        info = project_dirs.get(project_id)
        if info is None:
            conn.commit()
            return False

        _insert_project(conn, project_id, info)
        conn.commit()
        return True
    finally:
        conn.close()


def get_index_stats(db_path: Path | None = None) -> dict[str, str]:
    """Read meta table for index stats."""
    path = db_path or get_index_path()
    if not path.exists():
        return {}
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        rows = conn.execute("SELECT key, value FROM meta").fetchall()
        return dict(rows)
    finally:
        conn.close()


# --- Internal helpers ---


def _collect_project_dirs(cfg) -> dict[str, dict]:
    """Merge OneDrive + vault project directories into unified dict.

    Returns {project_id: {client, status, onedrive_path, vault_path, ...}}
    """
    projects: dict[str, dict] = {}

    # Scan OneDrive
    if cfg.projects_root.exists():
        for folder in sorted(cfg.projects_root.iterdir()):
            if folder.is_dir() and not folder.name.startswith((".", "_")):
                pid = folder.name.lower()
                client = folder.name.split("_")[0]
                projects[pid] = {
                    "client": client,
                    "status": "unknown",
                    "onedrive_path": str(folder).replace("\\", "/"),
                    "vault_path": None,
                    "products": [],
                    "topics": [],
                    "domains": [],
                    "people": [],
                    "region": None,
                    "industry": None,
                    "files_processed": 0,
                    "facts_count": 0,
                    "last_extracted": None,
                }
                # Try to read project-info.yaml from _knowledge/
                _enrich_from_onedrive(projects[pid], folder)

    # Scan vault
    from corp.models import VaultZone

    vault_projects = cfg.vault_path / VaultZone.PROJECTS.value
    if vault_projects.exists():
        for folder in sorted(vault_projects.iterdir()):
            if folder.is_dir() and not folder.name.startswith((".", "_")):
                pid = folder.name.lower()
                if pid not in projects:
                    projects[pid] = {
                        "client": folder.name.split("_")[0],
                        "status": "unknown",
                        "onedrive_path": None,
                        "vault_path": str(folder).replace("\\", "/"),
                        "products": [],
                        "topics": [],
                        "domains": [],
                        "people": [],
                        "region": None,
                        "industry": None,
                        "files_processed": 0,
                        "facts_count": 0,
                        "last_extracted": None,
                    }
                else:
                    projects[pid]["vault_path"] = str(folder).replace("\\", "/")

                # Enrich from vault project-info.yaml (overrides OneDrive)
                _enrich_from_vault(projects[pid], folder)

    return projects


def _enrich_from_onedrive(info: dict, folder: Path) -> None:
    """Read _knowledge/project-info.yaml from OneDrive folder."""
    info_file = folder / "_knowledge" / "project-info.yaml"
    if not info_file.exists():
        return
    try:
        with open(info_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return
        info["status"] = data.get("status", info["status"])
        info["products"] = data.get("products", [])
        info["topics"] = data.get("topics", [])
        info["people"] = data.get("people", [])
        info["files_processed"] = data.get("files_processed", 0)
        info["last_extracted"] = data.get("rendered_at", None)
        # Opportunity metadata
        opp = data.get("opportunity", {})
        if isinstance(opp, dict):
            info["region"] = opp.get("region", info.get("region"))
            info["industry"] = opp.get("industry", info.get("industry"))
    except (yaml.YAMLError, OSError, KeyError) as e:
        logger.debug("Failed to read OneDrive project-info: %s", e)


def _enrich_from_vault(info: dict, folder: Path) -> None:
    """Read project-info.yaml from vault folder."""
    info_file = folder / "project-info.yaml"
    if not info_file.exists():
        return
    try:
        with open(info_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return
        info["client"] = data.get("client", info["client"])
        info["status"] = data.get("status", info["status"])
        info["products"] = data.get("products", info["products"])
        info["topics"] = data.get("topics", info["topics"])
        info["domains"] = data.get("domains", [])
        info["people"] = data.get("people", info["people"])
        info["region"] = data.get("region", info.get("region"))
        info["industry"] = data.get("industry", info.get("industry"))
        info["files_processed"] = data.get("files_processed", info["files_processed"])
        info["facts_count"] = data.get("facts_count", 0)
        info["last_extracted"] = data.get("last_extracted", info.get("last_extracted"))
    except (yaml.YAMLError, OSError) as e:
        logger.debug("Failed to read vault project-info: %s", e)


def _insert_project(conn: sqlite3.Connection, pid: str, info: dict) -> None:
    """Insert a project row."""
    conn.execute(
        """INSERT OR REPLACE INTO projects
           (project_id, client, status, products, topics, domains, people,
            region, industry, files_processed, facts_count,
            last_extracted, onedrive_path, vault_path, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            pid,
            info["client"],
            info["status"],
            json.dumps(info.get("products", [])),
            json.dumps(info.get("topics", [])),
            json.dumps(info.get("domains", [])),
            json.dumps(info.get("people", [])),
            info.get("region"),
            info.get("industry"),
            info.get("files_processed", 0),
            info.get("facts_count", 0),
            info.get("last_extracted"),
            info.get("onedrive_path"),
            info.get("vault_path"),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


# ============================================================
# NOTES INDEXING — DO NOT REMOVE
# Scans vault for CKE-generated markdown notes, indexes into
# notes + notes_fts tables for full-text search.
# ============================================================


def _parse_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.debug("Failed to read %s: %s", filepath, e)
        return None
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(text[3:end])
    except yaml.YAMLError as e:
        logger.debug("Failed to parse frontmatter from %s: %s", filepath, e)
        return None


_RFP_VISIBLE_SOURCE_TYPES = {"documentation", "rfp"}
_RFP_VISIBLE_DOC_TYPES = {
    "product_doc",
    "architecture",
    "rfp_response",
    "security_questionnaire",
}


def _compute_rfp_visible(fm: dict) -> bool:
    """Determine if a note should be visible to the RFP agent.

    Rules (in priority order):
    1. confidential/restricted → never
    2. draft trust_level → never
    3. verified trust_level → always (rfp_kb entries)
    4. documentation/rfp source_type → yes
    5. product_doc/architecture/rfp_response/security_questionnaire doc_type → yes
    6. Everything else → no
    """
    conf = fm.get("confidentiality", "")
    if conf in ("confidential", "restricted"):
        return False

    trust = fm.get("trust_level", fm.get("confidence", "extracted"))
    if trust == "draft":
        return False
    if trust == "verified":
        return True

    if fm.get("source_type", "") in _RFP_VISIBLE_SOURCE_TYPES:
        return True
    if fm.get("doc_type", "") in _RFP_VISIBLE_DOC_TYPES:
        return True

    return False


def _index_cke_notes(conn: sqlite3.Connection, vault_root: Path) -> int:
    """Scan vault for knowledge notes and index into notes table.

    Scans known subdirectories first (01_Knowledge, legacy paths).
    If none of the known subdirs exist, scans vault_root itself — this
    supports extra roots like rfp_kb that contain markdown directly.
    """
    count = 0
    known_subdirs = [
        vault_root / "01_Knowledge",
        # Legacy paths (pre-restructure)
        vault_root / "knowledge",
        vault_root / "02_sources",
        vault_root / "04_evergreen" / "_generated",
    ]

    scan_dirs = [d for d in known_subdirs if d.exists()]

    # If none of the known subdirs exist, scan root directly (extra roots)
    if not scan_dirs and vault_root.exists():
        scan_dirs = [vault_root]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for md_file in scan_dir.rglob("*.md"):
            fm = _parse_frontmatter(md_file)
            if not fm:
                continue
            # rfp_kb entries have "id" but no "title" — synthesize title
            if "title" not in fm:
                if "id" in fm:
                    fm["title"] = fm["id"].replace("-", " ").replace("_", " ").title()
                else:
                    continue

            project_id = fm.get("project", "")
            if not project_id and "04_evergreen" in str(md_file):
                # Synthetic project_id for evergreen notes
                parts = md_file.relative_to(vault_root).parts
                project_id = "_" + "_".join(parts[1:3]) if len(parts) > 2 else "_evergreen"

            def _join_list(val: object) -> str:
                return ", ".join(val) if isinstance(val, list) else ""

            source_path_raw = fm.get("source_path", "")
            if source_path_raw:
                source_path_raw = str(source_path_raw).replace("\\", "/")

            conn.execute(
                """INSERT INTO notes
                   (project_id, client, title, type, source_type, layer,
                    source, topics, products, domains, people,
                    confidentiality, quality, language, date, valid_to,
                    model, tokens_used,
                    content_origin, source_category, source_locator,
                    routing_confidence, confidence, note_path,
                    extraction_version, depth, doc_type,
                    source_path, source_hash, extracted_at,
                    rfp_visible)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    project_id,
                    fm.get("client", ""),
                    fm.get("title", ""),
                    fm.get("type", ""),
                    fm.get("source_type", ""),
                    fm.get("layer", ""),
                    fm.get("source", ""),
                    _join_list(fm.get("topics", [])),
                    _join_list(fm.get("products", [])),
                    _join_list(fm.get("domains", [])),
                    _join_list(fm.get("people", [])),
                    fm.get("confidentiality", ""),
                    fm.get("quality", ""),
                    fm.get("language", ""),
                    fm.get("date", ""),
                    fm.get("valid_to", ""),
                    fm.get("model", ""),
                    fm.get("tokens_used", 0),
                    fm.get("content_origin", ""),
                    fm.get("source_category", ""),
                    fm.get("source_locator", ""),
                    fm.get("routing_confidence"),
                    fm.get("trust_level", "extracted"),
                    str(md_file).replace("\\", "/"),
                    fm.get("extraction_version"),
                    fm.get("depth", ""),
                    fm.get("doc_type", ""),
                    source_path_raw,
                    fm.get("source_hash", ""),
                    fm.get("extracted_at", ""),
                    1 if _compute_rfp_visible(fm) else 0,
                ),
            )
            count += 1

    conn.commit()
    logger.info("Indexed %d CKE notes from vault", count)
    return count


def _dedup_notes_by_hash(conn: sqlite3.Connection) -> int:
    """Remove duplicate notes with the same source_hash, keeping the latest.

    File identity = content hash (SHA256). Paths change when folders
    restructure. This runs AFTER all roots are indexed so cross-root
    duplicates are caught too.

    Returns number of duplicates removed.
    """
    dupes = conn.execute(
        """DELETE FROM notes
           WHERE id NOT IN (
               SELECT MAX(id) FROM notes GROUP BY source_hash
           )
           AND source_hash != ''
           AND source_hash IS NOT NULL"""
    ).rowcount
    if dupes:
        logger.info("Deduped %d notes with identical source_hash", dupes)
    return dupes
