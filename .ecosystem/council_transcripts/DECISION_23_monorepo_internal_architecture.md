# AI Council Debate: # AI Council Debate #23 — Monorepo Internal Architecture Refactoring

**Repo:** 

**Date:** 2026-03-28 23:45:22
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 267.7s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\PROMPT_council23_architecture_debate.md
**Cost:** ~$0.4563 (84,721 tokens)

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
I recommend enforcing strict process isolation by eliminating cross-package imports, mitigating attack surfaces by centralizing duplicate LLM parsing logic, and drastically reducing the blast radius of the CLI by decoupling it into modular command groups. 

## Alternatives Considered
- **Splitting `corp-by-os` into domain packages (Q2 Option B):** Rejected. Breaking a 15,724-line package into multiple packages introduces massive integration, deployment, and dependency-resolution risks. The security/architectural gain is negligible compared to the operational blast radius of fundamentally altering the monorepo's deployment topology.
- **Formalizing the `cke_client.py` boundary violation (Q1 Option A):** Rejected. Allowing a lazy internal import across package boundaries weakens defense-in-depth. It creates an untracked execution path that bypasses established API contracts, meaning an unexpected failure or compromised payload in CKE internals could directly crash the `overnight` orchestration layer.

## Decision Criteria
1. **Blast Radius Minimization:** Containment of potential bugs, compromised dependencies, or runtime failures to the smallest possible domain.
2. **Strict API Boundary Enforcement:** Maintaining pure isolation between orchestration (vault) and extraction engines.
3. **Attack Surface Reduction:** Elimination of unmonitored code paths (dead code) and consolidation of high-risk parsing logic.
4. **Constraint Checklist:** Zero changes to user-facing CLI behavior (`corp <command>`), and zero degradation to shared testing utility.

## Assumptions
1. The performance overhead of process instantiation (subprocess calls) for `overnight/cke_client.py` is entirely acceptable, given it operates as an asynchronous/batch process.
2. `corp-os-meta` is guaranteed to be deployed and available in all environments where CKE runs, ensuring centralized utilities don't cause `ModuleNotFoundError` during extraction.
3. Git history is secure, immutable, and easily accessible, rendering the retention of dead code in active branches completely unnecessary.

## Recommendation
**What to do now:**
- **Q1 (Boundary Violation): Eliminate.** Refactor `cke_client.py` to use subprocess calls to invoke CKE. Mimic the proven `corp-project-extractor` pattern to enforce a clean, isolated boundary.
- **Q2 (CLI Monolith): Split into Click command groups (Option A).** Break the 3,573-line `cli.py` into `cli/ingest.py`, `cli/retrieve.py`, etc. A master `cli.py` will import these groups to satisfy the constraint of maintaining the `corp <command>` interface. 
- **Q4 (Duplication): Centralize (Option A).** Delete CKE's `parse_llm_json`. Move `normalize_string_list` and the extraction-specific error handling into `corp-os-meta/utils.py` using parameterized flags, and enforce a single canonical parser.
- **Q5 (Dead Code): Delete (Option A).** Immediately remove `clean_kb.py`, `scan_kb.py`, `kb_to_markdown.py`, and `_paths.py` from `corp-rfp-agent`.

**What not to do now:**
- Do not attempt to flatten justifiable functional directories like `extraction/` (Q3 Option A/B). 
- Do not waste time renaming dataclasses (Q4 Option C) until runtime type-checking or serialization actually demands it. 

**What to defer until later:**
- **Q3 (Unnecessary Nesting): Selective flatten (Option B).** Defer flattening the 2-file sub-packages (`doctor/`, `freshness/`) until after the CLI monolith refactor is complete and stabilized, to prevent compounding import-resolution blast radii.

## Rationale
- **Isolation of Execution State (Q1):** Directly importing `CKE` internals into `corp-by-os` shares memory and execution state. If malicious or malformed input enters the `overnight` batch, a vulnerability in CKE could execute within the orchestration trust zone. Subprocesses enforce OS-level memory and runtime isolation.
- **Limiting Import Contagion (Q2):** A monolithic CLI with 71 commands across 18 domains requires loading dependencies for all domains at runtime. A vulnerable dependency or syntax error in a rarely used domain (e.g., `doctor`) can crash the critical path for `ingest`. Command groups lazily isolate these risks.
- **Consolidating Parsing Attack Surfaces (Q4):** LLM JSON parsing is inherently dangerous and a prime vector for injection or denial-of-service (e.g., deeply nested JSON). Maintaining two implementations (67 lines vs 97 lines) guarantees drift; a security patch applied to one will inevitably be missed in the other.
- **Auditable Baselines (Q5):** Dead code is an unmonitored attack surface. It rusts, avoids test coverage, and creates false positives during vulnerability scanning and dependency audits. Deletion provides immediate security hygiene.

## Trade-offs
- **Execution Overhead:** Enforcing a subprocess boundary for `cke_client.py` trades slightly increased CPU/memory overhead per invocation for strict architectural isolation.
- **Initial Refactoring Friction:** Decoupling `cli.py` into 8-10 files will cause temporary merge conflicts for any active PRs touching CLI commands, requiring coordination among internal developers.

## Risks
- **Risk:** The CKE subprocess call in `overnight` fails silently or obfuscates error tracebacks, complicating incident response. 
  - *Mitigation:* Implement rigorous `stdout/stderr` capturing and structured logging at the subprocess boundary. (Likelihood: Medium, Impact: High).
- **Risk:** Centralizing `parse_llm_json` breaks CKE due to subtle discrepancies in how the 30 extra lines handle edge cases. 
  - *Mitigation:* Deploy extensive unit tests covering known failure modes (hallucinated keys, malformed brackets) against the new unified function in `corp-os-meta` before integrating it back into CKE. (Likelihood: Low, Impact: High).

## Signals to Revisit
- If batch processing times for `overnight` jobs violate internal SLAs by >10% due to subprocess spin-up overhead, we must revisit Q1 to design a formal, authenticated internal API or RPC layer rather than reverting to direct imports.
- If Pydantic or external serialization boundaries begin throwing type conflicts due to the 10 dataclass name collisions, we will revisit Q4 and enforce strict namespace prefixing (e.g., `IngestManifest` vs `CKEManifest`).

*Latency: 37.89s | Tokens: 7084*

### Deepseek (deepseek-reasoner)

## Position
Split the CLI into domain groups, flatten shallow sub-packages, eliminate the boundary violation via subprocess, centralize the utility function, and delete dead code. These changes collectively reduce cognitive load and maintain clean boundaries without disrupting users or tests.

## Alternatives Considered
- **Extract overnight into separate package (Q1-C)**: Rejected because it adds package overhead for a single violation; subprocess keeps separation cleaner.
- **Split corp-by-os into domain packages (Q2-B)**: Rejected as overkill; Click groups achieve 80% of organizational benefit with 10% of the refactoring cost.

## Decision Criteria
1. Maintain clean package boundaries (no runtime coupling, especially for CKE).
2. Minimize user-facing changes (CLI commands and flags unchanged).
3. Reduce cognitive overhead for developers (smaller files, flatter structure).
4. Preserve test stability (no broken imports or behavior changes).
5. Avoid over-engineering (solve today’s problems, not hypothetical ones).

## Assumptions
1. The overnight batch process is not latency-sensitive (tolerates subprocess overhead).
2. Developers can update import paths during flattening without breaking existing work in progress.
3. The 71 CLI commands are logically groupable by domain (ingest, retrieve, etc.) without ambiguous overlaps.

## Recommendation
- **Q1**: Eliminate boundary violation — refactor `cke_client.py` to use subprocess calls.
- **Q2**: Split CLI into Click command groups — create 8-10 domain-specific files (ingest.py, retrieve.py, etc.) under a `cli/` module.
- **Q3**: Selective flatten — merge `doctor/` and `freshness/` into parent, keep `extraction/` hierarchy.
- **Q4**: Centralize `parse_llm_json` into corp-os-meta and rename colliding dataclasses (e.g., `CkeClassification`).
- **Q5**: Delete dead code — remove the four unused files.

**Do now**: Execute Q1, Q2, Q3, Q5 concurrently; they are independent and low-risk.  
**Do not now**: Restructure packages or change CLI command signatures.  
**Defer**: Further flattening of `extraction/` or renaming beyond the 10 colliding dataclasses.

## Rationale
- **Q1 subprocess adds ~50-100ms per CKE call** — acceptable for overnight batch (hours). Maintaining pure process isolation is worth the penalty.
- **Q2 splitting reduces cli.py from 3,573 to ~400 lines per file** — below the 1,000-line “graspability” threshold. Lazy loading within groups keeps CLI startup under 200ms.
- **Q3 flattening removes two unnecessary `__init__.py` files and reduces max depth from 6 to 5** — 40% of files move closer to root, improving IDE navigation.
- **Q4 centralization removes 97 lines of duplicate code** — CKE already imports corp-os-meta; adding `normalize_string_list` there is a 10-line change.
- **Q5 deletion removes 4 files (~800 lines)** — reduces `ls -R` noise and eliminates false positives for unused code detection.

## Trade-offs
- **Q1**: Adds subprocess overhead (~2x slower for CKE calls) and complicates error handling (exit codes vs. exceptions).
- **Q2**: Introduces a new `cli/` directory and 8 more files — slightly more complex import graph within corp-by-os.
- **Q3**: Breaks git blame history for moved files; requires updating 15-20 import statements.
- **Q4**: Makes corp-os-meta slightly heavier (adds CKE-specific error handling); tightens coupling between CKE and utilities.

## Risks
- **Q1 subprocess serialization bugs** (likelihood: medium, impact: medium) — mitigate with integration tests for each CKE invocation path.
- **Q2 Click group registration errors** (likelihood: low, impact: high) — mitigate by preserving the existing CLI test suite and adding a smoke test for all 71 commands.
- **Q3 import updates missed in tests** (likelihood: low, impact: low) — mitigate by running a full test suite after changes and using `grep -r "from doctor"`.
- **Q4 breaking CKE error handling** (likelihood: low, impact: medium) — mitigate by moving `normalize_string_list` with its existing tests and adding a compatibility wrapper during transition.

## Signals to Revisit
- **CLI startup time exceeds 500ms** — reconsider lazy loading strategy or merge some groups.
- **CKE subprocess calls become a performance bottleneck** (e.g., overnight batch doubles in duration) — revisit formalizing the dependency with optional imports.
- **New boundary violations appear** (more than one per quarter) — enforce stricter import linting and consider package extraction.

*Latency: 66.62s | Tokens: 5400*

### Openai (gpt-5.4)

## Position
Adopt the smallest set of structural changes that materially improve maintainability now: eliminate the one package-boundary violation via subprocess, split `corp-by-os/cli.py` into internal Click command-group modules behind the existing `corp <command>` surface, selectively flatten only obviously unjustified subpackages, centralize the duplicated utility in `corp-os-meta`, rename only the most confusing colliding dataclasses opportunistically, and delete confirmed dead code in `corp-rfp-agent`.

## Alternatives Considered
1. **Broader package restructuring inside `corp-by-os` or extracting `overnight/` into a new package now**  
   Rejected because it creates packaging, dependency, release, and import churn disproportionate to the actual findings. The audit says package count is not the problem; internal sprawl is. A team can ship CLI modularization and one boundary fix in days to low weeks, whereas a new package split is more likely a multi-week migration with regression risk.

2. **Minimal-touch approach: document the current state, keep direct imports/largely keep `cli.py`, and avoid structural refactors**  
   Rejected because it preserves the highest-leverage problems: the only real architecture violation remains, and a 3,573-line CLI file with 71 commands continues to impose daily change friction. This would optimize for short-term safety while knowingly leaving the main maintainability issue untouched.

## Decision Criteria
1. **Can a small team implement and operate this in the available time without destabilizing core workflows?**
2. **Preserve existing user-facing behavior, especially `corp <command>` compatibility for all 71 commands.**
3. **Restore and maintain clean package boundaries, since the audit found boundaries are otherwise healthy.**
4. **Target the actual source of navigability pain: `corp-by-os` internal sprawl, not package count.**
5. **Prefer low-churn, high-yield changes over theoretically cleaner but organizationally heavier redesigns.**

## Assumptions
1. `corp-by-os overnight` flows do not require in-process CKE calls for latency-sensitive interactive UX; subprocess overhead is acceptable for batch-style work.
2. The current test coverage or manual validation is sufficient to safely move Click command definitions across modules without changing command names/options.
3. `corp-os-meta` is a stable enough dependency to serve as the canonical home for shared parsing utilities used by CKE.
4. The dead `corp-rfp-agent` scripts are truly unused in any operational runbooks; if they are still manually invoked, deletion should be replaced with archival.

## Recommendation
**What to do now**
- **Q1:** Choose **Eliminate**. Refactor `overnight/cke_client.py` to invoke CKE through subprocess/CLI or another process boundary, matching the established ecosystem pattern.
- **Q2:** Choose **Split into Click command groups**. Break `corp-by-os/cli.py` into domain modules such as `cli/ingest.py`, `cli/retrieve.py`, `cli/overnight.py`, etc., with a thin root `cli.py` that registers groups/commands and preserves all current command names and entrypoints.
- **Q3:** Choose **Selective flatten-plus-one obvious cleanup**: merge `doctor/` and `freshness/` into simpler root-level modules, and also flatten `extraction/non_project/` upward because depth-6 for 3 files is unjustified. Do not broadly flatten everything else.
- **Q4:** Choose **Centralize** for `parse_llm_json`: make `corp-os-meta` the single implementation, move `normalize_string_list` there if still needed, and have CKE import it. For dataclass collisions, do **targeted renames only where cross-package confusion is frequent**, not a repo-wide renaming campaign.
- **Q5:** Choose **Delete** confirmed dead scripts in `corp-rfp-agent`.

**What not to do now**
- Do not split `corp-by-os` into more packages.
- Do not create a new `corp-overnight` package.
- Do not keep the direct CKE import violation and “document it.”
- Do not attempt a full domain-model naming overhaul across all 10 dataclass collisions in one pass.
- Do not change user-facing CLI syntax.

**What to defer until later**
- Revisit extracting `overnight` into its own package only if it grows materially or gains distinct ownership/runtime needs.
- Consider stronger lazy-loading for CLI modules later if startup time becomes a measured issue after modularization.
- Consider systematic dataclass naming conventions as part of a future repo-wide API hygiene pass, ideally alongside package docs and type exports.

## Rationale
- **The only true architecture violation is Q1**, so it should be fixed cleanly rather than normalized. One exception tends to become precedent; today it is 1 violation, but documenting it invites more. A subprocess boundary costs likely tens to hundreds of milliseconds per invocation, which is acceptable for overnight/batch flows and far cheaper than introducing a seventh package.
- **`cli.py` is the biggest maintainability hotspot by far**: 3,573 lines and 71 commands across 18 domains in one file. Splitting into ~8–10 modules of ~300–400 lines each reduces merge-conflict likelihood, improves code ownership, and lets developers find command code in minutes instead of hunting a monolith.
- **Package restructuring is the wrong level of intervention** given the audit result. `corp-by-os` is 15,724 lines, but the report explicitly says the 6-package split is defensible and subprocess boundaries are otherwise clean. Internal modularization addresses the real pain without introducing packaging/release complexity.
- **Selective flattening captures most of the readability gain with limited churn**. Moving two 2-file subpackages and a 3-file depth-6 subtree is low-risk and high-signal; flattening everything would create import churn without equivalent benefit.
- **Centralizing `parse_llm_json` removes real duplication while respecting the declared utility hierarchy**. Since CKE already depends on `corp-os-meta`, this is near-zero architectural risk. By contrast, renaming every colliding dataclass would touch many call sites for mostly cosmetic benefit; do that only where confusion is repeatedly causing mistakes.

## Trade-offs
- **Subprocess-based CKE invocation is less elegant and somewhat slower** than in-process imports. Expect per-call overhead roughly in the **50–300 ms** range depending on startup/environment; for overnight/batch work this is acceptable, but it is still a real efficiency loss.
- **CLI modularization increases file count** from 1 large CLI file to perhaps **8–10 modules plus a thin root**, which slightly raises navigation overhead for someone who wants “everything in one place.”
- **Selective rather than comprehensive flattening leaves some structural inconsistency behind**, because not every nested package will be normalized now.
- **Targeted dataclass renames leave some collisions in place**, so confusion is reduced rather than fully eliminated.
- **Deleting dead code removes easy in-repo historical reference**, relying on Git history instead.

## Risks
- **Risk: subprocess migration for `overnight/cke_client.py` breaks behavior parity with the current in-process path.**  
  Likelihood: Medium. Impact: Medium-High.  
  Mitigation: define a thin adapter around the subprocess interface, preserve existing inputs/outputs, and validate against a representative overnight run before removal of the old path.

- **Risk: splitting the CLI accidentally changes command registration, help text, or option parsing.**  
  Likelihood: Medium. Impact: High.  
  Mitigation: snapshot current `corp --help` and key subcommand help outputs; add smoke tests for all 71 commands at the registration/help level even if not full behavioral tests.

- **Risk: import-path changes from flattening break internal imports or stale docs/scripts.**  
  Likelihood: Medium. Impact: Medium.  
  Mitigation: keep flattening limited to the three clearly unjustified areas, update imports atomically, and provide temporary compatibility imports only if test failures show they are needed.

- **Risk: centralizing `parse_llm_json` subtly changes error behavior in CKE.**  
  Likelihood: Low-Medium. Impact: Medium.  
  Mitigation: merge the extra behavior CKE actually relies on into the canonical implementation before deleting the duplicate; add a couple of fixture-based parsing tests from both call contexts.

- **Risk: “confirmed dead” `corp-rfp-agent` scripts are still used ad hoc by one person a few times a year.**  
  Likelihood: Low. Impact: Low-Medium.  
  Mitigation: verify via repo search and owner confirmation before deletion; if uncertainty remains, archive instead of delete.

## Signals to Revisit
- `overnight` usage becomes interactive/latency-sensitive enough that subprocess overhead is materially harming operators, or CKE integration requires richer in-process APIs not exposed by CLI boundaries.
- `corp-by-os` continues to grow rapidly after CLI modularization—e.g. exceeds ~20k source lines or multiple domains gain separate ownership—making a package split newly justified.
- CLI startup/help performance regresses measurably after modularization, suggesting lazy loading should be introduced.
- Dataclass naming collisions cause repeated bugs, onboarding confusion, or import aliasing churn, indicating a repo-wide naming standard is now worth the migration cost.
- The supposedly dead `corp-rfp-agent` scripts are shown to still be referenced in operations or documentation.

*Latency: 33.94s | Tokens: 4440*

### Grok (grok-4.20-beta)

**## Position**
Eliminate the overnight boundary violation via subprocess (Q1B), split cli.py into Click command groups across files (Q2A), selectively flatten only the unjustified 2-file sub-packages (Q3B), centralize parse_llm_json while renaming all 10 colliding dataclasses (Q4A+C), and delete the confirmed dead code (Q5A).

**## Alternatives Considered**
- Full domain package split (Q2B): Rejected because it directly violates the already-decided "keep 6 packages" constraint and would require reworking the entire 15,724-line corp-by-os surface that the audit explicitly called defensible at the package boundary level.
- Formalize the CKE violation as a special case (Q1A): Rejected because it normalizes the single existing Python-level boundary violation, creating a precedent that undermines the audit's core finding that all other packages already use correct subprocess patterns.

**## Decision Criteria**
- Strict adherence to clean package boundaries and the explicit constraint that CKE remains a pure extraction engine with no orchestration knowledge.
- Reduction of cognitive load in the 53% corp-by-os code base (especially the 3,573-line cli.py) without any user-visible `corp` CLI changes.
- Minimization of duplication and name collisions that harm navigability.
- Respect for implementation realism and test stability (all imports must be updated, no broken tests).
- Low-stakes decisions should be resolved quickly rather than over-engineered.

**## Assumptions**
- Subprocess call overhead for overnight batch jobs is acceptable (estimated <3 seconds added latency on typical workloads).
- The existing lazy `is_available()` guard pattern can be replaced with a clean subprocess wrapper without introducing new runtime failures.
- Developers will correctly update imports during flattening and that the 10 dataclass collisions have no hidden semantic coupling across packages.
- The 6-package structure remains fixed; any recommendation that increases package count is out of scope.

**## Recommendation**
- **What to do now:** Create cli/ingest.py, cli/retrieve.py, cli/overnight.py, etc. (8-10 files) using Click group patterns so `corp` entrypoint still works; replace overnight/cke_client.py with a subprocess wrapper that calls the official CKE CLI; merge doctor/ and freshness/ into root-level modules; move normalize_string_list to corp-os-meta/utils.py and delete the CKE copy; rename all 10 colliding dataclasses to package-qualified names (CKEClassification, IngestManifest, etc.); delete the four dead files in corp-rfp-agent.
- **What not to do now:** Do not add CKE as a dependency, do not create a corp-overnight package, do not leave cli.py as a single 3,573-line file, do not keep duplicate parse_llm_json implementations.
- **What to defer until later:** Full extraction/non_project/ hierarchy cleanup, any performance optimization of the new subprocess calls, and potential future extraction of high-cohesion domains once the CLI split has been in production for one quarter.

**## Rationale**
- cli.py split reduces the largest file from 3,573 to ~350 lines average across 9 files, directly attacking the root cause of sprawl identified in the audit (53% of all code).
- Subprocess boundary for overnight preserves the audit's "only one violation" finding and prevents future developers from treating CKE internals as public API.
- Selective flattening of doctor/ and freshness/ reduces max import depth from 6 to 4 while leaving the 8-file extraction/ hierarchy intact, balancing navigability against unnecessary import churn.
- Centralizing parse_llm_json + renaming dataclasses eliminates the 10 name collisions that currently make IDE navigation ambiguous across 29.6k lines of code.
- Dead code deletion removes 4 files that have zero references post-migration, reducing repo noise with zero runtime risk.

**## Trade-offs**
- Accept ~1-3 seconds of added latency on overnight jobs (based on corp-project-extractor CLI timing) in exchange for zero Python-level coupling. 
- Incur one-time import refactoring cost (~180 lines for cke_client + ~40 import statements for flattening) but gain long-term boundary enforcement.
- Give up the convenience of direct calls for the single special-case overnight path.

**## Risks**
- Subprocess wrapper fails to handle all CKE error cases (likelihood: medium, impact: high on overnight batch). Mitigate with 100% test coverage of the wrapper against current cke_client.py behavior.
- Missed import during flattening breaks tests (likelihood: high, impact: medium). Mitigate by running the full test suite after each sub-package merge.
- Renamed dataclasses cause temporary confusion in cross-package code reviews (likelihood: low, impact: low). Mitigate with a 2-week deprecation alias period.

**## Signals to Revisit**
- Overnight batch jobs show >5 seconds consistent regression in production metrics.
- New cross-package Python imports appear in the next audit (violating the "only one violation" state).
- corp-by-os source lines drop below 40% of total after this cleanup, or CLI command usage patterns shift dramatically (>2x growth in any domain).
- The decided Click CLI for corp-rfp-agent reveals unexpected interactions with the new command groups.

*Latency: 23.17s | Tokens: 6578*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary lens is defense-in-depth, strict API boundaries, and blast radius containment. A monolithic CLI that loads 18 domains simultaneously is a supply chain vulnerability waiting to happen. An extraction engine sharing memory with an orchestration vault is a critical boundary violation. 

Here is my evaluation of the council’s proposals, followed by my binding architectural decision.

---

### Evaluation of Proposal A

**Steelman first:** If developer velocity and immediate cognitive relief are the highest priorities, this proposal perfectly balances reducing file sizes with maintaining existing workflows. It correctly identifies that Click groups solve the monolith problem natively without heavy architectural shifts.

**Your assessment:** Partially agree. I agree with the decisions for Q1, Q2, and Q5. However, I disagree with the partial rename of dataclasses in Q4 and the failure to flatten the depth-6 `extraction/non_project` path in Q3. 

**Strongest point:** Pointing out that centralization of `parse_llm_json` removes a duplicated attack surface. Having two different functions parsing untrusted LLM output guarantees that an injection patch applied to one will be missed in the other.

**Weakest assumption:** Assuming lazy loading within Click groups natively keeps CLI startup under 200ms without explicit click-plugins or manual lazy patterns. 

**Hidden assumptions:** Assumes `extraction/` folder structure is justified simply because it has 8 files, ignoring whether those 8 files actually require a multi-level hierarchy or just represent hidden, unreviewed code paths.

**Overlooked risks:** Passing potentially sensitive vault orchestration data via CLI args to the new CKE subprocess might expose data in OS process lists or logs if not carefully handled.

---

### Evaluation of Proposal B

**Steelman first:** If our primary objective is to harden the monorepo against both malicious inputs and internal dependency poisoning, this is the exact blueprint. It treats memory isolation, execution state, and single-chokepoint parsing as non-negotiable security primitives.

**Your assessment:** Strongly Agree. This proposal perfectly aligns with my blast-radius and defense-in-depth priorities. It recognizes that Q1 is not just a "clean code" issue, but a trust-zone violation.

**Strongest point:** The explicit justification for Q1: "If malicious or malformed input enters the overnight batch, a vulnerability in CKE could execute within the orchestration trust zone." This is the exact reason we enforce OS-level memory isolation between orchestration and extraction.

**Weakest assumption:** The assumption that unit tests can confidently catch all subtle discrepancies between the two `parse_llm_json` implementations. LLM output is inherently non-deterministic, and parsing edge cases are notoriously difficult to fully cover with static tests.

**Hidden assumptions:** Assumes CKE's extraction-specific error handling can be parameterized into `corp-os-meta` without polluting the meta package with domain-specific CKE logic.

**Overlooked risks:** By deferring Q3 (flattening), it allows unnecessarily deep directories to persist, which often become dark corners where unreviewed, experimental, or vulnerable code hides from casual code-review scrutiny.

---

### Evaluation of Proposal C

**Steelman first:** If navigating the codebase and resolving IDE type-hinting ambiguity is the primary bottleneck for developers, renaming all 10 colliding dataclasses and selectively flattening the most trivial folders will immediately resolve internal friction without changing external behavior.

**Your assessment:** Disagree with Position. While I agree with the boundary enforcement (Q1/Q2), I strongly object to a mass renaming of 10 dataclasses (Q4) that the audit explicitly noted as "harmless at runtime." 

**Strongest point:** Explicitly calling out that formalizing the CKE violation (Q1A) "creates a precedent that undermines the audit's core finding." Security postures degrade through documented exceptions.

**Weakest assumption:** Assumes developers will cleanly rename 10 core domain objects across 6 packages without breaking JSON serialization boundaries, database mappings, or downstream scripts that expect specific string keys.

**Hidden assumptions:** Assumes the dataclass name collisions are actually causing harm beyond minor IDE ambiguity.

**Overlooked risks:** Mass renaming of dataclasses introduces massive regression risk for zero security or isolation gain. It violates the principle of minimizing unnecessary blast radius during refactoring.

---

### Evaluation of Proposal D

**Steelman first:** If we must execute this cleanup in a short window with minimal regression risk, this proposal strips away the cosmetic chores (broad renaming, broad flattening) and surgically targets only the highest-leverage architectural violations.

**Your assessment:** Agree. This is a highly operational, pragmatic approach. It correctly identifies the depth-6 anomaly in Q3 as requiring immediate flattening, unlike B and C which ignored it.

**Strongest point:** Calling out the danger of the "minimal-touch approach." Leaving the direct CKE import violation untouched optimizes for short-term safety while knowingly leaving the main structural and security vulnerability active.

**Weakest assumption:** Assumes flattening the depth-6 directory concurrently with breaking apart a 3,573-line CLI file is safe. Moving files while aggressively refactoring imports is a recipe for catastrophic merge conflicts for any active PRs.

**Hidden assumptions:** Assumes the `corp-rfp-agent` dead scripts can be reliably confirmed as dead via repo search, ignoring the possibility of external CI/CD pipeline dependencies or cron jobs outside the repo executing them.

**Overlooked risks:** When replacing direct CKE imports with a subprocess call, passing large payloads (e.g., massive text blocks for extraction) via `stdin` or CLI flags might hit OS pipe buffer limits or `ARG_MAX` limits.

---

### Revised Recommendation

**I am updating my position to incorporate Proposal D's aggressive targeting of the depth-6 directory (Q3) while maintaining Proposal B's strict security rationale for memory isolation (Q1) and single-chokepoint sanitization (Q4).**

Here is the binding path forward to minimize the monorepo's attack surface and contain the blast radius of dependencies:

1. **Q1: Eliminate the Boundary Violation via Subprocess (Option B).**
   * *Security Rationale:* Orchestration (`corp-by-os/vault`) and Extraction (`CKE`) are different trust zones. Directly importing CKE shares execution state and memory. Untrusted LLM outputs handled by CKE must not have the ability to crash or compromise the orchestration layer's memory space. We will incur the ~100ms subprocess penalty to gain OS-level memory isolation.
2. **Q2: Split CLI into Click Command Groups (Option A).**
   * *Security Rationale:* A monolithic 3,573-line CLI means running `corp retrieve` forces the loading of dependencies for `ingest`, `doctor`, and `rfp`. If a sub-dependency in `doctor` is compromised, it poisons the runtime for the entire application. Splitting the CLI isolates execution paths.
3. **Q3: Aggressive Flattening (Option A variant).**
   * *Security Rationale:* Deeply nested, unjustified directories (`extraction/non_project` at depth-6) act as dark corners where unreviewed shadow-logic and bypasses accumulate. Flatten `extraction/non_project`, `doctor/`, and `freshness/` to max depth 4 to force visibility. 
4. **Q4: Centralize `parse_llm_json` (Option A) — No Renames.**
   * *Security Rationale:* LLM JSON parsing is our primary injection and Denial-of-Service vector. Maintaining two separate parsing loops is an unacceptable security risk. Centralize it in `corp-os-meta` as the single sanitization chokepoint. *Do not* rename the 10 harmless dataclasses; touching serialization boundaries introduces high runtime risk for purely cosmetic gains.
5. **Q5: Delete Dead Code (Option A).**
   * *Security Rationale:* Dead code circumvents testing, rusts rapidly, and creates false positives in vulnerability scanners. Delete it. Git history is our archive.

---

### Archive Results (per blueprint governance)

```powershell
# 1. Copy transcript to corp-monorepo
Copy-Item output\LATEST_DEBATE_OUTPUT.md `
    C:\Users\1028120\Documents\Dev\corp-monorepo\.ecosystem\council_transcripts\DECISION_23_monorepo_internal_architecture.md

# 2. Generate ADR-23 summary in corp-monorepo
New-Item -Path "C:\Users\1028120\Documents\Dev\corp-monorepo\decisions\ADR-23-monorepo-internal-architecture.md" -ItemType File -Value @"
# ADR-23: Monorepo Internal Architecture and Boundary Enforcement

**Date:** 2026-03-28
**Status:** Accepted

## Context
A recent architecture audit of our Python monorepo revealed that while our 6-package boundaries are generally defensible, `corp-by-os` suffers from severe internal sprawl (53% of all source code). Specifically, a 3,573-line `cli.py` monolith poses significant dependency blast-radius risks, and `overnight/cke_client.py` directly imports CKE internals, violating the trust boundary between the orchestration layer and the extraction engine. Furthermore, duplicated LLM JSON parsing logic exists, creating dual attack surfaces for injection vulnerabilities.

## Decisions
* **Q1 (Boundary Violation):** Eliminate. Refactor `overnight/cke_client.py` to use subprocess calls to invoke CKE. We enforce OS-level memory isolation between orchestration and untrusted extraction processes.
* **Q2 (CLI Monolith):** Split `cli.py` into internal Click command groups (e.g., `cli/ingest.py`, `cli/retrieve.py`). The main `cli.py` will lazily import these groups to preserve the `corp <command>` interface while isolating dependency execution paths.
* **Q3 (Unnecessary Nesting):** Flatten `extraction/non_project/`, `doctor/`, and `freshness/` upward to reduce max depth from 6 to 4, removing dark corners for unreviewed code.
* **Q4 (Duplication):** Centralize `parse_llm_json` into `corp-os-meta/utils.py` to act as a single sanitization chokepoint for LLM output. Delete the duplicated CKE implementation. Do not mass-rename harmless dataclass collisions to avoid serialization risks.
* **Q5 (Dead Code):** Delete the 4 confirmed dead scripts in `corp-rfp-agent`.

## Consequences
* Developers must build a robust subprocess wrapper for CKE invocations inside `overnight/`.
* Active PRs touching `corp-by-os/cli.py` will require re-basing to resolve merge conflicts once the CLI module split is merged.
* CI/CD linting rules must be updated to explicitly ban direct cross-package Python imports (e.g., `import CKE`) in `corp-by-os`.
"@

# 3. Commit decisions to repository
Set-Location -Path "C:\Users\1028120\Documents\Dev\corp-monorepo"
git add .ecosystem\council_transcripts\DECISION_23_monorepo_internal_architecture.md
git add decisions\ADR-23-monorepo-internal-architecture.md
git commit -m "docs: Council #23 — monorepo internal architecture decisions (ADR-23 + transcript)"
```

*Latency: 47.09s | Tokens: 13911*

### Deepseek (deepseek-reasoner)

---

## **Steelman & Assessment**

### **Proposal A**
**Steelman:**  
If the primary goal is maintainability without over-engineering, and if the overnight batch is truly non‑latency‑sensitive, then fixing the single boundary violation with subprocess, splitting the CLI into domain groups, flattening only the worst nesting, centralizing the utility, and deleting dead code is the optimal 80/20 solution. It directly addresses the audit’s top findings with minimal risk and no user impact.

**Assessment:** **Partially agree.**  
The approach is pragmatic and targets the highest‑leverage issues. However, it underestimates the performance impact of subprocess calls in batch contexts and overlooks the long‑term cost of leaving dataclass collisions unresolved.

**Strongest point:**  
“Maintain clean package boundaries (no runtime coupling, especially for CKE).” This aligns with the audit’s core finding and prevents architectural decay.

**Weakest assumption:**  
“The overnight batch process is not latency‑sensitive (tolerates subprocess overhead).”  
If overnight jobs scale to thousands of items, the ~100‑300 ms per‑call overhead compounds into hours of extra runtime, breaking SLAs. The proposal lacks a quantitative bound.

**Hidden assumptions:**
1. That CLI startup time will remain acceptable without lazy loading beyond groups.
2. That the 10 dataclass collisions are merely cosmetic and will not cause serialization or type‑checking failures as the codebase grows.

**Overlooked risks:**
- Subprocess error‑handling complexity in `cke_client.py` could lead to silent batch failures.
- Splitting the CLI without a registry test could miss command‑registration edge cases.
- Leaving dataclass collisions unresolved invites runtime type confusion when packages are used together in the same process.

---

### **Proposal B**
**Steelman:**  
If security and failure isolation are the paramount concerns, then eliminating all cross‑package imports, centralizing high‑risk parsing logic, and splitting the CLI to limit import contagion is the only safe path. This treats the monorepo as a multi‑tenant system where any coupling is a potential attack vector.

**Assessment:** **Disagree.**  
The security argument is overstated for an internal monorepo. The proposal sacrifices performance and simplicity for theoretical isolation gains without evidence of actual threat models. It also ignores the operational cost of subprocess error‑handling complexity.

**Strongest point:**  
“LLM JSON parsing is inherently dangerous and a prime vector for injection or denial‑of‑service.” Centralizing this logic reduces the attack surface and ensures consistent error handling.

**Weakest assumption:**  
“The performance overhead of process instantiation (subprocess calls) for overnight/cke_client.py is entirely acceptable.”  
No data supports this. Overnight batches could involve tens of thousands of calls; subprocess overhead could balloon runtime by 2–10×.

**Hidden assumptions:**
1. That the team has the bandwidth to implement robust subprocess wrappers with full error‑capture and logging.
2. That the security benefit of process isolation outweighs the latency and reliability hit.

**Overlooked risks:**
- Subprocess spawning could exhaust OS process limits in large batches.
- Increased complexity in error propagation could make debugging overnight failures harder, not easier.

---

### **Proposal C**
**Steelman:**  
If the goal is to fully resolve all audit findings in one pass—cleaning boundaries, reducing sprawl, eliminating duplication, and fixing name collisions—then this comprehensive approach delivers a coherent end‑state. It treats the monorepo as a system that must be internally consistent to scale.

**Assessment:** **Partially agree.**  
I agree with the technical choices (Q1‑B, Q2‑A, Q3‑B, Q4‑A+C, Q5‑A), but the proposal underestimates the coordination cost of renaming 10 dataclasses across the codebase and the performance impact of subprocess calls.

**Strongest point:**  
“cli.py split reduces the largest file from 3,573 to ~350 lines average across 9 files, directly attacking the root cause of sprawl.” This is the single highest‑impact change for developer productivity.

**Weakest assumption:**  
“Subprocess call overhead for overnight batch jobs is acceptable (estimated <3 seconds added latency on typical workloads).”  
This is a hand‑wave. Without workload profiling, we cannot accept this estimate.

**Hidden assumptions:**
1. That the team can safely rename dataclasses without breaking serialized data (e.g., pickle, JSON) or external integrations.
2. That the CLI split will not introduce registration race conditions or circular imports.

**Overlooked risks:**
- Dataclass renaming could break unpickled objects in existing vaults or caches.
- The CLI split might increase startup time if groups eagerly load heavy dependencies.

---

### **Proposal D**
**Steelman:**  
If the team’s capacity is limited and the priority is to ship improvements without disrupting ongoing work, then a minimal, targeted set of changes—fix the violation, split the CLI, flatten only the worst nesting, centralize the utility, rename only problematic dataclasses, delete dead code—is the most deployable path.

**Assessment:** **Agree.**  
This is the most realistic proposal. It acknowledges time constraints, focuses on high‑value changes, and explicitly defers lower‑value refactors. The risk assessments are concrete and the mitigations are actionable.

**Strongest point:**  
“Package restructuring is the wrong level of intervention given the audit result.” This respects the audit’s conclusion and avoids over‑engineering.

**Weakest assumption:**  
“The current test coverage or manual validation is sufficient to safely move Click command definitions across modules without changing command names/options.”  
This is optimistic; CLI refactors often uncover hidden coupling.

**Hidden assumptions:**
1. That the team has the discipline to revisit deferred items (like dataclass renaming) later.
2. That “targeted renames only where confusion is frequent” is a measurable criterion.

**Overlooked risks:**
- Partial dataclass renaming could increase inconsistency, making the naming scheme harder to understand.
- Deferring flattening of `extraction/non_project/` leaves a depth‑6 outlier that may never be addressed.

---

## **Revised Recommendation**

**I update my position to align with Proposal D, with the following modifications:**

1. **Q1: Eliminate via subprocess, but first profile.**  
   - Measure current `cke_client.py` call latency and batch volume.  
   - If subprocess overhead exceeds 5 % of total batch runtime, implement a buffered subprocess pool (e.g., `multiprocessing.Pool` with CLI invocations) to amortize startup costs.  
   - **Do not accept the violation; enforce the boundary, but optimize if needed.**

2. **Q2: Split CLI into domain groups with lazy loading.**  
   - Use Click’s `lazy_loading` pattern or `click‑plugins` to ensure startup time does not regress.  
   - Add a registry test that validates all 71 commands are reachable with the same options.

3. **Q3: Aggressively flatten all unjustified nesting.**  
   - Merge `doctor/` and `freshness/` into parent.  
   - Flatten `extraction/non_project/` (depth‑6 to depth‑4).  
   - **Depth‑6 for 3 files is indefensible; flatten it now to avoid permanent debt.**

4. **Q4: Centralize `parse_llm_json` and rename all colliding dataclasses.**  
   - Move `normalize_string_list` to `corp‑os‑meta` with CKE‑specific error handling as a parameter.  
   - Rename all 10 dataclasses using a script, but add `DeprecationWarning` aliases for one release cycle.  
   - **Collisions are not harmless; they cause IDE confusion and serialization risks. Fix them fully now to avoid compounding complexity.**

5. **Q5: Delete dead code after verifying with `git log` and team sign‑off.**  
   - Ensure no operational runbooks reference these scripts.  
   - If uncertainty exists, move to `scripts/archive/` with a README.

**Why the update?**  
Proposal D’s realistic scope and risk‑first mindset align with my architectural principles, but it underestimates the long‑term cost of partial fixes. Flattening depth‑6 and renaming all collisions are one‑time costs that prevent permanent navigability debt. The performance risk in Q1 must be quantified before implementation—a subprocess pool may be necessary to keep batch runtime within SLOs.

**What breaks first and at what order of magnitude?**  
The first breakage will be **overnight batch latency** if subprocess overhead is unmitigated. At 100 ms per call and 10,000 items, that’s 1,000 seconds (≈17 minutes) of pure overhead. This could push nightly batches into business hours. Mitigate with batched subprocess calls or a worker pool.

The second breakage could be **CLI startup time** if domain groups eagerly load all dependencies. At ~50 imports, startup could degrade from 200 ms to >2 s. Mitigate with lazy loading.

The third breakage is **serialization errors** if dataclass renaming breaks cached objects. This is a one‑time migration risk; mitigate with aliases and cache‑invalidation hooks.

**Implementation order:**
1. Profile overnight batch → design subprocess wrapper.
2. Split CLI with lazy loading.
3. Flatten nesting.
4. Centralize utility and rename dataclasses.
5. Delete dead code.

**Signals to stop:**
- Overnight batch runtime increases >10 % after subprocess change.
- CLI startup time exceeds 500 ms.
- More than 5 % of tests fail after dataclass renaming.

**Final stance:**  
Adopt Proposal D’s pragmatic scope but strengthen Q3 and Q4 to full fixes, and demand performance quantification for Q1 before implementation. This balances throughput, latency, and long‑term maintainability.

*Latency: 88.72s | Tokens: 11907*

### Openai (gpt-5.4)

## Proposal A

### Steelman first
This proposal is exactly right if the team is small, needs to ship improvements quickly, and the main pain is day-to-day maintainability rather than deep runtime architecture. If overnight processing is truly batch-oriented, subprocess overhead is operationally irrelevant. If `doctor/` and `freshness/` are obviously shallow wrappers with little internal cohesion, selective flattening gets most of the readability gain for very little churn. And if the dataclass name collisions are already causing real IDE/search friction, folding those renames into the cleanup window is efficient because people are already touching imports.

### Your assessment
**Partially agree.**

I agree with A on the highest-value decisions:
- **Q1 subprocess** over formalizing the violation
- **Q2 split `cli.py` into command-group modules**
- **Q3 selective flattening**
- **Q5 delete dead code**

I do **not** fully agree with bundling **repo-wide dataclass renames now** into Q4. That is the least leveraged part of the work and the easiest to let sprawl into mechanical churn. A small team can ship CLI modularization and one boundary cleanup; they can also centralize one duplicated utility. But renaming 10 colliding dataclasses across packages is where “good hygiene” starts eating the schedule.

### Strongest point
Its strongest point is the pragmatic one: **Click-group modularization gets most of the benefit of a package split without package-split cost.** That is exactly the right scale of intervention for this repo.

### Weakest assumption
The weakest assumption is that **the dataclass renames are cheap and low-risk enough to do now**. If that is false, this proposal expands from “targeted cleanup” into “broad cross-repo rename migration,” which increases merge conflicts, review fatigue, and regression risk for limited operational gain.

### Hidden assumptions
- It assumes the current CLI commands map cleanly into 8–10 stable domains without awkward cross-domain registrations.
- It assumes the CKE subprocess interface already exists in a form that can replace in-process calls without inventing new glue or output parsing complexity.

### Overlooked risks
- It does not say how to preserve behavior if some commands currently share helpers or state via the monolithic `cli.py`.
- It understates the cost of command registration regression testing for **71 commands**.
- It assumes dataclass renames won’t ripple into docs, tests, serialization, or ad hoc scripts.

---

## Proposal B

### Steelman first
This proposal is exactly right if the system operates under unusually strict security and isolation requirements, and if architectural cleanliness is being used as a proxy for reducing blast radius in production. If subprocess boundaries materially reduce operational risk, if duplicate LLM parsing logic is seen as a high-risk divergence point, and if the team can absorb a disciplined but focused cleanup now, then B’s posture makes sense: clean boundaries, one parser, no dead code, no package explosion.

### Your assessment
**Partially agree.**

The core decisions are mostly right:
- **Q1 subprocess**: yes
- **Q2 modular CLI**: yes
- **Q4 centralize utility**: yes
- **Q5 delete**: yes

But I disagree with two things:
1. **The framing is too security-maximalist for the actual problem.** The audit says the repo’s issue is internal navigability and one violation, not a compromised trust boundary program.
2. **Deferring Q3 entirely is too conservative.** Merging `doctor/` and `freshness/` is tiny, obvious cleanup. If a team is already touching imports during the CLI split, this is precisely the moment to remove the most unjustified nesting.

### Strongest point
The strongest point is: **do not normalize the only package-boundary violation.** Once “special-case lazy import of internals” is accepted, it stops being special.

### Weakest assumption
The weakest assumption is that **security isolation is the dominant decision driver here**. If it is not, the argument becomes overstated and can push the team toward over-design or over-testing relative to the repo’s actual operational maturity.

### Hidden assumptions
- It assumes subprocess execution is easier to observe and operate than in-process integration once logging and error capture are added.
- It assumes the canonical parser can absorb CKE-specific behavior cleanly without becoming a vague “god utility.”

### Overlooked risks
- It does not grapple enough with the implementation burden of parameterizing parser behavior into shared utils.
- It ignores the low-cost value of flattening the two obviously unnecessary subpackages.
- It risks turning a maintainability cleanup into a “security hardening” project, which can distort sequencing and scope.

---

## Proposal C

### Steelman first
This proposal is exactly right if the team has enough bandwidth for a coordinated cleanup sprint and wants to use this moment to remove multiple sources of navigational friction in one pass. If the dataclass collisions are already a recurring annoyance in reviews, IDE search, and onboarding, then renaming them while touching module boundaries may be the cheapest time to do it. If subprocess overhead is truly negligible and the team is disciplined about migration sequencing, C offers a thorough but still bounded cleanup.

### Your assessment
**Partially agree.**

C gets the major calls right:
- **Q1 subprocess**
- **Q2 split CLI**
- **Q3 selective flattening**
- **Q5 delete dead code**

But I disagree with its insistence on **renaming all 10 colliding dataclasses now**. That is the classic move that sounds clean in architecture review and becomes tedious, low-yield migration work in practice. This repo has a clear hotspot: `corp-by-os/cli.py`. Spend the team’s energy there first.

### Strongest point
The strongest point is the clear refusal to let the one cross-package import violation become accepted precedent.

### Weakest assumption
The weakest assumption is that **a full dataclass renaming campaign can be completed with modest cost and low confusion**. In reality, broad naming churn often produces temporary ambiguity, stale references, and review noise while delivering mainly cosmetic benefit.

### Hidden assumptions
- It assumes all collisions are equally harmful, rather than a few being the true offenders.
- It assumes there is enough repo-wide ownership alignment to land a naming migration cleanly.

### Overlooked risks
- It does not address migration fatigue from doing too many “correct” cleanups in one wave.
- It does not consider that temporary alias periods increase complexity and may linger.
- It understates how often naming changes conflict with active branches compared with structural internal file moves.

---

## Proposal D

### Steelman first
This proposal is exactly right if the team is small, time-constrained, and needs a plan that fixes the real problems without creating a second project. If the repo’s issue is internal sprawl, not package topology, then D is the best fit: remove the one real architecture violation, break up the giant CLI, clean up only the most obviously unjustified nesting, centralize true duplication, avoid broad naming churn, and delete dead code. If the team’s capacity is limited, D optimizes for changes they can realistically build, review, test, and operate.

### Your assessment
**Agree.**

This is the strongest proposal because it is the best calibrated to **what a real team can actually finish safely**.

I especially agree with:
- **Q1: Eliminate the violation via subprocess**
- **Q2: Split `cli.py` into command-group modules**
- **Q3: Flatten only the clearly unjustified areas**
- **Q4: Centralize the duplicated utility, but do only targeted dataclass renames if confusion is proven**
- **Q5: Delete dead code**

It focuses effort where the audit says the pain is, and it resists the temptation to convert a practical cleanup into a repo-wide naming crusade.

### Strongest point
The strongest point is the governing principle: **ship the smallest set of structural changes that materially improve maintainability now.** That is the correct lens for this council round.

### Weakest assumption
The weakest assumption is that **flattening `extraction/non_project/` is cheap enough to include alongside CLI modularization**. It is probably still worth doing, but if imports are hairier than expected, that specific flattening is the easiest item to cut without losing the core win.

### Hidden assumptions
- It assumes command grouping can be done without exposing latent coupling between domains hidden inside the current monolithic CLI.
- It assumes “targeted rename only where confusion is frequent” can be decided objectively enough that the team won’t bikeshed which collisions qualify.

### Overlooked risks
- It does not explicitly call out sequencing risk: doing Q1, Q2, and Q3 in parallel could create unnecessary merge and test churn.
- It could be more explicit about needing command-registration smoke coverage before moving 71 commands.

---

# Revised recommendation

**I update my position to align most closely with Proposal D.**

What changed my mind was not the architectural argument on boundaries or CLI modularization—I already leaned that way. The decisive evidence was the repeated contrast across proposals between:
- **high-yield, low-churn changes**: subprocess for the one violation, split the 3,573-line CLI, delete dead code
- **lower-yield, broad-churn changes**: rename all colliding dataclasses now, or defer obvious flattening for fear of import churn

D is the best package because it is the only one consistently asking the right first question: **can a team of this size actually build and run this in the time available?**

## Final recommendation by question

### Q1: Boundary violation
**Choose Option B — Eliminate via subprocess.**

Reason: one violation should not become policy. A subprocess boundary matches the rest of the ecosystem and avoids creating an informal API to CKE internals. Do **not** create a new package for a single exception. Do **not** formalize the lazy import.

### Q2: CLI monolith
**Choose Option A — Split into Click command groups across files.**

Reason: this is the highest-value maintainability change in the entire debate. It preserves `corp <command>` while making the codebase operable by a small team. Do **not** split into more packages. That is too much topology change for too little benefit.

### Q3: Unnecessary nesting
**Choose a D-style version of Option A/B: flatten the clearly unjustified areas now.**

Concretely:
- merge `doctor/`
- merge `freshness/`
- flatten `extraction/non_project/`

I am **not** recommending aggressive flattening everywhere. But I am also **not** deferring the obvious cases. If a subtree is depth-6 for 3 files, that is not “structure,” it is drag.

### Q4: Duplication and collisions
**Choose Option A for the utility duplication; reject a full naming campaign now.**

Concretely:
- centralize `parse_llm_json` in `corp-os-meta`
- move `normalize_string_list` there if needed
- have CKE import the canonical implementation

For dataclass collisions:
- **do not** rename all 10 now
- only rename the few that are demonstrably causing confusion in actively touched areas, if any

This is where I disagree most strongly with A/C. Full renaming is nice-to-have cleanup, not core architecture remediation.

### Q5: Dead code cleanup
**Choose Option A — Delete.**

Reason: low stakes, low ambiguity, low operational value in keeping it around. Git history is enough.

## Implementation sequencing I would recommend
Because this council should care about shippability, I would explicitly sequence the work:

1. **Q2 split CLI**
2. **Q1 subprocess boundary**
3. **Q3 flatten obvious nesting**
4. **Q4 utility centralization**
5. **Q5 dead code deletion** anytime

Why this order:
- CLI modularization is the biggest pain reducer.
- Boundary cleanup is important but isolated.
- Flattening should happen after command modules settle, not amid maximum file movement.
- Utility centralization is small and can trail.
- Dead code deletion is trivial and independent.

## Why the other proposals didn’t fully change my mind
- **A** was close, but it overcommits on dataclass renames.
- **B** gets too ideological and underweights easy structural cleanup.
- **C** is the most likely to ask a small team to do too much in one pass.
- **D** best matches the repo’s actual problem and the team’s likely capacity.

So my final position is:

**Adopt Proposal D’s shape, with explicit inclusion of flattening `extraction/non_project/` now, and explicitly reject a repo-wide dataclass renaming effort at this stage.**

*Latency: 46.03s | Tokens: 10480*

### Grok (grok-4.20-beta)

**What everyone is taking for granted**

Everyone assumes that:
1. The correct granularity of intervention is *inside* corp-by-os (file layout, CLI organization, import hygiene). No one questions whether a 15.7k-line package that owns 18 domains and the entire CLI surface is itself the architectural smell.
2. Subprocess = “clean boundary.” They treat OS-level isolation as an unalloyed good even for batch workloads that may issue hundreds of CKE calls per run. The performance and error-modeling cost is hand-waved with “it’s overnight.”
3. The 71-command `corp` CLI must remain a single namespace forever. The constraint is treated as immutable law rather than a design choice that might be the root cause of the monolith.

These are the premises the room has normalized without examination.

---

**Proposal A**

**Steelman:** If developer time is scarce, overnight really is latency-insensitive, the 71 commands partition cleanly into 8–10 domains, and the team can absorb ~60 import changes without creating new bugs, then this is the highest-ROI minimal intervention: it attacks the 3,573-line monolith, removes the only real boundary violation, trims obvious package cruft, eliminates duplication, and removes dead code. It is the pragmatic “80% benefit, 10% cost” path.

**Assessment:** Partially agree. I reject the Q4 recommendation. Renaming all 10 dataclasses is unnecessary ceremony. The collisions exist *across* package boundaries; Python already namespaces them. The proposal is reaching for aesthetic purity that will not improve runtime safety or even navigation meaningfully.

**Strongest point:** Explicitly calling out the “graspability threshold” (~1,000 lines) and targeting cli.py for that metric. This is concrete and correct.

**Weakest assumption:** That the commands “are logically groupable by domain without ambiguous overlaps.” Several commands (audit, doctor, freshness, rfp) are cross-cutting. The grouping will either become arbitrary or will leak concerns between files.

**Hidden assumptions:** 
- That Click group splitting + lazy loading will be trivial and will not regress CLI startup or help-text generation.
- That git blame history breakage on moved files is an acceptable cost for everyone (not just the people doing the refactor).

**Overlooked risks:** Shared setup/teardown code that currently lives in the monolith will now be duplicated or forced into a fragile common module, creating a new hidden coupling point inside the `cli/` package.

---

**Proposal B**

**Steelman:** If we treat the entire monorepo as a security boundary (untrusted LLM output, potential supply-chain attacks, defense-in-depth), then every direct import is a vector, every line of dead code is an unmonitored surface, and every duplicate parser is a missed security patch. Under that threat model, subprocess isolation, centralized parsing, and immediate dead-code deletion are non-negotiable hygiene. The proposal correctly refuses to normalize the violation.

**Assessment:** Disagree. The security framing is overdramatized for an internal corporate tool. We are not defending a public-facing parser. This proposal turns a maintainability issue into a threat model, then uses that inflated model to defer the cheap flattening work (Q3). It is solving the wrong problem at the wrong intensity.

**Strongest point:** The attack-surface argument for dead code is genuinely strong. Leaving migration scripts that have already run is sloppy.

**Weakest assumption:** That `corp-os-meta` is guaranteed to be present in every environment where CKE runs. The proposal never proves this; it just assumes the dependency graph will remain stable after the move.

**Hidden assumptions:** 
- That performance overhead of spawning a Python subprocess *per CKE invocation* in an overnight batch that may process thousands of items is irrelevant. 
- That developers will treat the new centralized parser as canonical rather than forking it again in six months.

**Overlooked risks:** By refusing to rename *any* dataclasses, the proposal leaves the exact navigability problem the audit called out. The “we’ll fix it when type checkers complain” stance is classic technical debt procrastination.

---

**Proposal C**

**Steelman:** This is the cleanest “do it all, do it properly, once” position that still respects the settled 6-package constraint. It fixes the real violation, modularizes the CLI, removes unnecessary packaging overhead, eliminates duplication *and* the name collisions that actually hurt IDE navigation, and deletes the dead code. If the team has the bandwidth, this is the version that leaves the codebase in the best state.

**Assessment:** Disagree. It over-indexes on renaming 10 dataclasses. That is a large diff for marginal gain. It also treats selective flattening as obviously correct when the audit itself questioned whether `extraction/` (8 files) justifies its depth. The proposal is too eager to declare victory on naming.

**Strongest point:** The explicit recognition that we should not create a seventh package just to solve one violation. That discipline is good.

**Weakest assumption:** That “<3 seconds added latency” on overnight is acceptable. No one has measured how many CKE calls a typical overnight run makes. If it is 200+ calls, we are looking at minutes, not seconds.

**Hidden assumptions:** That a 2-week deprecation alias period for renamed dataclasses will actually be cleaned up. History says these aliases live forever.

**Overlooked risks:** The combination of CLI splitting *and* widespread dataclass renaming creates a massive cross-cutting change. The chance of merge conflicts with every open PR touching corp-by-os is extremely high. The proposal underestimates coordination cost.

---

**Proposal D**

**Steelman:** The only proposal that tries to be truly surgical: fix the *actual* architecture violation, modularize the worst file, do the cheapest flattening that yields real readability wins, centralize the utility, and be pragmatic about naming. It correctly identifies that a full dataclass rename campaign is a future hygiene pass, not part of this cleanup.

**Assessment:** Disagree. It is still too conservative on flattening (`extraction/non_project/` at depth 6 for three files is indefensible) and too vague on naming (“targeted renames only where confusion is frequent”). Vague criteria produce inconsistent outcomes.

**Strongest point:** The decision criteria question (“Can a small team implement and operate this in the available time without destabilizing core workflows?”) is the right one. Most architecture councils ignore it.

**Weakest assumption:** That we can reliably know which dataclass collisions are “frequent sources of confusion.” This requires institutional memory that will be gone in 18 months.

**Hidden assumptions:** 
- That after we split cli.py into 8–10 files, the root `cli.py` will remain thin and stable. In practice it often becomes a registry full of imports.
- That “targeted renames” will not create a permanent two-tier naming system (some classes renamed, others not).

**Overlooked risks:** The proposal never addresses what happens to shared state or context objects that are currently passed between commands in the monolith. The new CLI structure may force either duplication or a new hidden “cli context” module.

---

**My Revised Recommendation**

The other proposals did not change my mind; they reinforced my contrarian read.

**Q1: Formalize (Option A)** — add CKE as an optional dependency in corp-by-os with documented lazy import + `is_available()` guard.  
Everyone treats subprocess as the moral choice. It is not. We are adding process overhead, worse error handling, and serialization complexity to a batch job for the sake of architectural purity on the *one* place where tight integration is arguably justified. The audit already called this the *only* violation and the existing guard is honest about it. Formalizing is more truthful than pretending we use the same pattern as corp-project-extractor when we manifestly do not.

**Q2: Split into Click command groups (Option A)** — I agree with all proposals here. The monolith must die. But I reject the unstated assumption that this will be the last time we touch the CLI. We will revisit command organization in <12 months.

**Q3: Aggressive flatten (Option A)** — merge `extraction/non_project/`, `doctor/`, and `freshness/`. Depth-6 for three files is ridiculous. The “extraction/ is justified because it has 8 files” argument is special pleading. Flatten it.

**Q4: Centralize parse_llm_json (Option A) but *reject* renaming dataclasses.**  
The collisions are harmless at runtime and the rename campaign is cosmetic. Centralize the utility, move `normalize_string_list`, add clear module docstrings explaining the canonical home. Stop there.

**Q5: Delete (Option A).** Obvious.

This combination is deliberately inconsistent with every proposal. It accepts a controlled, documented boundary violation because the alternative is worse engineering, while being more aggressive on folder structure than anyone except a pure Option A on Q3. That is the point. The room has converged on a comforting story about “clean boundaries and selective refactoring.” That story is internally inconsistent and rests on unexamined performance and coordination assumptions.

The real problem is that corp-by-os is a god package wearing a thin “orchestrator” costume. We are applying lipstick in the form of CLI groups and folder flattening. I am willing to call that out even if it makes the council uncomfortable.

*Latency: 27.58s | Tokens: 12464*

## Synthesis (by claude, non-participant)



# Decision Summary — Council #23: Monorepo Internal Architecture Refactoring

## Consensus

**Strong consensus (driven by independent reasoning and shared evidence):**

1. **Q2 — Split `cli.py` into Click command groups (Option A):** All four participants agreed unanimously. Each arrived at this independently via different lenses (maintainability, security, navigability, pragmatism). The evidence is unambiguous: 3,573 lines, 71 commands, 18 domains in one file. No participant found a credible reason to keep the monolith or escalate to a package split. This is the debate's highest-confidence decision.

2. **Q5 — Delete dead code (Option A):** Unanimous. Low-stakes, well-evidenced, no meaningful counterargument. One participant (OpenAI) prudently flagged verifying with the team before deletion, which is good hygiene but doesn't change the decision.

3. **Q4 — Centralize `parse_llm_json` in `corp-os-meta` (Option A for the utility):** All four agreed. CKE already depends on `corp-os-meta`, so the dependency path exists. The duplication is real (67 lines vs 97 lines with divergent error handling), and the risk of security-patch drift is a valid concern raised by Gemini.

4. **Q1 — The violation must not be left undocumented and unchanged:** All agreed the status quo is unacceptable. The disagreement (addressed below) is about *how* to resolve it, not whether to.

**Potential groupthink risk:** Three of four participants converged on subprocess for Q1 with nearly identical reasoning and hand-waved the performance cost with "it's overnight/batch." Only Grok challenged this directly. The subprocess consensus may be partially driven by the framing of the audit itself (which highlighted subprocess as "the correct pattern") rather than by independent cost-benefit analysis.

## Unresolved Disagreements

### Disagreement 1: Q1 — Subprocess vs. Formalize the CKE boundary violation

**The split:** Gemini, DeepSeek, OpenAI → Eliminate via subprocess (Option B). Grok → Formalize as optional dependency (Option A).

**The crux:** This is a *values* disagreement about whether architectural purity or operational pragmatism should dominate when they conflict. The factual question underneath it — *what is the actual performance cost of subprocess calls in overnight batch runs?* — was never answered by anyone. Every participant either asserted overhead was acceptable or asserted it might not be, without data.

**Which side had the stronger argument:**

Grok had the stronger *engineering* argument. Specifically:
- No participant provided data on how many CKE calls a typical overnight batch makes. If it's 10, subprocess overhead is trivial. If it's 1,000+, it could add meaningful runtime.
- The existing lazy-import pattern with `is_available()` is *already working* and is the *only* violation in the entire repo. The risk of it becoming precedent is real but manageable with linting.
- Subprocess invocation introduces genuinely worse error handling (exit codes vs. exceptions, stderr parsing, serialization boundaries) — Grok and DeepSeek both flagged this, but only Grok followed the implication to its conclusion.

However, the majority had the stronger *architectural* argument:
- One documented exception tends to become precedent. This is not theoretical; it's a well-observed pattern in codebases.
- The rest of the ecosystem uses subprocess boundaries. Consistency has real value for onboarding and maintenance.
- The constraint explicitly states "CKE is a pure extraction engine with no knowledge of vault/orchestration." A formalized optional dependency still means CKE internals are imported into the orchestration layer's memory space.

**My assessment:** The subprocess camp wins, but Grok's performance concern is legitimate and must be addressed as a prerequisite, not hand-waved. The correct answer is: **eliminate via subprocess, but measure first.**

### Disagreement 2: Q3 — Scope of flattening

**The split:** Gemini (Round 2) and Grok → Aggressive flatten including `extraction/non_project/`. DeepSeek (Round 1) and OpenAI → Selective flatten of only `doctor/` and `freshness/`, with OpenAI later including `extraction/non_project/`.

**The crux:** Whether `extraction/non_project/` (depth-6, 3 files) is "obviously unjustified" or "part of a justified 8-file extraction hierarchy."

**Which side had the stronger argument:** The flatten side. Depth-6 for 3 files is indefensible by any reasonable metric. The "extraction/ has 8 files" defense conflates the parent directory (which may be justified) with the nested subdirectory (which isn't). By Round 2, OpenAI explicitly moved to include this flattening. The debate converged to: flatten `doctor/`, `freshness/`, and `extraction/non_project/`.

### Disagreement 3: Q4 — Dataclass name collisions

**The split:** Grok and DeepSeek (Round 2) → Rename all 10 colliding dataclasses now. OpenAI and Gemini → Do not rename (or rename only targeted, proven sources of confusion).

**The crux:** Whether "harmless at runtime, confusing to navigate" is a problem worth solving now or a cosmetic concern that should wait.

**Which side had the stronger argument:** The "don't rename now" side. Here's why:
- The audit itself called collisions "harmless at runtime."
- DeepSeek's argument for renaming rested on "serialization risks" and "type-checking failures as the codebase grows" — but provided no evidence either has occurred or is imminent.
- Grok argued against renaming in Round 1 assessment of Proposal C ("a large diff for marginal gain") and then... also argued against renaming in their own recommendation. So the pro-rename camp was effectively just DeepSeek in Round 2.
- Renaming 10 dataclasses across 6 packages is a broad cross-cutting change. OpenAI correctly identified that this is where "good hygiene starts eating the schedule."
- The strongest counterargument (Grok's point that "institutional memory will be gone in 18 months" making it hard to know which collisions are confusing) is real, but it argues for a systematic future pass with clear criteria, not an ad-hoc rename now.

## Argument Quality Assessment

**Best-reasoned proposal:** OpenAI (Round 2). It consistently applied a single governing question — "can a small team actually ship this safely?" — and used it to discriminate between high-yield and low-yield changes. It was the only proposal to provide explicit implementation sequencing with justification for ordering. It steelmanned all other proposals fairly and identified the specific points of disagreement rather than asserting its own position.

**Second best:** Grok. It was the only participant willing to take a genuinely contrarian position (formalize Q1, aggressive flatten Q3), and it backed those positions with specific operational concerns that the majority hand-waved. Its observation that "corp-by-os is a god package wearing a thin orchestrator costume" is the most honest structural diagnosis in the debate, even though the council correctly can't solve that in this round.

**Weakest reasoning:** Gemini's security framing. Phrases like "trust zone violation," "attack surface," and "supply chain vulnerability" were applied to an internal Python monorepo's overnight batch job importing another internal package. The threat model was never grounded in actual risk. DeepSeek correctly called this out: "The security argument is overstated for an internal monorepo." Security framing can be useful for prioritization, but here it was used to inflate urgency without proportionate evidence.

**Single strongest argument in the entire debate:** OpenAI's principle: "One exception tends to become precedent; today it is 1 violation, but documenting it invites more." This is the dispositive argument for subprocess over formalization — not security theater about trust zones, but the pragmatic observation about how codebases decay. Simple, evidence-based, hard to refute.

**Single weakest argument in the entire debate:** Gemini's claim that deeply nested directories "act as dark corners where unreviewed shadow-logic and bypasses accumulate" as a *security* rationale for flattening. The actual rationale for flattening is navigability and cognitive overhead. Dressing it up as a security concern weakens the argument by making it unfalsifiable and overdramatic.

## Blind Spots

1. **Nobody measured anything.** The entire Q1 debate hinges on subprocess overhead vs. batch runtime, and not one participant asked "how many CKE calls does an overnight run actually make?" or "what is the current end-to-end runtime?" This is the single biggest gap. Grok flagged it but then also didn't resolve it.

2. **Shared state in the CLI monolith.** Grok alone mentioned this in passing: when 71 commands live in one file, they may share setup code, context objects, or helper functions. Splitting them into 8–10 modules will force decisions about where that shared logic lives. Nobody proposed a concrete strategy for this (e.g., a `cli/_common.py` or passing Click context objects).

3. **The `corp-rfp-agent` Click migration interaction.** The brief says this is already decided. But nobody examined how a new Click CLI for `corp-rfp-agent` interacts with the `corp-by-os` CLI modularization. Will `corp-rfp-agent` commands be accessible via `corp` or via a separate entrypoint? If the former, the CLI modularization design must account for it.

4. **Testing strategy for 71 commands.** Multiple participants mentioned "smoke tests" or "registry tests" but nobody specified what that means concretely. Testing 71 commands at even the help-text level is non-trivial and should be a prerequisite, not an afterthought.

5. **The god-package problem.** Grok correctly identified that `corp-by-os` at 15,724 lines across 18 domains is itself the architectural smell, and the proposed changes are internal cosmetics. The council correctly scoped this debate to internal quality (per the brief), but nobody acknowledged the strategic question: *after these changes, what signals would indicate the package itself needs splitting?* OpenAI came closest with a revisit signal but framed it only around growth, not domain divergence.

## Recommended Decision

### Q1: Boundary Violation — **Eliminate via subprocess (Option B), preceded by measurement**

Refactor `overnight/cke_client.py` to use subprocess calls matching the established ecosystem pattern. However, **before implementation**, measure the current number of CKE invocations per typical overnight run and establish a performance baseline. If subprocess overhead would exceed 10% of batch runtime, implement a batched invocation pattern (multiple items per subprocess call) rather than reverting to direct imports.

*Rationale:* The architectural consistency argument is decisive. The repo has one violation; fixing it closes the gap entirely. Grok's operational concern is valid but addressable through measurement and batching, not by normalizing the violation.

*Acknowledging the strongest objection:* Grok is right that subprocess introduces worse error handling and that no one measured the performance cost. This is why I require measurement first. But the architectural precedent argument outweighs the operational inconvenience — this is a one-time migration cost, while a formalized exception is a permanent maintenance burden.

### Q2: CLI Monolith — **Split into Click command groups (Option A)**

Create `cli/` directory with domain-specific modules (e.g., `cli/ingest.py`, `cli/retrieve.py`, `cli/overnight.py`, etc.). A thin root `cli.py` or `cli/__init__.py` registers all groups. All 71 commands remain accessible via `corp <command>`.

*Rationale:* Unanimous agreement, strongest evidence, highest-yield change. The only implementation detail that matters: identify shared CLI helpers/context currently in the monolith and place them in `cli/_common.py` before splitting.

### Q3: Unnecessary Nesting — **Flatten `doctor/`, `freshness/`, and `extraction/non_project/`**

Merge `doctor/` (2 files) and `freshness/` (2 files) into root-level modules. Flatten `extraction/non_project/` (3 files) upward into `extraction/`. This reduces max depth from 6 to 4.

*Rationale:* By Round 2, this was effectively consensus. Depth-6 for 3 files is unjustified. Two-file sub-packages have unjustified `__init__.py` overhead. The 8-file `extraction/` parent remains intact.

### Q4: Duplication — **Centralize `parse_llm_json`; do not rename dataclasses now**

Delete CKE's `parse_llm_json`. Move `normalize_string_list` to `corp-os-meta/utils.py` with the extra error-handling behavior CKE relied on. CKE imports from `corp-os-meta`.

Do **not** undertake a repo-wide dataclass renaming campaign. The collisions are harmless at runtime. If specific collisions are causing proven, repeated confusion, rename those individually as encountered — not as a batch project.

*Rationale:* Centralizing the utility is low-risk, high-value (CKE already depends on `corp-os-meta`). The renaming campaign is low-value, high-churn. OpenAI's argument that this is where "good hygiene starts eating the schedule" is correct.

*Acknowledging the strongest objection:* DeepSeek is right that collisions could eventually cause problems as the codebase grows. The correct response is to add a revisit trigger (see Signals to Revisit), not to preemptively rename 10 classes across 6 packages.

### Q5: Dead Code — **Delete (Option A)**

Remove `clean_kb.py`, `scan_kb.py`, `kb_to_markdown.py`, and `_paths.py` from `corp-rfp-agent`. Verify with a repo-wide search and owner confirmation first. Git history preserves them.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Subprocess CKE calls degrade overnight batch runtime beyond acceptable bounds | Medium | High | Measure call volume and baseline runtime *before* migration. Design subprocess wrapper to accept batched inputs if single-call overhead is problematic. Establish a 10% runtime regression threshold. |
| CLI split breaks command registration, help text, or option parsing for some of 71 commands | Medium | High | Snapshot current `corp --help` and all subcommand help text. Build an automated smoke test that validates all 71 commands are registered with correct names before merging. |
| Shared setup/context code in current `cli.py` has hidden coupling between command domains | Medium | Medium | Audit `cli.py` for module-level state, shared decorators, and cross-domain helper functions *before* splitting. Extract these into `cli/_common.py` first. |
| Import path changes from flattening break internal imports or stale references | Medium | Low-Medium | Run full test suite after each flattening PR. Use `grep -r` for old import paths. Keep scope limited to the three identified directories. |
| Centralized `parse_llm_json` subtly changes CKE error behavior | Low-Medium | Medium | Port CKE's extra error handling (the 30 additional lines) into the canonical implementation. Write tests against CKE's known edge cases before deleting the duplicate. |
| Subprocess wrapper obscures CKE error tracebacks, complicating debugging | Medium | Medium | Capture and log both stdout and stderr from subprocess calls. Map non-zero exit codes to specific exception types in the wrapper. |

## Action Items

**Phase 0 — Prerequisites (before any code changes)**
1. **Measure overnight batch CKE call volume.** Count how many times `cke_client.py` invokes CKE functions in a typical overnight run. Establish baseline runtime. This gates the Q1 implementation approach.
2. **Audit `cli.py` for shared state.** Identify module-level variables, shared decorators, context setup, and cross-domain helper functions. Document what will need to move to `cli/_common.py`.
3. **Snapshot CLI surface.** Capture `corp --help` and all 71 subcommand `--help` outputs. This becomes the regression baseline.
4. **Verify dead code is truly dead.** Repo-wide search for imports/references to the 4 target files. Check operational runbooks and any cron jobs outside the repo.

**Phase 1 — CLI Modularization (highest value, do first)**
5. Create `cli/` directory structure with `_common.py` for shared helpers.
6. Move commands into domain modules (~8–10 files). Maintain `corp <command>` entrypoint.
7. Add automated smoke test validating all 71 commands register correctly.
8. Validate against Phase 0 snapshot.

**Phase 2 — Boundary Cleanup**
9. Design subprocess wrapper for CKE invocations based on Phase 0 measurements. If call volume is high (>100 calls/run), implement batched invocation pattern.
10. Replace direct CKE imports in `overnight/cke_client.py` with subprocess calls.
11. Add integration tests covering all CKE invocation paths in overnight.
12. Add CI lint rule banning direct cross-package Python imports between `corp-by-os` and CKE.

**Phase 3 — Structural Cleanup**
13. Flatten `doctor/`, `freshness/`, and `extraction/non_project/`. Update all import paths.
14. Run full test suite. Grep for stale import paths.

**Phase 4 — Utility and Dead Code**
15. Merge CKE's `parse_llm_json` enhancements into `corp-os-meta/utils.py`. Move `normalize_string_list`.
16. Update CKE to import from `corp-os-meta`. Delete duplicate.
17. Delete 4 dead files in `corp-rfp-agent`.

**Signals to Revisit**
- Overnight batch runtime increases >10% after subprocess migration → consider batched invocation or worker pool.
- CLI startup exceeds 500ms after modularization → introduce lazy loading.
- Dataclass collisions cause a real bug or repeated onboarding confusion (tracked, not anecdotal) → schedule a systematic naming pass.
- `corp-by-os` exceeds 20k lines or a domain within it gains separate ownership → revisit package extraction.
- New cross-package Python import violations appear → tighten CI linting immediately.
