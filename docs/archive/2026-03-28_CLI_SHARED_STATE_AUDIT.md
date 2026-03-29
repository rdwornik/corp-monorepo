# CLI Shared State Audit — Phase 0 / Step 4
**Date:** 2026-03-28
**Scope:** `packages/corp-by-os/src/corp_by_os/cli.py`
**Purpose:** Inventory of module-level state that must be extracted to `cli/_common.py` before the CLI split (Phase 1 / ADR-23 Q2)

---

## Module-level constants

| Name | Line | Value | Notes |
|------|------|-------|-------|
| `CHECK` | 63 | `"Y"` | ASCII-safe checkmark for Windows legacy console |
| `DASH` | 64 | `"-"` | ASCII-safe dash separator |
| `EXTRACT_EXTENSIONS` | 1205 | set of file extensions | Used by `extract` and `ingest` commands |
| `OVERNIGHT_SCOPES` | 1331 | dict mapping scope → folder list | Keys: `all-non-project`, `source-library`, `rfp`, `templates`, `full-reshape` |

`OVERNIGHT_SCOPES` default (`all-non-project`) maps to `["30_Templates", "50_RFP", "60_Source_Library"]` — this is the 3-folder set that drives the overnight CKE call volume measurement (3 calls/run).

## Module-level objects

| Name | Line | Type | Notes |
|------|------|------|-------|
| `console` | 66 | `rich.console.Console` | Single shared Rich console — all commands use this |
| `logger` | 67 | `logging.Logger` | `logging.getLogger(__name__)` |

## Root CLI group

| Name | Lines | Notes |
|------|-------|-------|
| `cli` | 70–82 | `@click.group()`, sets verbose logging level, injects `PipelineConfig.production()` into `ctx.obj["config"]` |

The `ctx.obj["config"]` injection is the key shared state mechanism: every command downstream calls `ctx.obj["config"]` to get the `PipelineConfig`. This must remain in the root group or be passed via `@click.pass_context` in `cli/_common.py`.

## Common imports (candidates for `cli/_common.py`)

```python
# stdlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# third-party
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# internal
from corp_by_os.config import get_config
from corp_by_os.project_resolver import resolve_project
from corp_by_os.vault_io import list_projects, read_project_info, validate_vault
from corp_os_meta.pipeline_config import PipelineConfig
```

Individual domain modules will import only the subset they need. `get_config`, `PipelineConfig`, `Console`, `click`, `logging`, `Path` will be needed by most modules.

## Private helper functions

| Function | Line | Used by | Notes |
|----------|------|---------|-------|
| `_show_workflow_list` | 582 | `run` command | Lists available workflows |
| `_show_workflow_panel` | 601 | `run` command | Rich panel for single workflow |
| `_run_folder_extraction` | 1400 | `overnight`, `extract` | Core extraction loop |
| `_update_folder_file_statuses` | 1586 | `overnight` | Updates file status after extraction |
| `_run_full_reshape` | 1615 | `overnight` | Full reshape pipeline |
| `_run_freshness_phase` | 1760 | `overnight` | Freshness check phase |
| `_write_reshape_plan` | 1822 | `overnight` | Writes reshape plan to disk |
| `_execute_reshape_actions` | 1889 | `overnight` | Executes approved reshape actions |
| `_count_signatures` | 2690 | `dedup-report` | MinHash signature count |

**Grouping:** `_run_folder_extraction`, `_update_folder_file_statuses`, `_run_full_reshape`, `_run_freshness_phase`, `_write_reshape_plan`, `_execute_reshape_actions` all belong in `cli/overnight.py`. `_show_workflow_list`, `_show_workflow_panel` belong in `cli/run.py` (or inline). `_count_signatures` belongs in `cli/analytics.py`.

## Click command group hierarchy

| Group var | CLI name | Line | Subcommands |
|-----------|----------|------|-------------|
| `project` | `project` | 84 | list, show, open |
| `vault` | `vault` | 196 | validate |
| `task_group` | `task` | 625 | add, list, done |
| `index_group` | `index` | 745 | rebuild, stats |
| `analytics_group` | `analytics` | 882 | report, products, timeline, clients, overlap, compare, recent |
| `template_group` | `template` | 1119 | list, scan, select |
| `rfp_group` | `rfp` | 3224 | answer |

## Direct `@cli.command()` entries (25 commands)

doctor, trust-status, routing-review, routing-mark-reviewed, run, tasks, query, extract, overnight, cleanup-scan, apply-moves, cleanup, audit, ingest, ingest-inbox, dedup-report, files-stats, naming-stats, finalize, classify, retrieve, prep, freshness, ingest-extractions, folder-review, test-pipeline, chat

**Total: 71 CLI entry points** (7 groups + 3+1+3+2+7+3+1 subcommands + 25 direct commands)

## Proposed `cli/_common.py` contents

```python
# cli/_common.py — shared state for all CLI domain modules
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from corp_by_os.config import get_config
from corp_by_os.project_resolver import resolve_project
from corp_by_os.vault_io import list_projects, read_project_info, validate_vault
from corp_os_meta.pipeline_config import PipelineConfig

# ASCII-safe markers for Windows legacy console
CHECK = "Y"
DASH = "-"

console = Console()
logger = logging.getLogger(__name__)

EXTRACT_EXTENSIONS = ...  # moved from cli.py:1205
OVERNIGHT_SCOPES = ...    # moved from cli.py:1331
```

The root `cli` group (lines 70-82) should live in a thin `cli/__init__.py` or `cli/root.py` that imports all domain modules and registers their groups/commands.

## Phase 1 split plan

| File | Commands |
|------|----------|
| `cli/_common.py` | shared state, constants, console, logger |
| `cli/project.py` | project group + list, show, open |
| `cli/vault.py` | vault group + validate |
| `cli/task.py` | task group + add, list, done; tasks shortcut |
| `cli/index.py` | index group + rebuild, stats |
| `cli/analytics.py` | analytics group + 7 subcommands; dedup-report, files-stats, naming-stats |
| `cli/template.py` | template group + list, scan, select |
| `cli/rfp.py` | rfp group + answer; retrieve, prep |
| `cli/ingest.py` | ingest, ingest-inbox, ingest-extractions, extract, finalize, classify |
| `cli/overnight.py` | overnight + 6 private helpers; OVERNIGHT_SCOPES |
| `cli/workflow.py` | run command + _show_workflow_list, _show_workflow_panel |
| `cli/query.py` | query, trust-status, routing-review, routing-mark-reviewed, folder-review |
| `cli/maintenance.py` | doctor, cleanup, cleanup-scan, apply-moves, audit, freshness |
| `cli/misc.py` | chat, test-pipeline |
| `cli/root.py` | root cli group, registers all groups |
