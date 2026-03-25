# Task: Bootstrap corp-opportunity-manager

## Overview

New agent in the corp-by-os ecosystem. Manages the lifecycle of pre-sales opportunities: onboarding (folder creation, template copying, metadata), tracking, and eventually archiving. This is the "front door" — when a new opportunity arrives, this agent sets everything up and triggers downstream tools.

**Ecosystem position:**
```
corp-by-os (orchestrator)
    ↓ invokes
corp-opportunity-manager        ← THIS PROJECT
    ↓ triggers (future)
corp-project-extractor          (scan incoming docs)
corp-knowledge-extractor        (extract from recordings)
    ↓ validates via
corp-os-meta                    (shared schema + taxonomy)
```

**Key principle:** This agent doesn't extract knowledge from files — that's what the extractors do. This agent manages the PROJECT LIFECYCLE: creation, structure, metadata, templates, and eventually task tracking.

---

## The Manual Workflow Today (what we're automating)

### Step 1: Project Codes Excel (STAYS MANUAL — trigger point)
- User adds a row to `project_codes.xlsx` with: project name, client, product area, stage, dates
- This Excel lives in `MyWork/90_System/` (or similar)
- The Excel row IS the source of truth for "this opportunity exists"
- Future: Excel row contains a link back to the project folder

### Step 2: Folder Creation (AUTOMATE)
- Create folder in `MyWork/10_Projects/{Client}_{Product}/`
- Standard subfolder structure (from existing project patterns):
  ```
  Lenzing_Planning/
  ├── _knowledge/          # Created by corp-project-extractor later
  ├── _extracted/          # Created by corp-project-extractor later
  └── (files land here as opportunity progresses)
  ```
- Folder naming convention: `{Client}_{ProductArea}` (e.g., `Lenzing_Planning`, `Honda_WMS`)

### Step 3: Teams Channel Link (SEMI-MANUAL)
- Sales/account team creates a Teams channel for the opportunity
- User manually copies the Teams channel link
- Agent creates a `.url` shortcut or `_teams_channel.txt` reference file in the project folder
- Future (Graph API): agent could detect new channels or subscribe to notifications

### Step 4: PowerPoint Template (AUTOMATE)
- Copy corporate PPT template from `MyWork/30_Templates/` (or wherever it lives)
- Rename with convention: `{Client}_{Date}_{Topic}.pptx`
- Example: `Lenzing_2026-03-05_Discovery.pptx`
- Template path is configurable (not hardcoded)
- Future: pre-populate title slide with client name, date, BY branding

### Step 5: OneNote Section (AUTOMATE — but evaluate)
- Create a new section in the project's OneNote notebook
- Question: Is OneNote still valuable when Obsidian handles structured notes?
- Decision: implement as optional (config flag), revisit after Obsidian pipeline matures
- If OneNote: use Microsoft Graph API to create section
- If Obsidian: create `_knowledge/project-notes.md` with frontmatter from corp-os-meta

### Step 6: Company Overview (AUTOMATE — future)
- Fetch basic company info: industry, size, HQ, key products
- Sources: web search, LinkedIn, annual reports
- Output: `_knowledge/company-overview.md` with corp-os-meta frontmatter
- This gives immediate context before the first call

### Step 7: Task Creation (FUTURE — Graph API)
- Create tasks in Microsoft Planner or To Do
- Standard onboarding checklist: "Review briefing book", "Prep discovery deck", "Schedule internal alignment"
- Graph API integration

---

## Phase 1: MVP (what to build NOW)

### Input
User runs CLI command:
```powershell
com new "Lenzing" --product Planning --contact "Jan Kowalski (VP Supply Chain)"
```

Or more conversational (future, via corp-by-os):
```
"New opportunity: Lenzing, they need IBP/SIOP, contact is Jan Kowalski"
```

### MVP Actions
1. **Create project folder** in `10_Projects/{Client}_{Product}/`
2. **Copy PPT template** with naming: `{Client}_{Date}_Discovery.pptx`
3. **Create `_knowledge/` stub** with:
   - `notes.md` — empty human notes file
   - `project-info.yaml` — basic metadata (client, product, contact, created date, stage: discovery)
4. **Update project codes Excel** — add link to folder in the row (requires user to specify which row, or match by client name)
5. **Print summary** — Rich output showing what was created

### MVP Does NOT Do
- OneNote (Phase 2)
- Web research / company overview (Phase 2)
- Task creation in Planner (Phase 3)
- Voice/chat interface (Phase 4, via corp-by-os)

---

## Phase 2: Microsoft Graph Integration

### OneNote
- Create section in a designated notebook
- Graph API: `POST /me/onenote/notebooks/{id}/sections`
- Section name: `{Client} - {Product}`

### Company Overview
- Web search for company basics
- Generate `company-overview.md` with corp-os-meta validated frontmatter
- Fields: industry, HQ, revenue, employees, key products, recent news

### Excel Enhancement
- Read project_codes.xlsx via openpyxl
- Find row by client name, add folder link
- Or: create new row if --create-row flag

---

## Phase 3: Task Automation

### Planner / To Do Integration
- Graph API: create tasks from a configurable checklist template
- Template in YAML:
  ```yaml
  onboarding_tasks:
    - "Review briefing book"
    - "Prep discovery deck"  
    - "Schedule internal alignment call"
    - "Research client company"
    - "Identify key stakeholders"
  ```
- Assign to self, set due dates relative to first meeting date

---

## Phase 4: corp-by-os Integration

### Voice/Chat Interface
- User talks to corp-by-os: "New opportunity: Lenzing, IBP"
- corp-by-os parses intent → calls `com new "Lenzing" --product IBP`
- corp-by-os can chain: create opportunity → scan briefing book → extract → brief

---

## Project Structure

```
corp-opportunity-manager/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── src/
│   └── corp_opportunity_manager/
│       ├── __init__.py
│       ├── cli.py              # Click CLI, entry point "com"
│       ├── chat.py             # Rich terminal chat loop + intent router
│       ├── models.py           # OpportunityConfig, ProjectInfo, IntentResult
│       ├── config.py           # YAML config loader
│       ├── folder_manager.py   # Create folders, copy templates
│       ├── folder_standards.py # Structure audit, subfolder creation, naming
│       ├── excel_manager.py    # Read/update Project_Codes.xlsm
│       ├── llm_client.py       # Gemini Flash intent parsing
│       └── templates.py        # Template naming conventions
│
├── config/
│   └── default.yaml            # Paths, templates, naming, folder standards
│
├── tests/
│   ├── conftest.py
│   ├── test_chat.py
│   ├── test_excel_manager.py
│   ├── test_folder_manager.py
│   ├── test_folder_standards.py
│   ├── test_llm_client.py
│   └── test_templates.py
│
└── tasks/
    ├── todo.md
    └── lessons.md
```

### pyproject.toml
```toml
[project]
name = "corp-opportunity-manager"
version = "0.1.0"
description = "Opportunity lifecycle management for pre-sales workflows"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pyyaml>=6.0",
    "openpyxl>=3.1",
    "python-dotenv>=1.0",
    "corp-os-meta",
]

[project.optional-dependencies]
graph = ["msal>=1.24", "httpx>=0.25"]
dev = ["pytest>=7.0", "pytest-cov", "ruff"]

[project.scripts]
com = "corp_opportunity_manager.cli:cli"
```

### .env.example
```bash
PROJECTS_ROOT=C:\Users\1028120\OneDrive - Blue Yonder\MyWork\10_Projects
ARCHIVE_ROOT=C:\Users\1028120\OneDrive - Blue Yonder\MyWork\80_Archive
TEMPLATES_ROOT=C:\Users\1028120\OneDrive - Blue Yonder\MyWork\30_Templates
PROJECT_CODES_EXCEL=C:\Users\1028120\OneDrive - Blue Yonder\MyWork\90_System\project_codes.xlsx

# Microsoft Graph (Phase 2+)
# GRAPH_CLIENT_ID=
# GRAPH_TENANT_ID=
# ONENOTE_NOTEBOOK_ID=
```

### config/default.yaml
```yaml
naming:
  folder_pattern: "{client}_{product}"
  pptx_pattern: "{client}_{date}_{topic}.pptx"
  date_format: "%Y-%m-%d"

templates:
  discovery_deck: "BY_Discovery_Template.pptx"
  # Add more templates as needed

folder_structure:
  # Subfolders created automatically (empty for now — files land in root)
  # _knowledge/ and _extracted/ are created by corp-project-extractor when it runs
  create_dirs: []

stages:
  - discovery
  - qualification  
  - rfp
  - proposal
  - negotiation
  - won
  - lost
  - archived

products:
  # Normalized product names (from corp-os-meta taxonomy)
  - Planning
  - WMS
  - TMS
  - CatMan
  - Network
  - Platform
```

---

## CLI Commands (Phase 1)

```powershell
# Create new opportunity
com new "Lenzing" --product Planning --contact "Jan Kowalski (VP Supply Chain)"

# Create with more detail
com new "Lenzing" --product Planning --contact "Jan Kowalski" --stage rfp --template discovery

# List active opportunities (reads from project_codes.xlsx)
com list

# Show opportunity details
com show "Lenzing"

# Prepare a presentation
com prep-deck "Lenzing" --topic "Technical Deep Dive" --date 2026-03-15

# Archive opportunity
com archive "Lenzing" --reason lost --notes "Lost to o9 on pricing"
```

### Rich Output for `com new`
```
╭─── New Opportunity: Lenzing ──────────────────────────╮
│                                                        │
│  📁 Folder: MyWork/10_Projects/Lenzing_Planning/       │
│  📄 Deck:   Lenzing_2026-03-05_Discovery.pptx          │
│  📋 Info:   _knowledge/project-info.yaml                │
│  📝 Notes:  _knowledge/notes.md                         │
│                                                        │
│  Client:    Lenzing AG                                  │
│  Product:   Planning (IBP/SIOP)                         │
│  Contact:   Jan Kowalski (VP Supply Chain)              │
│  Stage:     discovery                                   │
│  Created:   2026-03-05                                  │
│                                                        │
│  Next steps:                                            │
│  → Add Teams channel link to project folder             │
│  → Review briefing book when received                   │
│  → Update project_codes.xlsx with folder link           │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

## Implementation Checklist

### Phase 0: Project Setup (DONE — v0.1.0)
- [x] Create repo, git init
- [x] pyproject.toml, .env.example, .gitignore
- [x] python -m venv .venv, pip install -e ".[dev]"
- [x] CLAUDE.md, tasks/todo.md, tasks/lessons.md
- [x] config/default.yaml
- [x] Initial commit, merge to main

### Phase 1: MVP (DONE — v0.1.0)
- [x] models.py — OpportunityConfig, ProjectInfo, CreationResult
- [x] config.py — load YAML + .env
- [x] folder_manager.py — create folder + copy template + rename
- [x] templates.py — naming convention logic
- [x] excel_manager.py — read Project_Codes.xlsm, find/update row, locked-file fallback
- [x] cli.py — `com new`, `com list`, `com show`, `com prep-deck`
- [x] test_folder_manager.py, test_excel_manager.py, test_templates.py (20/20 passing)
- [x] Tested on real MyWork folder (OneDrive paths, real Excel, real deck template)
- [x] Merged to main, tagged v0.1.0

### Phase 2: Chat Agent + Folder Standards (IN PROGRESS — feature/chat-agent)
- [x] Branch: feature/chat-agent
- [x] models.py — add IntentResult, StructureIssue
- [x] llm_client.py — Gemini Flash (google-genai SDK), structured JSON intent parsing
- [x] folder_standards.py — structure audit, subfolder creation (RFP/Meetings/Implementation), naming
- [x] chat.py — Rich terminal loop + intent router (8 intents)
- [x] cli.py — add `com chat` command
- [x] config updates (default.yaml folder_standards + llm sections, .env.example)
- [x] test_llm_client.py, test_folder_standards.py, test_chat.py (61/61 passing)
- [ ] Live test `com chat` with real Gemini API key
- [ ] Commit, merge to main, tag v0.2.0
- [ ] README.md

### Phase 3: Microsoft Graph Integration (FUTURE)
- [ ] graph_client.py — MSAL auth, OneNote section creation
- [ ] Company overview (web search → markdown)
- [ ] Planner/To Do task creation from YAML templates
- [ ] Merge, tag v0.3.0

---

## Key Design Decisions

1. **Excel stays manual trigger** — user adds row first, agent reads it. No auto-creating rows without explicit user action.
2. **corp-os-meta integration** — project-info.yaml validates against NoteFrontmatter schema.
3. **No hardcoded paths** — everything in .env + config/default.yaml.
4. **Templates are files, not code** — PPT templates live in OneDrive, agent just copies + renames.
5. **OneNote is optional** — config flag, default off until we evaluate Obsidian vs OneNote for project notes.
6. **Graph API is Phase 2** — MVP works without any API keys, just local file operations.
7. **AI-powered naming/classification comes later** — MVP uses explicit CLI args, future versions parse natural language via corp-by-os.
