"""Second pass: aggressive replacement of ALL remaining old package name references.

Replaces bare module references in code, comments, strings, etc.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Order matters: longest first
REPLACEMENTS = [
    ("corp.extractor", "corp.extractor"),
    ("corp.opportunity", "corp.opportunity"),
    ("corp.project", "corp.project"),
    ("corp.rfp", "corp.rfp"),
    ("corp.schema", "corp.schema"),
    ("corp", "corp"),
]

# Path-based replacements (old filesystem paths)
PATH_REPLACEMENTS = [
    ("src/corp/extractor/", "src/corp/extractor/"),
    ("src/corp/extractor", "src/corp/extractor"),
    ("src/corp/", "src/corp/"),
    ("src/corp", "src/corp"),
    ("src/corp/project/", "src/corp/project/"),
    ("src/corp/project", "src/corp/project"),
    ("src/corp/rfp/", "src/corp/rfp/"),
    ("src/corp/rfp", "src/corp/rfp"),
    ("src/corp/opportunity/", "src/corp/opportunity/"),
    ("src/corp/opportunity", "src/corp/opportunity"),
    ("src/corp/schema/", "src/corp/schema/"),
    ("src/corp/schema", "src/corp/schema"),
    ("src/corp/rfp/", "src/corp/rfp/"),
    ("src/corp/rfp", "src/corp/rfp"),
]


def fix_file(filepath: Path) -> bool:
    try:
        text = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False

    original = text

    # Apply path replacements first (longer patterns)
    for old, new in PATH_REPLACEMENTS:
        text = text.replace(old, new)

    # Apply module name replacements
    for old, new in REPLACEMENTS:
        # Replace all remaining occurrences with word-boundary awareness
        # Replace X.Y pattern (module attribute access)
        text = text.replace(f"{old}.", f"{new}.")
        # Replace X at end of line or before non-alphanumeric
        # Use regex for word-boundary replacement
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)

    if text != original:
        filepath.write_text(text, encoding="utf-8")
        return True
    return False


changed = 0
for ext in ("*.py", "*.yaml", "*.yml", "*.toml"):
    for f in sorted(REPO.rglob(ext)):
        rel = str(f.relative_to(REPO))
        if any(skip in rel for skip in ["__pycache__", ".venv", ".ruff_cache", ".pytest_cache"]):
            continue
        # Skip files in packages/ (will be cleaned up)
        if rel.startswith("packages"):
            continue
        if fix_file(f):
            changed += 1

print(f"Pass 2: updated {changed} files")
