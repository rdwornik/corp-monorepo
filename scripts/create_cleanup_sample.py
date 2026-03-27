"""Create 20% random sample of MyWork/10_Projects for sandbox cleanup testing.

Copies files to .sandbox/cleanup_pilot/input/<project>/ preserving project
folder as context. Saves a manifest.json with metadata for downstream scripts.

Does NOT modify source files.
"""
import json
import random
import shutil
from collections import Counter
from pathlib import Path

MYWORK = Path(r"C:\Users\1028120\Documents\MyWork\10_Projects")
SANDBOX = Path(r"C:\Users\1028120\Documents\Scripts\corp-monorepo\.sandbox\cleanup_pilot")

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

    # 20% stratified sample — seed 42 for reproducibility
    random.seed(42)
    target = max(int(len(all_files) * 0.20), 50)
    sample = random.sample(all_files, min(target, len(all_files)))

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
