# Corporate OS Monorepo

## Architecture (unified src/corp/ layout)

All 6 former packages consolidated into a single `src/corp/` namespace.
One `pyproject.toml` at repo root. One `pip install -e .`.

### Architecture Rules (non-negotiable)
- corp (ingest/) is SOLE vault writer
- CKE (extractor/) is PURE extraction engine — no vault writes
- Forward slashes everywhere in databases/paths
- API keys in env vars, NEVER in config files
- GEMINI_API_KEY is the standard (not GOOGLE_API_KEY)

### Source Layout

```
src/corp/
  schema/          corp-os-meta (taxonomy, models, schema.yaml)
  extractor/       corp-knowledge-extractor (CKE)
  ingest/          corp-by-os ingest pipeline
  retrieve/        corp-by-os retrieval
  cli/             corp-by-os CLI modules
  project/         corp-project-extractor (CPE)
  rfp/             corp-rfp-agent
  opportunity/     corp-opportunity-manager (COM)
```

### CLIs (2,404 tests)

| CLI | Entry point | Former package |
|-----|-------------|----------------|
| `corp` | `corp.cli:cli` | corp-by-os |
| `corp-meta` | `corp.schema.cli:main` | corp-os-meta |
| `cke` | `corp.extractor.scripts.run:cli` | corp-knowledge-extractor |
| `cpe` | `corp.project.cli:cli` | corp-project-extractor |
| `com` | `corp.opportunity.cli:cli` | corp-opportunity-manager |

## Development
- Feature branches: `feat/`, `fix/`, `refactor/`, `chore/`
- Commit messages: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`, `docs:`
- Run `./scripts/run-all-tests.ps1` before merging
- Check `~/.claude/skills/gotchas/` before modifying any module

## Key Config
- Centralized paths: `config/paths.toml`
- Naming convention: `config/naming_config.yaml` (19 type codes, 15 client aliases)
- Taxonomy: `src/corp/schema/taxonomy.yaml`
- Schema contract: `src/corp/schema/data/schema.yaml`
- Client aliases: `src/corp/extractor/data/client_aliases.yaml`
- Training data: `scripts/extract_training_data.py` → `tests/fixtures/`
- Environment variables override config

## Council Decisions: 24 (ADR summaries in `docs/decisions/`, full transcripts in `docs/decisions/transcripts/`)
- #14: Naming convention v2 — `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`
- #23: Monorepo internal architecture — flatten, centralize, delete dead code

## Safety
- NEVER let cleanup touch "OneDrive - Blue Yonder" paths
- Test after every change
- Git feature branches, never commit to main directly

## Session Protocol
1. Read last 5 entries from JOURNAL.md before starting work
2. After implementation, self-review: focus on error handling, edge cases, gotchas
3. Before merging, run: ./scripts/dev-check.ps1
4. Append session summary to JOURNAL.md before ending

## Session Handoff
When starting a new Claude.ai chat session, paste:
1. `docs/HANDOFF.md` (living doc, updated after each session)
2. Latest Council debate output (if pending)

`docs/HANDOFF.md` replaces per-session handoffs.
Update it at end of every major session:
```
python scripts/update_handoff.py
```

## Prompt Decision Rule
- 1 file, 1 module → conversational (just talk to Claude Code)
- 2-3 files, 1 module → conversational with context
- 3+ files, 2+ modules → formal .md prompt
- Architecture decision → AI Council debate
