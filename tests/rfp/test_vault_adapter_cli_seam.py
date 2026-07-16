"""Integration test pinning the ``corp retrieve --format json`` producer<->consumer seam.

Ground truth: docs/audits/2026-07-16-architecture-ground-truth.md Sec2 rows 231-232.

Producer: corp.cli.retrieve.retrieve_cmd, --format json branch (src/corp/cli/retrieve.py:74-101).
Consumer: corp.rfp.vault_adapter._retrieve_via_cli (src/corp/rfp/vault_adapter.py:117-157),
which shells out to ``corp retrieve <query> --format json --rfp-only --top <limit>`` and
reads back ``data["notes"]``.

The audit's finding for this seam: every existing test on EITHER side patches away the
crossing -- test_json_output.py drives the producer only, via CliRunner; this directory's
test_vault_adapter.py patches subprocess.run for the consumer. Nothing proves the two
sides actually agree on the wire. This test drives the REAL subprocess end to end: a
genuine ``corp retrieve`` process is spawned, and its real stdout is parsed by the real
consumer code. subprocess.run is intentionally left UNPATCHED -- that crossing is
exactly what this test pins.

Cross-process subtlety: the spawned ``corp retrieve`` process does not see pytest's
monkeypatch of Python objects (corp.config.get_config, corp.index_builder.get_index_path)
-- those patches live only in THIS process. The subprocess only inherits OS environment
variables. So the fixture below points the child process at a scratch vault + index.db
via VAULT_PATH / APP_DATA_PATH (monkeypatch.setenv -> os.environ -> inherited by
subprocess.run, since vault_adapter.py never passes an explicit env= kwarg).
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from corp.index_builder import _SCHEMA
from corp.rfp.vault_adapter import _retrieve_via_cli

_QUERY = "Seam Contract Platform Architecture"


@pytest.fixture()
def cli_seam_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a real index.db + vault note, then steer the corp CLI subprocess at them.

    Schema is imported from corp.index_builder (the same canonical _SCHEMA used by
    tests/test_retrieve/test_engine.py and test_json_output.py after the D-8 fix) so
    all three fixtures share one source of truth instead of hand-copied replicas.
    """
    vault = tmp_path / "vault"
    vault.mkdir()
    appdata = tmp_path / "appdata"
    appdata.mkdir()

    # get_index_path() == cfg.app_data_path / "index.db" (src/corp/index_builder.py:144-147)
    db_path = appdata / "index.db"

    note_file = vault / "seam_note.md"
    note_file.write_text(
        "---\ntitle: Seam Contract Platform Architecture\ntrust_level: verified\n"
        "extracted_at: '2026-07-16'\n---\n\n"
        "Blue Yonder seam-contract fixture body content for the retrieve CLI test.",
        encoding="utf-8",
    )

    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    conn.execute(
        """INSERT INTO notes
           (project_id, client, title, type, source_type,
            topics, products, domains, confidence, note_path, rfp_visible)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "seam_test",
            "SeamCo",
            "Seam Contract Platform Architecture",
            "documentation",
            "documentation",
            json.dumps(["Architecture"]),
            json.dumps(["Platform"]),
            json.dumps(["Platform"]),
            "verified",
            str(note_file),
            1,  # rfp_visible=1 -- required to survive the producer's --rfp-only flag
        ),
    )
    conn.commit()
    conn.close()

    # corp.config.get_config() (src/corp/config.py:74-77, :90-93) is what both
    # retrieve_cmd (cfg.vault_path) and get_index_path() (cfg.app_data_path) read.
    # The N1 recon confirmed VAULT_PATH drives the pipeline vault path; APP_DATA_PATH
    # is its index.db sibling. Setting them via monkeypatch.setenv mutates os.environ,
    # which subprocess.run inherits (vault_adapter.py never overrides env=).
    monkeypatch.setenv("VAULT_PATH", str(vault))
    monkeypatch.setenv("APP_DATA_PATH", str(appdata))

    # Pin the spawned `corp` to THIS checkout's entry point, not an arbitrary
    # PATH corp: prepend the running interpreter's Scripts dir (where the corp
    # console-script is installed for this interpreter -- sysconfig, so it is
    # correct for both a venv and a system/user install) so subprocess.run
    # resolves it first. Without this a stale/global corp could pass even if the
    # checked-out producer is broken (Codex N2). vault_adapter passes no env=, so
    # this os.environ PATH is what the child inherits.
    scripts_dir = sysconfig.get_path("scripts")
    monkeypatch.setenv("PATH", str(scripts_dir) + os.pathsep + os.environ.get("PATH", ""))

    # Pin the child's corp PACKAGE (not just the launcher location) to THIS
    # checkout's src/. Prior CLI-entry-point overwrites (CLAUDE.md gotcha: a
    # `pip install` from an _archived_ repo overwrites the monorepo entry point)
    # mean a launcher in this interpreter's scripts dir could still import a
    # stale editable/global corp. Prepending src/ to PYTHONPATH forces `import
    # corp` in the child to resolve to this checkout (Codex N2 r2).
    repo_src = Path(__file__).resolve().parents[2] / "src"
    monkeypatch.setenv("PYTHONPATH", str(repo_src) + os.pathsep + os.environ.get("PYTHONPATH", ""))

    return db_path


def test_retrieve_cli_seam_round_trip_unmocked(cli_seam_env: Path) -> None:
    """Real ``corp retrieve --format json`` subprocess -> real vault_adapter._retrieve_via_cli.

    subprocess.run is NOT patched anywhere in this test -- this is the actual
    cross-process boundary the audit found untested (ground-truth Sec2 row 232:
    "every test in tests/rfp/test_vault_adapter.py patches subprocess.run ... the real
    cross-process boundary is never exercised").

    Each asserted key pins one side of the contract:
      - note_id: vault_adapter.retrieve_for_rfp() keys its `sources` list off this
        (vault_adapter.py:99,106)
      - confidence: drives _TRUST_RANK filtering + sort order in
        vault_adapter.retrieve() (:57-68)
      - relevance_score: sort key and the LOW_CONFIDENCE_THRESHOLD gate in
        retrieve_for_rfp() (:94-101)
      - content: retrieve_for_rfp()'s "answer" field is read straight off this key
        (:98,105)
      - title: basic shape guard confirming the row round-tripped, not just any row

    If the producer (src/corp/cli/retrieve.py:74-101) stops emitting one of these keys,
    or the consumer's dict.get(...) calls (vault_adapter.py:57-66,94,98) drift to a
    different key name, this test fails.
    """
    # A missing corp CLI is a FAILURE, not a skip -- corp is an editable-install
    # entry point for the running interpreter and is always present when the suite
    # runs (the whole suite imports corp). Skipping would silently omit this seam
    # gate (Codex N2). The fixture prepended the interpreter's Scripts dir to PATH,
    # so this must resolve to THIS checkout's corp, not an unrelated/global install.
    resolved_corp = shutil.which("corp")
    assert resolved_corp is not None, (
        "corp CLI entry point not resolvable -- the checkout's editable install is "
        "broken; the producer<->consumer seam gate cannot run"
    )
    scripts_dir = sysconfig.get_path("scripts")
    assert os.path.samefile(Path(resolved_corp).parent, scripts_dir), (
        f"corp resolved to {resolved_corp!r}, not this interpreter's entry-point dir "
        f"{scripts_dir!r} -- refusing to pass against an unrelated/global corp"
    )

    # Verify the child actually imports THIS checkout's corp PACKAGE (not a stale
    # global/editable one), under the PYTHONPATH the fixture set. The real `corp
    # retrieve` child below inherits the same os.environ, so this probe reflects
    # exactly which corp it imports (Codex N2 r2).
    repo_src = Path(__file__).resolve().parents[2] / "src"
    probe = subprocess.run(
        [sys.executable, "-c", "import corp, sys; sys.stdout.write(corp.__file__)"],
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, f"child could not import corp: {probe.stderr}"
    child_corp = Path(probe.stdout.strip()).resolve()
    assert repo_src.resolve() in child_corp.parents, (
        f"child imports corp from {child_corp}, not this checkout's src {repo_src.resolve()} "
        "-- a stale global/editable corp would falsely pass this seam test"
    )

    notes = _retrieve_via_cli(_QUERY, limit=5)

    assert notes, (
        "producer<->consumer round trip returned zero notes -- the real `corp retrieve` "
        "subprocess produced no usable match; the seam is broken, not merely slow"
    )

    note = notes[0]
    for key in ("note_id", "confidence", "relevance_score", "content", "title"):
        assert key in note, f"missing key from real `corp retrieve --format json` output: {key}"

    assert note["title"] == "Seam Contract Platform Architecture"
    assert note["confidence"] == "verified"
    assert "seam-contract fixture body" in note["content"]
    assert isinstance(note["note_id"], int)
    assert isinstance(note["relevance_score"], (int, float))
