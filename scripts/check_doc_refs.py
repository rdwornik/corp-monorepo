"""Verify markdown file/path references in living docs.

Audit-only: reports broken references, does not modify any doc. Frozen-docs
directories (docs/archive/, docs/decisions/, docs/audits/) are excluded from
the scan — broken refs there are intentional historical record.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / "docs" / "ARCHITECTURE.md",
    *sorted((REPO_ROOT / "src" / "corp").rglob("README.md")),
]

# matches `[label](path)` where path ends in .md/.py/.yaml/.toml/.yml
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.(?:md|py|yaml|toml|yml))\)")

# also consider backtick-quoted explicit paths in code/prose
BACKTICK_PATH_RE = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:md|py|yaml|toml|yml))`")


@dataclass(frozen=True)
class BrokenRef:
    doc: str
    target: str
    resolved: str
    reason: str


def _clean_anchor(path: str) -> str:
    return path.split("#", 1)[0]


def _is_external(path: str) -> bool:
    return path.startswith(("http://", "https://", "mailto:"))


def verify(doc: Path) -> list[BrokenRef]:
    text = doc.read_text(encoding="utf-8", errors="ignore")
    found: list[tuple[str, str]] = []
    for m in LINK_RE.finditer(text):
        found.append(("link", m.group(2)))
    for m in BACKTICK_PATH_RE.finditer(text):
        # only test the ones that look like repo-relative paths
        raw = m.group(1)
        if "/" in raw:
            found.append(("backtick", raw))

    broken: list[BrokenRef] = []
    for kind, raw in found:
        if _is_external(raw):
            continue
        rel = _clean_anchor(raw).strip()
        # repo-absolute (starts with src/, docs/, scripts/, tests/, .github/, etc.)
        if rel.startswith(("src/", "docs/", "scripts/", "tests/", ".github/", "config/", "eval/")):
            target = REPO_ROOT / rel
        else:
            target = (doc.parent / rel).resolve()
        # Fallback: abbreviated module-relative paths (e.g., `providers/base.py`
        # inside docs/ARCHITECTURE.md) resolve to real files under src/corp/*/.
        if not target.exists() and "/" in rel:
            for candidate_root in (REPO_ROOT / "src" / "corp").rglob(rel):
                if candidate_root.exists():
                    target = candidate_root
                    break
        if not target.exists():
            broken.append(
                BrokenRef(
                    doc=str(doc.relative_to(REPO_ROOT)).replace("\\", "/"),
                    target=raw,
                    resolved=str(target).replace("\\", "/"),
                    reason=f"{kind}:missing",
                )
            )
    return broken


def main() -> int:
    all_broken: list[BrokenRef] = []
    total_refs = 0
    for doc in DOCS:
        if not doc.exists():
            continue
        # rough count, same regex surface as verify
        text = doc.read_text(encoding="utf-8", errors="ignore")
        total_refs += len(LINK_RE.findall(text)) + len(
            [m for m in BACKTICK_PATH_RE.findall(text) if "/" in m]
        )
        all_broken.extend(verify(doc))
    out = REPO_ROOT / ".audit" / "doc-refs-broken.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([asdict(b) for b in all_broken], indent=2), encoding="utf-8")
    print(f"docs checked: {len([d for d in DOCS if d.exists()])}")
    print(f"references seen: {total_refs}")
    print(f"broken: {len(all_broken)}")
    for b in all_broken:
        print(f"  {b.doc}: {b.target}  ->  {b.reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
