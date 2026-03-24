# CLAUDE.md — corp_os_meta

## What this repo does

Shared metadata schema and taxonomy for the corp-by-os agent ecosystem. Defines the frontmatter CONTRACT (Pydantic models) that all extraction tools must follow when producing Obsidian vault notes. Provides taxonomy normalization, validation with quarantine routing, product resolution, and a CLI for vault health management.

## Quick start

```bash
pip install -e C:\Users\1028120\Documents\Scripts\corp-os-meta
pytest tests/ -v
python -c "from corp_os_meta import NoteFrontmatter; print('OK')"
```

## Architecture

```
corp_os_meta/
├── models.py       — Pydantic models: NoteFrontmatter, enums (the contract)
├── normalize.py    — taxonomy loading, alias resolution, term normalization
├── validate.py     — schema validation + quarantine routing
├── products.py     — product key resolution, source tier classification
├── overlays.py     — structured extraction overlay schemas (architecture, security, etc.)
├── utils.py        — parse_llm_json (robust LLM JSON parsing)
├── cli.py          — Click CLI: validate, normalize, report commands
├── taxonomy.yaml   — canonical terms + aliases (topics, products, domains)
└── data/
    ├── products.yaml     — product catalog with display names + variants
    └── source_tiers.yaml — source reliability scoring
```

Entry point: `corp-meta` CLI (defined in pyproject.toml as `corp_os_meta.cli:main`)

Data flow: Extraction tools → normalize_frontmatter() → validate_frontmatter() → vault or _quarantine/

## Dev standards

- Python 3.12+, Windows-first (`py -m`, pathlib)
- `pyproject.toml` as single source of truth (no requirements.txt)
- `ruff` + `pytest` quality gate
- ZERO external dependencies beyond pydantic, pyyaml, click, rich, json-repair
- taxonomy.yaml changes must be backward-compatible (add, never rename without alias)
- New required fields in NoteFrontmatter = schema_version bump
- New optional fields = no version bump needed
- Every function must have tests
- No silent failures — log warnings, raise on errors
- Feature branches, no deletions without asking

## Key commands

```bash
# Validate a single note or entire vault
corp-meta validate path/to/note.md
corp-meta validate path/to/vault/ --recursive --strict

# Normalize taxonomy terms in-place
corp-meta normalize path/to/note.md --in-place

# Report on vault health
corp-meta report path/to/vault/

# Run tests
pytest tests/ -v
```

## Test suite

```bash
pytest tests/ -v    # 87 tests, all passing
```

Coverage: models, normalize, validate, preprocess, products, utils, deep extraction fields, dimension fields.

## Dependencies

- **pydantic** (>=2.0) — schema validation
- **pyyaml** (>=6.0) — taxonomy + config loading
- **click** (>=8.0) — CLI framework
- **rich** (>=13.0) — terminal output formatting
- **json-repair** (>=0.30) — fallback for malformed LLM JSON
- **python-dotenv** (>=1.0) — global .env loading for API keys

## API Keys

Keys loaded globally from `Documents/.secrets/.env` via PowerShell profile AND via `python-dotenv` in `cli.py` (works in all contexts: PS, Claude Code, VS Code).
Do NOT add API keys to local `.env`.
Check: `keys list` | Update: `keys set KEY value` | Reload: `keys reload`

This repo uses: **none** — pure metadata schema/taxonomy library with no external API calls.
Global .env is loaded in `cli.py` with `override=False` so env vars set by the shell take precedence.

## Integration points

This is the dependency root of the ecosystem. Other repos import it; it imports nothing from the ecosystem.

- **corp-by-os**: imports `validate_frontmatter()`, `normalize_frontmatter()` for vault writes
- **corp-knowledge-extractor**: imports Pydantic schemas, taxonomy, overlays for extraction output
- **corp-project-extractor**: consumes validated frontmatter via CKE output (indirect)

Changes to `NoteFrontmatter` or `taxonomy.yaml` affect ALL downstream repos.

## Related repos

- [ECOSYSTEM.md](../ECOSYSTEM.md) — full ecosystem overview
- [corp-by-os](../corp-by-os/) — root orchestrator (primary consumer)
- [corp-knowledge-extractor](../corp-knowledge-extractor/) — extraction engine (primary consumer)
- [corp-project-extractor](../corp-project-extractor/) — project folder classifier

## Known issues

- Code exceeds the <300 line target (999 lines across 8 modules)
- No test coverage for `cli.py` (CLI commands) or `overlays.py` (overlay schemas)
- `.claude/` directory is in `.gitignore` — local settings only
