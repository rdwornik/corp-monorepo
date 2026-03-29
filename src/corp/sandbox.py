"""SandboxManager: isolated pipeline environment for tests.

Creates a fully isolated copy of the pipeline environment in a temp directory.
All databases (ops.db, index.db, overnight_state.db) are initialized with the
real schema code — no DDL duplication.

Usage::

    with SandboxManager.context(tmp_path) as sb:
        # sb.config is a PipelineConfig pointing entirely at tmp_path
        ops = OpsDB(config=sb.config)
        ...
"""

from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from corp.schema.pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)


class SandboxManager:
    """Manages an isolated sandbox environment for pipeline testing."""

    def __init__(self, tmp_root: Path) -> None:
        self.tmp_root = tmp_root
        self.config = PipelineConfig.sandbox(tmp_root)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(self) -> SandboxManager:
        """Create directory structure and initialize all databases."""
        self._create_dirs()
        self._init_databases()
        return self

    def _create_dirs(self) -> None:
        """Create the sandbox directory tree."""
        dirs = [
            self.config.vault_path,
            self.config.mywork_root,
            self.config.projects_root,
            self.config.templates_root,
            self.config.archive_root,
            self.config.app_data_path,
            self.config.inbox_path,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _init_databases(self) -> None:
        """Initialize ops.db, index.db, and overnight_state.db schemas.

        Delegates to the real schema code in each module so DDL is never
        duplicated here.
        """
        from corp.index_builder import _SCHEMA as INDEX_SCHEMA
        from corp.ops.database import OpsDB
        from corp.overnight.state import OvernightState

        # ops.db — touch conn to trigger _init_schema()
        ops = OpsDB(config=self.config)
        _ = ops.conn  # lazily opens + runs schema
        ops.close()

        # overnight_state.db — constructor runs schema immediately
        state = OvernightState(config=self.config)
        state.close()

        # index.db — run schema directly (rebuild_index would do a full scan)
        import sqlite3

        self.config.index_db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.config.index_db_path))
        conn.executescript(INDEX_SCHEMA)
        conn.commit()
        conn.close()
        logger.debug("Sandbox databases initialized at %s", self.config.app_data_path)

    # ------------------------------------------------------------------
    # Corpus staging
    # ------------------------------------------------------------------

    def stage_files(self, source_dir: Path) -> list[Path]:
        """Copy files from source_dir into sandbox inbox.

        Returns the list of staged destination paths.
        """
        staged: list[Path] = []
        for src in source_dir.iterdir():
            if src.is_file():
                dst = self.config.inbox_path / src.name
                shutil.copy2(src, dst)
                staged.append(dst)
        return staged

    def snapshot_production(self, ops_db_path: Path | None = None) -> None:
        """Copy a production ops.db snapshot into the sandbox for read-only tests.

        If ops_db_path is None, skips silently (production DB may not exist in CI).
        """
        if ops_db_path is None or not ops_db_path.exists():
            logger.debug("No production ops.db to snapshot; skipping")
            return
        dst = self.config.ops_db_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ops_db_path, dst)
        logger.debug("Snapshot copied: %s -> %s", ops_db_path, dst)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def teardown(self, retries: int = 5, delay: float = 0.2) -> None:
        """Remove sandbox directory tree with retry for Windows file locks."""
        for attempt in range(retries):
            try:
                shutil.rmtree(self.tmp_root, ignore_errors=False)
                return
            except PermissionError:
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    logger.warning(
                        "Could not fully remove sandbox at %s after %d attempts",
                        self.tmp_root,
                        retries,
                    )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    @classmethod
    @contextmanager
    def context(cls, tmp_root: Path) -> Generator[SandboxManager, None, None]:
        """Context manager that creates and tears down the sandbox.

        Example::

            with SandboxManager.context(tmp_path) as sb:
                ops = OpsDB(config=sb.config)
        """
        sb = cls(tmp_root).create()
        try:
            yield sb
        finally:
            # tmp_path is managed by pytest; teardown only if we own it
            pass
