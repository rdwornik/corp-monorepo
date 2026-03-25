"""Pipeline test runner — end-to-end smoke test with full isolation.

Runs key pipeline stages in a temporary sandbox to verify configuration
and code correctness before running against production data.

Fixture mode (default): skips CKE API calls, uses mock extraction notes (~2s).
Live mode: makes real CKE API calls (costs money, requires GEMINI_API_KEY).

Usage::

    from corp_by_os.test_pipeline import run_pipeline_test
    from corp_os_meta.pipeline_config import PipelineConfig
    report = run_pipeline_test(PipelineConfig.production())
    if not report.all_passed:
        for step in report.steps:
            if not step.passed:
                print(f"FAIL {step.name}: {step.detail}")
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from corp_os_meta.pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public data model
# ---------------------------------------------------------------------------


@dataclass
class StepResult:
    """Result of a single pipeline test step."""

    name: str
    passed: bool
    duration_s: float
    detail: str = ""


@dataclass
class PipelineTestReport:
    """Aggregated results from a pipeline smoke test run."""

    steps: list[StepResult] = field(default_factory=list)
    sandbox_path: Path | None = None

    @property
    def all_passed(self) -> bool:
        """True if every step passed (and at least one step ran)."""
        return bool(self.steps) and all(s.passed for s in self.steps)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_pipeline_test(
    config: PipelineConfig,
    fixture_mode: bool = True,
    verbose: bool = False,
    tmp_root: Path | None = None,
    keep_sandbox: bool = False,
) -> PipelineTestReport:
    """Run the pipeline smoke test in an isolated sandbox.

    Args:
        config: PipelineConfig (reserved for future production-impact checks).
        fixture_mode: Skip CKE API calls; use mock extraction notes instead.
        verbose: Enable DEBUG logging during the run.
        tmp_root: Inject a temp directory (tests use pytest tmp_path).
                  Created via tempfile if None.
        keep_sandbox: Keep the sandbox directory after the run (for inspection).

    Returns:
        PipelineTestReport with a StepResult for each pipeline stage.
    """
    if verbose:
        logging.getLogger("corp_by_os").setLevel(logging.DEBUG)

    from corp_by_os.sandbox import SandboxManager

    _owns_tmp = tmp_root is None
    if _owns_tmp:
        tmp_root = Path(tempfile.mkdtemp(prefix="corp_pipeline_test_"))

    try:
        sb = SandboxManager(tmp_root).create()
        report = PipelineTestReport(sandbox_path=tmp_root)

        _steps = [
            _test_sandbox_init,
            _test_classify_and_rename,
            _test_vault_ingest,
            _test_index_rebuild,
            _test_retrieve,
        ]

        for step_fn in _steps:
            t0 = time.perf_counter()
            try:
                detail = step_fn(sb, fixture_mode=fixture_mode)
                passed = True
            except Exception as exc:
                detail = str(exc)
                passed = False
                logger.warning("Step %s failed: %s", step_fn.__name__, exc, exc_info=verbose)
            duration = time.perf_counter() - t0
            report.steps.append(
                StepResult(
                    name=step_fn.__name__.removeprefix("_test_"),
                    passed=passed,
                    duration_s=round(duration, 3),
                    detail=detail,
                )
            )

    finally:
        if _owns_tmp and not keep_sandbox:
            shutil.rmtree(tmp_root, ignore_errors=True)

    return report


# ---------------------------------------------------------------------------
# Step implementations
# Each function: (sb: SandboxManager, *, fixture_mode: bool) -> str
# Return a detail string on success; raise AssertionError/Exception on failure.
# ---------------------------------------------------------------------------


def _test_sandbox_init(sb, *, fixture_mode: bool) -> str:
    """Verify sandbox directory structure and all three databases were created."""
    checks = [
        ("ops.db", sb.config.ops_db_path),
        ("index.db", sb.config.index_db_path),
        ("overnight_state.db", sb.config.state_db_path),
        ("inbox", sb.config.inbox_path),
        ("vault", sb.config.vault_path),
    ]
    missing = [name for name, path in checks if not path.exists()]
    if missing:
        raise AssertionError(f"sandbox missing: {', '.join(missing)}")
    return "3 databases, inbox, vault ready"


def _test_classify_and_rename(sb, *, fixture_mode: bool) -> str:
    """Verify type code and client alias resolution against naming_config.yaml."""
    from corp_by_os.ingest.naming_config import get_client_alias, get_type_code

    checks = [
        # (label, actual, expected)
        ("SOW filename hint", get_type_code(filename="ACME_SOW_implementation.docx"), "SOW"),
        ("presentation doc_type", get_type_code(doc_type="presentation"), "PRES"),
        ("lenzing alias", get_client_alias("Lenzing"), "LENZ"),
        ("jlr alias", get_client_alias("Jaguar Land Rover"), "JLR"),
        ("unknown client fallback", get_client_alias(None), "GEN"),
    ]

    failures = [
        f"{label}: expected {exp!r}, got {actual!r}"
        for label, actual, exp in checks
        if actual != exp
    ]
    if failures:
        raise AssertionError("; ".join(failures))

    return f"{len(checks)} naming checks passed"


def _test_vault_ingest(sb, *, fixture_mode: bool) -> str:
    """Write mock CKE extraction notes and ingest them into the sandbox vault.

    In fixture mode, creates two minimal notes without making API calls.
    In live mode, this step would invoke CKE on real files (not yet implemented).
    """
    from corp_by_os.ingest.extractions import ingest_extractions

    if not fixture_mode:
        # Live mode: would invoke CKE on corpus files — not yet implemented
        return "skipped (live mode not yet implemented)"

    # Build a minimal CKE output_v2 structure
    cke_out = sb.config.mywork_root / "_cke_output"
    pkg_dir = cke_out / "source_library" / "test_series"
    extract_dir = pkg_dir / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)

    _mock_notes = [
        ("test_note_alpha.md", "Test Note Alpha", "Pipeline smoke test note A."),
        ("test_note_beta.md", "Test Note Beta", "Pipeline smoke test note B."),
    ]
    for filename, title, body in _mock_notes:
        content = f"---\ntitle: {title}\ntrust_level: extracted\n---\n{body}\n"
        (extract_dir / filename).write_text(content, encoding="utf-8")

    result = ingest_extractions(cke_out, sb.config.vault_path)

    if result.errors:
        raise AssertionError(f"ingest errors: {result.errors}")

    ingested = list(sb.config.vault_path.glob("01_Knowledge/*.md"))
    if len(ingested) < len(_mock_notes):
        raise AssertionError(
            f"expected {len(_mock_notes)} notes in 01_Knowledge/, found {len(ingested)}"
        )

    return f"{result.notes_ingested} notes ingested, 0 errors"


def _test_index_rebuild(sb, *, fixture_mode: bool) -> str:
    """Rebuild the SQLite search index against the sandbox vault."""
    from corp_by_os.index_builder import rebuild_index

    stats = rebuild_index(config=sb.config)

    return (
        f"index rebuilt: {stats.projects_indexed} projects, "
        f"{stats.facts_indexed} facts, {stats.notes_indexed} notes"
    )


def _test_retrieve(sb, *, fixture_mode: bool) -> str:
    """Run a search query against the sandbox index to verify the query engine."""
    from corp_by_os.query_engine import search_facts

    results = search_facts(query="test", db_path=sb.config.index_db_path)

    # Sandbox has no real facts, so empty result is expected — we only verify no crash
    return f"query ok: {len(results)} results"
