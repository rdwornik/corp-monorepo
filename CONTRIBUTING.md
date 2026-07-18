---
last_reviewed: 2026-07-13
reconciled_with: handoff-process@v5
status: active
owner: Rob
---

# Contributing to Corporate OS

<!-- scope: meta -->

Sole contributor: Rob. Audience: future Rob + AI agents (Claude Code, Codex) reading for orientation.

<!-- CANONICAL: Branch naming (sync verbatim from hub) -->
## Branch naming

<!-- scope: meta -->

```
feat/short-description
fix/short-description
docs/short-description
chore/short-description
```

Default branch: `main` (ADR-30).

Branch prefixes are `feat/ fix/ docs/ chore/` (these four only). Commit **types** follow Conventional Commits and additionally include `refactor` and `test` — commit types are **not** branch prefixes. Never commit directly to `main`: branch → `--no-ff` merge.

<!-- CANONICAL: Commit style (sync verbatim from hub) -->
## Commit style

<!-- scope: meta -->

Conventional Commits. Format: `type(scope): short imperative sentence`

```
feat(scope): add batch extraction resume support
fix(retrieve): handle missing vault_root in retrieve engine
refactor(inbox): extract inbox business logic from UI loop
chore: update dev dependencies
docs(adr): add ADR-26 Tach adoption decision
test(overnight): add coverage for state transitions
```

Scopes are optional but use the file/folder slug when it clarifies. See recent commits in `git log` for live examples.

<!-- CANONICAL: Backlog-id references — closure grammar + the D2 cross-repo rule sync verbatim from hub; the enforcement teeth are stated at pointer level (the concrete gate script is in the LOCAL comment below, not the contract prose). -->
### Backlog-id references (forward-only index)

<!-- scope: meta -->

Commit messages **extend** Conventional Commits (they do not replace them) with an optional backlog/ADR reference, so a closure is locatable by id (ADR-65: git is the technical record, forward-indexed via this convention):

```
fix(audit): widen check-8 stamp regex [#42]      # touches backlog item 42
feat(scripts): add backlog validator, closes [#57]   # closing commit for item 57
docs(adr): ADR-65 done-item disposition           # ADR number is itself the index
```

- **Touching** a backlog item: append `[#<id>]` to the summary.
- **Closing** a backlog item: add `closes [#<id>]` (summary or body) — pairs with the item leaving `BACKLOG.md` in the same or a following commit.
- **`closes` vs `advances`:** use `closes [#<id>]` on the commit that **finishes** an item — not `advances [#<id>]`. `advances` records intermediate progress only: the item stays open in `BACKLOG.md` **and** invisible to the closure detector (which keys on `closes`), so it silently accumulates as done-but-open and must be closed manually (this is what forced the manual close of #73). A multi-commit arc may use `advances` along the way, but the commit that completes the work must use `closes`.
- `<id>` is the task's stable inline `[#id]` marker (monotonic, never reused; corp uses the ADR-66 story-map inline id, not a YAML `id:` field).
- **Cross-repo references are repo-qualified.** A bare `[#<id>]` denotes a task in THIS repo only. To reference another fleet repo's backlog item, qualify it: `hub#<id>`, `ai#<id>`, `corp#<id>`. (Operator ruling, content-parity inventory D2 / #331 — qualified-refs chosen over a global allocator. Automated enforcement lands with #328; this is the convention it will check.)

This indexes commits **going forward only.** Git history is immutable — **historical commits are never rewritten** (ADR-65). Pre-convention closures are located via the SHAs already embedded in retired entries (preserved in the one-time migration JOURNAL map).

**Enforced by the carried `commit-msg` gate** (where installed): a commit that removes a `- [#id]` task from `BACKLOG.md` without referencing that id (`[#id]` or `closes [#id]`) is rejected. A reworded task (id present before and after) does not trigger. Install the commit-msg stage once per machine:

```
pre-commit install --hook-type commit-msg
```

<!-- LOCAL: in this repo the commit-msg gate is `backlog-id-on-close`, sourced from the pinned `.dev-knowledge` pre-commit repo (v1.3.1) — not a local script. -->

**"What's been implemented" query.** Because done tasks **leave** `BACKLOG.md` (ADR-65) and git is the implementation record, the list of completed tasks with their implementing commits is:

```
git log --grep 'closes \[#'
```

This is the detailed implementation history the active file deliberately does not carry.

## Pre-commit setup

<!-- scope: meta -->

Install once per machine:

```
pip install -e ".[dev,dedup,graph]"
pre-commit install
```

Run manually at any time:

```
pre-commit run --all-files
```

## Validators

<!-- scope: meta -->

<!-- LOCAL: this roster is set-matched to corp's live `.pre-commit-config.yaml`. Hub-only
     hooks (roster-freshness, audit-index-freshness, validate-hermetization, …) do NOT ship
     to corp; corp-local hooks (validate-audit-casing, validate-backlog twin) are carried.
     Keep this table in sync with `.pre-commit-config.yaml` and CLAUDE.md §9. -->

| Hook | Stage | What it does |
|------|-------|--------------|
| `ruff` | pre-commit | Lint gate (check-only; `pyproject.toml [tool.ruff.lint]` E/F/I — violations block, not auto-fixed) |
| `tach-check` | pre-commit | Import-layer boundaries (`interface > orchestration > core > foundation`) |
| `normalize-headers` | pre-commit | Normalize dated-log headers (JOURNAL/LESSONS) |
| `floor-hash-verify` | pre-commit | `.claude/CLAUDE-FLOOR.md` matches its sha256 sidecar (ADR-93) |
| `canonical_freshness` | pre-commit | `last_reviewed` A2 gate — a stale-edited canonical doc blocks the commit (ADR-85/81) |
| `validate-audit-casing` | pre-commit | `docs/audits/*.md` lowercase-kebab casing (ADR-101 R4, prospective; enumerated skip-set) |
| `validate-backlog` | pre-commit | `BACKLOG.md` story-map schema (plugin twin, ADR-78; E/S-agnostic floor validator) |
| `backlog-id-on-close` | commit-msg | Require `[#id]` when a `BACKLOG.md` task line is removed (hub-sourced, v1.3.1) |
| `block-ff-push` | pre-push | Refuse a direct-to-main / fast-forward push to `main` (hub-sourced, v1.3.1) |

## ADR process

<!-- scope: meta -->

Decisions that bind future sessions live in `docs/decisions/ADR-NN-topic.md`.

- Numbering: next integer after highest existing ADR
- Filename: `ADR-NN-short-kebab-topic.md`
- Status values: `Accepted | Superseded | Withdrawn`
- Minor prescription drift → amend in-place (add dated `## Amendment YYYY-MM-DD` section)
- Intent change or reversal → new ADR or AI Council reopen

<!-- LOCAL: corp foundational ADRs for style reference — ADR-14 (naming v2), ADR-23
     (monorepo internal architecture), ADR-26 (Tach adoption), ADR-27 (vault writer).
     Full list: `docs/decisions/README.md`. Orientation pointers: `ARCHITECTURE.md` (module
     map, layer definitions, design patterns); `tach.toml` (authoritative layer assignments). -->

## Handoff process

<!-- scope: meta -->

Protocol: the hub methodology protocol `HANDOFF_PROCESS.md` (read at the hub `../.dev-knowledge/protocols/` set; hub-pointer, never copied into a consumer) — **v5**. Handoffs centralize in `../.dev-knowledge/docs/handoffs/` per ADR-36/62 — **this repo carries no `docs/handoffs/`** (ADR-36 read-only contract; a handoff never writes to a target repo). Continuing a prior session: read the most recent corp-monorepo bundle there (start with its `HANDOFF_BOOT.md`), then the last 5 `JOURNAL.md` entries here.

Trigger: in Claude Code at `.dev-knowledge`, say "Make handoff for corp-monorepo".

`BACKLOG.md` (root): cross-session pending items per ADR-41. Universal mandate (ADR-38 amendment A5 — every repo). Review before chartering a new session.

<!-- CANONICAL: Definition of done — pointer level; the concrete Stop-hook script is in the LOCAL comment below (do not hard-code hub-local paths). -->
## Definition of done (session close)

<!-- scope: meta -->

The hub methodology protocol `DEFINITION_OF_DONE.md` (read at the hub `../.dev-knowledge/protocols/` set; hub-pointer, never copied into a consumer) is the single source of truth for what "done" means at session close (ADR-85): a session that produces commits adds a `JOURNAL.md` entry naming ≥1 commit SHA from this arc (**hard-gated**), and should update `BACKLOG.md` with a structural marker (**advisory** in v1). It is enforced **mechanically and deterministically** by the carried session-end Stop-hook (no LLM in the gate) — and the only escape is `/override [reason]`. The other living docs (`ARCHITECTURE`, `VISION`, `LESSONS`, this file) are "update when materially affected", not per-session-gated. Pointer only — the rules live in that file, not here (resident copies drift).

<!-- LOCAL: the concrete Stop-hook script in this repo is `scripts/session_end_backpressure.py`. -->

---

<!-- LOCAL (corp-specific operational appendices — retained past the canonical shell). -->

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

The six Phase 1 baseline violations were resolved in Phase 2 — `tach check` now passes with **zero violations** (verified 2026-05-27). Original baseline tracked in `docs/archive/2026-04-15-tach-baseline-violations.md`.

Do not add new violations without architectural justification.

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
