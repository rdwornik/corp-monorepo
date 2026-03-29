"""Pipeline test runner — end-to-end smoke test with full isolation.

Runs key pipeline stages in a temporary sandbox to verify configuration
and code correctness before running against production data.

Fixture mode (default): skips CKE API calls, uses mock extraction notes (~2s).
  If recorded fixtures exist in tests/fixtures/pipeline/recorded/, they are
  replayed instead of the hardcoded mock notes.

Live mode: makes real CKE API calls (costs money, requires GEMINI_API_KEY).

Record mode (--record): live mode + saves each extraction to a fixture JSON
  keyed by {content_hash[:12]}_{tier}.json so future fixture-mode runs replay
  real CKE output instead of mock notes.

Usage::

    from corp.test_pipeline import run_pipeline_test
    from corp.schema.pipeline_config import PipelineConfig
    report = run_pipeline_test(PipelineConfig.production())
    if not report.all_passed:
        for step in report.steps:
            if not step.passed:
                print(f"FAIL {step.name}: {step.detail}")
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from corp.schema.pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)

CHECK = "[bold green]PASS[/bold green]"
CROSS = "[bold red]FAIL[/bold red]"

# Path to recorded-fixture directory, relative to this source file.
# src/corp/test_pipeline.py  ->  ../../tests/fixtures/pipeline/recorded
_RECORDED_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "pipeline" / "recorded"
_CORPUS_DIR = _RECORDED_DIR.parent / "corpus"


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
    recorded_fixtures: int = 0
    recording_cost: float = 0.0

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
    record: bool = False,
) -> PipelineTestReport:
    """Run the pipeline smoke test in an isolated sandbox.

    Args:
        config: PipelineConfig (reserved for future production-impact checks).
        fixture_mode: Skip CKE API calls; use mock extraction notes instead.
            If recorded fixtures exist in tests/fixtures/pipeline/recorded/,
            they are replayed instead of hardcoded mock notes.
        verbose: Enable DEBUG logging during the run.
        tmp_root: Inject a temp directory (tests use pytest tmp_path).
                  Created via tempfile if None.
        keep_sandbox: Keep the sandbox directory after the run (for inspection).
        record: Run live CKE extraction and save responses as fixture JSONs.
            Implies fixture_mode=False (live API calls are made).

    Returns:
        PipelineTestReport with a StepResult for each pipeline stage.
    """
    if verbose:
        logging.getLogger("corp").setLevel(logging.DEBUG)

    from corp.sandbox import SandboxManager

    _owns_tmp = tmp_root is None
    if _owns_tmp:
        tmp_root = Path(tempfile.mkdtemp(prefix="corp_pipeline_test_"))

    _record_state: dict = {"fixtures": 0, "cost": 0.0}

    # --record implies live mode
    effective_fixture_mode = fixture_mode and not record

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
                detail = step_fn(
                    sb,
                    fixture_mode=effective_fixture_mode,
                    record=record,
                    _record_state=_record_state,
                )
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

    report.recorded_fixtures = _record_state["fixtures"]
    report.recording_cost = _record_state["cost"]
    return report


# ---------------------------------------------------------------------------
# Rich console formatter
# ---------------------------------------------------------------------------


def format_report(report: PipelineTestReport) -> None:
    """Print a Rich-formatted pipeline test report to stdout.

    Uses a Panel + Table layout for ADHD-scannable output.
    Exits with status 0/1 based on report.all_passed (caller responsibility).
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    _console = Console()

    table = Table(show_lines=False, box=None, pad_edge=False)
    table.add_column("Step", style="cyan", min_width=24)
    table.add_column("Status", justify="center", min_width=8)
    table.add_column("Time", justify="right", min_width=7)
    table.add_column("Detail", style="dim")

    for step in report.steps:
        status_text = (
            Text("PASS", style="bold green") if step.passed else Text("FAIL", style="bold red")
        )
        table.add_row(
            step.name,
            status_text,
            f"{step.duration_s:.2f}s",
            step.detail,
        )

    passed = sum(1 for s in report.steps if s.passed)
    total = len(report.steps)
    if report.all_passed:
        summary = f"[bold green]{passed}/{total} passed[/bold green]"
    else:
        summary = f"[bold red]{passed}/{total} passed[/bold red]"

    title = f"Pipeline Smoke Test  {summary}"
    _console.print(Panel(table, title=title, border_style="green" if report.all_passed else "red"))

    if report.sandbox_path:
        _console.print(f"[dim]Sandbox: {report.sandbox_path}[/dim]")


# ---------------------------------------------------------------------------
# Step implementations
# Each function: (sb, *, fixture_mode, record, _record_state) -> str
# Return a detail string on success; raise AssertionError/Exception on failure.
# ---------------------------------------------------------------------------


def _test_sandbox_init(
    sb,
    *,
    fixture_mode: bool,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
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


def _test_classify_and_rename(
    sb,
    *,
    fixture_mode: bool,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
    """Verify type code and client alias resolution against naming_config.yaml."""
    from corp.ingest.naming_config import get_client_alias, get_type_code

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


def _test_vault_ingest(
    sb,
    *,
    fixture_mode: bool,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
    """Write extraction notes into the sandbox vault.

    Fixture mode priority:
      1. Recorded fixtures (tests/fixtures/pipeline/recorded/) — real CKE output
      2. Hardcoded mock notes — always available fallback

    Live / record mode: invokes real CKE on corpus fixture files.
    """
    from corp.ingest.extractions import ingest_extractions

    if not fixture_mode:
        return _test_extract(sb, record=record, _record_state=_record_state)

    # --- Fixture mode: try recorded fixtures first ---
    recorded_manifest = _RECORDED_DIR / "manifest.json"
    if recorded_manifest.exists():
        return _replay_recorded_fixtures(sb, recorded_manifest)

    # --- Fall back to hardcoded mock notes ---
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


def _test_index_rebuild(
    sb,
    *,
    fixture_mode: bool,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
    """Rebuild the SQLite search index against the sandbox vault."""
    from corp.index_builder import rebuild_index

    stats = rebuild_index(config=sb.config)

    return (
        f"index rebuilt: {stats.projects_indexed} projects, "
        f"{stats.facts_indexed} facts, {stats.notes_indexed} notes"
    )


def _test_retrieve(
    sb,
    *,
    fixture_mode: bool,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
    """Run a search query against the sandbox index to verify the query engine."""
    from corp.query_engine import search_facts

    results = search_facts(query="test", db_path=sb.config.index_db_path)

    # Sandbox has no real facts, so empty result is expected — we only verify no crash
    return f"query ok: {len(results)} results"


# ---------------------------------------------------------------------------
# Private helpers — live extraction and fixture replay
# ---------------------------------------------------------------------------


def _test_extract(
    sb,
    *,
    record: bool = False,
    _record_state: dict | None = None,
) -> str:
    """Run real CKE extraction on corpus files (live / record mode).

    Processes each corpus file individually so we can map
    content_hash → extracted notes for recording.

    When record=True, saves per-file fixture JSONs to _RECORDED_DIR and
    writes a manifest.json with model, date, and total cost.
    """
    from corp.extraction.manifest_emitter import _resolve_doc_type
    from corp.ingest.extractions import ingest_extractions
    from corp.ingest.router import compute_file_hash
    from corp.overnight.cke_client import extract_sync, is_available, scan_local

    ok, err = is_available()
    if not ok:
        return f"skipped (CKE not available: {err})"

    if not _CORPUS_DIR.exists():
        return "skipped (corpus dir not found)"

    corpus_files = sorted(f for f in _CORPUS_DIR.iterdir() if f.is_file() and f.suffix != ".json")
    if not corpus_files:
        return "no corpus files to extract"

    # Tier 1 scan — local metadata only, no API cost
    scan_results = scan_local(_CORPUS_DIR)
    scan_by_name = {r["filename"]: r for r in scan_results if not r.get("error")}

    if record:
        _RECORDED_DIR.mkdir(parents=True, exist_ok=True)

    total_cost = 0.0
    total_done = 0
    recorded_entries: list[dict] = []

    for f_path in corpus_files:
        meta = scan_by_name.get(f_path.name, {})
        content_hash = meta.get("file_hash") or compute_file_hash(f_path)
        tier = meta.get("tier", 0)

        # Per-file staging dir so extracted notes map 1:1 to source file
        staging_dir = sb.config.mywork_root / "_cke_staging" / f_path.stem
        staging_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": 1,
            "project": "pipeline_test",
            "output_dir": str(staging_dir),
            "files": [
                {
                    "id": f_path.stem.replace(" ", "_"),
                    "path": str(f_path),
                    "doc_type": _resolve_doc_type(f_path.suffix),
                    "name": f_path.stem,
                    "content_origin": "pipeline_test",
                    "source_category": "test",
                }
            ],
        }

        manifest_path = staging_dir.parent / f"{f_path.stem}_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        result = extract_sync(manifest_path)
        file_cost = result.get("cost", 0.0)
        file_done = result.get("done", 0)
        total_cost += file_cost
        total_done += file_done

        if record and file_done > 0:
            notes = [
                {"filename": md.name, "content": md.read_text(encoding="utf-8")}
                for md in sorted(staging_dir.rglob("*.md"))
            ]
            fixture_filename = f"{content_hash[:12]}_{tier}.json"
            fixture_data = {
                "source_file": f_path.name,
                "content_hash": content_hash,
                "tier": tier,
                "extracted_at": datetime.now().isoformat(timespec="seconds"),
                "cost": file_cost,
                "notes": notes,
            }
            (_RECORDED_DIR / fixture_filename).write_text(
                json.dumps(fixture_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            recorded_entries.append(
                {
                    "source_file": f_path.name,
                    "content_hash": content_hash[:12],
                    "tier": tier,
                    "fixture_file": fixture_filename,
                }
            )

        if file_done > 0:
            ingest_result = ingest_extractions(staging_dir, sb.config.vault_path)
            if ingest_result.errors:
                logger.warning("Ingest errors for %s: %s", f_path.name, ingest_result.errors)

    if record and recorded_entries:
        rec_manifest = {
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "model": _get_cke_model(),
            "total_cost": round(total_cost, 6),
            "fixtures": recorded_entries,
        }
        (_RECORDED_DIR / "manifest.json").write_text(
            json.dumps(rec_manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if _record_state is not None:
            _record_state["fixtures"] += len(recorded_entries)
            _record_state["cost"] += total_cost

    suffix = f", {len(recorded_entries)} fixtures recorded" if record else ""
    return f"{total_done} files extracted, cost ${total_cost:.4f}{suffix}"


def _replay_recorded_fixtures(sb, manifest_path: Path) -> str:
    """Reconstruct CKE output_v2 from saved fixture JSONs and ingest into sandbox.

    This is the fast, free replay path used when recorded fixtures exist.
    """
    from corp.ingest.extractions import ingest_extractions

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_dir = manifest_path.parent

    cke_out = sb.config.mywork_root / "_cke_output"
    total_notes = 0

    for entry in manifest.get("fixtures", []):
        fixture_file = fixture_dir / entry["fixture_file"]
        if not fixture_file.exists():
            logger.warning("Fixture file missing: %s", fixture_file)
            continue

        fixture_data = json.loads(fixture_file.read_text(encoding="utf-8"))
        source_stem = Path(entry["source_file"]).stem.replace(" ", "_")

        # Reconstruct output_v2 layout: source_library/{source_stem}/extract/
        extract_dir = cke_out / "source_library" / source_stem / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        for note in fixture_data.get("notes", []):
            (extract_dir / note["filename"]).write_text(note["content"], encoding="utf-8")
            total_notes += 1

    result = ingest_extractions(cke_out, sb.config.vault_path)
    if result.errors:
        raise AssertionError(f"ingest errors: {result.errors}")

    model = manifest.get("model", "?")
    recorded_at = manifest.get("recorded_at", "?")
    return (
        f"{total_notes} recorded notes replayed "
        f"(model={model}, recorded={recorded_at}), "
        f"{result.notes_ingested} ingested"
    )


def _get_cke_model() -> str:
    """Best-effort read of the active model name from CKE config."""
    try:
        from corp.overnight.cke_client import load_cke_config

        cfg = load_cke_config()
        return cfg.get("model_override") or cfg.get("default_model") or cfg.get("model") or "gemini"
    except Exception:
        return "gemini"
