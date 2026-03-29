"""Centralized path resolution for corp-knowledge-extractor.

All config/template/prompt paths resolve from here. Only this file
needs updating when the package moves (e.g., monorepo merge).
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).parent  # src/corp.extractor/
SRC_DIR = PACKAGE_DIR.parent  # src/
REPO_ROOT = SRC_DIR.parent  # repo root
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATES_DIR = REPO_ROOT / "templates"
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATA_DIR = REPO_ROOT / "data"
