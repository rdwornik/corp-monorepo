"""Fix Path(__file__).parents[N] indices for new directory structure.

In the new structure, all packages are one level deeper:
  OLD: packages/<pkg>/src/<pkg_name>/<file>.py  (parents[2] = pkg root)
  NEW: src/corp/<subpkg>/<file>.py               (parents[3] = repo root)

For files in sub-subpackages (like anonymization/):
  OLD: parents[3] = pkg root
  NEW: parents[4] = repo root

Also fix config path references.
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
# RFP agent: src/corp/rfp/*.py — parents[2] -> parents[3]
# Also fix config paths: "config/X" -> "config/rfp/X"
# And prompts/X -> config/rfp/prompts/X
# ==========================================
rfp_dir = REPO / "src" / "corp" / "rfp"

# llm_router.py
f = rfp_dir / "llm_router.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
        ('"prompts/rfp_system_prompt_universal.txt"', '"config/rfp/prompts/rfp_system_prompt_universal.txt"'),
    ]):
        changed += 1

# rfp_answer_word.py
f = rfp_dir / "rfp_answer_word.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
    ]):
        changed += 1

# rfp_excel_agent.py
f = rfp_dir / "rfp_excel_agent.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
        ('"config/platform_matrix.json"', '"config/rfp/platform_matrix.json"'),
    ]):
        changed += 1

# rfp_feedback.py
f = rfp_dir / "rfp_feedback.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
        ('PROJECT_ROOT / "config" / "product_profiles"', 'PROJECT_ROOT / "config" / "rfp" / "product_profiles"'),
    ]):
        changed += 1

# validate_profiles.py
f = rfp_dir / "validate_profiles.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
        ('PROJECT_ROOT / "config" / "product_profiles"', 'PROJECT_ROOT / "config" / "rfp" / "product_profiles"'),
    ]):
        changed += 1

# answer_selector.py
f = rfp_dir / "answer_selector.py"
if f.exists():
    if fix_file(f, [
        ("parents[2]", "parents[3]"),
    ]):
        changed += 1

# anonymization/config.py — parents[4] stays correct (was wrong before, now right)
# But fix config path
f = rfp_dir / "anonymization" / "config.py"
if f.exists():
    if fix_file(f, [
        ('PROJECT_ROOT / "config/anonymization.yaml"', 'PROJECT_ROOT / "config/rfp/anonymization.yaml"'),
    ]):
        changed += 1

# ==========================================
# COM: src/corp/opportunity/config.py
# parent.parent.parent was old package root
# Now need parent.parent.parent.parent for repo root
# And config/ -> config/opportunity/
# ==========================================
f = REPO / "src" / "corp" / "opportunity" / "config.py"
if f.exists():
    text = f.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        'Path(__file__).resolve().parent.parent.parent / "config"',
        'Path(__file__).resolve().parent.parent.parent.parent / "config" / "opportunity"',
    )
    text = text.replace(
        "project_root = Path(__file__).resolve().parent.parent.parent",
        "project_root = Path(__file__).resolve().parent.parent.parent.parent",
    )
    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1

# ==========================================
# CPE: src/corp/project/cke_invoker.py — may have path refs
# ==========================================
f = REPO / "src" / "corp" / "project" / "cke_invoker.py"
if f.exists():
    text = f.read_text(encoding="utf-8")
    if "parents[" in text:
        text_new = text.replace("parents[2]", "parents[3]")
        if text_new != text:
            f.write_text(text_new, encoding="utf-8")
            changed += 1

print(f"Fixed path resolution in {changed} files")
