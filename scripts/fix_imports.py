"""Fix all imports from old package names to new corp.* namespace.

Run from repo root. Delete after consolidation.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Replacement rules — ORDER MATTERS: longest patterns first to avoid partial matches
REPLACEMENTS = [
    ("corp.extractor", "corp.extractor"),
    ("corp.opportunity", "corp.opportunity"),
    ("corp.project", "corp.project"),
    ("corp.rfp", "corp.rfp"),
    ("corp.schema", "corp.schema"),
    ("corp", "corp"),
]

# Special replacements for non-import contexts
SPECIAL_REPLACEMENTS = [
    # CKE config_loader was at config/config_loader.py, now at corp.extractor.config_loader
    ("from corp.extractor.config_loader import", "from corp.extractor.config_loader import"),
    ("from corp.extractor.config_loader ", "from corp.extractor.config_loader "),
    ("import corp.extractor.config_loader", "import corp.extractor.config_loader"),
]


def fix_file(filepath: Path) -> tuple[bool, int]:
    """Fix imports in a single file. Returns (changed, count_of_replacements)."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False, 0

    original = text
    count = 0

    # Apply special replacements first
    for old, new in SPECIAL_REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            count += 1

    # Apply main replacements
    for old, new in REPLACEMENTS:
        # Import statements: from X.Y import Z / from X import Z
        if f"from {old}." in text:
            text = text.replace(f"from {old}.", f"from {new}.")
            count += 1
        if f"from {old} " in text:
            text = text.replace(f"from {old} ", f"from {new} ")
            count += 1

        # import X.Y / import X
        if f"import {old}." in text:
            text = text.replace(f"import {old}.", f"import {new}.")
            count += 1
        # Careful: "import corp\n" but not "import corp_by_os_something"
        pattern = re.compile(rf"import {re.escape(old)}(\s|$)", re.MULTILINE)
        text = pattern.sub(f"import {new}\\1", text)
        if pattern.search(original):
            count += 1

        # String references (logger names, module paths in strings)
        if f'"{old}.' in text:
            text = text.replace(f'"{old}.', f'"{new}.')
            count += 1
        if f"'{old}." in text:
            text = text.replace(f"'{old}.", f"'{new}.")
            count += 1
        # Standalone string references
        if f'"{old}"' in text:
            text = text.replace(f'"{old}"', f'"{new}"')
            count += 1
        if f"'{old}'" in text:
            text = text.replace(f"'{old}'", f"'{new}'")
            count += 1

    if text != original:
        filepath.write_text(text, encoding="utf-8")
        return True, count
    return False, 0


def fix_yaml(filepath: Path) -> tuple[bool, int]:
    """Fix package references in YAML files."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False, 0

    original = text
    count = 0

    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            count += 1

    if text != original:
        filepath.write_text(text, encoding="utf-8")
        return True, count
    return False, 0


# Process all .py files
changed_py = 0
changed_yaml = 0
total_replacements = 0

for py in sorted(REPO.rglob("*.py")):
    rel = py.relative_to(REPO)
    if any(part in str(rel) for part in ["__pycache__", ".venv", ".ruff_cache", ".pytest_cache", "packages/"]):
        continue
    changed, count = fix_file(py)
    if changed:
        changed_py += 1
        total_replacements += count

# Process YAML and TOML files (not in packages/)
for pattern in ["*.yaml", "*.yml", "*.toml"]:
    for f in sorted(REPO.rglob(pattern)):
        rel = f.relative_to(REPO)
        if any(part in str(rel) for part in ["__pycache__", ".venv", "packages/", "node_modules"]):
            continue
        changed, count = fix_yaml(f)
        if changed:
            changed_yaml += 1
            total_replacements += count

print(f"Updated {changed_py} .py files, {changed_yaml} .yaml/.toml files")
print(f"Total replacement operations: {total_replacements}")
