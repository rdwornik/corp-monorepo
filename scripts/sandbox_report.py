"""Generate REVIEW_REPORT.md from rename + dedup previews.

Reads:
  .sandbox/cleanup_pilot/rename_preview.json
  .sandbox/cleanup_pilot/dedup_preview.json

Writes:
  .sandbox/cleanup_pilot/REVIEW_REPORT.md
"""
import json
from collections import Counter
from pathlib import Path

SANDBOX = Path(r"C:\Users\1028120\Documents\Scripts\corp-monorepo\.sandbox\cleanup_pilot")


def _load(name: str) -> list:
    p = SANDBOX / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    renames: list[dict] = _load("rename_preview.json")
    dupes: list[dict] = _load("dedup_preview.json")

    if not renames:
        raise SystemExit("rename_preview.json not found — run sandbox_rename_preview.py first")

    changed = [r for r in renames if r["changed"]]
    unchanged = [r for r in renames if not r["changed"]]
    no_type = [r for r in renames if not r["doc_type"]]
    low_conf = [r for r in renames if r.get("confidence", 1.0) < 0.5 and r["doc_type"]]

    type_counts = Counter(r["doc_type"] or "NONE" for r in renames)
    method_counts = Counter(r["method"] for r in renames)
    ext_counts = Counter(r["extension"] for r in renames)
    project_counts = Counter(r["project_folder"] for r in renames)

    high_dupes = [p for p in dupes if p["similarity"] > 0.8]
    med_dupes = [p for p in dupes if 0.6 < p["similarity"] <= 0.8]

    lines: list[str] = []
    w = lines.append

    w("# Sandbox Cleanup Pilot — Review Report")
    w("")
    w(f"**Sample:** {len(renames)} files from `MyWork/10_Projects/` (20% random)")
    w("")

    # ── 1. Summary ──────────────────────────────────────────────────────────
    w("## 1. Summary")
    w("")
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| Files in sample | {len(renames)} |")
    w(f"| Would be renamed | {len(changed)} ({len(changed)/len(renames)*100:.0f}%) |")
    w(f"| Already compliant | {len(unchanged)} ({len(unchanged)/len(renames)*100:.0f}%) |")
    w(f"| No classification | {len(no_type)} |")
    w(f"| Low confidence (<0.5) | {len(low_conf)} |")
    w(f"| Near-dup pairs (>0.5) | {len(dupes)} |")
    w(f"| HIGH similarity (>0.8) | {len(high_dupes)} |")
    w("")

    # ── 2. Classification distribution ──────────────────────────────────────
    w("## 2. Classification Distribution")
    w("")
    w("| doc_type | Count | % |")
    w("|----------|-------|---|")
    for t, n in type_counts.most_common():
        w(f"| {t} | {n} | {n/len(renames)*100:.0f}% |")
    w("")
    w("**Method breakdown:**")
    w("")
    w("| Method | Count |")
    w("|--------|-------|")
    for m, n in method_counts.most_common():
        w(f"| {m} | {n} |")
    w("")

    # ── 3. Top 20 rename examples ────────────────────────────────────────────
    w("## 3. Top 20 Rename Examples")
    w("")
    w("Files where classification confidence is highest:")
    w("")
    top = sorted(changed, key=lambda r: -r.get("confidence", 0))[:20]
    for r in top:
        w(f"**`{r['original']}`**")
        w(f"→ `{r['proposed']}`")
        w(f"  type=`{r['doc_type']}` | conf={r['confidence']:.2f} | method={r['method']} | project={r['project_folder']}")
        w("")

    # ── 4. Near-duplicate pairs ──────────────────────────────────────────────
    w("## 4. Near-Duplicate Pairs (Action Required)")
    w("")
    if not dupes:
        w("_No near-duplicate pairs detected in this sample._")
    else:
        w(f"**{len(high_dupes)} HIGH** (>0.80 similarity) — likely safe to review for deletion")
        w(f"**{len(med_dupes)} MED** (0.60–0.80) — inspect content before acting")
        w("")
        w("### HIGH Similarity (>0.80)")
        w("")
        if high_dupes:
            for p in high_dupes:
                xp = "SAME PROJECT" if p["same_project"] else f"DIFF PROJECT ({p['project_a']} vs {p['project_b']})"
                w(f"- **{p['similarity']:.3f}** [{xp}]")
                w(f"  - `{p['file_a']}`")
                w(f"  - `{p['file_b']}`")
        else:
            w("_None._")
        w("")
        w("### MED Similarity (0.60–0.80)")
        w("")
        if med_dupes:
            for p in med_dupes[:10]:
                xp = "SAME PROJECT" if p["same_project"] else f"DIFF PROJECT ({p['project_a']} vs {p['project_b']})"
                w(f"- **{p['similarity']:.3f}** [{xp}]")
                w(f"  - `{p['file_a']}`")
                w(f"  - `{p['file_b']}`")
            if len(med_dupes) > 10:
                w(f"_(+{len(med_dupes)-10} more in dedup_preview.json)_")
        else:
            w("_None._")
    w("")

    # ── 5. Problem files ─────────────────────────────────────────────────────
    w("## 5. Problem Files")
    w("")
    w(f"### No Classification ({len(no_type)} files)")
    w("")
    if no_type:
        w("These files will receive `MISC` type code — review if a better type exists:")
        w("")
        for r in no_type[:20]:
            w(f"- `{r['original']}` (project: {r['project_folder']}, ext: {r['extension']})")
        if len(no_type) > 20:
            w(f"_(+{len(no_type)-20} more)_")
    else:
        w("_None._")
    w("")
    w(f"### Low Confidence (<0.5) ({len(low_conf)} files)")
    w("")
    if low_conf:
        for r in low_conf[:20]:
            w(f"- `{r['original']}` → type=`{r['doc_type']}` conf={r['confidence']:.2f} (project: {r['project_folder']})")
        if len(low_conf) > 20:
            w(f"_(+{len(low_conf)-20} more)_")
    else:
        w("_None._")
    w("")

    # ── 6. Extension distribution ────────────────────────────────────────────
    w("## 6. File Type Distribution")
    w("")
    w("| Extension | Count |")
    w("|-----------|-------|")
    for ext, n in ext_counts.most_common():
        w(f"| {ext or '(none)'} | {n} |")
    w("")

    # ── 7. Project coverage ──────────────────────────────────────────────────
    w("## 7. Project Coverage")
    w("")
    w("| Project | Files in sample |")
    w("|---------|-----------------|")
    for proj, n in project_counts.most_common():
        w(f"| {proj} | {n} |")
    w("")

    # ── 8. Recommendations ──────────────────────────────────────────────────
    w("## 8. Recommendations")
    w("")
    misc_pct = type_counts.get("MISC", 0) / len(renames) * 100
    if misc_pct > 15:
        w(f"- **TAXONOMY GAP**: {misc_pct:.0f}% of files classified as MISC (threshold 15%). "
          "Review `naming_config.yaml` type codes for missing patterns.")
    if no_type:
        w(f"- **{len(no_type)} unclassified files** — check if filename patterns need expanding in `doc_type_classifier.py`.")
    if high_dupes:
        w(f"- **{len(high_dupes)} HIGH similarity pairs** — review manually, then decide which to keep.")
    if len(changed) / len(renames) > 0.9:
        w(f"- **{len(changed)/len(renames)*100:.0f}% files need renaming** — pipeline is working as expected.")
    w("- If renames look sensible, proceed with `sandbox_apply.py` (to be built) on this sample,")
    w("  then scale to full `10_Projects/` population.")
    w("")
    w("---")
    w("_Generated by sandbox_report.py_")

    report = "\n".join(lines)
    out = SANDBOX / "REVIEW_REPORT.md"
    out.write_text(report, encoding="utf-8")
    print(f"Report written: {out}")
    print(f"  {len(renames)} files | {len(changed)} renames | {len(dupes)} dup pairs")


if __name__ == "__main__":
    main()
