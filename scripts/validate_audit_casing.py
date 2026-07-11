#!/usr/bin/env python
"""validate_audit_casing.py -- corp consumer gate for hub ADR-101 R4 (fleet ruling d1).

Carries ONLY the R4 **casing** branch of the hub `validate_hermetization.py` gate into
corp-monorepo. The hub gate's other two branches are deliberately NOT carried and stay
hub-local (declared in `.methodology.yaml` as the `audit-casing-r4` divergence):
  * Rule A -- top-level tree-seal (sanctioned Tier-1 dirs/files + docs/<genre> set);
  * Rule B enum + date-shape grammar -- the CLOSED 11-class audit-class enum + YYYY-MM-DD
    shape. corp's audit files use free lowercase slugs (estate-recon, deep-dealloop,
    foundation-review) outside that enum, so carrying it would over-block legitimate files.

Authority: hub `docs/decisions/ADR-101-hermetization.md` R4 (fleet ruling d1; the parity
register lives in the hub, not corp). corp ADR-14 continues to govern MyWork content-file
naming ({YYYY-MM}_{TYPE}_{CLIENT}_ UPPERCASE codes, config/naming_config.yaml) -- OUT OF
SCOPE of this docs/audits/ gate.

**Prospective-only:** inspects only ADDED paths (`git diff --cached --diff-filter=A`), so
every existing file is grandfathered and never checked -- no retroactive rename over the 11
pre-existing UPPERCASE `_TYPE_` files the date-index already disambiguates. `--no-renames`
forces a rename to surface as delete+ADD so a rename that introduces a NEW off-casing
pathname is policed too. The 11 legacy names are ALSO carried as an explicit enumerated
skip-set (`LEGACY_GRANDFATHERED`) -- belt-and-suspenders, and grandfathering by ENUMERATION,
never by pattern (a blanket "UPPERCASE is exempt" rule would exempt future violations too).

Rule (BLOCK, exit 1): an added `docs/audits/*.md` (extension-case-insensitive, so an
uppercase `.MD` cannot dodge) whose FULL filename is not all-lowercase kebab-case -- no
UPPERCASE, no _underscore_, no CamelCase; sole carve-out a literal `.` in the slug for a
meaningful repo/version token (`.dev-knowledge`, `v3.4`).

**Name-CASING only** -- unlike the hub gate this does NOT check the date shape, the class
enum, or the slug grammar. Any all-lowercase-kebab name passes.

Read-only: reads the staged name-status; writes NOTHING. **Fail-OPEN but LOUD** on any git
error -- a hygiene gate must not brick every commit on a near-impossible git failure. Bypass
parity with peer hooks: `git commit --no-verify`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Optional

# --- ADR-101 section 6: the 11 pre-existing UPPERCASE _TYPE_ files, grandfathered by
# ENUMERATION (declared verbatim in `.methodology.yaml` audit-casing-r4). Belt-and-suspenders
# with the prospective --diff-filter=A: even a delete+re-add of one of these is exempt.
LEGACY_GRANDFATHERED: frozenset[str] = frozenset({
    "2026-07-07_AUDIT_demo-prep-recon.md",
    "2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md",
    "2026-07-07_BRIEF_algorithmic-adopt-map.md",
    "2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md",
    "2026-07-07_BRIEF_obsidian-operating-model-v2.md",
    "2026-07-07_BRIEF_ontology-north-star.md",
    "2026-07-07_EVIDENCE_by-product-docs-tree-analysis.md",
    "2026-07-07_HANDOFF_functional-architect.md",
    "2026-07-08_AUDIT_fa-campaign-self-review.md",
    "2026-07-08_BRIEF_metadata-charter-T1.md",
    "2026-07-11_AUDIT_root-parity-disposition.md",
})

# R4 casing: all-lowercase kebab-case + digits; `.` carve-out (repo/version tokens). No
# uppercase, no underscore, no other charset. Applied to the FULL filename (incl. the `.md`
# extension) so an uppercase `.MD` extension is caught too. Verbatim from hub ADR-101 R4.
_LOWER_KEBAB_DOT = re.compile(r"^[a-z0-9.-]+$")


# --- pure classifiers (unit-tested directly; no git) ----------------------------------

def _posix_parts(path: str) -> list[str]:
    """Repo-relative path -> its components, normalized to forward slashes."""
    return path.replace("\\", "/").strip("/").split("/")


def casing_violation(path: str) -> Optional[str]:
    """R4 casing check. Applies ONLY to an added docs/audits/*.md that is not grandfathered.
    Return a BLOCK reason, or None if clean / not in scope."""
    parts = _posix_parts(path)
    # Applicability is EXTENSION-CASE-INSENSITIVE so an uppercase `.MD` cannot dodge by
    # escaping the `.md` match; the casing rule below then rejects the uppercase extension.
    if not (len(parts) == 3 and parts[0] == "docs" and parts[1] == "audits"
            and parts[2].lower().endswith(".md")):
        return None  # not an audit .md -> silent
    fname = parts[2]
    if fname.lower() == "readme.md":
        return None  # the generated index, not an audit artifact
    if fname in LEGACY_GRANDFATHERED:
        return None  # enumerated legacy file -> exempt

    if not _LOWER_KEBAB_DOT.match(fname):
        return (f"casing: '{fname}' must be all-lowercase kebab-case everywhere incl. the "
                f".md extension (no UPPERCASE, no _underscore_, no CamelCase; only a `.` "
                f"inside the slug for a repo/version token) -- ADR-101 R4")
    return None


def check(added_paths: list[str]) -> list[str]:
    """Every added path -> the list of `path: reason` BLOCK strings (empty == clean)."""
    reasons: list[str] = []
    for p in added_paths:
        r = casing_violation(p)
        if r is not None:
            reasons.append(f"{p}: {r}")
    return reasons


# --- git glue (fail-open-loud) --------------------------------------------------------

def staged_added_paths() -> list[str]:
    """Paths staged with status A (added). Prospective-only: MODIFIED existing files are
    grandfathered. `--no-renames` forces a rename to surface as delete+ADD so a rename that
    introduces a NEW off-casing pathname is policed too. Fail-open on git error."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--diff-filter=A", "--no-renames", "--name-only"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git exited {out.returncode}")
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def main() -> int:
    try:
        added = staged_added_paths()
    except (OSError, RuntimeError) as exc:
        # Fail OPEN but LOUD: a casing convention gate, not a safety control.
        print(f"validate_audit_casing: WARNING -- could not read staged adds ({exc}); "
              f"casing check skipped", file=sys.stderr)
        return 0
    reasons = check(added)
    if reasons:
        print("validate_audit_casing: refused -- ADR-101 R4 docs/audits/ casing violation(s):",
              file=sys.stderr)
        for r in reasons:
            print(f"  {r}", file=sys.stderr)
        print("  Every docs/audits/*.md name is all-lowercase kebab-case (ADR-101 R4, fleet "
              "ruling d1). Rename the file, or bypass in good faith (peer-hook parity): "
              "git commit --no-verify.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
