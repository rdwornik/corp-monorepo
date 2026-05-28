"""Tests for index_builder module."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from corp.index_builder import (
    _compute_rfp_visible,
    _connect,
    _dedup_notes_by_hash,
    _ensure_schema,
    _index_cke_notes,
    _parse_frontmatter,
    get_index_stats,
    rebuild_index,
    update_project,
)

# --- Fixtures ---


@pytest.fixture()
def index_env(app_config, tmp_vault: Path, tmp_projects: Path, tmp_path: Path):
    """Set up environment with projects that have project-info and facts."""
    # Add _knowledge/project-info.yaml to one project
    lenzing = tmp_projects / "Lenzing_Planning"
    knowledge = lenzing / "_knowledge"
    knowledge.mkdir(parents=True)

    info = {
        "project": "Lenzing_Planning",
        "status": "active",
        "files_processed": 9,
        "products": ["Planning", "WMS"],
        "topics": ["Demand Planning", "SAP Integration", "Security"],
        "people": ["Jane Doe"],
        "rendered_at": "2026-03-08",
    }
    (knowledge / "project-info.yaml").write_text(
        yaml.dump(info),
        encoding="utf-8",
    )

    # Add facts.yaml
    facts = {
        "project": "Lenzing_Planning",
        "total_facts": 3,
        "facts": [
            {
                "fact": "SAP integration requires custom middleware for real-time data sync.",
                "source": "note-001",
                "source_title": "Integration Architecture",
                "topics": ["SAP Integration", "Architecture"],
            },
            {
                "fact": "Demand planning horizon is 18 months with weekly granularity.",
                "source": "note-002",
                "source_title": "Planning Requirements",
                "topics": ["Demand Planning"],
            },
            {
                "fact": "Security compliance requires SOC2 Type II certification.",
                "source": "note-003",
                "source_title": "Security Review",
                "topics": ["Security"],
            },
        ],
    }
    (knowledge / "facts.yaml").write_text(
        yaml.dump(facts, default_flow_style=False),
        encoding="utf-8",
    )

    # Honda has no _knowledge, just a folder
    # (already created by tmp_projects fixture)

    return tmp_path


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "appdata" / "index.db"


# --- Test: Schema ---


class TestSchema:
    def test_creates_tables(self, db_path: Path) -> None:
        conn = _connect(db_path)
        _ensure_schema(conn)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "projects" in table_names
        assert "facts" in table_names
        assert "notes" in table_names, "notes table missing — code was deleted"
        assert "meta" in table_names
        conn.close()

    def test_schema_idempotent(self, db_path: Path) -> None:
        conn = _connect(db_path)
        _ensure_schema(conn)
        _ensure_schema(conn)  # should not raise
        conn.close()


# --- Test: Rebuild ---


class TestRebuild:
    def test_indexes_projects(self, index_env, db_path: Path) -> None:
        stats = rebuild_index(db_path)
        assert stats.projects_indexed >= 5  # from tmp_projects fixture
        assert stats.rebuild_duration >= 0

    def test_indexes_facts(self, index_env, db_path: Path) -> None:
        stats = rebuild_index(db_path)
        assert stats.facts_indexed == 3  # Lenzing has 3 facts

    def test_projects_without_facts(self, index_env, db_path: Path) -> None:
        """Projects without facts.yaml should still be indexed."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT facts_count FROM projects WHERE project_id = ?",
            ("honda_planning",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 0

    def test_project_metadata_from_onedrive(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT client, status, products FROM projects WHERE project_id = ?",
            ("lenzing_planning",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert "Lenzing" in row[0]  # from folder name or vault project-info
        assert row[1] == "active"
        assert "Planning" in row[2]

    def test_meta_updated(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        meta = get_index_stats(db_path)
        assert "last_rebuild" in meta
        assert "total_projects" in meta
        assert "total_facts" in meta
        assert meta["total_facts"] == "3"

    def test_rebuild_is_idempotent(self, index_env, db_path: Path) -> None:
        stats1 = rebuild_index(db_path)
        stats2 = rebuild_index(db_path)
        assert stats1.projects_indexed == stats2.projects_indexed
        assert stats1.facts_indexed == stats2.facts_indexed

    def test_rebuild_survives_old_schema(self, index_env, db_path: Path) -> None:
        """Rebuild on a DB with an outdated notes schema (missing columns) must not crash."""
        import sqlite3

        # Create old-schema DB without the confidence column
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""\
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, client TEXT);
            CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, project_id TEXT, fact TEXT);
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY, project_id TEXT, title TEXT, note_path TEXT
            );
        """)
        conn.execute("INSERT INTO notes VALUES (1, 'old', 'Old Note', '/old.md')")
        conn.commit()
        conn.close()

        # Rebuild must succeed despite the old schema
        stats = rebuild_index(db_path)
        assert stats.projects_indexed >= 0
        assert stats.notes_indexed >= 0

    def test_vault_project_merged(self, index_env, db_path: Path, tmp_vault: Path) -> None:
        """Vault project (lenzing_planning in 01_projects) should merge with OneDrive."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT vault_path FROM projects WHERE project_id = 'lenzing_planning'",
        ).fetchone()
        conn.close()
        assert row is not None
        # vault_path should be set since tmp_vault has 01_projects/lenzing_planning
        assert row[0] is not None


# --- Test: Update Project ---


class TestUpdateProject:
    def test_update_existing(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        ok = update_project("lenzing_planning", db_path)
        assert ok is True

    def test_update_nonexistent(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        ok = update_project("nonexistent_xyz", db_path)
        assert ok is False

    def test_update_preserves_others(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        # Update Lenzing, Honda should still be there
        update_project("lenzing_planning", db_path)
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT project_id FROM projects WHERE project_id = 'honda_planning'",
        ).fetchone()
        conn.close()
        assert row is not None


# --- Test: FTS triggers ---


class TestFTS:
    def test_fts_populated(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT * FROM facts_fts WHERE facts_fts MATCH '\"SAP\"'",
        ).fetchall()
        conn.close()
        assert len(rows) >= 1

    def test_fts_returns_matching_facts(self, index_env, db_path: Path) -> None:
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT fact FROM facts_fts WHERE facts_fts MATCH '\"demand\"'",
        ).fetchall()
        conn.close()
        assert any("Demand" in r[0] for r in rows)


# --- Test: Notes indexing (regression — never delete) ---


@pytest.fixture()
def notes_env(app_config, tmp_vault: Path, tmp_projects: Path, tmp_path: Path):
    """Set up vault with CKE-generated notes in 02_sources and 04_evergreen."""
    # Create notes in 02_sources with frontmatter
    sources_proj = tmp_vault / "02_sources" / "lenzing_planning"
    sources_proj.mkdir(parents=True, exist_ok=True)

    note1 = """\
---
title: Platform Architecture Overview
project: lenzing_planning
client: Lenzing AG
type: extract
source_type: internal
topics:
  - Architecture
  - Platform
products:
  - Blue Yonder Platform
domains:
  - Product
---
# Platform Architecture Overview

Key findings from the architecture review.
"""
    (sources_proj / "platform-architecture.md").write_text(note1, encoding="utf-8")

    note2 = """\
---
title: Security Compliance Report
project: lenzing_planning
client: Lenzing AG
type: extract
source_type: internal
topics:
  - Security
  - Compliance
products:
  - Blue Yonder WMS
---
# Security Compliance Report

SOC2 requirements and audit findings.
"""
    (sources_proj / "security-compliance.md").write_text(note2, encoding="utf-8")

    # Create note in 04_evergreen/_generated
    evergreen = tmp_vault / "04_evergreen" / "_generated"
    evergreen.mkdir(parents=True, exist_ok=True)

    note3 = """\
---
title: Supply Chain Best Practices
type: evergreen
topics:
  - Supply Chain
  - Best Practices
---
# Supply Chain Best Practices

Cross-project patterns in supply chain planning.
"""
    (evergreen / "supply-chain-best-practices.md").write_text(note3, encoding="utf-8")

    # Also add project-info and facts for index_env compatibility
    lenzing = tmp_projects / "Lenzing_Planning"
    knowledge = lenzing / "_knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)

    info = {
        "project": "Lenzing_Planning",
        "status": "active",
        "files_processed": 9,
        "products": ["Planning", "WMS"],
        "topics": ["Demand Planning", "SAP Integration", "Security"],
        "people": ["Jane Doe"],
        "rendered_at": "2026-03-08",
    }
    (knowledge / "project-info.yaml").write_text(
        yaml.dump(info),
        encoding="utf-8",
    )

    facts = {
        "project": "Lenzing_Planning",
        "total_facts": 1,
        "facts": [
            {
                "fact": "SAP integration requires custom middleware.",
                "source": "note-001",
                "source_title": "Integration Architecture",
                "topics": ["SAP Integration"],
            },
        ],
    }
    (knowledge / "facts.yaml").write_text(
        yaml.dump(facts, default_flow_style=False),
        encoding="utf-8",
    )

    return tmp_path


class TestNotesIndexing:
    """Regression tests — these ensure notes indexing can never be silently deleted."""

    def test_rebuild_indexes_notes(self, notes_env, db_path: Path) -> None:
        """rebuild_index must populate the notes table from vault markdown."""
        stats = rebuild_index(db_path)
        assert stats.notes_indexed >= 3, (
            f"Expected >= 3 notes indexed, got {stats.notes_indexed}. "
            "Notes indexing code may have been deleted."
        )

    def test_notes_table_has_rows(self, notes_env, db_path: Path) -> None:
        """The notes table must contain rows after rebuild."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        conn.close()
        assert count >= 3, f"notes table has {count} rows, expected >= 3"

    def test_notes_fts_searchable(self, notes_env, db_path: Path) -> None:
        """notes_fts must return results for indexed note titles."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT title FROM notes_fts WHERE notes_fts MATCH '\"Platform\"'",
        ).fetchall()
        conn.close()
        assert len(rows) >= 1, "FTS search for 'Platform' returned 0 results"
        assert any("Platform" in r[0] for r in rows)

    def test_notes_fts_searches_topics(self, notes_env, db_path: Path) -> None:
        """notes_fts must index topics for search."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT title FROM notes_fts WHERE notes_fts MATCH '\"Security\"'",
        ).fetchall()
        conn.close()
        assert len(rows) >= 1, "FTS search for 'Security' in topics returned 0 results"

    def test_notes_project_id_set(self, notes_env, db_path: Path) -> None:
        """Notes with project field should have project_id set."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT project_id, title FROM notes WHERE project_id = 'lenzing_planning'",
        ).fetchall()
        conn.close()
        assert len(rows) >= 2, f"Expected >= 2 Lenzing notes, got {len(rows)}"

    def test_evergreen_notes_indexed(self, notes_env, db_path: Path) -> None:
        """Notes in 04_evergreen/_generated must also be indexed."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute(
            "SELECT title FROM notes WHERE title LIKE '%Supply Chain%'",
        ).fetchall()
        conn.close()
        assert len(rows) >= 1, "Evergreen note not indexed"

    def test_meta_total_notes(self, notes_env, db_path: Path) -> None:
        """meta table must track total_notes count."""
        rebuild_index(db_path)
        meta = get_index_stats(db_path)
        assert "total_notes" in meta, "total_notes missing from meta table"
        assert int(meta["total_notes"]) >= 3

    def test_parse_frontmatter_valid(self, tmp_path: Path) -> None:
        """_parse_frontmatter must extract YAML from markdown files."""
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: Test Note\ntopics:\n  - A\n---\nBody text.\n", encoding="utf-8")
        fm = _parse_frontmatter(md)
        assert fm is not None
        assert fm["title"] == "Test Note"
        assert fm["topics"] == ["A"]

    def test_parse_frontmatter_no_yaml(self, tmp_path: Path) -> None:
        """_parse_frontmatter returns None for files without frontmatter."""
        md = tmp_path / "no_fm.md"
        md.write_text("# Just a heading\n\nNo frontmatter here.\n", encoding="utf-8")
        assert _parse_frontmatter(md) is None

    def test_parse_frontmatter_missing_file(self, tmp_path: Path) -> None:
        """_parse_frontmatter returns None for missing files."""
        assert _parse_frontmatter(tmp_path / "nonexistent.md") is None


# --- Test: Extra index roots (rfp_kb) ---


class TestExtraIndexRoots:
    """Verify INDEX_EXTRA_ROOTS adds notes from external directories."""

    def test_extra_root_indexed(
        self, notes_env, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Notes from extra roots are indexed alongside vault notes."""
        # Create an rfp_kb-like directory with markdown
        rfp_kb = tmp_path / "rfp_kb"
        rfp_kb.mkdir()

        kb_note = """\
---
title: High Availability SLA Details
id: kb-rfp-planning-0001
doc_type: rfp_response
trust_level: verified
products:
  - Blue Yonder Demand Planning
topics:
  - High Availability
  - SLA
category: technical
---
## Question
How does Blue Yonder ensure high availability?
## Answer
Blue Yonder provides 99.97% SLA with multi-region deployment.
"""
        (rfp_kb / "ha-sla.md").write_text(kb_note, encoding="utf-8")

        monkeypatch.setenv("INDEX_EXTRA_ROOTS", str(rfp_kb))
        from corp.config import get_config

        get_config.cache_clear()

        try:
            stats = rebuild_index(db_path)
            # Should include vault notes (3 from notes_env) + 1 from rfp_kb
            assert stats.notes_indexed >= 4, (
                f"Expected >= 4 notes (3 vault + 1 rfp_kb), got {stats.notes_indexed}"
            )

            # Verify rfp_kb note is searchable
            conn = _connect(db_path)
            rows = conn.execute(
                "SELECT title FROM notes_fts WHERE notes_fts MATCH '\"Availability\"'",
            ).fetchall()
            conn.close()
            assert len(rows) >= 1, "rfp_kb note not found in FTS"
        finally:
            get_config.cache_clear()

    def test_rfp_kb_frontmatter_parsed(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """rfp_kb markdown with trust_level maps to confidence column."""
        rfp_kb = tmp_path / "rfp_kb"
        rfp_kb.mkdir()

        kb_note = """\
---
title: WMS Integration Guide
id: kb-wms-001
trust_level: verified
products:
  - Blue Yonder WMS
topics:
  - WMS
  - Integration
---
Content about WMS integration.
"""
        (rfp_kb / "wms-integration.md").write_text(kb_note, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, rfp_kb)
        assert count == 1

        row = conn.execute(
            "SELECT confidence, products, topics FROM notes WHERE title = ?",
            ("WMS Integration Guide",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "verified"  # trust_level -> confidence
        assert "Blue Yonder WMS" in row[1]
        assert "WMS" in row[2]

    def test_id_only_frontmatter_indexed(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """rfp_kb entries with 'id' but no 'title' get title synthesised from id."""
        rfp_kb = tmp_path / "rfp_kb"
        rfp_kb.mkdir()

        kb_note = """\
---
id: kb-rfp-planning-0042
doc_type: rfp_response
trust_level: verified
products:
  - Blue Yonder Demand Planning
topics:
  - High Availability
  - SLA
---
## Question
How does Blue Yonder ensure high availability?
## Answer
Blue Yonder provides 99.97% SLA.
"""
        (rfp_kb / "ha-sla.md").write_text(kb_note, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, rfp_kb)
        assert count == 1

        row = conn.execute(
            "SELECT title, confidence, topics FROM notes",
        ).fetchone()
        conn.close()
        assert row is not None
        # Title synthesised from id: "kb-rfp-planning-0042" -> "Kb Rfp Planning 0042"
        assert "Kb Rfp Planning 0042" in row[0]
        assert row[1] == "verified"
        assert "High Availability" in row[2]

    def test_no_title_no_id_skipped(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """Markdown with neither title nor id is skipped."""
        rfp_kb = tmp_path / "rfp_kb"
        rfp_kb.mkdir()

        no_id_note = """\
---
doc_type: unknown
---
Some content without title or id.
"""
        (rfp_kb / "orphan.md").write_text(no_id_note, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, rfp_kb)
        conn.close()
        assert count == 0

    def test_missing_extra_root_skipped(
        self, notes_env, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-existent extra root is skipped with warning, not crash."""
        monkeypatch.setenv("INDEX_EXTRA_ROOTS", str(tmp_path / "nonexistent_kb"))
        from corp.config import get_config

        get_config.cache_clear()

        try:
            stats = rebuild_index(db_path)
            # Should still index vault notes successfully
            assert stats.notes_indexed >= 3
        finally:
            get_config.cache_clear()


# --- Test: RFP visibility ---


class TestRfpVisible:
    """Verify _compute_rfp_visible classification rules."""

    def test_product_doc_visible(self) -> None:
        fm = {"source_type": "documentation", "doc_type": "product_doc"}
        assert _compute_rfp_visible(fm) is True

    def test_rfp_response_visible(self) -> None:
        fm = {"doc_type": "rfp_response"}
        assert _compute_rfp_visible(fm) is True

    def test_architecture_doc_visible(self) -> None:
        fm = {"doc_type": "architecture"}
        assert _compute_rfp_visible(fm) is True

    def test_security_questionnaire_visible(self) -> None:
        fm = {"doc_type": "security_questionnaire"}
        assert _compute_rfp_visible(fm) is True

    def test_verified_always_visible(self) -> None:
        fm = {"trust_level": "verified"}
        assert _compute_rfp_visible(fm) is True

    def test_rfp_source_type_visible(self) -> None:
        fm = {"source_type": "rfp"}
        assert _compute_rfp_visible(fm) is True

    def test_meeting_notes_not_visible(self) -> None:
        fm = {"source_type": "meeting", "doc_type": "meeting"}
        assert _compute_rfp_visible(fm) is False

    def test_training_not_visible(self) -> None:
        fm = {"source_type": "training"}
        assert _compute_rfp_visible(fm) is False

    def test_competitive_not_visible(self) -> None:
        fm = {"source_type": "competitive"}
        assert _compute_rfp_visible(fm) is False

    def test_confidential_never_visible(self) -> None:
        fm = {"source_type": "documentation", "confidentiality": "confidential"}
        assert _compute_rfp_visible(fm) is False

    def test_restricted_never_visible(self) -> None:
        fm = {"source_type": "documentation", "confidentiality": "restricted"}
        assert _compute_rfp_visible(fm) is False

    def test_draft_never_visible(self) -> None:
        fm = {"trust_level": "draft", "source_type": "documentation"}
        assert _compute_rfp_visible(fm) is False

    def test_empty_frontmatter_not_visible(self) -> None:
        assert _compute_rfp_visible({}) is False

    def test_confidential_overrides_verified(self) -> None:
        """Confidentiality check runs before trust_level."""
        fm = {"trust_level": "verified", "confidentiality": "confidential"}
        assert _compute_rfp_visible(fm) is False

    def test_rfp_visible_column_in_rebuild(self, notes_env, db_path: Path) -> None:
        """rebuild_index populates rfp_visible column."""
        rebuild_index(db_path)
        conn = _connect(db_path)
        rows = conn.execute("SELECT title, rfp_visible FROM notes").fetchall()
        conn.close()
        assert len(rows) >= 3
        # All test notes have source_type=internal or no source_type,
        # so rfp_visible should be 0 for most
        rfp_values = {r[0]: r[1] for r in rows}
        assert all(isinstance(v, int) for v in rfp_values.values())


# --- Test: Index-level dedup ---


class TestIndexDedup:
    """Index-level dedup uses source_hash (content identity), not path."""

    def test_dedup_by_source_hash(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """Notes with same source_hash are deduped — only latest kept."""
        vault = tmp_path / "dedup_vault"
        vault.mkdir()

        # Two notes with the same source_hash but different paths
        note1 = """\
---
title: First Version
source_hash: deadbeef1234
source_path: C:/MyWork/old/file.pptx
extracted_at: "2026-03-01"
---
First extraction.
"""
        note2 = """\
---
title: Second Version
source_hash: deadbeef1234
source_path: C:/MyWork/new/file.pptx
extracted_at: "2026-03-20"
---
Second extraction (newer, same content hash).
"""
        (vault / "note_v1.md").write_text(note1, encoding="utf-8")
        (vault / "note_v2.md").write_text(note2, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, vault)

        # _index_cke_notes inserts both; dedup happens in rebuild_index
        # Call dedup manually here

        dupes = _dedup_notes_by_hash(conn)
        count -= dupes

        assert count == 1, f"Expected 1 after dedup, got {count}"

        rows = conn.execute("SELECT title FROM notes").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "Second Version"

    def test_different_hash_kept(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """Notes with different source_hash are both kept."""
        vault = tmp_path / "diff_hash_vault"
        vault.mkdir()

        note1 = """\
---
title: File A
source_hash: hash_aaa
---
Content A.
"""
        note2 = """\
---
title: File B
source_hash: hash_bbb
---
Content B.
"""
        (vault / "a.md").write_text(note1, encoding="utf-8")
        (vault / "b.md").write_text(note2, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, vault)

        dupes = _dedup_notes_by_hash(conn)
        count -= dupes

        assert count == 2

        rows = conn.execute("SELECT title FROM notes").fetchall()
        conn.close()
        assert len(rows) == 2

    def test_no_dedup_for_empty_hash(self, app_config, db_path: Path, tmp_path: Path) -> None:
        """Notes without source_hash are NOT deduped."""
        vault = tmp_path / "no_dedup_vault"
        vault.mkdir()

        for i in range(3):
            note = f"""\
---
title: Note {i}
---
Content {i}.
"""
            (vault / f"note_{i}.md").write_text(note, encoding="utf-8")

        conn = _connect(db_path)
        _ensure_schema(conn)
        count = _index_cke_notes(conn, vault)

        dupes = _dedup_notes_by_hash(conn)
        count -= dupes
        conn.close()

        assert count == 3
