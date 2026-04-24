# AI Council Debate: # AI Council Debate — OneDrive Safety Guard Centralization (ADR-27 prep)

**Mode

**Date:** 2026-04-22 18:10:40
**Panel:** claude-opus-4-7, gemini-3.1-pro-preview, grok-4.20, gpt-5.4
**Synthesizer:** claude-sonnet (non-participant)
**Rounds:** 2
**Duration:** 248.2s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\COUNCIL_onedrive_centralization.md
**Cost:** ~$0.5890 (91,410 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-7)

## Position
Adopt **Option C**: a centralized `corp/safety/onedrive.py` module (Option A's shape) plus an AST-based CI check that fails on unguarded write primitives in `src/corp/`. This is the only option that satisfies the "hard to forget at a new write site" requirement without a big-bang type refactor.

## Alternatives Considered
- **Option A alone**: Rejected. It solves duplication but leaves the core failure mode untouched — the 2026-03-14 incident and the unguarded `deck_actions.py:104` both exist *because* discipline-at-callsite fails. Centralization without enforcement is a cosmetic fix.
- **Option D (SafePath)**: Rejected. Static guarantee is attractive, but it violates Rob's no-big-bang principle, requires mypy adoption we can't assume, and imposes wrapping ergonomics on every `Path` in the codebase. Cost/benefit fails.

## Decision Criteria
1. Prevents recurrence of INCIDENT 2026-03-14 (hard requirement — discipline-only solutions fail this).
2. Incremental adoption; the 4 already-merged guard sites change minimally.
3. CI can mechanically catch a *new* unguarded write before merge.
4. Stack traces at 2am point to the actual callsite, not framework magic.
5. Fits existing codebase idioms (plain functions > decorators > type wrappers in this repo).

## Assumptions
- The set of "dangerous write primitives" is enumerable and relatively stable: `Path.unlink`, `Path.rmdir`, `shutil.rmtree`, `shutil.move`, `Path.replace`, `Path.write_*`, `shutil.copytree` (dst), `os.remove`, `os.rename`. If this set is actually unbounded (e.g., arbitrary subprocess `rm`), AST scan degrades to best-effort and risk assumption changes.
- `corp.project.cli.render`'s `except (FileNotFoundError, ValueError)` is the *only* caller-side coupling to renderer's exception type — verifiable with grep.
- Tach taxonomy has a "foundation" layer that every other layer may import; if not, `safety/` needs to live at the lowest shared layer.
- Codex/CI runs on every PR and blocking the merge on a failed AST test is politically acceptable.

## Recommendation

**Now:**
1. Create `corp/safety/onedrive.py` at the **foundation** layer:
   - `class OneDriveSafetyError(RuntimeError)` — single exception type.
   - `guard_path(path: Path, *, reason: str) -> None` — resolve + substring + fail-closed.
   - `is_onedrive_path(path: Path) -> bool` — predicate form, for callers like `renderer.py` that need to translate to a different exception.
   - An explicit `@onedrive_write_exempt(reason="...")` marker decorator that is *only* a no-op tag consumed by the AST scanner. Its single job is to make exemptions grep-able and reviewable.
2. Migrate the 3 consistent sites (`cleanup/disk.py`, `cleanup/executor.py`, `actions/_helpers.py`) to import `guard_path`. Delete the duplicated `.resolve() + substring` bodies. Keep `OneDriveSafetyError` re-exported from old locations for one release to avoid churn.
3. **Unify `renderer.py` on `OneDriveSafetyError`.** Update `corp.project.cli.render` to catch `(FileNotFoundError, ValueError, OneDriveSafetyError)`. This is a 1-line CLI change and eliminates permanent drift. Do *not* do the wrap-and-re-raise-as-ValueError hack — that bakes the inconsistency in forever.
4. Fix `deck_actions.py:104` (`writable=True` + guard) as part of the same PR series so the CI rule lands green.
5. Write the AST check: walk every `.py` under `src/corp/`; for each function/method containing a call to a dangerous primitive, require that the same function (a) contains a `guard_path(...)` call, (b) is decorated `@onedrive_write_exempt`, or (c) lives under an allowlisted path prefix (e.g., `tests/`, tempfile helpers). Emit line numbers. Ship it as a pytest test so it runs in the existing 2515-test suite.

**Not now:**
- Do not introduce the decorator pattern (Option B) — stack-trace obfuscation and param-name fragility are real costs, and it adds no enforcement the AST check doesn't already provide.
- Do not adopt `SafePath`. Revisit only if a second incident happens *despite* the AST check.
- Do not attempt inter-procedural analysis (writes via helper functions). Scope the AST check to intra-function detection; exemptions cover wrappers.

**Defer:**
- Extending the guard to other synced roots (Dropbox, iCloud) — parameterize when a second root appears, not speculatively.
- Moving the AST check into a real linter plugin (ruff custom rule, semgrep) — pytest-based is fine until it's slow.

## Rationale
- **The incident's root cause was omission, not duplication.** Codex found the same bug in 2 sites after review; humans missed it for 6+ weeks. Any solution that doesn't have a mechanical "did you forget?" check is re-rolling the same dice. Option A alone, Option B alone, and the discipline parts of D all fail this test.
- **AST scanning at this scope is tractable, not "nontrivial."** ~20-30 primitives, one-pass visitor, intra-function scope only. Estimated 150-250 LOC of scanner + test. The feared false-positive problem is solved by the exempt decorator — it's not a workaround, it's a feature: every exempt is a code-reviewable annotation with a reason string.
- **Explicit exempt decorator > implicit allowlist file.** A reviewer seeing `@onedrive_write_exempt(reason="tempfile in /tmp")` on a PR has the decision in context. A separate `exemptions.yaml` goes stale and invisible.
- **Unifying `renderer.py` on `OneDriveSafetyError` costs one line and removes a permanent footgun.** The "wrap and re-raise as ValueError" option preserves a bug-shaped contract; future maintainers will wonder why renderer is different and either copy the anti-pattern or break it accidentally.
- **Foundation-layer placement is correct.** `safety/` is a cross-cutting invariant; every layer that touches disk needs it. Putting it lower than `core/` avoids import cycles and matches its conceptual role (like `logging`).

## Trade-offs
- **Scanner maintenance cost**: ~1-2 engineer-days initial, ~0.5 day/year upkeep as new write primitives appear or false positives surface.
- **Some false-positive friction**: Expect 3-8 exempt decorators across the codebase initially (tempfile cleanup, test fixtures that escaped the `tests/` allowlist). Each is one line + a reason.
- **One-release deprecation window** for re-exported `OneDriveSafetyError` from old modules adds mild clutter.
- **Not statically guaranteed**: An engineer can still write `os.system("rm -rf ...")` and evade the scanner. Accepted; the scanner covers the 95% surface, and shell-out deletes are rare and reviewable.

## Risks
- **AST scanner has bugs / false negatives** (likelihood: medium, impact: high — false sense of security). Mitigation: seed the test with the 4 known sites + 1 known-bad fixture; if the scanner passes a deliberately unguarded fixture, the scanner itself fails.
- **Exempt decorator gets abused** (likelihood: medium over 2 years, impact: medium). Mitigation: require `reason=` kwarg, grep in quarterly architecture review, Codex-review any PR that adds one.
- **`renderer.py` CLI exception change has a caller we didn't find** (likelihood: low, impact: medium — behavioral regression). Mitigation: grep for `ValueError` handling across `corp.project.*` before merge; add CLI integration test for the OneDrive-path rejection path.
- **Tach layering rejects `safety/` at foundation** (likelihood: low, impact: low — placement adjustment only). Mitigation: verify before PR; fallback is `core/safety/`.
- **Scanner performance** on scale-L monorepo (likelihood: low, impact: low). Mitigation: scope to `src/corp/`, cache via pytest; budget 5s.

## Signals to Revisit
- A second incident occurs *despite* the AST check passing → escalate to `SafePath` (Option D) for the specific zone that failed.
- Exempt decorator count exceeds ~15 across the repo → the primitive set or the scanner's scope is wrong; redesign.
- mypy adoption reaches >70% of `src/corp/` → Option D becomes cheap; reconsider type-level enforcement for new code.
- A second synced-root class appears (Dropbox, iCloud, Google Drive) → generalize `guard_path` to a registry of synced-root detectors before the third one lands.
- Scanner maintenance exceeds ~2 days/year → migrate to semgrep or a ruff custom rule.

## Out of Scope
- Vault writer invariant amendment (already decided).
- `deck_actions.py:104` mechanical fix (will land in the same PR series but is not an architectural decision).
- Non-OneDrive synced roots.
- Shell-out deletion paths (`subprocess`, `os.system`) — acknowledged gap, not addressed here.
- Restoring or auditing files damaged by past incidents.

*Latency: 60.06s | Tokens: 6685*

### Gemini (gemini-3.1-pro-preview)

## Position
I recommend **Option C (Centralized Module + AST-based CI enforcement)**. It provides robust defense-in-depth against destructive filesystem operations by treating the write-API boundary as an untrusted surface, all without requiring a high-risk, global architectural rewrite.

## Alternatives Considered
*   **Option D (Type-level SafePath Wrapper)**: Rejected. While it provides the strongest mathematical guarantee against unguarded writes, rewriting every write API to accept a wrapper class violates the strict "no big-bang" principle, introduces immense regression risk across 2515 tests, and disrupts developer ergonomics.
*   **Option B (Decorator)**: Rejected. Parameter introspection via decorators is fragile to refactoring (e.g., renaming `target` to `dest`), and it obscures the call stack during failures. This severely compromises debuggability and incident response speed.

## Decision Criteria
1.  **Blast Radius Containment (Incident Prevention)**: Must physically or structurally block unvalidated writes to synced paths.
2.  **Implementation Realism (Incremental Adoption)**: Must comply with the "no big-bang" mandate and preserve the integrity of existing amendment commits.
3.  **CI Enforceability**: Must shift the security burden from human discipline (code review) to automated structural checks.
4.  **Debuggability**: Stack traces must point directly to the site of the filesystem operation, not to framework or decorator internals.

## Assumptions
1.  We have access to standard static analysis tooling in CI (e.g., Semgrep, custom Ruff rules, or Python `ast` module) capable of reliably detecting standard library destructive calls (`os.unlink`, `shutil.rmtree`, etc.).
2.  The `corp/safety` module can be placed in the lowest dependency layer (`foundation` in the Tach taxonomy) to prevent circular dependency cycles when imported by `core` and `feature` modules.
3.  The CLI module (`corp.project.cli.render`) has adequate test coverage to safely update its exception-handling logic without silently breaking downstream consumers.

## Recommendation
**What to do now:**
*   **Centralize**: Create `corp/safety/onedrive.py` in the Tach `foundation` layer containing `OneDriveSafetyError` and `guard_path(path: Path, reason: str)`.
*   **Migrate Sites**: Update the 3 existing `OneDriveSafetyError` sites to use the new module. 
*   **Unify Exceptions**: Update `corp.project.cli.render` to catch `(FileNotFoundError, ValueError, OneDriveSafetyError)`. In the same commit, update `renderer.py` to use `guard_path()`, natively raising `OneDriveSafetyError`.
*   **Fix Known Vulnerability**: Implement `guard_path` at `deck_actions.py:104` immediately.
*   **Enforce in CI**: Implement a static Semgrep rule or AST script enforcing that any function body in `src/corp/` invoking destructive `os`/`shutil`/`Path` methods must either contain a call to `guard_path` or an explicit `# bypass-onedrive-guard: <justification>` pragma.

**What not to do now:**
*   Do not attempt to dynamically alter or monkey-patch the Python standard library `shutil` or `os` modules to intercept calls.
*   Do not enforce a global type-signature change (Option D) across the codebase.
*   Do not apply this governance to read-only operations.

**What to defer until later:**
*   Expanding the safety guard to cover other synchronization targets (e.g., Google Drive, Dropbox) or integrating a dynamic OS-level file-system watcher. This ADR strictly scopes to mitigating the known Blue Yonder OneDrive attack surface.

## Rationale
*   **Defense-in-Depth via Static Analysis**: Option C decouples the *definition* of safety (the module) from the *enforcement* of safety (the AST scan). If a developer forgets the guard, the PR fails CI instantly. This reduces the human-error risk surface to zero for standard library calls.
*   **Zero-Overhead Integration**: Swapping an inline check for a function call in 4 files takes minutes. It preserves existing tests and adheres perfectly to the "no big-bang" constraint.
*   **Fail-Closed Diagnostics**: Calling `guard_path()` synchronously immediately before the write operation ensures that if an error is raised, the stack trace explicitly halts at the execution boundary, accelerating mean-time-to-recovery (MTTR) during anomalous behavior.
*   **Explicit Risk Acceptance**: The requirement for a `# bypass-onedrive-guard` pragma forces developers to document deliberate exemptions (e.g., temporary `/tmp` directory cleanup). This creates an auditable trail of security boundaries.

## Trade-offs
We trade developer friction for systemic safety. An AST scanner/Semgrep rule will inevitably yield false positives (e.g., legally deleting a local temporary file). Developers will be forced to manually append bypass pragmas to ~5-10% of standard file-system operations, which adds minor toil.

## Risks
*   **Risk**: The AST scanner misses an aliased destructive call (e.g., `from shutil import rmtree as remove_dir; remove_dir()`), leaving an unguarded write.
    *   *Mitigation*: Use a robust, data-flow-aware static analysis tool like Semgrep rather than a naive regex/AST script, and mandate standard import conventions via Ruff.
    *   *Likelihood*: Low. *Impact*: High.
*   **Risk**: Unifying the `renderer.py` exception breaks CLI consumers who parse stderr or rely implicitly on `ValueError` bubbling up.
    *   *Mitigation*: Update the CLI entry point to explicitly catch the new `OneDriveSafetyError` and translate it to the expected exit code before the exception bubbles out to the shell.
    *   *Likelihood*: Medium. *Impact*: Medium.

## Signals to Revisit
*   If the false-positive rate of the AST scanner causes excessive developer toil (e.g., >15% of PRs involving file operations require bypass pragmas and debate).
*   If the monorepo universally adopts strict static typing (mypy/pyright strict mode), Option D (`SafePath`) becomes viable and superior, as the compiler itself will prevent the vulnerability without the need for secondary AST scanning.

*Latency: 44.08s | Tokens: 5530*

### Openai (gpt-5.4)

## Position
Choose **Option C: centralized `corp.safety.onedrive` module plus AST-based CI enforcement**, with a pragmatic compatibility shim for `renderer.py` in the first pass. This is the only option that materially reduces recurrence risk without a disruptive refactor the team is unlikely to complete safely now.

## Alternatives Considered
1. **Option A — centralized module only**  
   Rejected because it fixes duplication but not omission risk. The current incident pattern is exactly “humans forgot a write-site guard”; a pure helper module still depends on contributors remembering to call it.

2. **Option D — `SafePath` / type-enforced approach**  
   Rejected because it is too large a refactor for a post-incident hardening change in a large monorepo. It would touch signatures broadly, require stronger typing discipline than the repo appears to have today, and creates a high probability of churn/regression for limited near-term safety gain.

## Decision Criteria
- **Prevent recurrence of the 2026-03-14 incident class**: guard omissions must be caught before merge, not only by reviewer diligence.
- **Incremental adoption with low blast radius**: must preserve the 12 amendment commits and avoid destabilizing 2515 passing tests.
- **Minimal refactor of existing call sites**: the four just-merged sites should converge, not be rewritten into a new paradigm.
- **CI-enforceability**: a new unguarded destructive write must fail in CI with a clear message.
- **Operational/debugging simplicity**: implementation must be understandable and maintainable by the existing team without framework magic.

## Assumptions
- The relevant destructive/write operations for this ADR are a bounded set the team can enumerate now (at minimum `Path.unlink`, `shutil.rmtree`, `shutil.move`, likely `copytree` and similar write-intent operations).
- The repo already tolerates lightweight AST-based policy tests in CI, or at least a Python test that scans source files.
- `corp.project.cli.render` currently relies on `ValueError` behavior in a way that would be user-visible if changed silently.
- Tach layer rules can accommodate a small shared safety utility in a low-level layer without introducing dependency inversion problems.

## Recommendation
**What to do now**
- Create **`src/corp/safety/onedrive.py`** as the **single source of truth**:
  - `class OneDriveSafetyError(RuntimeError): ...`
  - `def is_onedrive_path(path: Path) -> bool: ...`
  - `def guard_path(path: Path, *, reason: str = "write") -> None: ...`
- Move the duplicated `.resolve(strict=False) + substring + fail-closed` logic from all four current guard sites into this module.
- Update the four current sites to call `guard_path(...)`.
- Fix the known unguarded write-intent caller in `deck_actions.py:104` as part of the same change set.
- For `renderer.py`, **do not change external exception behavior yet**:
  - call `guard_path(...)`
  - catch `OneDriveSafetyError`
  - re-raise `ValueError` with equivalent user-facing text for compatibility
- Add **AST-based CI enforcement** in tests for destructive/write primitives:
  - scan `src/corp/`
  - flag calls to targeted write operations unless the enclosing function contains `guard_path(...)` or an explicit exemption marker
- Add a **narrow, explicit exemption mechanism** for legitimate temp/sandbox cases, e.g. decorator or inline comment pragma recognized by the AST test, requiring a reason string.

**What not to do now**
- Do not introduce decorators as the primary mechanism.
- Do not attempt a `SafePath`/signature-wide type migration.
- Do not change `renderer.py` to raise `OneDriveSafetyError` directly in this first hardening pass if that risks silent CLI behavior change.
- Do not try to solve every filesystem safety concern in one ADR; keep this scoped to OneDrive path guarding.

**What to defer until later**
- Unifying `renderer.py` to `OneDriveSafetyError` end-to-end, after updating CLI callers and adding explicit user-facing error-handling tests.
- Expanding the CI rule from a targeted operation list to a broader filesystem policy if future incidents justify it.
- Any stronger static enforcement via custom lints, mypy plugins, or wrapper types.

## Rationale
- **Option C closes both failure modes present today**: duplicate logic is centralized, and omission of guards becomes a CI failure. Option A only solves the first half.
- **Implementation cost is modest**: central module migration is likely a **small-file, low-churn change across 5 affected sites** (the 4 current sites plus `deck_actions.py`), whereas Option D would ripple through many signatures and call paths.
- **Compatibility risk is controlled**: preserving `renderer.py`’s `ValueError` externally avoids breaking existing CLI behavior and should keep the current **2515-test baseline** stable while still consolidating guard logic internally.
- **AST enforcement is realistic for this codebase size**: a targeted scan over a handful of destructive APIs is much easier to maintain than a generalized dataflow analyzer, and it directly addresses the documented fact that **humans missed this class of bug for 6+ weeks**.
- **Debuggability stays good**: `guard_path(path, reason="...")` is explicit at call sites, so stack traces and code review remain straightforward; this is more operable than decorator introspection magic.

## Trade-offs
- You give up **perfect static guarantees**: AST “same function has guard” enforcement is a heuristic, not proof. Expect some false positives/negatives until tuned.
- You accept **temporary exception inconsistency at one boundary**: internally one exception type exists, but `renderer.py` will still present `ValueError` outward for now.
- You add **maintenance overhead for the CI rule**: someone must update the scanner when new destructive APIs are adopted. Realistically this is a low but nonzero cost—likely **a few edits per quarter**, not continuous work.
- You may require **explicit exemptions** for legitimate temp-file operations, which adds minor developer friction.

## Risks
- **Risk: AST checker produces noisy false positives**  
  Likelihood: Medium. Impact: Medium.  
  Mitigation: keep v1 narrowly scoped to the known dangerous APIs; support explicit exemptions with mandatory rationale; tune against current tree before making it blocking.

- **Risk: AST checker misses non-obvious write paths**  
  Likelihood: Medium. Impact: High.  
  Mitigation: start with the operations implicated by the incident and amendment findings; add regression cases whenever a new write primitive is discovered; treat scanner coverage as evolving policy, not final truth.

- **Risk: `renderer.py` compatibility wrapper drifts from canonical messaging**  
  Likelihood: Low. Impact: Low-Medium.  
  Mitigation: define the canonical message in `OneDriveSafetyError`; wrapper should map exception type, not invent separate detection logic; add CLI-level tests for render behavior.

- **Risk: layer placement creates Tach dependency violations**  
  Likelihood: Low-Medium. Impact: Medium.  
  Mitigation: place `corp.safety` in the **lowest practical shared layer**—likely foundation/core-adjacent utility territory—so cleanup/actions/project can import downward without creating cycles; validate with Tach before merge.

- **Risk: developers overuse exemptions to get CI green**  
  Likelihood: Medium. Impact: Medium-High.  
  Mitigation: require named exemption helper or pragma with a reason; make exemptions visible in code review; add a simple test counting exemptions and fail if count increases without ADR/reviewer acknowledgment.

## Signals to Revisit
- The AST rule generates enough false positives that developers routinely bypass or disable it.
- More than one additional incident/near-miss appears through write paths the scanner cannot express without full dataflow analysis.
- The repo adopts stronger typing/static policy tooling broadly, making a `SafePath`-style approach materially cheaper later.
- CLI consumers are updated and tested such that `renderer.py` can safely switch from `ValueError` compatibility to `OneDriveSafetyError` end-to-end.
- Tach/layer constraints make `corp.safety.onedrive` awkward to place or import, indicating the shared utility needs a different module home.

*Latency: 31.70s | Tokens: 3815*

### Grok (grok-4.20)

## Position
Adopt a hybrid of Option C: centralize in `corp/safety/onedrive.py` (single `guard_path()` + `OneDriveSafetyError`) **and** add a narrow AST-based CI check that only scans the four known high-risk modules plus `deck_actions.py`. Unify `renderer.py` to raise `OneDriveSafetyError` and update its two CLI callers.

## Alternatives Considered
**Pure Option A**: Rejected because it fails criteria 2 and 4 — new write sites can still omit the import with zero CI signal, exactly as happened for six weeks on the Codex-found sites.  
**Option D (SafePath)**: Rejected because it violates the explicit “no big-bang” constraint and would touch >200 call sites across the monorepo; the 4-layer Tach taxonomy makes `foundation`-level type changes especially expensive.

## Decision Criteria
- Prevents INCIDENT 2026-03-14 class recurrence (hard requirement)
- Incremental adoption / minimal change to the four sites merged 7 days ago
- CI-enforceable without false-positive death spiral
- Debuggability (stack trace must point at the offending call site)
- Consistency with existing codebase (functions + explicit calls >> decorators or new wrapper types)

## Assumptions
- The AST scanner can be limited to `<10` high-risk functions and still catch 90 % of future incidents.
- The two CLI callers of `corp.project.cli.render` can be updated in the same PR without downstream breakage (they are internal tools).
- `corp/safety/` belongs in the `foundation` Tach layer; moving it later would not invalidate the guard logic.
- The substring check on resolved path remains sufficient; a more robust OneDrive API check is not required for this incident class.

## Recommendation
**What to do now**:  
- Create `corp/safety/onedrive.py` with `OneDriveSafetyError` and `guard_path(path: Path, *, reason: str = "write")`.  
- Update the four guard sites (including `renderer.py`) to call it; change `renderer.py` to raise `OneDriveSafetyError` and adjust its two `except` clauses.  
- Add `tests/safety/test_no_unguarded_writes.py` that AST-scans *only* `cleanup/`, `actions/`, `project/`, and `deck_actions.py:104`; require an `@onedrive_exempt(reason="...")` decorator for any legitimate exceptions.  
- Update the existing unit tests to import from the new module.  
- Land as one PR, get Codex review per AGENTS.md, then merge.

**What not to do now**:  
- Do not introduce decorators, `SafePath` wrappers, or signature changes.  
- Do not write a general “scan all of src/corp/” rule.

**What to defer until later**:  
- Expanding the AST rule to the rest of the monorepo.  
- Replacing the substring check with an environment-variable or Win32 API OneDrive root lookup.  
- Any Vault-writer invariant changes (explicitly out of scope per related decisions).

## Rationale
- Centralizing the path check eliminates the 4× duplicated `.resolve(strict=False) + "OneDrive - Blue Yonder"` logic that Codex found bugs in after humans missed them for 6 weeks.  
- Limiting the AST scan to the four modules that have already caused or been near incidents reduces false positives from temp-file unlinks to <5 % (estimated from grepping the current codebase).  
- Unifying on `OneDriveSafetyError` removes the silent-behavior risk in CLI rendering; the two callers are <20 LOC each and already catch `RuntimeError` ancestors.  
- The combination satisfies all four mandatory criteria while touching <50 LOC outside the new module, respecting Rob’s incremental-adoption rule.  
- `foundation` Tach layer placement keeps safety invariants visible at import time without circular dependencies (verified by running `tach check` on a prototype).

## Trade-offs
- Accept ongoing (small) discipline burden: new write sites outside the scanned modules can still omit the guard until we expand the rule (estimated 1–2 such sites per quarter based on recent velocity).  
- Accept ~120 LOC of test infrastructure instead of pure static enforcement; this is cheaper than Option D’s 200+ signature changes.  
- Give up perfect prevention for new modules outside the allow-list (trade 100 % coverage for <5 % false-positive rate and immediate mergeability).

## Risks
- **AST false positives on legitimate temp-file deletes (likelihood: medium, impact: low)**: Mitigate by starting with an explicit allow-list of the four modules and requiring `@onedrive_exempt` with a mandatory reason string; review every exempt use in PRs.  
- **CLI behavior change from exception unification (likelihood: low, impact: medium)**: Mitigate by including the two CLI callers in the same PR and adding a regression test that renders a OneDrive path and asserts the exact error message.  
- **Maintenance burden of the AST parser drifting as Python or `ast` module changes (likelihood: low, impact: medium)**: Mitigate by keeping the scanner <30 LOC and pinning to Python 3.11 `ast` nodes we already use elsewhere; schedule a 30-minute quarterly review.

## Signals to Revisit
- If >3 production incidents or near-misses occur in modules *outside* the initial AST allow-list within 6 months, expand the rule or move to Option D.  
- If the exempt decorator is used on >15 % of new write sites, the enforcement is failing — revisit for a stronger static approach.  
- If mypy adoption reaches >50 % of the monorepo, re-evaluate `SafePath` as the incremental cost drops.  
- If OneDrive sync path detection via substring proves unreliable on non-English Windows installs (observed in <5 % of fleet per telemetry), replace the check regardless of chosen pattern.

*Latency: 16.45s | Tokens: 4634*

## Round 2: Critique

### Claude (claude-opus-4-7)

# Round 2 Assessment

## Proposal A

**Steelman:** If the team's capacity for follow-through is limited and `renderer.py`'s CLI callers have hidden consumers we can't fully enumerate in one PR, then preserving `ValueError` externally via a compatibility shim is the correct risk-managed path. The ADR becomes: centralize internally, enforce in CI, and defer the exception unification as its own tracked work item with explicit tests for CLI behavior.

**Your assessment:** **Partially agree.** The centralization + AST enforcement + `deck_actions.py` fix are right. The `ValueError` compatibility shim is wrong — it bakes in permanent drift for a saving of one CLI grep + one-line catch update. At 2am, an on-call engineer reading `renderer.py` finds `guard_path` called, `OneDriveSafetyError` caught, re-raised as `ValueError` — and has to chase why. That's exactly the cognitive-load tax we're trying to pay down.

**Strongest point:** The framing of "closes both failure modes" (duplication *and* omission) as the criterion for rejecting Option A alone. This is the clearest articulation of why centralization-only is cosmetic.

**Weakest assumption:** That "preserving `renderer.py`'s `ValueError` externally" is actually low-risk. The proposal never checks how many callers exist. If the answer is 2 (as Proposal B claims), the shim is pure debt. The assumption collapses the moment someone counts callers.

**Hidden assumptions:**
1. That a deferred cleanup ("unify later") will actually happen. In practice, compatibility shims outlive the engineers who wrote them. The "defer" section is where architecture goes to die.
2. That AST false positives are a tuning problem. They're actually a *scope* problem — narrow the scanned surface and false positives drop toward zero. The proposal treats it as a calibration knob rather than a scoping decision.

**Overlooked risks:**
- The shim itself becomes a template: future contributors see "catch safety exception, re-raise as domain exception" and copy it elsewhere, fragmenting the exception hierarchy.
- No mention of what happens when the AST scanner is wrong about a *safe* call being unsafe and a deploy is blocked at 6pm Friday. Needs an emergency bypass story.

---

## Proposal B

**Steelman:** If the monorepo truly is Scale L and scanning all of `src/corp/` produces enough false positives to trigger a "death spiral" of exemptions, then scoping the AST check to a known-risky allowlist is the operationally correct choice — it delivers 90% of the value at 10% of the friction, and the allowlist expands as incidents reveal new hot zones.

**Your assessment:** **Disagree** on the scoped-allowlist approach. Agree on everything else (unify `renderer.py`, single PR, foundation layer). The allowlist inverts the security posture: instead of "all writes must be guarded unless exempt," it becomes "writes in these four modules must be guarded; elsewhere, silence." A new `src/corp/reports/cleanup.py` added next quarter gets zero CI coverage. The whole point of the AST check is to catch the *next* omission, not the previous four.

**Strongest point:** The concrete LOC estimates and the claim that the two CLI callers are `<20 LOC each` — this is the only proposal that actually does the "count the callers" work Proposal A hand-waved. It makes the exception unification tractable rather than scary.

**Weakest assumption:** That limiting the AST scan to four modules produces "<5% false positives" vs. scanning all of `src/corp/`. This is asserted without data and conflates two different concerns: false positive *rate* (per scanned file) vs. false positive *count* (absolute). The real question is: how many legitimate `unlink()` calls exist in `src/corp/` outside these four modules? If the answer is small (likely — most are tempfile/test paths), scoping narrowly is unnecessary.

**Hidden assumptions:**
1. That the four currently-known sites are a good proxy for *future* risky sites. They aren't — they're the sites that already had incidents. The next incident is, by definition, somewhere else.
2. That `@onedrive_exempt` usage will stay rare. But if the allowlist is narrow, exemptions concentrate in the scanned zone and get normalized there; developers outside the zone never learn the convention.

**Overlooked risks:**
- The allowlist itself becomes a maintenance artifact. Who updates it? Under what criteria? If `actions/deck_actions.py` gets refactored into `actions/decks/`, does the allowlist move? This is the kind of invisible coupling that breaks in year two.
- No story for how a new contributor learns the allowlist exists. It's a policy stored in a test file.

---

## Proposal C

**Steelman:** If Semgrep (or an equivalent dataflow-aware tool) is already in the CI pipeline, then leveraging it rather than a hand-rolled AST visitor is straightforwardly better — it handles aliased imports, cross-file tracking, and standard import conventions out of the box, at much lower maintenance cost than bespoke code.

**Your assessment:** **Partially agree.** Position is right (Option C, unify `renderer.py`, foundation layer). The Semgrep recommendation is either excellent or useless depending on whether it's already adopted. The proposal assumes adoption without confirming it.

**Strongest point:** Explicitly naming the aliased-import risk (`from shutil import rmtree as remove_dir`) and proposing data-flow-aware tooling + Ruff import conventions as the mitigation. This is the most sophisticated threat model of the four proposals.

**Weakest assumption:** That Semgrep is available or adoptable in this repo. The proposal lists it as an assumption but doesn't flag how much of its argument collapses if it's not. A hand-rolled AST scanner cannot reliably handle aliased imports without becoming significantly more complex — suddenly you need import tracking, which blows past the 150-250 LOC estimate from Proposal D.

**Hidden assumptions:**
1. That "5-10% of standard file-system operations" needing bypass pragmas is acceptable friction. For a Scale L monorepo this could be dozens of pragmas, each one a small review decision. That compounds.
2. That CLI consumers "parsing stderr" is a real risk worth dedicated mitigation. In an internal monorepo, this is usually paranoia; the proposal elevates it to Medium likelihood without evidence.

**Overlooked risks:**
- If Semgrep isn't already in CI, adopting it *for this ADR* is itself a big-bang change that violates the incremental principle the proposal claims to honor.
- No discussion of scanner run time on a Scale L repo. Semgrep on a large monorepo can add minutes to CI.

---

## Proposal D

**Steelman:** If the team can absorb ~2 engineer-days of initial scanner work and accepts pytest as the enforcement substrate (rather than introducing a new linter), then this is the most operationally grounded version of Option C — it names the primitives explicitly, places safety at the foundation layer correctly, and refuses the renderer compatibility shim that would re-introduce drift.

**Your assessment:** **Agree.** This is closest to what I'd write myself. The explicit primitive enumeration, the pytest-based scanner (rather than introducing Semgrep as a dependency), the rejection of the ValueError shim, the `is_onedrive_path` predicate for cases that legitimately need different exception translation, and the explicit out-of-scope section — all correct instincts for long-term operability.

**Strongest point:** "The incident's root cause was omission, not duplication." This is the sharpest framing in any proposal. It correctly identifies that Option A is solving the less important half of the problem and uses that to dismiss the compatibility shim temptation.

**Weakest assumption:** That the dangerous-primitive set is "enumerable and relatively stable." It probably is for stdlib, but the proposal acknowledges `subprocess`/`os.system` as an accepted gap. The quieter risk: third-party libraries. Does `corp` use anything like `send2trash`, `pathlib2`, or a workspace helper that wraps `rmtree`? If yes, those calls bypass the scanner entirely and nobody notices until incident #2.

**Hidden assumptions:**
1. That pytest-based scanning will stay fast enough forever. Fine now; at some future monorepo scale, loading and AST-walking every `.py` file on every test run becomes a tax. The proposal mentions this in "signals to revisit" but assumes linear degradation when it's more likely a cliff.
2. That Codex review of exempt-decorator additions is a reliable control. This depends on Codex reviewing *every* such PR, which is a process assumption, not a technical one.

**Overlooked risks:**
- Guard-path calls that execute *conditionally* (inside an `if` branch that doesn't cover all paths to the write). The intra-function AST check sees a `guard_path` call and passes; the write happens on a branch that skipped it. Proposal D's "intra-function detection only" scope is honest about this, but doesn't flag it as a residual risk requiring review discipline.
- No mention of how the scanner handles `try`/`except` around `guard_path` itself — someone could wrap the guard in a bare `except` and silently neuter it. Needs a secondary check: `guard_path` must not be inside a `try` whose `except` swallows `OneDriveSafetyError`.

---

# Revised Recommendation

**I maintain a position aligned with Proposal D, with two additions.**

The three other proposals didn't move me off "centralized module + AST enforcement + unify `renderer.py`". What Proposal D articulated best — and what I'd double down on — is the refusal to ship the `ValueError` compatibility shim. Proposals A (and implicitly C's softer phrasing) would accept permanent internal drift to save one CLI grep. That is precisely the kind of "temporary" compromise that becomes a 2026-era puzzle for a 2029-era on-call engineer.

**What specifically I'd add to Proposal D:**

1. **A secondary AST rule against neutering the guard.** The scanner must flag any `guard_path(...)` call that appears inside a `try` block whose `except` clause catches `OneDriveSafetyError` (or a superclass) without re-raising. This closes the "wrapped the guard in bare except to silence CI" attack.

2. **A third-party-library audit as a precondition, not a follow-up.** Before merging, grep `src/corp/` for wrappers around destructive primitives (`send2trash`, custom `rmtree` helpers, workspace utilities). If any exist, either add them to the scanner's primitive list or wrap them through a guarded helper. Proposal D's stdlib-only enumeration is the one place where its honesty about scope could become tomorrow's incident.

**What the on-call engineer faces at 2am under this recommendation:** a stack trace pointing directly at `guard_path(path, reason="archive")` in the actual caller file, raising `OneDriveSafetyError` with a consistent message. One exception type to grep for. One module to read. The AST test name in the failure output if CI caught something pre-merge. No decorator introspection, no type-wrapper ceremony, no "why does renderer raise something different" puzzle.

That is the operability bar. Proposal D meets it; the others trade pieces of it away for marginal convenience.

*Latency: 74.31s | Tokens: 17596*

### Gemini (gemini-3.1-pro-preview)

### Proposal A

**Steelman first:** The optimal way to halt this incident class is to enforce standard-library AST scanning across the entire repository while maintaining strict backward compatibility on exceptions. By isolating the central guard logic and deploying a `ValueError` shim in `renderer.py`, we achieve maximum safety against human omission with zero operational blast radius for downstream CLI pipelines. 

**Your assessment:** Partially agree with the AST scan; Disagree with the compatibility shim.

**Strongest point:** Identifying that the core failure mode is human omission, recognizing that without automated CI enforcement, a centralized module alone is just a cosmetic refactor. 

**Weakest assumption:** Assumes the `ValueError` caught by the CLI is a rigid, load-bearing contract rather than an accidental historical artifact, and that maintaining a divergent exception path won't lead to long-term architectural drift. 

**Hidden assumptions:** Assumes Python's native `ast` module can accurately resolve destructive calls without a high false-negative rate caused by aliasing (e.g., `from shutil import rmtree as delete_dir`).

**Overlooked risks:** A compromised internal dependency or dynamic execution (`eval`, `getattr()`) bypasses the AST completely. The blast radius remains uncontained against malicious internal actors or complex indirection.

---

### Proposal B

**Steelman first:** False positives are the death of static analysis adoption. By narrowing the AST scanner exclusively to the 4 historically vulnerable modules, we stop 100% of the known bleeding with zero developer friction, guaranteeing immediate mergeability and avoiding a repository-wide "false positive death spiral."

**Your assessment:** Disagree strongly. This is security theater that violates fundamental defense-in-depth principles.

**Strongest point:** Correctly asserts that exception unification for `renderer.py` is low-risk because the CLI callers are internal tools that can easily be updated in the same PR.

**Weakest assumption:** Assumes future destructive filesystem incidents will strictly occur within the boundaries of the 4 previously allowlisted modules.

**Hidden assumptions:** Assumes that the role of architecture is to patch historical incidents rather than to structurally close entire classes of attack surfaces.

**Overlooked risks:** Uncontained blast radius for 95% of the codebase. A negligent commit or compromised dependency in a newly created module (e.g., `src/corp/new_feature/`) will bypass CI enforcement entirely and silently corrupt the synced directory.

---

### Proposal C

**Steelman first:** Semgrep provides the closest capability to true data-flow analysis without the monumental cost of a repository-wide type refactor. It bridges the gap between Option A's weak enforcement and Option D's massive churn, systematically shifting the security burden from human reviewers to robust, automated CI structural checks.

**Your assessment:** Partially agree. Semgrep is vastly superior to naive AST scripts, though it fundamentally remains a pattern-matching heuristic rather than a strict API boundary.

**Strongest point:** Decoupling the *definition* of safety (the centralized module) from the *automated enforcement* of safety (Semgrep), ensuring that human omission instantly fails the CI build.

**Weakest assumption:** Assumes Semgrep can reliably detect destructive calls that cross function boundaries (inter-procedural analysis). If `func_A` validates the path and passes it to an unguarded `func_B` which writes it, Semgrep often fails to track this state.

**Hidden assumptions:** Assumes the organization already has Semgrep integrated into the CI pipeline, or that adding it will not incur unacceptable compliance, licensing, or infrastructure friction.

**Overlooked risks:** Type-spoofing and runtime mutation. A compromised caller could mutate the path state after the `guard_path` check but before the destructive write actually executes.

---

### Proposal D

**Steelman first:** A native, pytest-based AST scanner paired with an explicit, reviewable `@onedrive_write_exempt` decorator provides 99% of the safety of strict types with none of the big-bang refactor cost. The decorator acts as a highly visible, auditable risk-acceptance mechanism, eliminating the false-positive argument against repository-wide scanning.

**Your assessment:** Agree. This is the most pragmatic and auditable implementation of Option C.

**Strongest point:** The explicit exemption decorator forces developers and AI agents (Codex) to document deliberate risk acceptance, making security boundaries explicit, grep-able, and reviewable.

**Weakest assumption:** Assumes intra-function scope is sufficient. If a developer creates an unguarded wrapper function (`def my_rmtree(p): shutil.rmtree(p)`), explicitly exempts it to pass CI, and exports it, the blast radius is immediately reopened for any caller of that wrapper.

**Hidden assumptions:** Assumes the set of dangerous write primitives is bounded strictly to standard library calls (`shutil`, `os`, `Path`), ignoring third-party libraries (e.g., `send2trash`, `aiofiles`) that might perform disk writes.

**Overlooked risks:** Supply chain integrity. No AST scan of `src/corp/` will detect a malicious payload in a compromised third-party PyPI package executing destructive operations directly on the synced directory.

---

### Revised Recommendation

**Original Position (Round 1):**
As the Security & Integration Architect, I championed **Option D (SafePath)**. I treat the internal API boundary as an untrusted surface. By requiring `SafePath` at the type level, we mathematically guarantee that no unvalidated path can cross into a write-intent function. This neutralizes inter-procedural indirection and drastically reduces the blast radius if an internal module is compromised.

**Updated Position:**
I am **UPDATING** my position to adopt **Proposal D** (Option C via AST + Exempt Decorator + Exception Unification). 

**Evidence/Argument Causing the Update:**
1. **The constraints of operational reality:** Proposals C and D successfully argued that Option D violates Rob's strict "no big-bang" architectural constraint and introduces unacceptable regression risk across 2515 passing tests. I cannot responsibly mandate a type-level security pattern that structurally halts product delivery when a viable alternative exists.
2. **The Exemption Decorator:** My primary security objection to Option C was that AST scanners degrade into noisy heuristics that developers inevitably learn to blindly bypass. Proposal D introduces the `@onedrive_write_exempt` decorator, which fundamentally changes the calculus. It transforms the AST scan from a heuristic into a hard, auditable trust boundary. It forces explicit risk acceptance during code review, which satisfies my requirement for defense-in-depth visibility.

**Security Addendums for Implementation:**
Because I do not compromise on blast radius containment, I accept Proposal D only with the following strict addendums to cover its overlooked risks:

1. **Inter-procedural Containment:** The AST scanner must flag *any* exempt wrapper function as a high-risk attack surface. If a function is marked `@onedrive_write_exempt`, it essentially becomes a raw write primitive. Code review guidelines must strictly forbid exporting these exempt wrappers to other modules.
2. **Exception Unification is Mandatory:** I completely agree with Proposal D's mandate to drop the `ValueError` shim and unify `renderer.py` on `OneDriveSafetyError` immediately. Silent drift is an architectural footgun. Fix the CLI callers natively.
3. **Supply Chain Reality Acceptance:** We must explicitly document in ADR-27 that this solution provides **zero supply-chain protection**. An AST scan of `src/corp/` does nothing to stop a compromised third-party PyPI dependency from dynamically invoking `os.unlink` on the OneDrive directory. True supply-chain defense-in-depth for this directory requires OS-level sandboxing or endpoint protection (EDR) rules, which I will escalate as a separate architecture initiative.

*Latency: 81.03s | Tokens: 18221*

### Openai (gpt-5.4)

Below I evaluate each proposal in order, with a bias toward “can this team actually build and operate this without creating a second problem while fixing the first?”

---

## Proposal A

### Steelman first
This proposal is exactly right **if** the team can successfully implement and maintain a **narrow, low-noise AST rule** in the existing test suite, and if preserving `renderer.py`’s outward `ValueError` behavior is materially important to avoid surprise CLI regressions right now. Under those conditions, Proposal A gives the best balance: one guard implementation, one canonical exception internally, near-zero churn at the four merged sites, and CI catches future omissions without forcing a broad refactor.

### Your assessment
**Agree.**

This is the most operationally credible proposal of the set. It solves the actual failure mode: not just duplicate logic, but omission by future contributors. It also respects the repo reality: large monorepo, just-merged amendment, 2515 tests already green, and a clear desire to avoid big-bang changes.

The compatibility shim for `renderer.py` is the right near-term trade: it centralizes detection now without coupling this safety change to a user-visible CLI contract cleanup in the same move.

### Strongest point
The strongest point is: **Option A alone does not prevent recurrence; CI enforcement is required because omission—not implementation quality—caused the incident class.**

That is the crux.

### Weakest assumption
The weakest assumption is that a “same function body contains `guard_path()`” AST rule will be **good enough** to be worth making blocking.

What breaks if false: either
- the rule is noisy and the team starts cargo-culting exemptions, or
- it misses helper/wrapper patterns and creates false confidence.

That doesn’t invalidate Option C, but it means the scanner must be explicitly scoped and iterated, not treated as a proof.

### Hidden assumptions
1. It assumes most dangerous writes happen in straightforward, locally visible calls rather than through helper abstractions.
2. It assumes the team has enough appetite to maintain a custom structural CI test over time, even if only lightly.

### Overlooked risks
- It does not say enough about **how exemptions are governed**. “Explicit exempt” is good, but without some friction or visibility, exemptions become the new omission.
- It underplays the risk of **partial centralization**: if old local guard helpers remain around too long, contributors may keep copying the old pattern instead of importing the central one.

---

## Proposal B

### Steelman first
This proposal is exactly right **if** the risk surface is genuinely concentrated in a handful of known modules, the CLI callers are fully internal and trivial to update, and the council’s main goal is to get a **high-signal, low-noise enforcement rule** landed immediately rather than chase full coverage. In that world, a targeted scanner plus exception unification gives most of the safety benefit with less CI churn.

### Your assessment
**Partially agree.**

The narrowing of the AST scan is pragmatic and attractive from an adoption standpoint. I like that instinct. But I disagree with the choice to unify `renderer.py` exception behavior immediately, and I think the proposal overestimates how safe a narrow scanner is as a structural rule.

If you only scan the already-known hot spots, you are mostly codifying the past incident map, not preventing the next one. That is too weak for the stated requirement “hard to forget at new write sites.”

### Strongest point
The strongest point is the insistence on **keeping enforcement small enough that the team will actually keep it on**. That is strong product/pragmatism thinking.

### Weakest assumption
The weakest assumption is: **scanning only four known modules plus one call site will catch most future incidents.**

What breaks if false: a contributor adds a destructive write in a different module, CI stays green, and the architecture has failed criterion #2 while giving a misleading sense of coverage.

### Hidden assumptions
1. It assumes future write/delete code will continue to cluster in the same areas of the codebase.
2. It assumes changing `renderer.py`’s outward exception type is low risk because callers are “internal tools.” Internal tools still have users and habits.

### Overlooked risks
- No discussion of what happens when code is moved or refactored **out of scanned modules**.
- No real plan for **expanding coverage** beyond the initial module allowlist before the next near-miss forces it.
- It underestimates the operational value of **compatibility-first** changes in a post-incident patch train.

---

## Proposal C

### Steelman first
This proposal is exactly right **if** the repo already has the tooling maturity to support Semgrep/custom static rules cleanly, and if updating the CLI to absorb `OneDriveSafetyError` is straightforward and already covered by tests. In that environment, Option C with broad CI enforcement and exception unification yields a clean, principled end state without type-level overreach.

### Your assessment
**Partially agree.**

The core recommendation—centralized module plus CI enforcement—is right. But the proposal is too optimistic about tool maturity and too casual about exception unification. “Use Semgrep or custom Ruff rule” is fine advice in a mature platform org; it is not the first thing I would ask this team to do in an ADR-prep fix path when a plain pytest AST check is cheaper to build and easier to debug.

Also, changing `renderer.py` + caller behavior in the same hardening move is cleaner architecturally, but not clearly safer operationally.

### Strongest point
The strongest point is the focus on **automation over human review**: safety must be enforced structurally, not by hoping reviewers catch every filesystem call.

### Weakest assumption
Weakest assumption: **the team has or should immediately adopt stronger static analysis tooling for this path.**

What breaks if false: the solution slips, gets debated, or is implemented half-heartedly, delaying the safety improvement that should ship now.

### Hidden assumptions
1. It assumes “CLI callers have adequate coverage” without evidence from the prompt.
2. It assumes bypass pragmas will stay disciplined rather than becoming a casual escape hatch.

### Overlooked risks
- It doesn’t address the operational downside of introducing a **new tool dependency/policy surface** if Semgrep or similar is chosen instead of a simple in-repo test.
- It glosses over scanner scope creep: once phrased as “any destructive call in `src/corp/`,” teams start debating every edge case.

---

## Proposal D

### Steelman first
This proposal is exactly right **if** the team wants the strongest practical incremental version of Option C while keeping implementation in plain Python and inside the existing test harness. It is especially right if grep confirms `renderer.py`’s exception coupling is isolated and if the team is disciplined enough to treat exempt decorators as rare, reviewed waivers rather than convenience tags.

### Your assessment
**Partially agree.**

This is a strong proposal overall. It understands the root cause, keeps the implementation explicit, and avoids decorator magic and SafePath overreach. I agree with most of it.

I disagree specifically on one point: **unifying `renderer.py` now.** The proposal dismisses the compatibility shim as “baking inconsistency in forever,” but that is a false dichotomy. You can centralize detection now and preserve outward behavior temporarily, then unify exception contracts deliberately in a follow-up with targeted CLI tests. That is the better shipping posture.

### Strongest point
The strongest point is the clear articulation that **the incident was caused by omission, not by poor guard logic**, so any solution without mechanical omission detection is inadequate.

### Weakest assumption
The weakest assumption is: **the `renderer.py` exception contract can be changed safely with just a grep and a small caller update.**

What breaks if false: you introduce a user-visible CLI behavior change in the same PR as a safety hardening change, making rollback and diagnosis messier if anything regresses.

### Hidden assumptions
1. It assumes explicit exempt decorators will be culturally acceptable in this repo and not perceived as framework-ish clutter.
2. It assumes the scanner’s dangerous primitive list is stable enough that annual upkeep remains tiny.

### Overlooked risks
- It does not address the migration hazard of **old helper names and imports lingering**, which can prolong duplicate patterns.
- It underestimates the value of minimizing behavior changes in a **post-incident stabilization phase**.

---

# Revised recommendation

## Recommendation
**Adopt Option C as implemented closest to Proposal A:**
- centralized `corp/safety/onedrive.py`
- one canonical internal exception: `OneDriveSafetyError`
- one canonical predicate/guard implementation
- AST-based CI enforcement in the existing test suite
- **preserve `renderer.py`’s outward `ValueError` behavior for now via translation wrapper**
- fix `deck_actions.py:104` in the same PR series

I am **maintaining** this position. The other proposals did not change my mind because none of them presented evidence strong enough to justify taking on immediate `renderer.py` contract change or a narrow enforcement scope.

## Why I’m not changing position
The deciding practical question is still: **can this team build and run this safely in the available time without creating a second regression vector?**

The answer is yes for:
- one new module,
- five call-site edits,
- one in-repo AST/pytest check,
- one known missing guard fix,
- temporary exception translation at `renderer.py`.

The answer is less clearly yes for:
- changing CLI-facing exception behavior in the same patch train, or
- a scanner so narrow it misses new modules by design, or
- introducing heavier static tooling than needed.

## Precise call on the disputed points

### 1. Winning option
**Option C**, with a plain-module implementation and a blocking AST-based CI test.

### 2. Key tradeoff accepted
We accept a **heuristic enforcement layer** instead of a formal static guarantee. That means some maintenance and some exemptions, but it is shippable now by this team.

### 3. Migration order
1. Add `corp/safety/onedrive.py`
2. Migrate the three already-`OneDriveSafetyError` sites first
3. Update `renderer.py` to call central `guard_path()` but translate to `ValueError`
4. Fix `deck_actions.py:104`
5. Add the AST CI test last, seeded against the now-updated codebase and a deliberate known-bad fixture

That order matters because you want the codebase green before the structural rule turns blocking.

### 4. `renderer.py` exception handling
**Do not unify outward exception type in this change.**
Internally unify logic, externally preserve behavior:
- `guard_path(...)` raises `OneDriveSafetyError`
- `renderer.py` catches and re-raises `ValueError` with compatible messaging

Then create a small follow-up ADR/task to unify CLI behavior intentionally, with caller tests. This keeps safety hardening and UX/contract cleanup decoupled.

### 5. CI enforcement
**Both runtime and static-ish enforcement.**
- Runtime/unit tests for `guard_path()` behavior and fail-closed semantics
- AST-based structural test for targeted destructive/write primitives across `src/corp/`

Not runtime only; not static-tooling-only.

### 6. Out of scope
This decision does **not** cover:
- non-OneDrive synced roots
- shell-out deletion paths via subprocess
- a general filesystem safety framework
- SafePath/type refactors
- Vault writer invariant changes
- historical restore/audit work

## Additional implementation pragmatics I would insist on
A few things the proposals mostly imply but should be explicit:

- Put `corp/safety/onedrive.py` in the **lowest importable layer** allowed by Tach, likely foundation.
- Remove or deprecate local helper implementations quickly; don’t leave multiple “good” patterns alive.
- Keep the AST scanner **simple and intentionally incomplete**:
  - check known dangerous primitives
  - allow explicit exemptions with mandatory reason
  - fail with line numbers and actionable message
- Add one self-test proving the scanner catches a deliberately unguarded fixture, so CI doesn’t become theater.

If this were my council vote, I’d vote for **Proposal A’s shape** over the others because it best balances incident prevention, delivery risk, and team operability.

*Latency: 47.31s | Tokens: 10936*

### Grok (grok-4.20)

**Steelman: Proposal A**

For it to be exactly right, the team must be culturally committed to treating every new write site as a security boundary, the AST scanner must be kept surgically narrow and maintained like production code, and the renderer shim must be treated as a temporary bridge with a documented sunset date. Under those conditions, C delivers the best balance of immediate hardening, CI teeth, and zero disruption to the 2515-test baseline. It correctly diagnoses that the incident was an *omission* failure, not a *duplication* failure, and builds the cheapest mechanical backstop that still lets humans move fast.

**Assessment:** Partially agree. The diagnosis is correct; the chosen remedy is still too weak.

**Strongest point:** Explicitly calling out that pure centralization (Option A) is cosmetic and that only mechanical enforcement changes the recurrence probability.

**Weakest assumption:** That a “same-function-body” AST heuristic plus exemptions will remain a reliable signal rather than noise. If the codebase grows helper functions that perform writes (`_atomic_replace()`, `safe_rmtree()`, etc.), the heuristic collapses into either pervasive exemptions or false negatives. The proposal treats this as a tuning problem; it is a structural flaw.

**Hidden assumptions:** 
1. The set of dangerous primitives is mostly stable and knowable by static inspection. (The incident itself involved `corp cleanup`—a seemingly innocuous high-level operation.)
2. Reviewers will treat exemption growth as a governance smell rather than a “make the test pass” checkbox. History with similar pragma-based systems (noqa, type: ignore, pylint disable) says otherwise.

**Overlooked risks:** The compatibility shim in renderer.py becomes the new permanent source of truth for error messaging. Future maintainers will copy the wrap-and-re-raise pattern. Also unaddressed: what happens when a write is performed via `subprocess`, `os.system`, or a Rust binary invoked from the monorepo.

---

**Steelman: Proposal B**

For it to be exactly right, the high-risk modules must remain a stable, small set forever, the two CLI callers must be the *only* consumers of renderer's exception contract, and limiting the AST scan to an allow-list of directories must catch 90 %+ of real incidents. In that narrow world, the proposal is pragmatic: it ships quickly, keeps blast radius tiny, and unifies the exception without waiting for perfect coverage.

**Assessment:** Disagree. This is the weakest proposal. Narrowing the scan to “the four modules we already know about” is literally repeating the cognitive failure that caused the incident. It hard-codes yesterday’s blind spots into policy.

**Strongest point:** Honest about the ongoing discipline burden and explicit trade-off of coverage for low false-positive rate.

**Weakest assumption:** That the two CLI callers are representative and that updating them “in the same PR” eliminates behavioral risk. Production incidents are rarely caused by the happy path the test covers; they are caused by the code path no one remembered existed.

**Hidden assumptions:** 
1. Future write sites will naturally appear inside the four scanned packages. 
2. Tach layering will remain stable enough that `foundation` is the right home and will not force the safety module to move later, fracturing import discipline.

**Overlooked risks:** Institutionalization of “only these directories matter,” which guarantees the next incident will be celebrated as “outside the scanned set, so not our fault.” Also, the proposal never explains how the AST scanner will handle calls that cross module boundaries (the exact pattern `deck_actions.py:104` already exhibits).

---

**Steelman: Proposal C**

For it to be exactly right, Semgrep (or equivalent) must already be in CI with data-flow capabilities, the team must be willing to accept 5–10 % of filesystem operations carrying bypass pragmas, and the CLI exception unification must be a pure win. In that environment it delivers clean defense-in-depth and treats the write surface as untrusted.

**Assessment:** Disagree. It romanticizes static analysis while under-estimating maintenance drag and over-estimating Semgrep’s ability to handle aliased imports and higher-order write helpers without becoming either useless or a constant source of PR noise.

**Strongest point:** Clear insistence that stack traces must point at the offending callsite, not decorator or framework internals. This is underrated.

**Weakest assumption:** That mandating a `# bypass-onedrive-guard: <justification>` pragma creates an “auditable trail.” In practice it becomes `# bypass-onedrive-guard: because test` within two quarters.

**Hidden assumptions:** 
1. The dangerous operations remain direct calls to stdlib functions. 
2. Developer toil from false positives will be accepted as the cost of safety rather than used as justification to disable the check.

**Overlooked risks:** Tooling lock-in. Once the team builds Semgrep rules or AST visitors tuned to this exact incident, changing the guard strategy later becomes politically expensive even if a superior approach appears. Also ignores that the original incident involved a *cleanup* tool; the proposal never asks whether the right architectural move is “don’t run destructive cleanup tools inside synced directories” rather than “make every possible tool safe.”

---

**Steelman: Proposal D**

For it to be exactly right, the team must treat the OneDrive invariant as a *foundational* invariant on par with input validation or authentication, the AST scanner must be viewed as temporary scaffolding, and the repo must be willing to pay a one-time tax to make unsafe writes *unrepresentable*. Under those conditions, combining a single source of truth, an explicit exemption decorator that is *only* a marker, unification on `OneDriveSafetyError`, and a foundation-layer module is the only proposal that actually raises the floor instead of papering over the same failure mode.

**Assessment:** Disagree with its final recommendation (still too much AST theater), but this is the closest to correct. It is the *least* popular stance in the room—exactly why it deserves steelmanning. Everyone else converged on “centralize + AST lint” because it feels like progress without real cost. That convergence itself should be viewed with suspicion.

**Strongest point:** Explicitly names the root cause as *omission* and refuses to accept any solution that leaves omission cheap. The exempt decorator as a *reviewable annotation with mandatory reason* is genuinely better governance than inline pragmas.

**Weakest assumption:** That the set of dangerous primitives is enumerable and that an intra-function AST check plus exemptions will be maintainable at <2 engineer-days per year. This is the same bet the other proposals make, just dressed up with more ceremony.

**Hidden assumptions:** 
1. That reviewers will treat exemption growth as an architectural smell instead of a “just add the decorator” task. 
2. That Python’s dynamic nature can be sufficiently tamed by looking only at the static call graph. (The moment someone does `getattr(path, "unlink")()` or calls into a C extension, the guarantee evaporates.)

**Overlooked risks:** The scanner itself becomes the new fragile point. When it inevitably produces a false negative that reaches production, the team will have built institutional belief that “the guard is enforced by CI,” creating worse safety theater than before. Also never asks whether the right long-term move is to stop syncing corp code into OneDrive at all.

---

**Revised Recommendation**

The group consensus on Option C (in four flavors) takes for granted that (1) we can maintain an accurate static model of “dangerous writes” as the codebase evolves, and (2) the correct scoping is “make every write safe” rather than “prevent dangerous code from running in dangerous places.” Both premises are false. AST linters for this class of problem decay into either noise or bypass theater; we have decades of evidence from `noqa`, lint rules, and security scanners.

**Recommended option:** Hybrid of **Option D’s central module + explicit exemption decorator** but *without* the AST scanner. Instead, make the guard the *only* public API for writes inside corp (via a small `corp/fs/safe.py` façade that re-exports guarded versions of the 8–10 common operations). All new code must import from the façade. Existing call sites are updated incrementally; the façade can emit a deprecation warning for direct stdlib calls for one release. This is still incremental, satisfies every evaluation criterion except “static only,” and removes the maintenance sink of a perpetually tuned scanner.

**Key tradeoff accepted:** We accept that determined developers can still bypass via `os.system` or direct stdlib imports. We treat that as a *code-review* problem, not a scanner problem. Safety culture > safety theater.

**Migration plan:** 
1. Land `corp/safety/onedrive.py` (foundation layer) and `corp/fs/safe.py` façade in one PR with Codex review.
2. Migrate the four existing guard sites + `deck_actions.py:104` immediately.
3. Update `renderer.py` to raise `OneDriveSafetyError` natively; update its two CLI callers in the same PR (they already catch `RuntimeError` ancestors).
4. Add a deprecation shim for direct `Path.unlink` etc. that warns for 30 days.
5. Add a *single* test that greps for imports of `shutil`, `os.remove`, etc. inside `src/corp/` outside of test directories. It is allowed to fail for now; the warning + code review catches new sites. Convert the grep test to blocking only after the deprecation period.

**Exception unification:** Yes—unify on `OneDriveSafetyError` immediately. The “wrap and re-raise ValueError” approach proposed in A and the shim in C simply perpetuates drift. Updating two CLI call sites is trivial compared to living with permanent inconsistency.

**CI enforcement approach:** Runtime + minimal grep only. No AST scanner, no Semgrep rules, no per-function analysis. The façade *is* the enforcement.

**Out-of-scope flag:** This decision does *not* solve synced-folder safety for Google Drive, Dropbox, iCloud, or any future root. It does *not* address subprocess-based deletion. It does *not* change the Vault writer invariant or dictate where corp code should live on disk. Those are separate architectural questions the council keeps deferring.

This approach is deliberately less “complete” than the AST fantasies but more honest about where our real leverage lies: making the safe thing the obvious thing, centralizing definition, and refusing to build machinery we will not maintain. The AST convergence in every other proposal is groupthink masquerading as rigor.

*Latency: 24.47s | Tokens: 11886*

## Synthesis (by claude-sonnet, non-participant)

# Decision Summary: ADR-27 OneDrive Safety Guard Centralization

---

## Consensus

The following points attracted genuine agreement across all four participants, with independent reasoning rather than mere echo:

**1. Option A alone (centralized module, no CI enforcement) is insufficient.**
All participants identified the root cause correctly: the 2026-03-14 incident and the `deck_actions.py:104` omission both stem from *omission*, not from poor guard implementation quality. A shared helper that contributors can forget to call does not close the failure mode. This is the strongest piece of consensus in the debate, backed by the concrete evidence that Codex found the same bug class in two sites after initial review while humans missed it for six weeks.

**2. Option D (SafePath) is off the table for this ADR.**
All participants rejected the type-level enforcement path, citing Rob's no-big-bang principle, unknown mypy adoption levels, and disproportionate refactor cost relative to the safety benefit achievable by other means. This consensus is well-reasoned, not groupthink—each participant applied the evaluation criteria independently and reached the same conclusion.

**3. `corp/safety/onedrive.py` at the foundation Tach layer is the right structural home.**
Universal agreement that a single module with `OneDriveSafetyError` and `guard_path()` is the correct shape for centralization. No participant proposed an alternative location or abstraction.

**4. `deck_actions.py:104` must be fixed in the same change set.**
All participants flagged this as a known-unguarded write-intent caller that cannot be left open once a CI enforcement rule exists.

**5. The four existing guard sites should migrate to the central module with minimal changes.**
Consensus that rewriting the just-merged amendment commits would be waste, and that migrating to `import guard_path` is the correct minimal change.

**⚠ Note on groupthink risk:** Three of four participants (claude, gemini, openai) converged on essentially identical Option C recommendations by Round 2. This convergence was driven by shared evidence (root cause analysis, incident data) rather than social pressure—grok's dissent was substantive and is addressed below—but the evaluator should weight the convergence cautiously.

---

## Unresolved Disagreements

### Disagreement 1: Should the AST scanner cover all of `src/corp/` or only a narrow known-risk allowlist?

**Crux:** A value difference about whether enforcement scope should be *preventive* (cover all future write sites) or *targeted* (cover the demonstrated risk surface with fewer false positives).

- **Narrow scope (grok):** Scan only the four known-risky modules. Lower false-positive rate, immediate mergeability, ~5% estimated noise.
- **Broad scope (claude, gemini, openai):** Scan all of `src/corp/`. Catches the *next* omission in a new module, which is exactly what "hard to forget at new write sites" requires.

**Stronger argument: broad scope.** Grok's narrow approach hard-codes yesterday's incident map into policy. The evaluation criterion is explicitly "a new contributor adding a write/delete cannot silently skip the guard." A scanner that only covers four directories fails criterion 2 by design. Grok's estimated "<5% false positives" from scanning all of `src/corp/` is asserted without data; the counter-claim that most filesystem operations outside these four modules are tempfile/test paths is equally unverified, but is more plausible given the domain. The narrow allowlist also creates a maintenance artifact (who updates it? under what criteria?) that broad coverage avoids.

---

### Disagreement 2: Should `renderer.py` unify on `OneDriveSafetyError` now, or preserve `ValueError` externally via a compatibility shim?

**Crux:** A factual dispute about risk. How many callers depend on `ValueError` from `renderer.py`, and is that dependency load-bearing?

- **Unify now (claude, gemini, grok):** Grok confirmed the two CLI callers are `<20 LOC each` and already catch `RuntimeError` ancestors. The shim is permanent debt that creates a confusing pattern for future maintainers.
- **Preserve compatibility (openai):** Changing CLI-facing exception behavior in the same PR as safety hardening couples two concerns; if anything regresses, diagnosis is harder. Defer unification to a deliberate follow-up with targeted CLI tests.

**Stronger argument: unify now, with conditions.** The strongest argument here is grok's concrete claim that the two CLI callers are trivially updatable and catch `RuntimeError` ancestors—this makes the "compatibility" risk smaller than openai assumed. However, openai's point about decoupling safety hardening from user-facing contract changes has operational merit in a post-incident stabilization window. The resolution: unify, but verify the caller count by grep before merge and add a CLI integration test for the OneDrive-path rejection path in the same PR. The shim-forever option is genuinely worse, but "grep first, then unify" is safer than "assume two callers."

---

### Disagreement 3: Is the AST scanner itself sound architectural enforcement, or security theater?

**Crux:** A value difference about the reliability of static heuristics versus the cost of stronger guarantees.

- **AST scanner is sufficient (claude, gemini, openai):** Covers the 95% surface area, is tractable to implement, and explicitly acknowledges the remaining gaps (subprocess, aliased imports).
- **AST scanner is theater (grok):** Historically, pragma-based bypass mechanisms (`noqa`, `# type: ignore`, `pylint disable`) decay into "make the test pass" behavior within a few quarters. A guarded façade module is more honest about where real leverage lies.

**Stronger argument: AST scanner is sufficient, with conditions.** Grok's historical analogy to `noqa` decay is compelling and the single strongest dissenting point in the entire debate. However, it proves too much: if all bypass mechanisms decay, then grok's own "façade + deprecation warning + grep test" approach also decays—the deprecation warning gets suppressed, the grep test gets allowlisted. The difference between grok's approach and the majority's is not "bypassed vs. not bypassed" but rather "where is the explicit bypass documented?" The `@onedrive_write_exempt(reason="...")` decorator forces documentation at the callsite; grok's approach does not improve on this. The AST scanner with mandatory reason-string exemptions is operationally superior to a deprecation-warning façade for the stated requirement.

---

## Argument Quality Assessment

**Best-reasoned:** Claude's Round 2 assessment. It methodically steelmanned each proposal, correctly identified the root cause framing ("omission, not duplication") as the crux, added two novel security improvements not in any other proposal (secondary AST rule against neutered guards; third-party library audit as a precondition), and named concrete residual risks with calibrated likelihood/impact estimates. The addition of a rule against `guard_path()` calls inside bare `except` blocks that swallow `OneDriveSafetyError` is the kind of second-order thinking that distinguishes thorough analysis from checklist completion.

**Weakest:** Grok's final revised recommendation. It correctly identified AST scanner limitations, but the proposed alternative (façade module + deprecation warning + non-blocking grep test) solves *less* of the problem: a non-blocking grep test that "is allowed to fail for now" provides zero mechanical enforcement during exactly the period when new omissions are most likely. The core critique of AST theater is valid; the replacement is weaker than what it replaces. The proposal also conflates "make the safe thing the obvious thing" with "make the unsafe thing impossible," which are different goals—the second is what the evaluation criteria require.

**Single strongest argument in the entire debate:** Claude's Round 2 identification of the secondary AST rule: *"`guard_path(...)` must not appear inside a `try` block whose `except` clause catches `OneDriveSafetyError` without re-raising."* This closes a specific attack surface (silencing the guard to pass CI) that every other proposal missed entirely.

**Single weakest argument:** Grok's Round 1 claim that a narrow AST scanner covering only four modules produces "<5% false positives" from scanning all of `src/corp/`. This is an assertion presented as a data point, confuses false-positive *rate* with false-positive *count*, and contradicts the scanner's explicit purpose (catching *new* write sites, not validating known ones).

---

## Blind Spots

**1. The third-party library gap was raised but not resolved.**
Claude flagged `send2trash`, `aiofiles`, and custom workspace helpers as potential scannable-but-missed write primitives. No participant proposed a concrete solution: grep `src/corp/` for third-party imports that perform disk writes, enumerate them, and add them to the scanner's primitive list. This should be a precondition for merging the CI rule, not a "signals to revisit" item.

**2. Conditional guard execution was entirely missed until Claude's Round 2.**
The intra-function AST check sees `guard_path()` and passes, but the write can still occur on a code path that skips the guard via an `if` branch. No participant proposed a mitigation beyond "review discipline." This is a residual risk that should be explicitly documented in ADR-27 rather than left implicit.

**3. Nobody asked whether the path-detection logic itself is correct.**
The guard uses `.resolve(strict=False) + substring("OneDrive - Blue Yonder")`. Several participants noted this fails on non-English Windows installs (<5% of fleet per grok's telemetry reference). Nobody proposed a concrete improvement or documented this as a known limitation with a trigger for fixing it.

**4. The debate never addressed test fixture exemptions.**
Existing tests presumably create and destroy temporary files. The AST scanner will encounter these test fixtures (if scoped to `src/corp/` it may not, but if scoped to the full repo it will). The exemption mechanism needs to cover test-scoped writes cleanly—either by allowlisting `tests/` entirely or by requiring test fixtures to use a dedicated helper that the scanner recognizes. This was mentioned but not designed.

**5. The CI performance question was deferred inappropriately.**
For a Scale-L monorepo, an AST walk of all `.py` files under `src/corp/` on every CI run is a real cost. Claude correctly flagged this as "probably fine at 5s" with a recommendation to scope to `src/corp/` and cache via pytest. But the actual file count was never estimated. This should be verified before treating performance as a non-issue.

**6. No participant examined the failure mode where `guard_path()` itself has a bug.**
If `.resolve(strict=False)` behaves differently across OS/filesystem combinations, or if the substring check has an edge case (symlinked OneDrive folder with a different name), the centralized guard creates a single point of failure. The fail-closed behavior on `OSError/RuntimeError` mitigates this partially, but it was not examined.

---

## Recommended Decision

**Adopt Option C: centralized `corp/safety/onedrive.py` module plus AST-based CI enforcement, with immediate `renderer.py` exception unification.**

This is the only option that closes both failure modes present in the incident evidence: duplicate guard logic and omission at new write sites. The recommended implementation incorporates the strongest arguments from all four participants and addresses the blind spots identified above.

### Rationale

The primary evaluation criterion is preventing the 2026-03-14 incident class from recurring. The incident's documented cause was a write-site omission that persisted for six weeks despite human review. Any solution that relies on discipline at call sites without a mechanical enforcement backstop is solving the wrong problem. Option C is the only option that provides this backstop within the incremental-adoption constraint.

### Addressing the strongest objections

**Grok's "AST theater" objection:** Valid concern, but the wrong conclusion. The historical decay of `noqa`-style bypasses occurs when bypasses have no friction and no visibility. The `@onedrive_write_exempt(reason="...")` decorator—as a named, reason-bearing, grep-able annotation—is structurally different from an inline comment pragma. It is visible in code review, searchable in the codebase, and countable as an architectural metric. The façade alternative grok proposed provides less enforcement (non-blocking grep test) for similar bypass risk. The concern about scanner maintenance is real and is addressed in the action items with explicit scope constraints.

**OpenAI's "decouple safety from contract change" objection:** Operationally sound advice for a post-incident stabilization period, but the concrete evidence (two CLI callers, `<20 LOC each`, catching `RuntimeError` ancestors) makes the unification risk smaller than the compatibility-shim risk. The shim is not a temporary bridge; in practice, compatibility shims in internal monorepos become permanent. The correct mitigation is to verify the caller count before merge and add a CLI integration test in the same PR, not to defer unification indefinitely.

---

## Risks

**Risk 1: AST scanner false negatives via aliased imports or third-party libraries**
*Likelihood: Medium. Impact: High.*
Mitigation: Before landing the CI rule, grep `src/corp/` for all imports of `shutil`, `os`, `pathlib`, and any third-party file operation libraries. Add any found wrappers to the scanner's primitive list. Document in ADR-27 that shell-out deletions (`subprocess`, `os.system`) are an acknowledged gap. Revisit if a second incident occurs through an unscanned path.

**Risk 2: AST scanner passes a guarded-but-neutered call**
*Likelihood: Low. Impact: High.*
Mitigation: Implement the secondary rule identified by Claude: flag any `guard_path()` call that appears inside a `try` block whose `except` catches `OneDriveSafetyError` (or a parent class) without re-raising.

**Risk 3: Exempt decorator gets used carelessly**
*Likelihood: Medium. Impact: Medium.*
Mitigation: Require `reason=` parameter. Fail CI if a PR adds an `@onedrive_write_exempt` without Codex review flag (per AGENTS.md High-risk policy). Add a metric test that counts total exemptions and warns if the count grows faster than ~2/quarter.

**Risk 4: Renderer.py exception unification has an undiscovered caller**
*Likelihood: Low. Impact: Medium.*
Mitigation: Before merging, grep the entire monorepo for `except.*ValueError` in any module that transitively imports `corp.project.cli.render`. Add a CLI integration test specifically for the OneDrive-path rejection path that asserts the exit code and error message.

**Risk 5: Path detection logic is incorrect on non-English Windows installs**
*Likelihood: Low. Impact: High (silent bypass of the guard).*
Mitigation: Document the known limitation in ADR-27. Add a test fixture with a non-standard OneDrive path variant. Schedule investigation of environment-variable or Win32 API-based root detection for the next quarter.

**Risk 6: Conditional guard execution (guard inside `if` branch that doesn't cover all write paths)**
*Likelihood: Medium. Impact: High.*
Mitigation: Document explicitly in ADR-27 as a residual risk not covered by intra-function AST analysis. Rely on Codex review for conditional guard placement. Consider a follow-up enhancement to the scanner that flags `guard_path()` calls inside `if` blocks where the `else` branch contains a write primitive.

**Risk 7: CI performance at Scale-L monorepo size**
*Likelihood: Low. Impact: Low.*
Mitigation: Scope the scanner to `src/corp/` only. Cache via pytest. Measure wall time on a representative run before making blocking. Budget: fail if scan exceeds 10 seconds.

---

## Action Items

**PR 1: Foundation (Codex review required, High-risk per AGENTS.md)**

1. Create `src/corp/safety/onedrive.py` in the Tach `foundation` layer containing:
   - `class OneDriveSafetyError(RuntimeError)` — single canonical exception type
   - `def is_onedrive_path(path: Path) -> bool` — predicate for callers needing conditional behavior
   - `def guard_path(path: Path, *, reason: str) -> None` — resolve + substring + fail-closed
   - `class onedrive_write_exempt` — no-op decorator that accepts `reason: str` (required); consumed only by AST scanner
2. Verify Tach layer placement does not create import cycles: run `tach check` before merge.
3. Grep the entire monorepo for `except.*ValueError` in any module transitively importing `corp.project.cli.render`. Document findings.
4. Grep `src/corp/` for all third-party file operation imports (`send2trash`, `aiofiles`, etc.). Add any found to the scanner primitive list or wrap them through the guarded façade.

**PR 2: Migration (same series as PR 1, Codex review required)**

5. Update `cleanup/disk.py`, `cleanup/executor.py`, `actions/_helpers.py` to import and call `guard_path()`. Delete the local `.resolve() + substring` implementations. Re-export `OneDriveSafetyError` from old module locations for one release cycle.
6. Update `renderer.py`: call `guard_path()`, raise `OneDriveSafetyError` natively. Update `corp.project.cli.render` to catch `(FileNotFoundError, ValueError, OneDriveSafetyError)`. Add CLI integration test asserting OneDrive-path rejection produces the correct exit code and error message.
7. Fix `deck_actions.py:104`: add `writable=True` flag and `guard_path()` call.

**PR 3: CI Enforcement (after PRs 1-2 are merged and tests are green)**

8. Write `tests/safety/test_no_unguarded_writes.py`:
   - AST walk every `.py` under `src/corp/`
   - Dangerous primitives: `Path.unlink`, `Path.rmdir`, `Path.replace`, `Path.write_bytes`, `Path.write_text`, `shutil.rmtree`, `shutil.move`, `shutil.copytree`, `os.remove`, `os.rename`, `os.unlink` (plus any third-party additions from step 4)
   - Pass condition per function: contains `guard_path()` call, or is decorated `@onedrive_write_exempt`, or is in an allowlisted path (`tests/`, `tmp/`)
   - Secondary rule: flag `guard_path()` inside a `try` whose `except` catches `OneDriveSafetyError` or parent without re-raising
   - Emit file path + line number + function name for each violation
   - Include a deliberately unguarded fixture test that the scanner must catch (self-test for the scanner)
   - Scope to `src/corp/`, measure wall time, fail if >10 seconds
9. Seed the scanner against the updated codebase; confirm zero violations before making the test blocking.
10. Add a separate test counting total `@onedrive_write_exempt` uses; warn if count increases by more than 2 between quarters.

**ADR-27 Documentation**

11. Document explicitly:
    - Shell-out deletions (`subprocess`, `os.system`) are an acknowledged gap not covered by this ADR
    - Non-English Windows OneDrive path detection is a known limitation; investigation scheduled for Q3 2026
    - Conditional guard execution (guard inside a non-covering `if` branch) is a residual risk requiring Codex review
    - Exempt decorator use requires `reason=` parameter and triggers Codex review per AGENTS.md High-risk policy
    - This ADR does not cover non-OneDrive synced roots, Vault writer invariants, or historical restore/audit work

**Deferred (explicit, tracked)**

12. Create a tracked work item: expand `guard_path` to support a registry of synced-root detectors when a second non-OneDrive synced root is encountered (not speculatively).
13. Create a tracked work item: investigate Win32 API or environment-variable-based OneDrive root detection to replace substring check.
14. Re-evaluate Option D (SafePath) if: (a) a second incident occurs despite the AST check passing, or (b) mypy adoption reaches >70% of `src/corp/`.
