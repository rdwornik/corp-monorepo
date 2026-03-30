"""Centralized path resolution for corp.extractor.

All config/template/prompt paths resolve from here.
Updated for unified src/corp/ package structure.
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).parent  # src/corp/extractor/
CORP_DIR = PACKAGE_DIR.parent  # src/corp/
SRC_DIR = CORP_DIR.parent  # src/
REPO_ROOT = SRC_DIR.parent  # repo root
CONFIG_DIR = REPO_ROOT / "config" / "extractor"
TEMPLATES_DIR = CONFIG_DIR / "templates"
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATA_DIR = PACKAGE_DIR / "data"  # src/corp/extractor/data/
