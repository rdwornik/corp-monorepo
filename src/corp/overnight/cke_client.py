"""Subprocess wrapper around CKE CLI.

Enforces the corp → CKE process boundary (Architecture Rule,
ECOSYSTEM.md): no direct Python imports from corp.extractor.
All operations invoke `cke` via subprocess.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from corp.schema.folder_names import ARCHIVE

logger = logging.getLogger(__name__)

# Resolve CKE package directory — same env-var pattern as CPE's cke_invoker.py
_CKE_DIR = Path(
    os.environ.get(
        "CKE_PATH",
        str(Path(__file__).parents[3] / "src" / "corp" / "extractor"),
    )
)


def _resolve_cke_cmd() -> tuple[str, ...]:
    """Return the command tuple to invoke the `cke` CLI.

    Resolution order (mirrors CPE's cke_invoker.py):
    1. Per-package venv/Scripts/python.exe + scripts/run.py
    2. `cke` on PATH (pip-installed globally or in active venv)
    3. Active sys.executable + scripts/run.py
    """
    run_script = _CKE_DIR / "scripts" / "run.py"

    # Prefer per-package venv if present
    cke_python = _CKE_DIR / "venv" / "Scripts" / "python.exe"
    if cke_python.exists() and run_script.exists():
        return (str(cke_python), str(run_script))

    # Fall back to PATH-installed cke (most common case)
    cke_cli = shutil.which("cke")
    if cke_cli:
        return (cke_cli,)

    # Last resort: run.py via active interpreter
    if run_script.exists():
        return (sys.executable, str(run_script))

    raise FileNotFoundError(
        f"Cannot locate `cke` CLI. CKE_DIR={_CKE_DIR}, PATH cke={shutil.which('cke')}"
    )


def is_available() -> tuple[bool, str]:
    """Check if the `cke` CLI is reachable. Returns (ok, error_message)."""
    if shutil.which("cke"):
        return True, ""

    cke_python = _CKE_DIR / "venv" / "Scripts" / "python.exe"
    run_script = _CKE_DIR / "scripts" / "run.py"
    if cke_python.exists() and run_script.exists():
        return True, ""

    return False, f"cke not found on PATH and no venv at {_CKE_DIR}"


def load_cke_config() -> dict[str, Any]:
    """Best-effort read of CKE config from settings.yaml.

    Used only by test_pipeline.py to resolve the active model name for
    fixture recording. In subprocess mode, CKE owns its config — we read
    the YAML directly rather than importing CKE internals.
    Returns empty dict on any failure (callers must handle gracefully).
    """
    settings_path = _CKE_DIR / "config" / "settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        import yaml  # already a dep via corp.schema

        with open(settings_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception as exc:
        logger.debug("Could not read CKE settings.yaml: %s", exc)
        return {}


def estimate_cost(manifest_path: Path) -> dict[str, Any]:
    """Not supported in subprocess mode.

    This function had no production callers before the subprocess
    migration. Use `cke process-manifest --dry-run-tiers` instead.
    """
    raise NotImplementedError(
        "estimate_cost() is not available in subprocess mode. "
        "Run `cke process-manifest --dry-run-tiers <manifest>` for cost estimates."
    )


def _parse_summary(stdout: str) -> dict[str, Any]:
    """Parse the human-readable summary that `cke process-manifest` prints.

    Rich strips markup when stdout is a pipe (non-TTY), so we get plain
    text like "Done: 5\nErrors: 0\n...". ANSI codes are stripped
    defensively in case Rich's TTY detection misfires.
    """
    done = 0
    error = 0
    skipped = 0
    total = 0
    cost = 0.0
    tiers: dict[int, int] = {}

    for line in stdout.splitlines():
        # Defensive: strip any residual ANSI escape codes
        line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()

        m = re.match(r"Done:\s*(\d+)", line)
        if m:
            done = int(m.group(1))
            continue
        m = re.match(r"Errors:\s*(\d+)", line)
        if m:
            error = int(m.group(1))
            continue
        m = re.match(r"Skipped:\s*(\d+)", line)
        if m:
            skipped = int(m.group(1))
            continue
        m = re.match(r"Total:\s*(\d+)", line)
        if m:
            total = int(m.group(1))
            continue
        m = re.match(r"Estimated API cost:\s*\$([0-9.]+)", line)
        if m:
            cost = float(m.group(1))
            continue
        # "Tiers: local=N, text-AI=N, multimodal=N"
        m = re.match(r"Tiers:\s*local=(\d+),\s*text-AI=(\d+),\s*multimodal=(\d+)", line)
        if m:
            tiers = {1: int(m.group(1)), 2: int(m.group(2)), 3: int(m.group(3))}

    return {
        "done": done,
        "error": error,
        "skipped": skipped,
        "total": total,
        "cost": cost,
        "tiers": tiers,
    }


def _run_cke(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a CKE CLI command, capturing output for parsing.

    Uses encoding="utf-8" + errors="replace" to handle Windows cp1252
    and Rich box-drawing characters that cause UnicodeDecodeError when
    text=True defaults to the system code page.
    """
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def extract_batch(
    manifest_path: Path,
    model: str | None = None,
    poll_interval: int = 60,
    timeout: int = 28800,
    resume: bool = True,
) -> dict[str, Any]:
    """Submit manifest to Gemini Batch API via `cke process-manifest --batch`.

    Args:
        manifest_path: Path to CKE-compatible manifest JSON.
        model: Gemini model override (None = use CKE default).
        poll_interval: Seconds between batch status checks.
        timeout: Max wait time in seconds (default 8h).
        resume: Skip already-completed files.

    Returns: {total, done, error, skipped, cost, tiers}
    """
    cmd = list(_resolve_cke_cmd()) + [
        "process-manifest",
        str(manifest_path),
        "--batch",
        f"--batch-poll-interval={poll_interval}",
        f"--batch-timeout={timeout}",
    ]
    if model:
        cmd += ["--model", model]
    if resume:
        cmd.append("--resume")

    logger.info("extract_batch: %s", " ".join(str(c) for c in cmd))
    result = _run_cke(cmd)

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0:
        logger.error(
            "cke process-manifest --batch failed (rc=%d):\n%s",
            result.returncode,
            result.stderr,
        )

    summary = _parse_summary(result.stdout)
    logger.info("extract_batch summary: %s", summary)
    return summary


def extract_sync(
    manifest_path: Path,
    model: str | None = None,
    max_rpm: int = 80,
    resume: bool = True,
) -> dict[str, Any]:
    """Synchronous extraction via `cke process-manifest`.

    Args:
        manifest_path: Path to CKE-compatible manifest JSON.
        model: Gemini model override.
        max_rpm: Max requests per minute.
        resume: Skip already-completed files.

    Returns: {total, done, error, skipped, cost, tiers}
    """
    cmd = list(_resolve_cke_cmd()) + [
        "process-manifest",
        str(manifest_path),
        f"--max-rpm={max_rpm}",
    ]
    if model:
        cmd += ["--model", model]
    if resume:
        cmd.append("--resume")

    logger.info("extract_sync: %s", " ".join(str(c) for c in cmd))
    result = _run_cke(cmd)

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0:
        logger.error(
            "cke process-manifest failed (rc=%d):\n%s",
            result.returncode,
            result.stderr,
        )

    summary = _parse_summary(result.stdout)
    logger.info("extract_sync summary: %s", summary)
    return summary


def scan_local(
    path: Path,
    recursive: bool = True,
    exclude: tuple[str, ...] = (
        ARCHIVE,
        ".corp",
        "_knowledge",
        ".venv",
        "__pycache__",
        ".git",
    ),
) -> list[dict]:
    """Run CKE Tier 1 local scan via `cke scan` — no API calls.

    Returns:
        List of FileScanResult dicts with keys:
        path, filename, extension, size_bytes, file_hash, tier, metadata, error
    """
    # Write scan output to a temp file so we get structured JSON back
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = list(_resolve_cke_cmd()) + ["scan", str(path), "-o", str(tmp_path)]
        if not recursive:
            cmd.append("--no-recursive")
        for ex in exclude:
            cmd += ["--exclude", ex]

        logger.info("scan_local: %s", " ".join(str(c) for c in cmd))
        result = _run_cke(cmd)

        if result.returncode != 0:
            logger.error("cke scan failed (rc=%d):\n%s", result.returncode, result.stderr)
            return []

        if not tmp_path.exists():
            logger.warning("cke scan produced no output file")
            return []

        data = json.loads(tmp_path.read_text(encoding="utf-8"))
        return data.get("results", [])

    except (FileNotFoundError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        logger.error("scan_local failed: %s", exc)
        return []
    finally:
        tmp_path.unlink(missing_ok=True)
