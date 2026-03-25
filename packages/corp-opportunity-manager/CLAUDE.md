# CLAUDE.md — corp-opportunity-manager

## What this repo does

Pre-sales opportunity lifecycle management CLI for Blue Yonder. Creates project folders, copies deck templates, manages metadata in Excel, and provides a conversational chat agent (Gemini Flash) for natural-language opportunity management in Polish or English.

## Quick start

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -e ".[dev,llm]"
cp .env.example .env     # then edit paths (NOT api keys)
pytest                   # 61 tests, all passing
```

## Architecture

```
src/corp_opportunity_manager/
  cli.py              Click CLI entry point (`com` command)
  chat.py             Rich terminal chat loop + intent router (8 intents)
  llm_client.py       Gemini Flash structured JSON intent parsing
  folder_manager.py   Folder creation, template copying, metadata
  folder_standards.py Structure audit, subfolder creation, naming conventions
  excel_manager.py    Read/update Project_Codes.xlsm (handles locked files)
  models.py           Dataclasses: OpportunityConfig, IntentResult, etc.
  config.py           YAML + .env config loader
  templates.py        Naming convention logic (folders, decks)
```

**Data flow:** CLI/chat → config loader → folder_manager/excel_manager → filesystem/Excel

**Entry point:** `com` (installed via `pyproject.toml [project.scripts]`)

## Dev standards

- Python 3.10+, Windows-first (PowerShell, `py -m`, pathlib)
- `pyproject.toml` as single source of truth (no requirements.txt)
- `ruff` lint + format, `pytest` quality gate
- Feature branches, no direct commits to main
- Logging not print, dataclasses not dicts
- Click CLI, Rich output
- Config in `config/default.yaml`, secrets in `.env`
- Type hints everywhere

## Key commands

```powershell
# Create new opportunity
com new "Lenzing" -p Planning -c "Jan Kowalski (VP Supply Chain)"

# List opportunities (from Excel or folders)
com list

# Show project details
com show "Lenzing"

# Copy a new deck template
com prep-deck "Lenzing" -t "Technical Deep Dive" --date 2026-03-15

# Interactive chat agent (requires GEMINI_API_KEY)
com chat
```

## Test suite

```bash
pytest tests/ -v    # 61 tests
```

Coverage:
- `test_folder_manager.py` — folder creation, template copy, metadata
- `test_excel_manager.py` — Excel read/write, locked file fallback
- `test_templates.py` — naming convention logic
- `test_folder_standards.py` — structure audit, subfolder creation
- `test_llm_client.py` — Gemini intent parsing (mocked)
- `test_chat.py` — chat session routing (mocked)

Gaps: `cli.py` (Click commands) and `config.py` have no dedicated tests.

## Dependencies

| Package | Purpose |
|---|---|
| click | CLI framework |
| rich | Terminal output (tables, panels, prompts) |
| pyyaml | Config file loading |
| openpyxl | Excel read/write |
| python-dotenv | .env file loading |
| google-genai (optional) | Gemini Flash LLM for chat agent |

## API Keys

Keys loaded globally from `Documents/.secrets/.env` via PowerShell profile.
Do NOT add API keys to local `.env`.
Check: `keys list` | Update: `keys set KEY value` | Reload: `keys reload`

This repo uses: `GEMINI_API_KEY`

## Configuration

- `config/default.yaml` — naming patterns, folder standards, stages, products, LLM settings
- `.env` — project-specific paths only (PROJECTS_ROOT, TEMPLATES_ROOT, etc.) — NO API keys
- `.env.example` — template with all expected variables

## Integration points

- **corp-by-os**: invoked via subprocess `com new` in workflows
- **Shared state**: reads Project_Codes.xlsm from 90_System/ (shared with corp-sca-time-automation)

COM is a standalone opportunity lifecycle tool. It does not write to the Obsidian vault.

## Related repos

- [ECOSYSTEM.md](../ECOSYSTEM.md) — full ecosystem overview
- [corp-by-os](../corp-by-os/) — orchestrator (invokes COM via workflows)
- [corp-os-meta](../corp-os-meta/) — shared schema

## Ecosystem

Part of the corp-by-os ecosystem:
- **corp-by-os** — orchestrator
- **corp-os-meta** — shared schemas
- **corp-knowledge-extractor** — extraction engine
- **corp-rfp-agent** — RFP automation
- **ai-council** — multi-model debate

## Known issues

- `cli.py` and `config.py` have no dedicated test coverage
- `com chat` not yet live-tested with real Gemini API key
- `callable` type hint in `chat.py:296` should be `typing.Callable` (mypy would flag)
- Excel ZipFile warning in tests (openpyxl read_only mode cleanup)
