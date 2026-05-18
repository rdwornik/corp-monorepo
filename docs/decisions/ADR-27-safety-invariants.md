# ADR-27: Safety Invariants — OneDrive Guard Centralization and Vault Writer Narrowing

**Date:** 2026-04-22
**Status:** Accepted
**Decider:** AI Council 2026-04-22 (Decision 1); Rob with Claude review (Decision 2)
**Panelists (Decision 1):** claude-opus-4-7, gemini-3.1-pro-preview, grok-4.20, gpt-5.4
**Synthesizer (Decision 1):** claude-sonnet (non-participant)
**Debate transcript:** `docs/decisions/transcripts/DECISION_27_onedrive_centralization.md`
**Related:** ADR-23 (sole-writer invariant origin), ADR-26 (Tach 4-layer model), hotfix `onedrive-safety-p1` (merged 2026-04-21), INCIDENT 2026-03-14

## Context

Two safety invariants in the `src/corp/` namespace reached the point where either ambiguity or discipline-only enforcement is no longer acceptable.

**OneDrive exclusion** was already documented in ARCHITECTURE.md ("OneDrive exclusion — cleanup/audit NEVER touch 'OneDrive - Blue Yonder' paths"). INCIDENT 2026-03-14 showed that callsite discipline fails in practice: a cleanup path deleted files under the synced tree because a guard was simply omitted at one write site. Hotfix `hotfix/onedrive-safety-p1` (merged 2026-04-21) added fail-closed guards at four mutation sites (`cleanup/disk.py`, `cleanup/executor.py`, `actions/_helpers.py`, `project/renderer.py`) with the resolve-before-check pattern mandated by Codex review. Centralization was explicitly deferred to this ADR; `renderer.py` still raises `ValueError` instead of the shared `OneDriveSafetyError`, and `actions/deck_actions.py:104` remains a known unguarded write-intent caller.

**Vault single-writer invariant** from ADR-23 stated "corp (ingest/) is SOLE vault writer." Codex review 2026-04-21 flagged `actions/vault_actions.py:36` as a violation. Verification broadened the scope: eight write sites across five modules in `src/corp/actions/` (`vault_actions.py`, `archive_actions.py`, `brief_actions.py`, `analytics_actions.py`, `monitoring_actions.py`) write directly to the vault, predating the ADR-23 consolidation. The invariant had never been enforced mechanically — it described an intent, not a rule.

Both decisions are documented together because they are foundation-layer safety invariants, both land in `src/corp/safety/` (per ADR-26 Tach taxonomy), and both share the same enforcement pattern: a pytest-based CI check that walks the AST of `src/corp/` and fails on unapproved write primitives. A future maintainer asking "how does this repo prevent data-loss and integrity bugs?" should find one document, not two.

Implementation is out of scope for this ADR and lands in four separate PRs (three for OneDrive, one for vault writer).

---

## Decision 1 — OneDrive safety guard centralization

### Context

Four write sites now use the resolve-then-substring pattern inline. A fifth (`deck_actions.py:104`) is a known gap. Adding a sixth write site anywhere in `src/corp/` creates a new hole whenever a contributor forgets the guard — the exact failure mode that caused INCIDENT 2026-03-14. Duplication is the visible cost; the underlying risk is omission, which no amount of documentation, style review, or runtime testing reliably catches before a production delete.

### Options considered

- **Option A — Centralized helper module only.** Move the four inline guards into `corp/safety/onedrive.py`. Rejected: eliminates duplication but still depends on callsite discipline; does not prevent omission at a new write site.
- **Option B — Decorator `@onedrive_safe(param="path")`.** Wrap write-site functions. Rejected: parameter-name string is fragile (renames silently break protection); decorator obscures stack traces during debugging; adds no enforcement the AST scanner does not already provide.
- **Option C — Centralized module plus AST-based CI enforcement.** Shared `guard_path` helper plus a pytest test that walks `src/corp/` looking for dangerous write primitives inside functions that neither call `guard_path` nor carry an explicit `@onedrive_write_exempt(reason=...)` marker. **Chosen (3-of-4 Council consensus).**
- **Option D — `SafePath` type wrapper.** Wrap every `Path` in a type that refuses OneDrive operations at construction. Rejected unanimously: big-bang refactor across the repo; presumes mypy coverage that is not yet in place; violates the project's no-big-bang principle.
- **Grok's hybrid — façade plus non-blocking grep plus deprecation warning.** Rejected in synthesis: enforcement strictly weaker than Option C's AST check for equivalent bypass risk, and the `noqa`-style decay Grok warned about is addressed by Option C's required `reason=` kwarg on the exempt decorator.

### Decision

Adopt Option C. Create `src/corp/safety/onedrive.py` at the Tach **foundation** layer. Enforce via an AST-based pytest test in `tests/safety/test_no_unguarded_writes.py` that runs as part of the standard test suite and blocks merges on violation. Unify all four existing guard sites on the shared helper. Unify `renderer.py` on `OneDriveSafetyError` rather than `ValueError`, updating the two CLI callers that currently catch `ValueError` ancestors.

### Design

**Module:** `src/corp/safety/onedrive.py`, foundation layer (importable from every other layer). Verify no Tach cycle before merging PR-1; fallback placement is `corp/core/safety/` if the Tach taxonomy does not already expose a foundation-layer location.

**Public API:**

| Symbol | Purpose |
|--------|---------|
| `class OneDriveSafetyError(RuntimeError)` | Single exception type raised by guards. |
| `is_onedrive_path(path: Path) -> bool` | Predicate form for callers that translate to a different exception (transitional, used by `renderer.py` only during PR-2). |
| `guard_path(path: Path, *, reason: str) -> None` | Resolve-then-substring check. Fail-closed on `OSError`/`RuntimeError` from `.resolve(strict=False)`. Raises `OneDriveSafetyError` on match. |
| `@onedrive_write_exempt(reason=...)` | No-op tag decorator consumed only by the AST scanner. Makes exemptions grep-able and code-reviewable. Required `reason=` keyword argument. |

**CI enforcement:** pytest test at `tests/safety/test_no_unguarded_writes.py`.

- Scope: every `.py` file under `src/corp/`.
- Dangerous primitives: `Path.unlink`, `Path.rmdir`, `Path.replace`, `Path.write_bytes`, `Path.write_text`, `shutil.rmtree`, `shutil.move`, `shutil.copytree`, `os.remove`, `os.rename`, `os.unlink`.
- Rule 1: for each function containing a call to a dangerous primitive, require `guard_path(...)` in the same function, `@onedrive_write_exempt(reason=...)`, or an allowlisted path prefix (`tests/`, tempfile helpers at explicit paths).
- Rule 2 (closes a silent-neutering attack vector): a `guard_path()` call inside a `try` block whose matching `except OneDriveSafetyError` does not re-raise must be flagged.
- Self-test: the scanner includes a deliberately unguarded fixture; if the scanner passes that fixture, the scanner itself fails.
- Performance budget: test fails if execution exceeds 10 seconds. Scanner is intra-function only; inter-procedural analysis is out of scope.

**Renderer unification:** `renderer.py` raises `OneDriveSafetyError` natively instead of wrapping as `ValueError`. The two CLI callers that catch `(FileNotFoundError, ValueError)` are updated to include `OneDriveSafetyError`. Wrap-and-re-raise was explicitly rejected in Council synthesis as permanent drift.

### Consequences

**Positive.** Omission becomes a CI failure, not a latent bug. A new write site is mechanically required to either guard or explicitly exempt with a reason string. `renderer.py` stops being the odd one out. `deck_actions.py:104` gets fixed as part of PR-2 instead of lingering as a known gap. The exempt-decorator count becomes a quarterly architecture metric (grep-able, reviewable, bounded).

**Negative.** Scanner maintenance cost (estimated ~0.5 engineer-days per year as new write primitives or false positives surface). The foundation-layer `safety/` module is a new cross-cutting dependency that every layer may import; Tach must accept this placement. The scanner has bugs just like any other code — it is a single point of failure for the invariant.

**Neutral.** Re-exports of `OneDriveSafetyError` from the four existing sites remain for one release cycle to avoid churn, then are deleted in a cleanup commit.

### Consensus and dissent

AI Council 2026-04-22 debated Option C with a four-model panel and Claude Sonnet as synthesizer. Claude, Gemini, and OpenAI recommended Option C. Grok dissented, proposing a façade plus non-blocking grep plus deprecation warning, and analogized the exempt decorator's long-term decay risk to `noqa` proliferation. Synthesis judged Grok's alternative as strictly weaker enforcement for equivalent bypass risk. Grok's decay concern is acknowledged as real; mitigation is the required `reason=` kwarg (grep-able text), quarterly architecture review of the exempt count, and Codex-review discipline on any PR that adds a new exemption.

### Acknowledged limitations (explicit, not footnotes)

1. **Non-English Windows OneDrive path detection.** The `OneDrive - Blue Yonder` substring is in English; non-English Windows installs localize the folder name. Estimated <5% of fleet. Trigger for fix: user report or a second incident on a localized install. Investigation scheduled Q3 2026.
2. **Shell-out deletions.** `subprocess.run(["rm", ...])`, `os.system("del ...")`, and similar are out of AST scanner scope. Rely on Codex review.
3. **Conditional guard execution.** A `guard_path()` call inside an `if` branch that does not cover every write path in the function is not caught by intra-function AST analysis. Rely on Codex review.
4. **Third-party file operation libraries.** `send2trash`, `aiofiles`, and others are not in the primitive list. The primitive set must be audited before PR-3 merge; any third-party lib in use that bypasses the scanner is either added to the primitive list or explicitly accepted in the acknowledged-limitations section of that PR.
5. **Guard itself can have bugs.** Centralization is a single point of failure; a bug in `guard_path` or the AST scanner bypasses every caller at once. Partial mitigation: fail-closed on any `OSError`/`RuntimeError` during path resolution, plus the scanner self-test fixture.

### Migration plan (three PRs)

| PR | Scope | Gate |
|----|-------|------|
| PR-1 Foundation | Create `corp/safety/onedrive.py`. Verify no Tach cycle. Enumerate third-party write libraries in use. Grep monorepo for `except.*ValueError` in callers of `corp.project.cli.render`. | Codex review approval |
| PR-2 Migration | Migrate the four existing guard sites to `guard_path()`. Unify `renderer.py` on `OneDriveSafetyError` and update two CLI callers. Fix `deck_actions.py:104` (`writable=True` + guard). Add CLI integration test for OneDrive-path rejection. | PR-1 merged + Codex review approval |
| PR-3 CI enforcement | Ship AST scanner with self-test. Performance budget check. Seed against clean tree. Enable blocking. | PR-2 merged + Codex review approval |

Each PR is independently reviewable. Each requires Codex review per the repo's high-risk-architectural-change policy in `AGENTS.md`.

---

## Decision 2 — Vault single-writer invariant amendment

### Context

ADR-23's invariant ("corp ingest/ is SOLE vault writer") was aspirational. Eight write sites in `src/corp/actions/` pre-date ADR-23 consolidation and have been operating correctly since at least 2026-03-09 (commit `48934c5`):

| Module | Sites | Target content |
|--------|-------|----------------|
| `vault_actions.py` | 2 | `project-info.yaml`, index file |
| `archive_actions.py` | 2 | archived `project-info.yaml` updates |
| `brief_actions.py` | 1 | project brief markdown |
| `analytics_actions.py` | 1 | analytics dashboard |
| `monitoring_actions.py` | 1 | monitoring dashboard |

These writes target specific non-source zones. No tests enforced the invariant; the Codex finding on 2026-04-21 surfaced the drift between doc and code.

### Options considered

- **Option A — Rewrite all eight sites to route through `vault_io`.** Rejected: large diff across business-logic modules, high regression risk, zero pre-existing invariant tests to catch routing errors introduced by the refactor, and `vault_io` would need to grow specialized write methods for each non-source zone anyway.
- **Option B — Amend the invariant to match actual, correct architecture.** Narrow the sole-writer rule to `.md` sources with YAML frontmatter under `02_sources/` (the ingest pipeline's output). Explicitly whitelist `actions/*` writes to a bounded set of non-source zones. **Chosen.**

### Decision

`vault_io.write_note` remains the sole writer for **`.md` notes with YAML frontmatter under `02_sources/`** (the ingest pipeline's canonical output). Approved `actions/*` modules may write directly to zones on an explicit whitelist: **DASHBOARDS, METADATA, BRIEFS**. Any write outside the whitelist routes through `vault_io`. Writes to `02_sources/` from outside `ingest/` or `extraction/vault_writer.py` remain forbidden.

### Design

- Extend `VaultZone` enum (`src/corp/models.py`) to add `METADATA` and `BRIEFS` entries where the concept does not already map cleanly onto an existing zone. `DASHBOARDS` is already present.
- Add predicate `vault_io.is_writable_by_actions(zone: VaultZone) -> bool` returning `True` only for the whitelisted zones. Single source of truth for the whitelist.
- Write pattern at existing eight sites: call the predicate before writing; if whitelisted, write directly; otherwise route through `vault_io.write_note`. Existing sites already target correct zones per inventory — the predicate codifies what was already happening.
- CI enforcement: pytest test at `tests/safety/test_vault_writer_invariant.py`. Walks `src/corp/actions/` AST for direct writes under `cfg.vault_path`. For each write site, resolve the target path's zone and assert the zone is in the whitelist. Fail the test (and block merges) on violation.

### Consequences

**Positive.** Invariant becomes testable. Reflects actual working architecture. Minimal diff at eight existing sites (predicate call + direct write, already the correct target). Future action-module contributors get a clear rule: is the zone whitelisted? Yes → write directly. No → route through `vault_io`.

**Negative.** Original ADR-23 purity is broken; the sole-writer story now has a bounded exception. Whitelist grows by accretion if zone additions are not reviewed architecturally.

**Neutral.** `vault_io.write_note` remains sole writer for sources — the value of that invariant (source hash tracking, frontmatter integrity, ingest audit trail) is unchanged.

### Acknowledged limitations

1. **Whitelist discipline.** New zones added to the whitelist bypass the invariant without further review if process is lax. Mitigation: Codex-review any PR that adds a zone entry; quarterly architectural review of the whitelist.
2. **Zone-scope violations.** A dashboard action that accidentally writes brief-shaped content to `DASHBOARDS` is not caught — the check asserts zone membership, not content shape.
3. **`VaultZone` enum coupling.** Any zone renames cascade to the whitelist and the CI test.

### Migration plan (one PR)

| PR | Scope | Gate |
|----|-------|------|
| PR-4 Vault writer narrowing | Add `METADATA` and `BRIEFS` to `VaultZone`. Add `is_writable_by_actions` predicate. Add CI test. Update ARCHITECTURE.md vault-writer section to cite the narrowing. Update ADR-23 cross-reference to point to ADR-27. Do NOT rewrite the eight existing write sites — inventory confirms they already target whitelisted zones. | Codex review approval |

---

## Out of scope (both decisions)

- **Non-OneDrive synced roots.** Dropbox, Google Drive, iCloud. Generic synced-root detection is deferred until a second root is encountered in practice. Parameterize the guard when that happens, not speculatively.
- **Historical audit of past bypass commits.** Not a safety issue going forward. Git history is preserved.
- **`ingest/*` and `extraction/vault_writer.py` vault-writer rules.** Unchanged. They remain sole writers for sources.
- **Propagation to other repos.** This ADR covers `corp-monorepo` only. The `ai-council`, `corp-ops`, and `corp-sca-time-automation` repos are out of scope. If they adopt this pattern later, a separate ADR in each repo should cite ADR-27.

## Revisit triggers

- Second incident of the INCIDENT 2026-03-14 class despite the AST scanner passing → escalate to Option D (`SafePath` type wrapper).
- mypy adoption reaches >70% of `src/corp/` → reconsider Option D as meaningfully cheaper than it is today.
- More than one non-OneDrive synced root encountered in practice → generalize the guard to a registry pattern.
- Exempt decorator count grows faster than ~2 per quarter → architectural review of why guards are being skipped.
- Whitelist (Decision 2) grows by more than one zone per year → architectural review of the narrowing scope.
- Second synced service encountered on a different machine (e.g. Dropbox) → generalize module structure beyond `onedrive.py`.

## Signals this ADR is working

- Zero unguarded writes in `src/corp/` per the AST scanner over a full quarter.
- Zero vault-writer-invariant violations per the whitelist CI check over a full quarter.
- Exempt decorator count stable or growing slowly, each entry with a documented `reason=` string.
- No recurrence of INCIDENT 2026-03-14 class over 12 months.

## Related work

- Hotfix `hotfix/onedrive-safety-p1` merged 2026-04-21
- Verification evidence: `docs/audits/2026-04-21-p1-verification.md`
- Codex reviews: `docs/audits/2026-04-21-codex-hotfix-review.md` (initial and post-amendment)
- Council debate transcript: `docs/decisions/ADR-27-council-onedrive-centralization.md`
- ADR-23: re-export shim pattern (precedent for minimal-diff migrations) and origin of the sole-writer invariant that Decision 2 amends
- ADR-26: Tach 4-layer model and foundation-layer placement rules
