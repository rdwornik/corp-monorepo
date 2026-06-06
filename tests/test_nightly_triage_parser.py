"""Anti-drift unit checks for the nightly-conformance contract.

This test pins BOTH ends of the machine contract so the generator and the
consumer cannot silently drift apart (LESSONS 2026-06-05, "fixture/production
drift — a hand-made fixture validates the PARSER, not the SYSTEM"):

  * the WRITE side is the real generator, ``scripts/render_conformance_digest.py``
    (loaded here by path, no editable install needed — works in a fresh clone);
  * the READ side is the Action, ``.github/workflows/nightly-conformance-triage.yml`` —
    the marker regex, digest-path regex, and section-extraction logic are read
    LIVE from the YAML and applied to the freshly-generated digest, so a change
    on either side that breaks the contract fails this test.

The fixtures are GENERATED from the committed workflow-return inputs by the real
renderer (not hand-shaped to fit the reader); the committed golden ``.md`` files
are regenerated and compared, so a renderer change that alters the shape is
caught here.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = REPO_ROOT / "scripts" / "render_conformance_digest.py"
ACTION_YML = REPO_ROOT / ".github" / "workflows" / "nightly-conformance-triage.yml"
FIXTURES = Path(__file__).parent / "fixtures" / "nightly-triage"

SURVIVOR_INPUT = FIXTURES / "survivor_workflow_return.json"
SURVIVOR_GOLDEN = FIXTURES / "2026-06-06-conformance-nightly-digest.md"
CLEAN_INPUT = FIXTURES / "clean_workflow_return.json"
CLEAN_GOLDEN = FIXTURES / "clean-digest.md"


# --- load the real renderer module (the WRITE side) -------------------------
def _load_renderer():
    spec = importlib.util.spec_from_file_location(
        "render_conformance_digest", RENDERER_PATH
    )
    assert spec and spec.loader, "could not locate the renderer module"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


renderer = _load_renderer()


def _render(input_path: Path) -> str:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return renderer.render(payload, "2026-06-06", "spec-orchestration")


# --- extract the contract from the Action YAML (the READ side) ---------------
def _yml_text() -> str:
    return ACTION_YML.read_text(encoding="utf-8")


def _extract_quoted_regex(keyword: str) -> str:
    """Pull the single-quoted ERE from the Action YAML that CONTAINS ``keyword``
    and a ``[0-9]`` character class. Selecting on both uniquely identifies the
    actual grep regex (vs a ``'%s'`` argument, a glob in a comment, or the
    literal marker example in an issue body). This reads the LIVE contract.

    Scan PER LINE -- single-quoted regexes live on one line, and per-line
    pairing avoids stray apostrophes elsewhere in the file ("doesn't",
    "night's") misaligning the quote pairs."""
    candidates = [
        q
        for line in _yml_text().splitlines()
        for q in re.findall(r"'([^']*)'", line)
        if keyword in q and "[0-9]" in q
    ]
    assert candidates, (
        f"no single-quoted regex containing {keyword!r} + a digit class in the Action YAML"
    )
    return candidates[0]


def marker_regex() -> str:
    # MARKER="$(grep -oE '<!-- counts: raw=[0-9]+ survived=[0-9]+ killed=[0-9]+ -->' ...)"
    return _extract_quoted_regex("<!-- counts:")


def digest_path_regex() -> str:
    # guard: grep -Eq '^docs/audits/[0-9]{4}-[0-9]{2}-[0-9]{2}-conformance-nightly-digest\.md$'
    return _extract_quoted_regex("conformance-nightly-digest")


def _parse_marker(md: str, regex: str):
    """Mirror the Action: grep -oE <marker> | head -n1, then sed survived=."""
    found = re.findall(regex, md)
    marker = found[0] if found else ""
    if not marker:
        return None
    m = re.search(r"survived=([0-9]+)", marker)
    return int(m.group(1)) if m else None


def _extract_section(md: str, start_prefix: str) -> str:
    """Mirror the Action awk: capture from a line starting with ``start_prefix``
    until the next ``## `` heading or a ``---`` rule."""
    out: list[str] = []
    cap = False
    for line in md.splitlines():
        if not cap and line.startswith(start_prefix):
            cap = True
            out.append(line)
            continue
        if cap and line.startswith("## "):
            break
        if cap and re.match(r"^---\s*$", line):
            break
        if cap:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_renderer_module_loads():
    assert hasattr(renderer, "render") and hasattr(renderer, "build_marker")


def test_golden_fixtures_match_current_generator():
    """Fixture-from-generator: the committed golden .md must equal what the
    current renderer produces from the committed input. Catches renderer drift."""
    assert _render(SURVIVOR_INPUT) == SURVIVOR_GOLDEN.read_text(encoding="utf-8")
    assert _render(CLEAN_INPUT) == CLEAN_GOLDEN.read_text(encoding="utf-8")


def test_marker_parses_with_live_action_regex_survivor():
    md = _render(SURVIVOR_INPUT)
    survived = _parse_marker(md, marker_regex())
    assert survived == 2, (
        "Action marker regex must extract survived=2 from the generated digest"
    )


def test_marker_parses_with_live_action_regex_clean():
    md = _render(CLEAN_INPUT)
    survived = _parse_marker(md, marker_regex())
    assert survived == 0, "clean night must parse to survived=0 (auto-merge, no issue)"


def test_findings_and_next_actions_extract_survivor():
    md = _render(SURVIVOR_INPUT)
    findings = _extract_section(md, "## Findings")
    nextact = _extract_section(md, "## Next Actions")

    # survivor finding text lands in Findings, under High/Med
    assert "### High" in findings and "### Med" in findings
    assert "client aliases" in findings
    assert "inbox.py" in findings
    # next-action text lands in Next Actions
    assert "Refresh the two drifted ARCHITECTURE.md counts" in nextact
    # Killed / Checked-clean must NOT leak into either issue block
    assert "Killed Findings" not in findings and "Killed Findings" not in nextact
    assert "Checked-and-clean" not in findings and "Checked-and-clean" not in nextact
    assert "router.py" not in findings  # a killed finding's text


def test_clean_night_makes_no_survivor_block():
    md = _render(CLEAN_INPUT)
    findings = _extract_section(md, "## Findings")
    # On a clean night the Action does not open an issue (survived==0); the
    # findings section is an explicit "none" placeholder, never empty/dead.
    assert "_None" in findings


def test_fail_closed_when_marker_absent():
    """A digest with no marker -> the live regex finds nothing -> the Action's
    emptiness check fires the fail-closed path (open issue, do not merge)."""
    md_no_marker = "# digest\n\n## Findings (PROPOSALS ONLY)\n\n- something\n"
    assert _parse_marker(md_no_marker, marker_regex()) is None


def test_survivor_fixture_filename_matches_digest_path_regex():
    """The golden survivor fixture is named like a real digest, and the Action's
    diff-guard path regex must accept that exact path."""
    rel = f"docs/audits/{SURVIVOR_GOLDEN.name}"
    assert re.search(digest_path_regex(), rel), (
        f"digest-path regex {digest_path_regex()!r} should match {rel!r}"
    )
    # a non-digest path must be rejected
    assert not re.search(digest_path_regex(), "src/corp/cli.py")


def test_built_marker_shape_matches_action_regex():
    """The renderer's own marker, for arbitrary counts, satisfies the Action regex."""
    marker = renderer.build_marker(6, 2, 4)
    assert re.findall(marker_regex(), marker) == [marker]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
