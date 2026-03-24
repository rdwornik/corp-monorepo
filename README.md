# Corporate OS Monorepo

Unified knowledge management ecosystem for pre-sales engineering.

## Packages

| Package | Version | Tests | Role |
|---------|---------|-------|------|
| corp-os-meta | 1.0.0 | 108 | Shared schema & taxonomy |
| corp-knowledge-extractor | 0.8.0 | 670 | Tiered AI extraction engine |
| corp-by-os | 0.3.0 | 847 | Root orchestrator, sole vault writer |
| corp-project-extractor | 0.1.0 | 45 | Project folder classifier |

## Setup

```bash
# Create venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all packages in dev mode
pip install -e packages/corp-os-meta
pip install -e packages/corp-knowledge-extractor
pip install -e packages/corp-by-os
pip install -e packages/corp-project-extractor

# Run all tests
./scripts/run-all-tests.ps1
```

## Architecture

See `config/paths.toml` for centralized path configuration.
Each package maintains its own `pyproject.toml` and test suite.
CLI entry points: `corp`, `cke`, `cpe`, `corp-meta`.
