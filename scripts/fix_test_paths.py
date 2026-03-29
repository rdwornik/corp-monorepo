"""Fix path references in test files for new directory structure.

CKE tests moved from packages/corp-knowledge-extractor/tests/ to tests/extractor/
- parent.parent was package root -> now need parent.parent.parent for repo root
- templates/ -> config/extractor/templates/
- config/ -> config/extractor/
- scripts/ -> src/corp/extractor/scripts/

RFP tests moved from packages/corp-rfp-agent/tests/ to tests/rfp/
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
changed = 0


def fix_file(filepath: Path, replacements: list[tuple[str, str]]) -> bool:
    text = filepath.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        filepath.write_text(text, encoding="utf-8")
        return True
    return False


# ==========================================
# CKE tests: tests/extractor/
# Pattern: Path(__file__).parent.parent / "X" -> repo_root / "Y"
# repo_root from tests/extractor/ = Path(__file__).parent.parent.parent
# ==========================================
ext_tests = REPO / "tests" / "extractor"

for f in sorted(ext_tests.glob("*.py")):
    text = f.read_text(encoding="utf-8")
    original = text

    # Fix sys.path.insert that added package root
    # sys.path.insert(0, str(Path(__file__).parent.parent))
    # -> sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    text = text.replace(
        'sys.path.insert(0, str(Path(__file__).parent.parent))',
        'sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))',
    )

    # Fix sys.path.insert for scripts/
    # sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    # -> sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "corp" / "extractor" / "scripts"))
    text = text.replace(
        'sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))',
        'sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "corp" / "extractor" / "scripts"))',
    )

    # Fix templates path
    # Path(__file__).parent.parent / "templates"
    # -> Path(__file__).parent.parent.parent / "config" / "extractor" / "templates"
    text = text.replace(
        'Path(__file__).parent.parent / "templates"',
        'Path(__file__).parent.parent.parent / "config" / "extractor" / "templates"',
    )

    # Fix config path (general)
    # Path(__file__).parent.parent / "config" / "prompts" / ...
    # -> Path(__file__).parent.parent.parent / "config" / "extractor" / "prompts" / ...
    text = text.replace(
        'Path(__file__).parent.parent / "config" / "prompts"',
        'Path(__file__).parent.parent.parent / "config" / "extractor" / "prompts"',
    )

    # Path(__file__).parent.parent / "config" / "settings.yaml"
    text = text.replace(
        'Path(__file__).parent.parent / "config" / "settings.yaml"',
        'Path(__file__).parent.parent.parent / "config" / "extractor" / "settings.yaml"',
    )

    # Path(__file__).parent.parent / "config" / ...
    text = text.replace(
        'Path(__file__).parent.parent / "config"',
        'Path(__file__).parent.parent.parent / "config" / "extractor"',
    )

    # Fix data path in test_hybrid_classifier
    # parents[1] / "src/corp.extractor/data"
    text = text.replace(
        'parents[1] / "src/corp.extractor/data"',
        'parents[2] / "src" / "corp" / "extractor" / "data"',
    )

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# RFP tests: tests/rfp/
# Fix cli_smoke test subprocess paths
# ==========================================
rfp_tests = REPO / "tests" / "rfp"

f = rfp_tests / "test_cli_smoke.py"
if f.exists():
    text = f.read_text(encoding="utf-8")
    original = text
    # These tests run subprocess with old paths
    text = text.replace('src/corp/rfp/rfp_answer_word.py', 'src/corp/rfp/rfp_answer_word.py')
    text = text.replace('src/corp.rfp/rfp_answer_word.py', 'src/corp/rfp/rfp_answer_word.py')
    text = text.replace('src/corp.rfp/rfp_excel_agent.py', 'src/corp/rfp/rfp_excel_agent.py')
    text = text.replace('src/corp.rfp/rfp_feedback.py', 'src/corp/rfp/rfp_feedback.py')
    text = text.replace('src/corp.rfp/validate_profiles.py', 'src/corp/rfp/validate_profiles.py')
    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# RFP tests: fix path references for config
# ==========================================
for f in sorted(rfp_tests.glob("*.py")):
    text = f.read_text(encoding="utf-8")
    original = text

    # Fix paths that reference config/ from old package root
    # parent.parent was package root, now need parent.parent.parent for repo root
    text = text.replace(
        'Path(__file__).parent.parent / "config"',
        'Path(__file__).parent.parent.parent / "config" / "rfp"',
    )
    text = text.replace(
        'Path(__file__).parent.parent / "prompts"',
        'Path(__file__).parent.parent.parent / "config" / "rfp" / "prompts"',
    )

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# CPE tests: tests/project/
# ==========================================
proj_tests = REPO / "tests" / "project"

for f in sorted(proj_tests.glob("*.py")):
    text = f.read_text(encoding="utf-8")
    original = text

    text = text.replace(
        'Path(__file__).parent.parent / "config"',
        'Path(__file__).parent.parent.parent / "config" / "project"',
    )
    text = text.replace(
        'Path(__file__).parent.parent / "schemas"',
        'Path(__file__).parent.parent.parent / "config" / "project" / "schemas"',
    )

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# COM tests: tests/opportunity/
# ==========================================
opp_tests = REPO / "tests" / "opportunity"

for f in sorted(opp_tests.glob("*.py")):
    text = f.read_text(encoding="utf-8")
    original = text

    text = text.replace(
        'Path(__file__).parent.parent / "config"',
        'Path(__file__).parent.parent.parent / "config" / "opportunity"',
    )

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# Schema tests: tests/schema/ — shouldn't need path fixes (uses package imports)
# ==========================================

# ==========================================
# Corp-by-os tests promoted to tests/ root
# These used parent.parent which was packages/corp-by-os/
# Now parent is tests/, need parent.parent for repo root
# But most tests use imports, not path lookups
# ==========================================

print(f"Fixed test path references in {changed} files")
