"""One-shot script to move all package files to new src/corp/ structure.

Uses git mv to preserve history. Run from repo root.
Delete this script after consolidation is complete.
"""
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
errors = []
moved = 0


def run(cmd: str) -> bool:
    """Run a shell command, return True on success."""
    global moved
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(REPO))
    if result.returncode != 0:
        # Skip "already exists" errors for dirs
        if "already exists" not in result.stderr and "not under version control" not in result.stderr:
            errors.append(f"FAIL: {cmd}\n  {result.stderr.strip()}")
            return False
    moved += 1
    return True


def mkdirs(*paths: str):
    """Create directories (no git tracking needed for empty dirs)."""
    for p in paths:
        (REPO / p).mkdir(parents=True, exist_ok=True)


def git_mv(src: str, dst: str) -> bool:
    """git mv a file or directory."""
    src_path = REPO / src
    if not src_path.exists():
        errors.append(f"SKIP (not found): {src}")
        return False
    # Ensure parent of destination exists
    (REPO / dst).parent.mkdir(parents=True, exist_ok=True)
    return run(f'git mv "{src}" "{dst}"')


def git_mv_contents(src_dir: str, dst_dir: str, skip_pycache=True):
    """Move all files/dirs from src_dir to dst_dir."""
    src = REPO / src_dir
    if not src.exists():
        errors.append(f"SKIP (dir not found): {src_dir}")
        return
    mkdirs(dst_dir)
    for item in sorted(src.iterdir()):
        if skip_pycache and item.name == "__pycache__":
            continue
        if item.name == ".ruff_cache" or item.name == ".pytest_cache":
            continue
        dst = f"{dst_dir}/{item.name}"
        git_mv(f"{src_dir}/{item.name}", dst)


print("=" * 60)
print("CONSOLIDATION MOVE SCRIPT")
print("=" * 60)

# ============================================================
# PHASE 1: Create directory structure
# ============================================================
print("\n[1/7] Creating directory structure...")
mkdirs(
    "src/corp",
    "src/corp/schema",
    "src/corp/schema/data",
    "src/corp/extractor",
    "src/corp/extractor/frames",
    "src/corp/extractor/providers",
    "src/corp/extractor/slides",
    "src/corp/extractor/data",
    "src/corp/extractor/scripts",
    "src/corp/project",
    "src/corp/rfp",
    "src/corp/rfp/anonymization",
    "src/corp/opportunity",
    # corp-by-os promoted dirs
    "src/corp/cli",
    "src/corp/cleanup",
    "src/corp/extraction",
    "src/corp/ingest",
    "src/corp/ops",
    "src/corp/overnight",
    "src/corp/retrieve",
    # Test dirs
    "tests/schema",
    "tests/extractor",
    "tests/extractor/fixtures",
    "tests/project",
    "tests/rfp",
    "tests/rfp/fixtures",
    "tests/opportunity",
    # Config dirs
    "config/extractor",
    "config/extractor/prompts",
    "config/extractor/templates",
    "config/project",
    "config/project/schemas",
    "config/rfp",
    "config/rfp/product_profiles",
    "config/rfp/product_profiles/_effective",
    "config/rfp/product_profiles/_overrides",
    "config/rfp/prompts",
    "config/opportunity",
)

# ============================================================
# PHASE 2: Move corp-os-meta → src/corp/schema/
# ============================================================
print("\n[2/7] Moving corp-os-meta -> src/corp/schema/...")
meta_src = "src/corp/schema"
meta_dst = "src/corp/schema"

# Move individual .py files (not dirs)
for py in sorted((REPO / meta_src).glob("*.py")):
    git_mv(f"{meta_src}/{py.name}", f"{meta_dst}/{py.name}")

# Move taxonomy.yaml
git_mv(f"{meta_src}/taxonomy.yaml", f"{meta_dst}/taxonomy.yaml")

# Move data/ contents
git_mv_contents(f"{meta_src}/data", f"{meta_dst}/data")

# Move tests
git_mv_contents("packages/corp-os-meta/tests", "tests/schema")

# ============================================================
# PHASE 3: Move CKE → src/corp/extractor/
# ============================================================
print("\n[3/7] Moving CKE -> src/corp/extractor/...")
cke_src = "src/corp/extractor"
cke_dst = "src/corp/extractor"

# Move top-level .py files
for py in sorted((REPO / cke_src).glob("*.py")):
    git_mv(f"{cke_src}/{py.name}", f"{cke_dst}/{py.name}")

# Move subpackages
for subpkg in ["frames", "providers", "slides"]:
    git_mv_contents(f"{cke_src}/{subpkg}", f"{cke_dst}/{subpkg}")

# Move data/ (inside package)
git_mv_contents(f"{cke_src}/data", f"{cke_dst}/data")

# Move scripts/ (CLI entry point)
cke_scripts = "packages/corp-knowledge-extractor/scripts"
for item in sorted((REPO / cke_scripts).iterdir()):
    if item.name == "__pycache__":
        continue
    git_mv(f"{cke_scripts}/{item.name}", f"src/corp/extractor/scripts/{item.name}")

# Move CKE config files
cke_cfg = "packages/corp-knowledge-extractor/config"
for item in sorted((REPO / cke_cfg).iterdir()):
    if item.name == "__pycache__":
        continue
    if item.is_dir():
        # prompts/ dir
        git_mv_contents(f"{cke_cfg}/{item.name}", f"config/extractor/{item.name}")
    else:
        git_mv(f"{cke_cfg}/{item.name}", f"config/extractor/{item.name}")

# Move CKE templates
cke_tmpl = "packages/corp-knowledge-extractor/templates"
if (REPO / cke_tmpl).exists():
    git_mv_contents(cke_tmpl, "config/extractor/templates")

# Move CKE tests
cke_tests = "packages/corp-knowledge-extractor/tests"
for item in sorted((REPO / cke_tests).iterdir()):
    if item.name in ("__pycache__", ".pytest_cache"):
        continue
    if item.is_dir():
        # fixtures/ dir
        git_mv_contents(f"{cke_tests}/{item.name}", f"tests/extractor/{item.name}")
    else:
        git_mv(f"{cke_tests}/{item.name}", f"tests/extractor/{item.name}")

# ============================================================
# PHASE 4: Move corp-by-os → src/corp/ (promoted)
# ============================================================
print("\n[4/7] Moving corp-by-os -> src/corp/ (promoted to root)...")
cbo_src = "src/corp"
cbo_dst = "src/corp"

# Move subpackage directories
for subpkg in ["cli", "cleanup", "extraction", "ingest", "ops", "overnight", "retrieve"]:
    subpkg_path = REPO / cbo_src / subpkg
    if subpkg_path.exists() and any(subpkg_path.glob("*.py")):
        git_mv_contents(f"{cbo_src}/{subpkg}", f"{cbo_dst}/{subpkg}")

# Skip empty dirs: doctor, freshness, extraction/non_project

# Move top-level .py files
for py in sorted((REPO / cbo_src).glob("*.py")):
    git_mv(f"{cbo_src}/{py.name}", f"{cbo_dst}/{py.name}")

# Move corp-by-os config/ YAML files to repo-root config/
cbo_cfg = "packages/corp-by-os/config"
for item in sorted((REPO / cbo_cfg).iterdir()):
    if item.name in ("__pycache__", "__init__.py", "settings.py"):
        continue  # Skip legacy Python files
    if item.suffix in (".yaml", ".yml"):
        git_mv(f"{cbo_cfg}/{item.name}", f"config/{item.name}")

# Move corp-by-os tests
cbo_tests = "packages/corp-by-os/tests"
# First: move root-level test files
for item in sorted((REPO / cbo_tests).iterdir()):
    if item.name in ("__pycache__", ".pytest_cache", ".ruff_cache"):
        continue
    if item.is_file():
        git_mv(f"{cbo_tests}/{item.name}", f"tests/{item.name}")
    elif item.is_dir():
        if item.name == "fixtures":
            # Move fixtures contents
            git_mv_contents(f"{cbo_tests}/fixtures", "tests/fixtures")
        elif item.name in ("integration", "unit"):
            # These already exist or are empty at repo root
            pass
        else:
            # test_cleanup, test_ingest, etc — move entire dir
            git_mv_contents(f"{cbo_tests}/{item.name}", f"tests/{item.name}")

# Move corp-by-os scripts to repo scripts
cbo_scripts = "packages/corp-by-os/scripts"
for item in sorted((REPO / cbo_scripts).iterdir()):
    if item.name == "__pycache__":
        continue
    # Check if file already exists in repo scripts/
    dst = f"scripts/{item.name}"
    if (REPO / dst).exists():
        errors.append(f"COLLISION: {dst} already exists, skipping {cbo_scripts}/{item.name}")
    else:
        git_mv(f"{cbo_scripts}/{item.name}", dst)

# ============================================================
# PHASE 5: Move CPE → src/corp/project/
# ============================================================
print("\n[5/7] Moving CPE -> src/corp/project/...")
cpe_src = "src/corp/project"
cpe_dst = "src/corp/project"

git_mv_contents(cpe_src, cpe_dst)

# Move CPE config
git_mv_contents("packages/corp-project-extractor/config", "config/project")

# Move CPE schemas
cpe_schemas = "packages/corp-project-extractor/schemas"
if (REPO / cpe_schemas).exists():
    git_mv_contents(cpe_schemas, "config/project/schemas")

# Move CPE tests
cpe_tests = "packages/corp-project-extractor/tests"
for item in sorted((REPO / cpe_tests).iterdir()):
    if item.name in ("__pycache__", ".pytest_cache"):
        continue
    if item.is_dir():
        git_mv_contents(f"{cpe_tests}/{item.name}", f"tests/project/{item.name}")
    else:
        git_mv(f"{cpe_tests}/{item.name}", f"tests/project/{item.name}")

# ============================================================
# PHASE 6: Move rfp-agent → src/corp/rfp/
# ============================================================
print("\n[6/7] Moving rfp-agent -> src/corp/rfp/...")
rfp_src = "src/corp/rfp"
rfp_dst = "src/corp/rfp"

# Move top-level .py files
for py in sorted((REPO / rfp_src).glob("*.py")):
    git_mv(f"{rfp_src}/{py.name}", f"{rfp_dst}/{py.name}")

# Move anonymization subpackage
git_mv_contents(f"{rfp_src}/anonymization", f"{rfp_dst}/anonymization")

# Move rfp config
rfp_cfg = "packages/corp-rfp-agent/config"
for item in sorted((REPO / rfp_cfg).iterdir()):
    if item.name == "__pycache__":
        continue
    if item.is_dir():
        # product_profiles/ — move the whole tree
        if item.name == "product_profiles":
            pp = f"{rfp_cfg}/product_profiles"
            for sub in sorted((REPO / pp).iterdir()):
                if sub.is_dir():
                    git_mv_contents(f"{pp}/{sub.name}", f"config/rfp/product_profiles/{sub.name}")
        else:
            git_mv_contents(f"{rfp_cfg}/{item.name}", f"config/rfp/{item.name}")
    else:
        git_mv(f"{rfp_cfg}/{item.name}", f"config/rfp/{item.name}")

# Move rfp prompts
rfp_prompts = "packages/corp-rfp-agent/prompts"
if (REPO / rfp_prompts).exists():
    git_mv_contents(rfp_prompts, "config/rfp/prompts")

# Move rfp scripts to repo scripts (with prefix to avoid collision)
rfp_scripts = "packages/corp-rfp-agent/scripts"
if (REPO / rfp_scripts).exists():
    for item in sorted((REPO / rfp_scripts).iterdir()):
        if item.name == "__pycache__":
            continue
        dst = f"scripts/rfp_{item.name}" if (REPO / f"scripts/{item.name}").exists() else f"scripts/{item.name}"
        git_mv(f"{rfp_scripts}/{item.name}", dst)

# Move rfp tests
rfp_tests = "packages/corp-rfp-agent/tests"
for item in sorted((REPO / rfp_tests).iterdir()):
    if item.name in ("__pycache__", ".pytest_cache"):
        continue
    if item.is_dir():
        git_mv_contents(f"{rfp_tests}/{item.name}", f"tests/rfp/{item.name}")
    else:
        git_mv(f"{rfp_tests}/{item.name}", f"tests/rfp/{item.name}")

# ============================================================
# PHASE 7: Move COM → src/corp/opportunity/
# ============================================================
print("\n[7/7] Moving COM -> src/corp/opportunity/...")
com_src = "src/corp/opportunity"
com_dst = "src/corp/opportunity"

git_mv_contents(com_src, com_dst)

# Move COM config
git_mv_contents("packages/corp-opportunity-manager/config", "config/opportunity")

# Move COM tests
com_tests = "packages/corp-opportunity-manager/tests"
for item in sorted((REPO / com_tests).iterdir()):
    if item.name in ("__pycache__", ".pytest_cache"):
        continue
    if item.is_dir():
        git_mv_contents(f"{com_tests}/{item.name}", f"tests/opportunity/{item.name}")
    else:
        git_mv(f"{com_tests}/{item.name}", f"tests/opportunity/{item.name}")

# ============================================================
# REPORT
# ============================================================
print(f"\n{'=' * 60}")
print(f"DONE: {moved} git mv operations")
if errors:
    print(f"\n⚠ {len(errors)} issues:")
    for e in errors:
        print(f"  {e}")
else:
    print("No errors!")
