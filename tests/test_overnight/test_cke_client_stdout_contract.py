"""Pins the cke_client <-> CKE stdout-literal-line response contract.

Ground truth: docs/audits/2026-07-16-architecture-ground-truth.md Sec2 row 244.

corp.overnight.cke_client.extract_sync() shells out to the `cke` CLI and parses its
plain-text summary lines back into a dict via _parse_summary() (cke_client.py:109-159).
The audit flagged this as a fragile contract with NO test coverage: the ingest router
test suite mocks corp.ingest.router._run_extraction itself, so nothing drives the real
router->cke_client path (or even extract_sync alone) against so much as a fake CKE.
If CKE's printed label text ever drifts (e.g. "Done:" -> "Completed:"), extract_sync
silently returns a zero for that field instead of erroring.

This test does NOT mock _run_cke, _parse_summary, subprocess.run, or the ingest
router's _run_extraction. It only monkeypatches _resolve_cke_cmd() -- which merely
picks WHICH executable to invoke -- to point at a fake `cke` stand-in script. The real
subprocess.run call inside _run_cke and the real _parse_summary regex parsing both
execute against that fake process's genuine stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from corp.overnight.cke_client import extract_sync

# The exact literal lines _parse_summary (cke_client.py:109-159) expects, matched
# precisely against its regexes:
#   r"Done:\s*(\d+)"                                    -> "Done: 2"
#   r"Errors:\s*(\d+)"                                  -> "Errors: 1"
#   r"Skipped:\s*(\d+)"                                 -> "Skipped: 0"
#   r"Total:\s*(\d+)"                                   -> "Total: 3"
#   r"Estimated API cost:\s*\$([0-9.]+)"                -> "Estimated API cost: $0.42"
#   r"Tiers:\s*local=(\d+),\s*text-AI=(\d+),\s*multimodal=(\d+)" -> "Tiers: local=1, text-AI=1, multimodal=1"
_FAKE_CKE_SCRIPT = '''\
"""Fake cke CLI stand-in -- ignores argv, prints a fixed summary, exits 0."""
import sys

print("Total: 3")
print("Done: 2")
print("Errors: 1")
print("Skipped: 0")
print("Estimated API cost: $0.42")
print("Tiers: local=1, text-AI=1, multimodal=1")
sys.exit(0)
'''


@pytest.fixture()
def fake_cke_script(tmp_path: Path) -> Path:
    """A stand-in `cke` executable emitting the exact literal lines _parse_summary expects."""
    script = tmp_path / "fake_cke.py"
    script.write_text(_FAKE_CKE_SCRIPT, encoding="utf-8")
    return script


@pytest.fixture()
def fake_manifest(tmp_path: Path) -> Path:
    """Minimal manifest file.

    extract_sync() only stringifies this path into argv -- it never opens the file
    itself (the real CKE process would, but our fake script ignores its args) -- a
    real path on disk keeps the fixture realistic regardless.
    """
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": []}), encoding="utf-8")
    return manifest


class TestCkeClientStdoutContract:
    def test_extract_sync_parses_real_subprocess_stdout(
        self,
        fake_cke_script: Path,
        fake_manifest: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """extract_sync() against a fake `cke`: real subprocess.run + real _parse_summary.

        monkeypatch only replaces _resolve_cke_cmd's RESOLUTION (which binary to run);
        _run_cke's subprocess.run call and _parse_summary's regex parsing are the real
        production code paths, unmocked. This pins the exact label strings the real CKE
        CLI must keep emitting for corp to correctly read total/done/error/skipped/cost/
        tiers back out.
        """
        monkeypatch.setattr(
            "corp.overnight.cke_client._resolve_cke_cmd",
            lambda: (sys.executable, str(fake_cke_script)),
        )

        result = extract_sync(fake_manifest)

        assert result == {
            "total": 3,
            "done": 2,
            "error": 1,
            "skipped": 0,
            "cost": 0.42,
            "tiers": {1: 1, 2: 1, 3: 1},
        }
