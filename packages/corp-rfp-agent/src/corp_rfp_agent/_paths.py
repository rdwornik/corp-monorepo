"""Centralized path resolution for corp-rfp-agent.

All config/data/prompt paths resolve from here. Only this file
needs updating when the package moves (e.g., monorepo merge).
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).parent          # src/corp_rfp_agent/
SRC_DIR = PACKAGE_DIR.parent                 # src/
REPO_ROOT = SRC_DIR.parent                   # repo root
DATA_DIR = REPO_ROOT / "data"
KB_DIR = DATA_DIR / "kb"
CONFIG_DIR = REPO_ROOT / "config"
PROMPTS_DIR = REPO_ROOT / "prompts"
