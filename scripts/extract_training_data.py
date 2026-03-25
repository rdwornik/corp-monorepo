"""Extract training data from all CKE extraction outputs.

Parses YAML frontmatter from every .md in _outputs/, generates:
  1. Classifier test fixtures (filename → doc_type)
  2. Tag normalization golden set
  3. Product normalization fixtures
  4. People filter fixtures
  5. Quality prediction data
  6. Routing pattern data

Usage:
    python scripts/extract_training_data.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO_ROOT / "packages" / "corp-knowledge-extractor" / "_outputs"
CKE_FIXTURES = REPO_ROOT / "packages" / "corp-knowledge-extractor" / "tests" / "fixtures"
BOS_FIXTURES = REPO_ROOT / "packages" / "corp-by-os" / "tests" / "fixtures"
REPORT_DIR = REPO_ROOT / ".ecosystem" / "archive"

# ---------- frontmatter parser ----------

def parse_frontmatter(md_path: Path) -> dict | None:
    """Parse YAML frontmatter from a .md file."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            return None
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end])
    except Exception:
        return None


def collect_all_notes() -> list[dict]:
    """Collect frontmatter from every extraction note in _outputs/."""
    notes = []
    skip_names = {"index.md", "synthesis.md", "README.md", "inventory.md"}

    for md in OUTPUTS_DIR.rglob("*.md"):
        if md.name.startswith("_") or md.name in skip_names:
            continue
        # Only include notes inside extract/ subdirs (actual extraction output)
        if "extract" not in md.parts:
            continue
        fm = parse_frontmatter(md)
        if fm and "title" in fm:
            # Tag with batch info
            try:
                outputs_idx = list(md.parts).index("_outputs")
                fm["_source_batch"] = md.parts[outputs_idx + 1]
            except (ValueError, IndexError):
                fm["_source_batch"] = "unknown"
            fm["_filename"] = md.name
            fm["_path"] = str(md.relative_to(REPO_ROOT))
            notes.append(fm)
    return notes


# ---------- fixture generators ----------

def gen_classifier_fixtures(notes: list[dict]) -> list[dict]:
    """Generate filename → doc_type pairs for classifier testing."""
    fixtures = []
    seen = set()

    for note in notes:
        source = note.get("source_path") or note.get("source") or ""
        if not source:
            continue
        filename = Path(source).name
        doc_type = note.get("doc_type")
        if not doc_type or doc_type in ("general", "unknown"):
            continue
        # Deduplicate by filename
        if filename in seen:
            continue
        seen.add(filename)

        fixtures.append({
            "filename": filename,
            "extension": Path(filename).suffix.lower(),
            "doc_type": doc_type,
            "source_type": note.get("source_type"),
            "client": note.get("client"),
            "batch": note.get("_source_batch"),
        })

    return sorted(fixtures, key=lambda f: (f["doc_type"], f["filename"]))


def gen_tag_golden_set(notes: list[dict]) -> list[dict]:
    """Generate tag frequency data and golden set."""
    tag_counter: Counter = Counter()
    tag_batches: dict[str, set] = defaultdict(set)

    for note in notes:
        batch = note.get("_source_batch", "unknown")
        for tag in note.get("tags", []):
            tag_counter[tag] += 1
            tag_batches[tag].add(batch)

    golden = []
    for tag, count in tag_counter.most_common(200):
        golden.append({
            "tag": tag,
            "count": count,
            "batches": sorted(tag_batches[tag]),
        })

    return golden


def gen_topic_normalization(notes: list[dict]) -> list[dict]:
    """Generate topic frequency for normalization testing."""
    topic_counter: Counter = Counter()

    for note in notes:
        for t in note.get("topics", []):
            topic_counter[t] += 1

    return [
        {"topic": topic, "count": count}
        for topic, count in topic_counter.most_common()
    ]


def gen_product_fixtures(notes: list[dict]) -> list[dict]:
    """Generate product name frequency for normalization testing."""
    product_counter: Counter = Counter()

    for note in notes:
        for p in note.get("products", []):
            product_counter[p] += 1

    return [
        {"product": product, "count": count}
        for product, count in product_counter.most_common()
        if count >= 2  # Only products seen 2+ times
    ]


_ROLE_WORDS = {
    "manager", "director", "vp", "vice", "president", "head", "lead",
    "engineer", "developer", "analyst", "consultant", "specialist",
    "coordinator", "administrator", "officer", "executive", "chief",
    "senior", "junior", "principal", "associate", "team", "group",
    "technical", "account", "project", "program", "solution", "solutions",
    "architect", "partner", "customer", "client", "sales", "support",
    "operations", "supply", "chain", "logistics", "warehouse", "planning",
    "delivery", "implementation", "pre-sales", "presales",
}


def _classify_person(name: str) -> str:
    """Heuristic: real person vs role vs organization."""
    lower = name.lower().strip()

    # Organizations: contains Inc, AG, Ltd, LLC, GmbH, Corp, Group, Company
    if re.search(r'\b(inc|ag|ltd|llc|gmbh|corp|group|company|team)\b', lower):
        return "organization"

    # Roles: mostly common role words
    words = set(re.findall(r'[a-z]+', lower))
    role_overlap = words & _ROLE_WORDS
    if len(role_overlap) >= len(words) * 0.6 and len(words) >= 2:
        return "role"

    # Has parenthesized title → likely real person with title
    if re.search(r'\(.*\)', name):
        return "real_person"

    # Has 2+ capitalized words not all role words → likely real person
    cap_words = re.findall(r'[A-Z][a-z]+', name)
    if len(cap_words) >= 2:
        cap_lower = {w.lower() for w in cap_words}
        if not cap_lower.issubset(_ROLE_WORDS):
            return "real_person"

    # Single word or ambiguous
    if len(words) <= 1:
        return "ambiguous"

    return "role"


def gen_people_fixtures(notes: list[dict]) -> list[dict]:
    """Generate people filter fixtures with classification."""
    people_counter: Counter = Counter()

    for note in notes:
        for p in note.get("people", []):
            people_counter[p] += 1

    fixtures = []
    for person, count in people_counter.most_common():
        classification = _classify_person(person)
        expected = "keep" if classification == "real_person" else "filter"
        fixtures.append({
            "input": person,
            "count": count,
            "expected": expected,
            "type": classification,
        })

    return fixtures


def gen_quality_data(notes: list[dict]) -> list[dict]:
    """Generate quality prediction dataset."""
    data = []
    for note in notes:
        source = note.get("source_path") or note.get("source") or ""
        key_facts = note.get("key_facts", [])
        fact_count = len(key_facts) if isinstance(key_facts, list) else 0

        data.append({
            "extension": Path(source).suffix.lower() if source else "",
            "doc_type": note.get("doc_type"),
            "depth": note.get("depth"),
            "model": note.get("model"),
            "quality": note.get("quality"),
            "quality_score": note.get("quality_score", 0),
            "fact_count": fact_count,
            "topic_count": len(note.get("topics", [])),
            "product_count": len(note.get("products", [])),
            "tokens_used": note.get("tokens_used", 0),
            "batch": note.get("_source_batch"),
        })

    return data


def gen_routing_patterns(notes: list[dict]) -> list[dict]:
    """Generate source_path → routing pattern data."""
    patterns = []
    seen = set()

    for note in notes:
        source = note.get("source_path") or note.get("source") or ""
        if not source:
            continue

        source_p = Path(source.replace("\\", "/"))
        filename = source_p.name
        if filename in seen:
            continue
        seen.add(filename)

        # Extract the MyWork-relative folder structure
        parts = source_p.parts
        folder_pattern = ""
        for i, part in enumerate(parts):
            if part == "MyWork" and i + 1 < len(parts):
                # Get 2-3 levels after MyWork
                remaining = parts[i + 1:]
                folder_pattern = "/".join(remaining[:-1][:3])
                break

        if not folder_pattern:
            continue

        patterns.append({
            "filename": filename,
            "extension": source_p.suffix.lower(),
            "folder_pattern": folder_pattern,
            "client": note.get("client"),
            "doc_type": note.get("doc_type"),
            "type": note.get("type"),
        })

    return sorted(patterns, key=lambda p: p["folder_pattern"])


# ---------- analysis ----------

def analyze(
    notes: list[dict],
    classifier: list[dict],
    tags: list[dict],
    products: list[dict],
    people: list[dict],
    quality: list[dict],
    routing: list[dict],
) -> str:
    """Generate markdown analysis report."""
    # doc_type distribution
    doc_types = Counter(n.get("doc_type", "unknown") for n in notes)
    # quality by extension
    ext_quality: dict[str, list] = defaultdict(list)
    for q in quality:
        if q["quality_score"] and q["extension"]:
            ext_quality[q["extension"]].append(q["quality_score"])
    # quality by doc_type
    dt_quality: dict[str, list] = defaultdict(list)
    for q in quality:
        if q["quality_score"] and q["doc_type"]:
            dt_quality[q["doc_type"]].append(q["quality_score"])

    lines = [
        "# Training Data Extraction Report",
        "",
        f"**Date:** 2026-03-25",
        f"**Source:** {len(notes)} extraction notes from _outputs/",
        "",
        "## Generated Fixtures",
        "",
        "| Fixture | Count | Location |",
        "|---------|-------|----------|",
        f"| Classifier training | {len(classifier)} pairs | CKE/tests/fixtures/classifier_training.json |",
        f"| Tag golden set | {len(tags)} tags | CKE/tests/fixtures/tag_golden_set.json |",
        f"| Product normalization | {len(products)} products | CKE/tests/fixtures/product_normalization.json |",
        f"| People filter | {len(people)} entries | CKE/tests/fixtures/people_filter.json |",
        f"| Quality prediction | {len(quality)} entries | CKE/tests/fixtures/quality_prediction.json |",
        f"| Routing patterns | {len(routing)} entries | corp-by-os/tests/fixtures/routing_patterns.json |",
        "",
        "## Batch Distribution",
        "",
        "| Batch | Notes |",
        "|-------|-------|",
    ]
    batch_counts = Counter(n.get("_source_batch") for n in notes)
    for batch, count in batch_counts.most_common():
        lines.append(f"| {batch} | {count} |")

    lines += [
        "",
        "## Doc Type Distribution",
        "",
        "| doc_type | Count |",
        "|----------|-------|",
    ]
    for dt, count in doc_types.most_common():
        lines.append(f"| {dt} | {count} |")

    lines += [
        "",
        "## Quality by Extension",
        "",
        "| Extension | Count | Avg Score | Min | Max |",
        "|-----------|-------|-----------|-----|-----|",
    ]
    for ext in sorted(ext_quality, key=lambda e: -len(ext_quality[e])):
        scores = ext_quality[ext]
        lines.append(
            f"| {ext} | {len(scores)} | {sum(scores)/len(scores):.0f} "
            f"| {min(scores)} | {max(scores)} |"
        )

    lines += [
        "",
        "## Quality by Doc Type (top 10)",
        "",
        "| doc_type | Count | Avg Score |",
        "|----------|-------|-----------|",
    ]
    for dt in sorted(dt_quality, key=lambda d: -sum(dt_quality[d])/len(dt_quality[d]))[:10]:
        scores = dt_quality[dt]
        lines.append(f"| {dt} | {len(scores)} | {sum(scores)/len(scores):.0f} |")

    lines += [
        "",
        "## People Classification Summary",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]
    people_types = Counter(p["type"] for p in people)
    for ptype, count in people_types.most_common():
        lines.append(f"| {ptype} | {count} |")

    lines += [
        "",
        "## Top 20 Products",
        "",
        "| Product | Count |",
        "|---------|-------|",
    ]
    for p in products[:20]:
        lines.append(f"| {p['product']} | {p['count']} |")

    lines += [
        "",
        "## Top 20 Topics",
        "",
    ]
    topic_counter = Counter()
    for n in notes:
        for t in n.get("topics", []):
            topic_counter[t] += 1
    lines.append("| Topic | Count |")
    lines.append("|-------|-------|")
    for topic, count in topic_counter.most_common(20):
        lines.append(f"| {topic} | {count} |")

    lines.append("")
    return "\n".join(lines)


# ---------- main ----------

def _write_json(path: Path, data: list | dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return len(data) if isinstance(data, list) else 1


def main() -> None:
    print(f"Scanning {OUTPUTS_DIR} ...")
    notes = collect_all_notes()
    print(f"Found {len(notes)} extraction notes")

    if not notes:
        print("ERROR: No notes found. Check _outputs/ directory.", file=sys.stderr)
        sys.exit(1)

    # Save raw metadata
    raw_path = CKE_FIXTURES / "training_data_raw.json"
    _write_json(raw_path, notes)
    print(f"  Raw metadata: {raw_path} ({len(notes)} notes)")

    # Generate fixtures
    classifier = gen_classifier_fixtures(notes)
    n = _write_json(CKE_FIXTURES / "classifier_training.json", classifier)
    print(f"  Classifier training: {n} pairs")

    tags = gen_tag_golden_set(notes)
    n = _write_json(CKE_FIXTURES / "tag_golden_set.json", tags)
    print(f"  Tag golden set: {n} tags")

    topics = gen_topic_normalization(notes)
    n = _write_json(CKE_FIXTURES / "topic_normalization.json", topics)
    print(f"  Topic normalization: {n} topics")

    products = gen_product_fixtures(notes)
    n = _write_json(CKE_FIXTURES / "product_normalization.json", products)
    print(f"  Product normalization: {n} products")

    people = gen_people_fixtures(notes)
    n = _write_json(CKE_FIXTURES / "people_filter.json", people)
    print(f"  People filter: {n} entries")

    quality = gen_quality_data(notes)
    n = _write_json(CKE_FIXTURES / "quality_prediction.json", quality)
    print(f"  Quality prediction: {n} entries")

    routing = gen_routing_patterns(notes)
    n = _write_json(BOS_FIXTURES / "routing_patterns.json", routing)
    print(f"  Routing patterns: {n} entries")

    # Analysis report
    report = analyze(notes, classifier, tags, products, people, quality, routing)
    report_path = REPORT_DIR / "2026-03-25_TRAINING_DATA_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
