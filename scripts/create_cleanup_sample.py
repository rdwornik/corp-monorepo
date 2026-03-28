"""Create 20% random sample of MyWork/10_Projects for sandbox cleanup testing.

Copies files to .sandbox/cleanup_pilot/input/<project>/ preserving project
folder as context. Saves a manifest.json with metadata for downstream scripts.

Does NOT modify source files.
"""
import json
import os
import random
import shutil
from collections import Counter
from pathlib import Path

MYWORK = Path(os.environ["USERPROFILE"]) / "Documents" / "MyWork" / "10_Projects"
SANDBOX = Path(__file__).resolve().parents[1] / ".sandbox/cleanup_pilot"

SKIP_EXTENSIONS = {".tmp", ".lnk", ".url"}
SKIP_PREFIXES = (".", "~$")  # hidden + Office lock files


def _should_skip(f: Path) -> bool:
    return (
        f.name.startswith(SKIP_PREFIXES)
        or f.suffix.lower() in SKIP_EXTENSIONS
    )


def main() -> None:
    if not MYWORK.exists():
        raise SystemExit(f"Source not found: {MYWORK}")

    # Clean previous run
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    (SANDBOX / "input").mkdir(parents=True)
    (SANDBOX / "output").mkdir()

    # Collect all eligible files with metadata
    all_files: list[dict] = []
    for f in MYWORK.rglob("*"):
        if not f.is_file() or _should_skip(f):
            continue
        rel = f.relative_to(MYWORK)
        project = rel.parts[0] if len(rel.parts) > 1 else "root"
        all_files.append(
            {
                "source": str(f),
                "relative": str(rel),
                "name": f.name,
                "extension": f.suffix.lower(),
                "size": f.stat().st_size,
                "project": project,
            }
        )

    # Stratified 20% sample — cap per-project at 15 to avoid large-project dominance
    MAX_PER_PROJECT = 15
    random.seed(42)

    from collections import defaultdict

    by_project: dict[str, list[dict]] = defaultdict(list)
    for entry in all_files:
        by_project[entry["project"]].append(entry)

    pool: list[dict] = []
    for proj_files in by_project.values():
        random.shuffle(proj_files)
        pool.extend(proj_files[:MAX_PER_PROJECT])

    target = max(int(len(all_files) * 0.20), 50)
    sample = random.sample(pool, min(target, len(pool)))

    # Copy to sandbox, preserving project folder as top-level context
    copied = 0
    errors: list[str] = []
    for entry in sample:
        src = Path(entry["source"])
        dest = SANDBOX / "input" / entry["project"] / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(src), str(dest))
            copied += 1
        except OSError as exc:
            errors.append(f"{src.name}: {exc}")

    # Save manifest
    manifest = {
        "total_mywork_files": len(all_files),
        "sample_size": len(sample),
        "sample_pct": round(len(sample) / len(all_files) * 100, 1),
        "copied": copied,
        "errors": errors,
        "files": sample,
    }
    (SANDBOX / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Summary
    print(f"Sample created: {copied} files ({manifest['sample_pct']:.0f}%)")
    print(f"From {len({e['project'] for e in sample})} project folders")
    print(f"Location: {SANDBOX / 'input'}")
    if errors:
        print(f"  WARNING: {len(errors)} copy errors:")
        for e in errors[:5]:
            print(f"    {e}")

    exts = Counter(e["extension"] for e in sample)
    print("\nExtension distribution:")
    for ext, n in exts.most_common():
        label = ext if ext else "(no ext)"
        print(f"  {n:>4}  {label}")


if __name__ == "__main__":
    main()
