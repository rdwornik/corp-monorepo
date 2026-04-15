# corp.opportunity -- COM (Opportunity Manager)

## What this module does

Manages the opportunity lifecycle: creating new opportunities with proper
folder structure, managing project codes in Excel, preparing presentation
decks from templates, and tracking opportunity stages. Invoked via `com` CLI.

## Key files

| File | What it does |
|------|-------------|
| cli.py | `com` CLI: new, list, show, prep-deck, chat |
| config.py | Settings from config/opportunity/default.yaml |
| folder_manager.py | Create/manage opportunity folder structures |
| folder_standards.py | Folder naming and structure standards |
| excel_manager.py | Project codes Excel workbook management |
| llm_client.py | LLM integration for opportunity analysis |
| templates.py | Deck template management |
| chat.py | Interactive opportunity chat |
| models.py | Opportunity data models |

## Dependencies

- **Depends on:** corp.opportunity internal only (core layer)
- **Used by:** corp.cli (via agents.yaml registration)

## Data flow

New opportunity -> create folders -> register in Excel -> prep deck from template -> track stages
