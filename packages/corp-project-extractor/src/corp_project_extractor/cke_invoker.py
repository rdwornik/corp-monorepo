"""Invoke corp-knowledge-extractor's batch CLI.

Runs CKE as a subprocess -- maintains CLI boundary per orchestrator pattern.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# CKE location -- env var > monorepo > standalone fallback
CKE_DIR = Path(
    os.environ.get(
        "CKE_PATH",
        "C:/Users/1028120/Documents/Scripts/corp-monorepo/packages/corp-knowledge-extractor",
    )
)


def _resolve_cke_python(cke: Path) -> tuple[str, ...]:
    """Resolve how to invoke CKE: venv python > installed cke CLI > sys.executable.

    Returns:
        Command prefix tuple (python, script) or (cke_cli,).
    """
    # 1. Per-package venv (standalone layout)
    cke_python = cke / "venv" / "Scripts" / "python.exe"
    run_script = cke / "scripts" / "run.py"
    if cke_python.exists() and run_script.exists():
        return (str(cke_python), str(run_script))

    # 2. CKE installed as CLI entry point (monorepo / pip install -e)
    cke_cli = shutil.which("cke")
    if cke_cli:
        return (cke_cli,)

    # 3. Current Python with run.py
    if run_script.exists():
        return (sys.executable, str(run_script))

    raise FileNotFoundError(f"CKE not found. Checked: {cke_python}, PATH, {run_script}")


def invoke_cke_batch(
    manifest_path: Path,
    resume: bool = True,
    max_rpm: int = 100,
    cke_dir: Path | None = None,
) -> subprocess.CompletedProcess:
    """Invoke CKE's process-manifest command.

    Args:
        manifest_path: Path to cke_manifest.json
        resume: Skip already-completed files
        max_rpm: Max Gemini API requests per minute
        cke_dir: Override CKE installation directory

    Returns:
        CompletedProcess with return code
    """
    cke = cke_dir or CKE_DIR
    prefix = _resolve_cke_python(cke)

    cmd = [
        *prefix,
        "process-manifest",
        str(manifest_path.resolve()),
        "--max-rpm",
        str(max_rpm),
    ]

    if resume:
        cmd.append("--resume")

    logger.info("Invoking CKE: %s", " ".join(cmd))

    # Stream output to terminal in real-time
    result = subprocess.run(
        cmd,
        cwd=str(cke),
        capture_output=False,
        text=True,
    )

    if result.returncode != 0:
        logger.error("CKE exited with code %d", result.returncode)
    else:
        logger.info("CKE batch processing completed successfully")

    return result
