# Corporate OS Monorepo

Unified knowledge management ecosystem for pre-sales engineering.

## Packages

| Package | Version | Tests | CLI | Role |
|---------|---------|-------|-----|------|
| corp-os-meta | 1.0.0 | 117 | `corp-meta` | Shared schema & taxonomy |
| corp-knowledge-extractor | 0.8.0 | 693 | `cke` | Tiered AI extraction engine |
| corp-by-os | 0.3.0 | 900 | `corp` | Root orchestrator, sole vault writer |
| corp-project-extractor | 0.1.0 | 45 | `cpe` | Project folder classifier |
| corp-rfp-agent | 0.3.0 | 155 | scripts | AI-powered RFP answering engine |
| Integration | — | 8 | — | Cross-package integration tests |
| **Total** | | **1,918** | | |

## Setup

```bash
# Create venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all packages in dev mode
pip install -e packages/corp-os-meta
pip install -e packages/corp-knowledge-extractor
pip install -e "packages/corp-by-os[dev,llm]"
pip install -e packages/corp-project-extractor
pip install -e "packages/corp-rfp-agent[dev]"

# Run all tests
./scripts/run-all-tests.ps1
```

## Architecture

See `config/paths.toml` for centralized path configuration.
Each package maintains its own `pyproject.toml` and test suite.
CLI entry points: `corp`, `cke`, `cpe`, `corp-meta`.
