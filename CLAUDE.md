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
  schema/          taxonomy, models, schema.yaml
  extractor/       CKE — knowledge extraction engine
  ingest/          ingest pipeline (sole vault writer)
  retrieve/        retrieval engine
  cli/             CLI modules
  project/         CPE — project extractor
  rfp/             RFP agent
  opportunity/     COM — opportunity manager
```

### CLIs (2,404 tests)

| CLI | Entry point | Module |
|-----|-------------|--------|
| `corp` | `corp.cli:cli` | ingest, retrieve, cli |
| `corp-meta` | `corp.schema.cli:main` | schema |
| `cke` | `corp.extractor.scripts.run:cli` | extractor |
| `cpe` | `corp.project.cli:cli` | project |
| `com` | `corp.opportunity.cli:cli` | opportunity |

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

## Learned Rules (project-specific, graduated from corrections)
- Never run `pip install` from `_archived_*` repos — overwrites monorepo CLI entry points. Only install from corp-monorepo root.
  verify: Grep("pip install", path="corp-monorepo/") → confirm no install instructions point to archived repos
- git subtree branches must NEVER be rebased — always merge. Rebase causes duplicate commits and lost history.
  verify: manual (process rule — check before any rebase on monorepo branches)
- CKE output must be staged in `scope/client/package/` hierarchy BEFORE running `corp ingest-extractions`. Flat dirs → 0 notes ingested.
  verify: Grep("ingest-extractions", path="corp-monorepo/") → check any docs/scripts for flat-dir usage
- status.json concurrent reads must use try/except with 2-3 retries — CKE writes while polling reads cause JSONDecodeError.
  verify: Grep("json.loads", path="corp-monorepo/src/corp/") → confirm retry wrapper exists

## Session Protocol
1. **Read `VISION.md`** (repo root) — understand the project's purpose and scope before any work.
2. Read last 5 entries from JOURNAL.md before starting work
3. After implementation, self-review: focus on error handling, edge cases, gotchas
4. Before merging, run: ./scripts/dev-check.ps1
5. Append session summary to JOURNAL.md before ending. Per-entry shape (ADR-49, cutover 2026-05-18):
   `### YYYY-MM-DD — <topic>` then `- Did:` / `- Result:` / `- Changes:` / `- Abandoned:` / `- Next:`.
   `Changes:` is the change record — there is no CHANGELOG anymore. Append-only; never edit prior entries.

## Session Handoff

Handoffs for this repo are generated in `.dev-knowledge` per
ADR-42 / `HANDOFF_PROCESS.md`, NOT in this repo (ADR-36 read-only
contract). Bundles live at
`.dev-knowledge/docs/handoffs/{YYYY-MM-DD}-corp-monorepo-{type}/`
(flat 11-file folder; type defaults to `session-sync`).

Trigger: in Claude Code at `.dev-knowledge`, say
"Make handoff for corp-monorepo" (Stage 1) → paste the OLD browser
chat response into `stage2-response.md` → say "Complete handoff for
corp-monorepo" (Stage 3).

See `.dev-knowledge/protocols/HANDOFF_PROCESS.md` for the operational
spec and `.dev-knowledge/docs/decisions/ADR-42-handoff-format-v3.md`
for authority.

## Prompt Decision Rule
- 1 file, 1 module → conversational (just talk to Claude Code)
- 2-3 files, 1 module → conversational with context
- 3+ files, 2+ modules → formal .md prompt
- Architecture decision → AI Council debate
