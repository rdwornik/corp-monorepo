# actions/

> Domain-split action handlers for the workflow engine, replacing the monolithic built_in_actions.py.

## Responsibility

Provides a decorator-based action registry (`@register_action`) that maps action names to handler functions. Each domain module (analytics, archive, brief, deck, inbox, index, knowledge, monitoring, task, vault) registers its actions at import time. The workflow engine and chat loop resolve action names via `get_action()`.

## Key Exports

- `register_action(name)` — decorator to register a built-in action handler
- `get_action(name)` — look up a registered action by name
- `analytics_actions` — index stats, dedup reports
- `archive_actions` — vault zone archival
- `brief_actions` — project brief generation
- `inbox_actions` — inbox routing trigger
- `knowledge_actions` — knowledge extraction trigger
- `task_actions` — task add/list/done actions

## Dependencies

- `corp.models` — StepResult, VaultZone
- `corp.config` — get_config()
- `corp.schema` — folder_names (INBOX constant)

## Layer

Static: 3 | Runtime: 6
