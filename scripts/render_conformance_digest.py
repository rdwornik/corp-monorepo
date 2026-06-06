#!/usr/bin/env python3
"""Render the nightly conformance digest markdown from the conformance-corp
workflow's structured output.

This is the **code-owned write path** for the nightly conformance loop. Per the
executing-path lesson (PLAYBOOK "Routine/night deployment standard"; LESSONS
2026-06-05): in the cloud the native Workflow launcher is absent, so the
workflow .js is read as a *spec*, not run -- any throw-on-mismatch validator
*inside* the .js is inert there. The load-bearing count guarantee therefore
lives HERE, in code that actually runs in cloud (the Routine invokes this via
Bash) and in the Action parser that reads only the marker.

Contract (marker D+C):
  * Counts are authoritative integers from the workflow's `counts` block.
  * This script RECOMPUTES the marker from those counts and writes it verbatim
    on its own line: ``<!-- counts: raw=N survived=N killed=N -->``.
  * If the input also carries a `counts_marker` and it DISAGREES with the
    recomputed one, this script EXITS NON-ZERO (fail-closed) -- code, not prose,
    owns the marker at write time.

The section headers below are the contract the Action's body extraction matches
(``## Findings (PROPOSALS ONLY)`` with ``### High/Med/Low`` inside; then
``## Next Actions (proposals for operator)``). Keep them in sync with
``.github/workflows/nightly-conformance-triage.yml``; the parser unit test
(``tests/test_nightly_triage_parser.py``) pins both ends so they cannot drift.

Self-contained: standard library only (no `corp` import) so it runs in a fresh
clone with no editable install.

Usage:
  python scripts/render_conformance_digest.py --input digest.json --date 2026-06-06 \
      --execution-path spec-orchestration --out docs/audits/2026-06-06-conformance-nightly-digest.md
  # --input - reads JSON from stdin; omit --out to write to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

MARKER_RE = re.compile(r"^<!-- counts: raw=\d+ survived=\d+ killed=\d+ -->$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def build_marker(raw: int, survived: int, killed: int) -> str:
    """The one true marker. Single spaces, exact shape -- matches the Action regex."""
    return f"<!-- counts: raw={raw} survived={survived} killed={killed} -->"


def _coerce_int(value, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        sys.exit(f"render-digest: count '{name}' is not an integer: {value!r}")


def _extract_counts(payload: dict) -> tuple[int, int, int]:
    """Pull authoritative counts from the workflow return, tolerating either the
    full return object or the inner digest object."""
    counts = payload.get("counts")
    if counts is None and isinstance(payload.get("digest"), dict):
        counts = payload["digest"].get("counts")
    if not isinstance(counts, dict):
        sys.exit(
            "render-digest: input has no `counts` block (raw_findings/survived_skeptic/killed_false_positive)."
        )
    raw = _coerce_int(counts.get("raw_findings"), "raw_findings")
    survived = _coerce_int(counts.get("survived_skeptic"), "survived_skeptic")
    killed = _coerce_int(counts.get("killed_false_positive"), "killed_false_positive")
    return raw, survived, killed


def _digest_block(payload: dict) -> dict:
    """Return the digest sub-object (findings_by_severity / next_actions / etc.),
    accepting either the full workflow return or the bare digest."""
    digest = payload.get("digest")
    if isinstance(digest, dict):
        return digest
    return payload


def _bullets(items, empty: str) -> list[str]:
    items = [str(x).strip() for x in (items or []) if str(x).strip()]
    if not items:
        return [empty]
    return [f"- {x}" for x in items]


def render(payload: dict, date: str, execution_path: str) -> str:
    if not DATE_RE.match(date):
        sys.exit(f"render-digest: --date must be YYYY-MM-DD, got {date!r}")

    raw, survived, killed = _extract_counts(payload)
    marker = build_marker(raw, survived, killed)

    # Fail-closed: if the workflow handed us a marker, it MUST agree with the
    # recomputed one. Code owns the marker; a disagreement means the contract
    # broke upstream -- refuse to write rather than emit a lying digest.
    supplied = payload.get("counts_marker")
    if supplied is None and isinstance(payload.get("digest"), dict):
        supplied = payload["digest"].get("counts_marker")
    if supplied is not None and str(supplied).strip() != marker:
        sys.exit(
            "render-digest: counts_marker disagreement (fail-closed): "
            f"supplied={supplied!r} but code-computed={marker!r}."
        )
    # Defence in depth: our own marker must match the Action's regex.
    if not MARKER_RE.match(marker):
        sys.exit(f"render-digest: built marker fails the Action regex: {marker!r}")

    digest = _digest_block(payload)
    fbs = digest.get("findings_by_severity") or {}
    summary = str(digest.get("summary") or "").strip() or "_No summary provided._"

    lines: list[str] = []
    lines.append(f"# corp-monorepo — Nightly Conformance Digest ({date})")
    lines.append("")
    lines.append(f"- **Date:** {date}")
    lines.append(
        "- **Generator:** `scripts/render_conformance_digest.py` (code-owned write path)"
    )
    lines.append(
        "- **Workflow:** `conformance-corp` (`.claude/workflows/conformance-corp.js`)"
    )
    lines.append(
        "- **Nature:** read-only documentation-conformance review — proposals only, no fixes (self-contained per ADR-72)."
    )
    lines.append(f"- **Execution path:** {execution_path}")
    lines.append("")
    # Machine-readable counts contract (C is read by the Action; this is the
    # write side). MUST be on its own line.
    lines.append(marker)
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")
    # --- Findings (the Action extracts from here to the next `## `) ----------
    lines.append("## Findings (PROPOSALS ONLY)")
    lines.append("")
    if survived == 0:
        lines.append(
            "_None — all checked claims conform. See checked-and-clean below._"
        )
        lines.append("")
    else:
        for sev_key, sev_title in (("high", "High"), ("med", "Med"), ("low", "Low")):
            lines.append(f"### {sev_title}")
            lines.append("")
            lines.extend(
                _bullets(
                    fbs.get(sev_key), f"_No {sev_title.lower()}-severity findings._"
                )
            )
            lines.append("")
    # --- Next Actions (the Action extracts from here to the next `## `) ------
    lines.append("## Next Actions (proposals for operator)")
    lines.append("")
    if survived == 0:
        lines.append("_No action required — clean night._")
    else:
        lines.extend(
            _bullets(digest.get("next_actions"), "_No next actions proposed._")
        )
    lines.append("")
    # --- Sections below are excluded from the issue body (after the awk stop) -
    lines.append("## Killed Findings")
    lines.append("")
    killed_items = []
    skeptic = payload.get("skeptic") or {}
    for k in skeptic.get("killed_findings") or []:
        claim = str(k.get("claim", "")).strip()
        reason = str(k.get("kill_reason", "")).strip()
        if claim:
            killed_items.append(f"{claim} — _{reason}_" if reason else claim)
    lines.extend(_bullets(killed_items, "_No findings killed this run._"))
    lines.append("")
    lines.append("## Checked-and-clean (so absence is informative)")
    lines.append("")
    lines.extend(
        _bullets(digest.get("checked_clean"), "_No checked-clean items recorded._")
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render the nightly conformance digest markdown."
    )
    ap.add_argument(
        "--input",
        required=True,
        help="JSON file with the workflow return, or - for stdin.",
    )
    ap.add_argument(
        "--date",
        required=True,
        help="Digest date, YYYY-MM-DD (the Routine's local date).",
    )
    ap.add_argument(
        "--execution-path",
        default="spec-orchestration",
        help="native | spec-orchestration (which path produced the run).",
    )
    ap.add_argument("--out", default=None, help="Output .md path; default stdout.")
    args = ap.parse_args(argv)

    if args.input == "-":
        payload = json.load(sys.stdin)
    else:
        with open(args.input, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    if not isinstance(payload, dict):
        sys.exit("render-digest: input JSON must be an object (the workflow return).")

    md = render(payload, args.date, args.execution_path)

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
