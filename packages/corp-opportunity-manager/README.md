# corp-opportunity-manager

Pre-sales opportunity lifecycle management CLI for Blue Yonder. Automates project folder creation, presentation template copying, Excel metadata tracking, and provides a conversational chat agent powered by Gemini Flash for natural-language opportunity management in Polish or English.

## Features

- **Folder scaffolding** — creates standardized project directories with metadata stubs
- **Deck templating** — copies and renames PowerPoint templates with naming conventions
- **Excel integration** — reads/updates Project_Codes.xlsm, handles locked files gracefully
- **Structure auditing** — checks project folders against naming and layout standards
- **Subfolder creation** — on-demand RFP, Meetings, Implementation Services structures
- **Chat agent** — natural language interface via Gemini Flash (Polish/English, 8 intents)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev,llm]"   # dev = pytest/ruff, llm = google-genai
```

Copy `.env.example` to `.env` and set your paths:

```bash
PROJECTS_ROOT=C:\Users\...\MyWork\10_Projects
TEMPLATES_ROOT=C:\Users\...\MyWork\30_Templates
PROJECT_CODES_EXCEL=C:\Users\...\MyWork\90_System\Project_Codes.xlsm
GEMINI_API_KEY=your-key-here
```

## Usage

```powershell
# Create new opportunity (folder + deck + metadata)
com new "Lenzing" -p Planning -c "Jan Kowalski (VP Supply Chain)"

# List opportunities (from Excel or project folders)
com list

# Show project details
com show "Lenzing"

# Copy a new deck template
com prep-deck "Lenzing" -t "Technical Deep Dive" --date 2026-03-15

# Interactive chat agent (requires GEMINI_API_KEY)
com chat
```

### Chat Agent (`com chat`)

Type naturally — the agent parses intent and manages your opportunities:

```
You: Mam nowe opportunity, Lenzing, potrzebuja IBP, kontakt Jan Kowalski
Agent: Created Lenzing_Planning/ with deck and metadata

You: Przygotuj prezentacje na technical deep dive, 15 marca
Agent: Lenzing_2026-03-15_Technical_Deep_Dive.pptx created

You: Sprawdz strukture Lenzing
Agent: Lenzing_Planning/ audit: _knowledge/ ok, missing Meetings/ folder
```

**Supported intents:** create_opportunity, prep_deck, show_project, list_projects, create_subfolder, check_structure, chitchat, clarify

## Architecture

```
src/corp_opportunity_manager/
  cli.py              Click CLI entry point
  chat.py             Rich terminal chat loop + intent router
  llm_client.py       Gemini Flash structured JSON intent parsing
  folder_manager.py   Folder creation, template copying, metadata
  folder_standards.py Structure audit, subfolder creation, naming conventions
  excel_manager.py    Read/update Project_Codes.xlsm (handles locked files)
  models.py           Dataclasses: OpportunityConfig, IntentResult, etc.
  config.py           YAML + .env config loader
  templates.py        Naming convention logic
```

Configuration lives in `config/default.yaml` (behavior) and `.env` (paths/secrets).

## Testing

```bash
pytest tests/ -v
```

61 tests covering folder management, Excel operations, template naming, folder standards, LLM intent parsing, and chat session routing.

## Related repos

- **corp-by-os** — orchestrator
- **corp-os-meta** — shared schemas
- **corp-knowledge-extractor** — extraction engine
- **corp-rfp-agent** — RFP automation
- **ai-council** — multi-model debate

## License

Internal use only — Blue Yonder Pre-Sales Engineering
