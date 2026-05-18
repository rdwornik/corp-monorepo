# Corporate OS Monorepo

Unified knowledge management ecosystem for pre-sales engineering.

## Modules

All code lives in `src/corp/` under a single `pyproject.toml`.

| Module | CLI | Tests | Role |
|--------|-----|-------|------|
| `corp/schema/` | `corp-meta` | 118 | Shared schema & taxonomy |
| `corp/extractor/` | `cke` | 838 | Tiered AI extraction engine |
| `corp/ingest/` `corp/retrieve/` `corp/cli/` | `corp` | 926 | Root orchestrator; sole writer for `02_sources/` (ADR-27) |
| `corp/project/` | `cpe` | 45 | Project folder classifier |
| `corp/rfp/` | — | 155 | AI-powered RFP answering engine |
| `corp/opportunity/` | `com` | 62 | Opportunity lifecycle management |
| Integration | — | 9 | Cross-module integration tests |
| **Total** | | **2,412** | |

## Setup

```bash
# Create venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install in dev mode (single command)
pip install -e ".[dev,llm]"

# Run all tests
./scripts/run-all-tests.ps1
```

## Architecture

See `config/paths.toml` for centralized path configuration.
See `CLAUDE.md` for architectural invariants and dependency rules.
CLI entry points: `corp`, `cke`, `cpe`, `corp-meta`, `com`.
