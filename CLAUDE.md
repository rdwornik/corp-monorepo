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

## Council Decisions: 21 (ADR summaries in `decisions/`, full transcripts in `.ecosystem/council_transcripts/`)
- #14: Naming convention v2 — `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`

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
1. `.ecosystem/MASTER_HANDOFF.md` (living doc, updated after each session)
2. Latest Council debate output (if pending)

`MASTER_HANDOFF.md` replaces per-session handoffs.
Update it at end of every major session:
```
python scripts/update_handoff.py
```

## Prompt Decision Rule
- 1 file, 1 package → conversational (just talk to Claude Code)
- 2-3 files, 1 package → conversational with context
- 3+ files, 2+ packages → formal .md prompt
- Architecture decision → AI Council debate
