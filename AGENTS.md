# AGENTS.md — Codex Code Review Configuration

> **Read first:** `VISION.md` (repo root) — understand the project's purpose and scope before reviewing.

> This file is read automatically by Codex CLI (OpenAI).
> Codex is a **read-only code reviewer** in this repo. It does not build, fix, or modify.

## Role: Review Only

**Codex MUST NOT:**
- Modify any file
- Create branches or commits
- Run any command that writes, deletes, or modifies state. Read-only commands (git diff, git log, cat, type) are explicitly allowed.
- Suggest applying fixes directly — only report findings

**Codex MUST:**
- Read code and report issues
- Reference specific file:line locations
- Prioritize findings (critical / high / medium / low)
- Be concise — no lengthy explanations, just finding + why + suggested fix direction

## Architecture Context

### Repo: corp-monorepo
Single unified Python package at `src/corp/` with 5 CLI entry points: `corp`, `corp-meta`, `cke`, `cpe`, `com`.

### Module Structure
```
src/corp/
  schema/        foundation — taxonomy, models, validation, folder constants
  extractor/     core — CKE knowledge extraction engine (Gemini/Claude)
  extraction/    foundation — extraction orchestration, manifests, vault writing
  ingest/        orchestration — file routing pipeline (classify → rename → route → extract)
  ops/           core — SQLite facade + 5 per-entity repositories
  actions/       orchestration — 12 domain-split workflow action modules
  retrieve/      core — FTS5 retrieval engine
  cleanup/       core — MyWork file hygiene
  overnight/     core — batch extraction pipeline
  project/       core — project scanning/extraction
  opportunity/   core — opportunity lifecycle
  rfp/           core — RFP answering pipeline
  cli/           interface — Click command groups
```

### Dependency Rule (ENFORCED BY TACH)
Dependencies flow DOWN layers only. A module in a higher layer may only import from layers below it.

Layers (top → bottom):
- interface — entry points: cli/, chat, sandbox, test_pipeline
- orchestration — workflow coordination: actions/, workflow_engine, ingest/, query_engine, index_builder, task/template managers, built_in_actions
- core — domain services: extractor, ops, retrieve, intent_router, llm_router, project, opportunity, rfp, overnight, vault_io, config, audit, integrity, freshness_scanner, cleanup, project_resolver
- foundation — shared types and base config: schema/ (utility), models, routing_types (utility), extraction/

Tach enforces this at pre-commit and CI. See `tach.toml` for canonical module-to-layer assignments.
Violation example: if `schema/` imports from `ingest/` → Tach blocks the commit.

### Key Invariants
1. `ingest/` is SOLE writer for `02_sources/` `.md` notes — CKE produces JSON, ingest writes .md. Narrowed by ADR-27: `actions/*` may write directly to whitelisted non-source zones; all other writes route through `vault_io.write_note()`.
2. `extractor/` is PURE extraction — no vault writes, no database writes
3. Forward slashes in all database paths and stored references
4. API keys only via env vars (never in config files or code)
5. OneDrive paths are READ-ONLY — never modify, move, or delete
6. Record-before-move — ops.db logged BEFORE filesystem operations
7. WAL mode on all SQLite databases

### Databases (3)
- `ops.db` — file registry, assets, packages, ingest events, routing feedback (8 tables)
- `index.db` — FTS5 vault index, notes, facts, projects (6 tables + triggers)
- `overnight_state.db` — batch extraction runs, file status, batches (3 tables)

### Config
- `PipelineConfig` (frozen dataclass) — primary structured config
- `AppConfig` (frozen, lru_cached) — vault/mywork paths + agents
- API keys: `~/Documents/.secrets/.env` → env vars only
- YAML configs in `config/` — naming, workflows, content registry, extractor settings

## Review Checklist

### Review Modes

**Diff review (default):** When reviewing a branch diff, check Critical + High only. Skip Medium and Low — they add noise to focused reviews.

**Full audit (explicit):** When asked for a full repo scan, check all severity levels. Use this monthly or after major refactors.

Codex assumes diff review mode unless the prompt explicitly says "full audit."

When reviewing code changes, check ALL of the following:

### Critical (block merge)
> CRITICAL = blocks merge. Runtime bugs, data loss risk, security issues, architectural invariant violations.
- [ ] **Import direction** — enforced by `tach check` in pre-commit and CI (see `tach.toml`). Codex skips this check.
- [ ] **OneDrive safety** — no code modifies/deletes files under `OneDrive - Blue Yonder`
- [ ] **API keys** — no secrets hardcoded in code or config files
- [ ] **SQL injection** — all queries use parameterized `?` placeholders, never f-strings
- [ ] **Silent swallow** — no `except Exception: pass` without logging
- [ ] **Vault writer invariant** — only `ingest/` and `extraction/vault_writer.py` write to vault

### High (should fix before merge)
> HIGH = issues that change runtime behavior or silently degrade data. Convention violations belong in MEDIUM or LOW.
- [ ] **Missing error handling** — file I/O, API calls, subprocess without try/except
- [ ] **Hardcoded paths** — Windows paths, usernames, absolute paths in code (use PipelineConfig)
- [ ] **Broad exceptions** — `except Exception:` where specific types are known
- [ ] **Race conditions** — concurrent file access, SQLite from multiple processes
- [ ] **Test coverage** — new public functions without corresponding test

### Medium (note for follow-up)
- [ ] **Type hints missing** — public functions without return type annotations
- [ ] **Stale references** — old package names (corp_by_os, corp_os_meta, corp_knowledge_extractor) — no runtime impact
- [ ] **print() in library** — should be `logging` in non-CLI modules, `console.print()` in CLI only
- [ ] **os.path.join** — should be `pathlib.Path` for filesystem operations
- [ ] **Magic numbers** — unnamed constants (use `folder_names.py` or config)
- [ ] **Function length** — functions >100 lines are candidates for extraction
- [ ] **Parameter count** — functions with >6 parameters need a dataclass

### Low (cosmetic)
- [ ] **Docstrings** — public classes/functions without module-level or function docstring
- [ ] **Naming** — inconsistent naming patterns within a module
- [ ] **Import order** — ruff handles this, but flag if obviously wrong

## Output Format

Report findings as:

```
## [CRITICAL/HIGH/MEDIUM/LOW] filename:line — short description

**What:** One sentence describing the issue.
**Why:** One sentence explaining the risk.
**Fix direction:** One sentence suggesting approach (not implementation).
```

Group by severity. If no issues found at a severity level, omit the section.
