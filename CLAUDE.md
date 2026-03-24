# Corporate OS Monorepo

## Architecture Rules (non-negotiable)
- corp-by-os is SOLE vault writer
- CKE is PURE extraction engine — no vault writes
- Forward slashes everywhere in databases/paths
- Subprocess boundaries between packages (not Python imports)
- Each package has its own pyproject.toml and tests

## Development
- Feature branches: `feat/`, `fix/`, `refactor/`, `chore/`
- Commit messages: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`, `docs:`
- Run `./scripts/run-all-tests.ps1` before merging
- Check `~/.claude/skills/gotchas/` before modifying any package

## Path Configuration
- Central config: `config/paths.toml`
- Environment variables override config
- API keys in env vars, NEVER in config files
- GEMINI_API_KEY is the standard (not GOOGLE_API_KEY)

## Safety
- NEVER let cleanup touch "OneDrive - Blue Yonder" paths
- Test after every change
- Git feature branches, never commit to main directly
