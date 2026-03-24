# Lessons — corp_os_meta

## Architecture Decisions
- taxonomy.yaml lives inside the package so it's always co-located with the code
- Taxonomy is cached after first load (per-process singleton)
- Unknown terms are preserved (not dropped) — allows organic growth
- Validation returns a 3-tuple (result, model, issues) for flexibility
- tool_meta dict provides tool-specific namespace without schema changes
