# Contributing to Corporate OS

## Branch Naming

```
feat/short-description
fix/short-description
refactor/short-description
chore/short-description
docs/short-description
```

## Commit Style

Conventional commits. Format: `type: short imperative sentence`

```
feat: add batch extraction resume support
fix: handle missing vault_root in retrieve engine
refactor: extract inbox business logic from UI loop
chore: update dev dependencies
docs: add ADR-26 Tach adoption decision
test: add coverage for overnight state transitions
ci: add Tach GitHub Actions workflow
```

Never commit to main directly. Open a PR. Squash or merge as appropriate.

## Development Flow

Install (once):
```
pip install -e ".[dev,dedup,graph]"
pre-commit install
```

Before each PR:
```
pytest -x --tb=short
pre-commit run --all-files
tach check
```

Or use the convenience script:
```
./scripts/dev-check.ps1
```

## Import Boundary Rules (Tach)

The repo enforces a 4-layer import architecture via `tach check` in pre-commit and CI.

```
interface > orchestration > core > foundation
```

A module at layer N may only import from layers N and below. Never upward.
Layer assignments are defined in `tach.toml`. See `docs/decisions/ADR-26-tach-adoption.md`.

### Adding a new import between modules

If your code adds an import from module A to module B that did not exist before:

1. Run `tach sync --add` manually:
   ```
   tach sync --add
   ```

2. Inspect the diff to `tach.toml`:
   ```
   git diff tach.toml
   ```
   Does this new dependency make architectural sense?
   Does it introduce a layer violation (e.g., core importing orchestration)?

3. Commit `tach.toml` alongside your code change in the SAME commit:
   ```
   git add src/corp/your_module.py tach.toml
   git commit -m "feat: ..."
   ```
   The dependency declaration and the code change belong together.
   Never sync as a separate commit — the diff IS the design review.

`tach sync` is NOT an auto-fix. It is a deliberate declaration of intent.
Do not run it to make a failing check pass without reviewing what changed.

### Resolving a Tach boundary violation

If `tach check` fails for your changes, options in order of preference:

1. **Fix the import** — restructure your code to respect layer rules.
   If module A (core) needs something from module B (orchestration), consider
   whether B should actually be in core, or whether A should move up.

2. **Refactor** — expose the needed functionality via a lower-layer module.
   Example: extract a protocol or data-only helper into core that orchestration implements.

3. **Reclassify** — if the layer assignment in `tach.toml` is simply wrong
   (the module has no real interface-level deps), update the layer and document why.

4. **Document as a known violation** — only if the violation is a pre-existing
   architectural debt being tracked in `docs/audits/`. Never add `# tach-ignore`
   silently; always document the reason.

### Known baseline violations (Phase 1)

The six Phase 1 baseline violations were resolved in Phase 2 — `tach check` now passes with **zero violations** (verified 2026-05-27). Original baseline tracked in `docs/audits/2026-04-15-tach-baseline-violations.md`.

Do not add new violations without architectural justification.

## Architecture Reference

`ARCHITECTURE.md` — module map, layer definitions, design patterns
`docs/decisions/` — all ADRs (30 decisions)
`tach.toml` — authoritative layer assignments
