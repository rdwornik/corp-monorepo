# Corporate OS Monorepo

## Architecture Rules (non-negotiable)
- corp-by-os is SOLE vault writer
- CKE is PURE extraction engine — no vault writes
- Forward slashes everywhere in databases/paths
- Subprocess boundaries between packages (not Python imports)
- Each package has its own pyproject.toml and tests

## Packages (2,153+ tests)

| Package | CLI | Version | Tests |
|---------|-----|---------|-------|
| corp-os-meta | `corp-meta` | 1.0.0 | 118 |
| corp-knowledge-extractor | `cke` | 0.8.0 | 838 |
| corp-by-os | `corp` | 0.3.0 | 926 |
| corp-project-extractor | `cpe` | 0.1.0 | 45 |
| corp-rfp-agent | scripts | 0.3.0 | 155 |
| corp-opportunity-manager | `com` | 0.2.0 | 62 |
| Integration | — | — | 9 |

## Development
- Feature branches: `feat/`, `fix/`, `refactor/`, `chore/`
- Commit messages: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`, `docs:`
- Run `./scripts/run-all-tests.ps1` before merging
- Check `~/.claude/skills/gotchas/` before modifying any package

## Key Config
- Centralized paths: `config/paths.toml`
- Naming convention: `packages/corp-by-os/config/naming_config.yaml` (19 type codes, 15 client aliases)
- Training data: `scripts/extract_training_data.py` → `tests/fixtures/` in CKE and corp-by-os
- Environment variables override config
- API keys in env vars, NEVER in config files
- GEMINI_API_KEY is the standard (not GOOGLE_API_KEY)

## Council Decisions: 14 (see `.ecosystem/decisions/`)
- #14: Naming convention v2 — `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`

## Safety
- NEVER let cleanup touch "OneDrive - Blue Yonder" paths
- Test after every change
- Git feature branches, never commit to main directly
