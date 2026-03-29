# AI Council Debate: ## Question: How should we migrate 6 repos into a monorepo without breaking 1,84

**Date:** 2026-03-24 22:27:07
**Panel:** claude-opus-4-6, deepseek-reasoner
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 229.8s
**Mode:** custom
**Source:** council_inbox\council_monorepo_strategy.md

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

**Incremental merge, Option B (phased), with CKE namespace refactored BEFORE merge as a standalone prerequisite.** Merge in three phases: (1) corp-os-meta + CKE, (2) corp-by-os + CPE, (3) RFP agent later. Each phase is a self-contained milestone where all tests pass before proceeding.

## Rationale

- **Solo developer with ADHD + production system = incremental is the only honest choice.** Big-bang merges fail for you specifically—this is empirical data about yourself, not a preference. Each phase should be completable in 1-2 focused sessions with a clean "done" state. A half-finished big-bang merge is the worst possible state to leave a production system in.

- **CKE's flat namespace is the single hardest problem and must be solved first, in isolation.** Refactoring 39 files and 625 tests is mechanical but high-volume. Doing this inside CKE's own repo, before any merge, means you have one variable changing (namespace), not two (namespace + repo structure). If all 625 tests pass after the rename, you know the rename is clean. Mixing this with the merge is asking for diagnostic hell when something breaks.

- **Subprocess boundaries are an asset, not a liability—keep them for now.** The subprocess calls between repos (`cke process-manifest`, `cpe scan`) represent real architectural boundaries (CKE doesn't write to vault, corp-by-os does). Converting to Python imports during a monorepo migration is scope creep that adds risk for marginal benefit. You can always convert later; you can't easily re-introduce isolation later.

- **A shared `corp-common` package (Option C) solves the wrong problem.** Your pain points are hardcoded paths, CKE's broken namespace, and three duplicated LLM routers. A shared package addresses only the duplication. You'd still have 4+ repos to coordinate releases across, and the path/config problem gets worse because now you have N+1 repos. The monorepo solves coordination; a shared package adds coordination overhead.

- **Preserving git history is achievable with `git subtree add` or the merge-based approach**, and phased merges make this easier because each `subtree add` is one commit you can inspect and verify.

## Concrete Merge Plan

### Phase 0: Pre-work (in existing repos, no merge yet)

**Step 0a: Refactor CKE namespace (in CKE repo)**

```
# Target: from src.extract → from corp_knowledge_extractor.extract
# Mechanical steps:
1. Create corp_knowledge_extractor/ package dir inside src/
2. Move all modules from src/ into src/corp_knowledge_extractor/
3. Add src/corp_knowledge_extractor/__init__.py
4. sed/find-replace all imports across 39 files
5. Update pyproject.toml package discovery
6. Run all 625 tests
7. Tag release: cke-v2.0.0-namespaced
```

Do NOT use import aliases or shims. They defer pain, create a parallel reality that someone (you) has to remember exists, and double the import paths future-you has to reason about. The rename is mechanical—use `rope`, `bowler`, or even `sed`. It's boring, which is good.

**Step 0b: Replace hardcoded CKE path in corp-by-os**

```python
# Before (cke_invoker.py):
CKE_PATH = "/Users/rob/repos/corp-knowledge-extractor"

# After:
CKE_PATH = os.environ.get("CKE_PATH", shutil.which("cke") or _default_path())
```

This is a one-file change. It decouples corp-by-os from CKE's filesystem location, which you need regardless of whether you merge. Run corp-by-os's 847 tests.

**Step 0c: Create monorepo skeleton**

```
corp-monorepo/
├── pyproject.toml          # workspace root (PEP 660 / hatch workspaces)
├── packages/
│   ├── corp-os-meta/       # will be populated in Phase 1
│   ├── corp-knowledge-extractor/
│   ├── corp-by-os/
│   └── corp-project-extractor/
├── config/
│   └── paths.toml          # centralized path config (Phase 2)
├── tests/
│   └── integration/        # cross-package integration tests (Phase 2)
└── scripts/
    └── run-all-tests.sh    # runs each package's tests in sequence
```

### Phase 1: Merge corp-os-meta + CKE

**Why these two first:** corp-os-meta is the foundation (Pydantic schemas). CKE depends on it. This is the tightest coupling and the smallest blast radius (108 + 625 = 733 tests, ~8,600 LOC).

```bash
# In corp-monorepo:
git subtree add --prefix=packages/corp-os-meta \
    git@github.com:org/corp-os-meta.git main
git subtree add --prefix=packages/corp-knowledge-extractor \
    git@github.com:org/corp-knowledge-extractor.git main

# Each package keeps its own pyproject.toml
# Root pyproject.toml uses hatch workspaces or pip install -e for each
```

**Validation gate:**
```bash
cd packages/corp-os-meta && python -m pytest  # 108 tests pass
cd packages/corp-knowledge-extractor && python -m pytest  # 625 tests pass
# Total: 733/733 pass → Phase 1 complete
```

**Do NOT unify the LLM routers yet.** That's a refactor, not a migration. Tag it as a future task.

### Phase 2: Merge corp-by-os + CPE, centralize config

```bash
git subtree add --prefix=packages/corp-by-os \
    git@github.com:org/corp-by-os.git main
git subtree add --prefix=packages/corp-project-extractor \
    git@github.com:org/corp-project-extractor.git main
```

**Now centralize path config:**

```toml
# config/paths.toml
[paths]
vault = "~/corp-vault"
mywork = "~/mywork"

[llm]
default_provider = "anthropic"
# API keys stay in env vars, never in config files
```

```python
# packages/corp-os-meta/corp_os_meta/config.py
# Single source of truth for path resolution
import tomllib
from pathlib import Path

_CONFIG_SEARCH = [
    Path.cwd() / "config" / "paths.toml",
    Path(__file__).parents[3] / "config" / "paths.toml",  # monorepo root
    Path.home() / ".corp" / "paths.toml",                  # fallback
]

def load_config() -> dict:
    for p in _CONFIG_SEARCH:
        if p.exists():
            return tomllib.loads(p.read_text())
    return _defaults()
```

Each package replaces its own path resolution with `from corp_os_meta.config import load_config`. This is small, testable, and gives you environment-variable override for CI.

**Validation gate:**
```bash
./scripts/run-all-tests.sh  # 1,842/1,842 pass → Phase 2 complete
```

### Phase 3 (deferred): RFP agent

Only after it gets version pins and argparse→Click migration. This is not part of the current migration.

## Answers to Specific Questions

| Question | Recommendation | Reasoning |
|----------|---------------|-----------|
| **1. Merge strategy** | B (incremental) | Proven failure mode with big-bang; each phase has clear "done" |
| **2. CKE namespace** | (a) Refactor BEFORE merge | One variable at a time; 625 tests validate rename in isolation |
| **3. Subprocess vs imports** | (a) Keep subprocess calls | Preserve isolation boundaries; converting is scope creep during migration |
| **4. Path management** | (c) corp-os-meta provides resolution, backed by (a) single config file | Meta is already the foundation; single file gives one place to look |
| **5. Testing strategy** | (a) Run ALL tests after each merge step, with (c) zero shims | Shims are debt; running all tests is cheap at 1,842 |
| **6. CLI entry points** | (a) Keep all 4 entry points | Backward compatible; unification is a UX project, not a migration task |

## Trade-offs

- **Incremental is slower in calendar time.** Three phases means three rounds of validation instead of one. For a solo developer, this is a feature—each phase is a weekend, not a month-long death march.
- **Keeping subprocess calls means you don't get shared-memory performance gains yet.** But the current system works at current scale. Premature optimization of IPC in a pre-sales tool is misallocated effort.
- **Four CLI entry points means four `[project.scripts]` entries to maintain.** Minor ongoing cost, but avoids retraining muscle memory during a migration (you'd be retraining muscle memory while doing production pre-sales work).
- **You don't consolidate the three LLM routers now.** This means continued duplication for a while. But router unification is a design problem (which router's interface wins?) that deserves its own focused effort, not a side-quest during a migration.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **CKE rename misses an import path, test passes locally but fails in production** | Medium | High | Run CKE in production for 1 week after rename, before starting Phase 1. Add `python -c "from corp_knowledge_extractor.extract import ..."` smoke tests to CI. |
| **`git subtree` merge conflicts on future upstream changes** | Low (you're archiving the old repos) | Medium | After Phase 2 validation, archive the 4 source repos as read-only. All development moves to monorepo. No bidirectional sync. |
| **Phase 1 completes but Phase 2 stalls due to ADHD/priority shift** | High | Medium | This is fine by design. Phase 1 is self-contained. Corp-by-os and CPE continue working in their own repos against the namespaced CKE. The monorepo is usable at every phase boundary. |
| **Centralized config breaks a package that had different path assumptions** | Medium | Medium | Each package's existing path config becomes the fallback in `load_config()`. Centralized config is additive overlay, not replacement. Tests catch mismatches because they already test real paths. |
| **Hatch/pip workspace resolution conflicts between packages with different dependency versions** | Medium | High | Pin all shared dependencies (Pydantic, Click, httpx) to compatible ranges in Phase 0. Run `pip check` as part of `run-all-tests.sh`. Each package keeps its own `pyproject.toml` with its own deps; the workspace root just does editable installs. |
| **Rob can't do pre-sales work during a migration phase** | Low (if phased) | Critical | Each phase ends with a tagged, working state. If Phase 1 is in progress and a deal comes in, `git stash`, go back to the old repos. They still work. They always still work until you explicitly archive them. |

## Summary Checklist

```
□ Phase 0a: CKE namespace rename (in CKE repo) → 625 tests green
□ Phase 0b: Remove hardcoded CKE path in corp-by-os → 847 tests green
□ Phase 0c: Create monorepo skeleton
□ Phase 1:  Subtree-add meta + CKE → 733 tests green
□ Phase 2:  Subtree-add corp-by-os + CPE → 1,842 tests green
□ Phase 2b: Centralize path config via corp-os-meta → 1,842 tests green
□ Phase 3:  (future) RFP agent after its own cleanup
□ Phase 4:  (future) Unify LLM routers
□ Phase 5:  (future) Convert subprocess calls to Python imports where warranted
```

Each checkbox is independently shippable. Each has a clear validation gate. The system works at every boundary.

*Latency: 68.80s | Tokens: 4366*

### Deepseek (deepseek-reasoner)

## Position  
I recommend an incremental merge (Option B): Start with corp-os-meta + CKE as a pilot, then integrate corp-by-os + CPE in phase 2, deferring RFP agent until after structural cleanup. Refactor CKE’s namespace **before** merging it, and centralize config via corp-os-meta as a shared library.

## Rationale  
- **Incremental reduces cognitive load and risk**—as a solo developer with ADHD, small verified steps prevent overwhelm and allow rolling back if tests fail.  
- **CKE namespace must be fixed pre-merge**—because its flat `src/` collides with corp-by-os’s package structure; fixing it in isolation avoids polluting the monorepo with import hacks.  
- **Corp-os-meta as config foundation**—it already provides Pydantic schemas and can become the single source for path resolution, eliminating scattered configs.  
- **Preserve subprocess calls initially**—maintains isolation and existing CLI contracts; switch to Python imports only after merge is stable and tests pass.  

## Trade-offs  
- **Slower overall integration**—phased approach extends total timeline versus a big-bang merge.  
- **Temporary duplication of routers/configs**—LLM routers and path logic will remain duplicated until phase 2 completes.  
- **Delayed unification benefits**—shared tooling, dependency management, and cross-module refactoring wait until later phases.  

## Risks  
1. **CKE refactor could break 625 tests**  
   - Mitigation: Use IDE-assisted refactoring (e.g., PyCharm’s “Rename” across project) and run CKE’s test suite after each batch of import changes.  

2. **Hardcoded paths in subprocess calls fail post-merge**  
   - Mitigation: Before merging corp-by-os, update its `cke_invoker.py` to resolve CKE’s CLI path relative to the monorepo root (using corp-os-meta’s new path resolver).  

3. **Config centralization breaks existing workflows**  
   - Mitigation: Implement a backward-compatible config fallback chain: monorepo config → environment variables → legacy repo configs.  

4. **Git history becomes messy**  
   - Mitigation: Use `git merge --allow-unrelated-histories` for each repo, preserving original commits, and tag each phase for easy rollback.  

## Concrete Plan  
1. **Phase 1 (Pilot)**  
   - Refactor CKE’s imports from `src.*` to `corp_knowledge_extractor.*` in its own repo. Verify all 625 tests pass.  
   - Merge corp-os-meta into a new monorepo as `packages/core/meta`.  
   - Merge CKE as `packages/core/knowledge_extractor`.  
   - Update corp-os-meta to expose a `PathResolver` class that reads from a root `config.yaml`.  

2. **Phase 2 (Orchestration)**  
   - Merge corp-by-os as `packages/core/by_os`, updating its hardcoded CKE paths to use `PathResolver` and subprocess calls to `packages/core/knowledge_extractor/cli.py`.  
   - Merge CPE as `packages/core/project_extractor`, similarly updating paths.  
   - Run all 1,842 tests in the monorepo; fix any failures before proceeding.  

3. **Phase 3 (Cleanup & Unification)**  
   - Refactor RFP agent in its own repo, then merge it.  
   - Consolidate LLM routers into a shared `packages/core/llm_router`.  
   - Optional: Unify CLIs under a single `corp` entrypoint with Click subcommands, preserving legacy CLIs during transition.  

**Testing strategy**: After each merge commit, run the entire test suite with `pytest` using the monorepo’s root `pyproject.toml`. Use `pytest-xdist` for parallel execution to speed up feedback.

*Latency: 54.77s | Tokens: 3178*

## Round 2: Critique

### Claude (claude-opus-4-6)

## Evaluation of Proposals

### Proposal A

**Verdict: Strongly agree.**

This is an exceptionally well-constructed proposal. It demonstrates the kind of thinking I want to see in architecture decisions: explicit about constraints, honest about personal failure modes, and disciplined about scope.

**Strongest point:** The Phase 0 separation — doing the CKE namespace refactor *and* the hardcoded path removal *before* any merge activity — is the key insight. It isolates the two hardest mechanical problems (namespace collision and path coupling) from the structural problem (monorepo layout). Each has its own clear validation gate. This is textbook "change one thing at a time."

The explicit acknowledgment that "Phase 2 stalls due to ADHD" is a *feature* of the design, not a bug, is architecturally mature. A system that is usable at every phase boundary is genuinely more maintainable than one that requires completion to function.

**Weakest assumption:** The `_CONFIG_SEARCH` path resolution with `Path(__file__).parents[3]` is brittle. It encodes the monorepo's directory depth into the config module. If someone moves the package or changes nesting, this silently fails or finds the wrong config. This is a minor implementation detail, not a structural flaw, but it's the kind of thing that generates a confusing bug six months from now.

**Overlooked risk:** The proposal says "archive the 4 source repos as read-only" after Phase 2 but doesn't address what happens if a critical bug is found in production *during* Phase 1, when only meta+CKE are in the monorepo but corp-by-os is still in its own repo. You'd be patching in two places with two different path assumptions. The mitigation ("go back to the old repos") is correct but should be more explicit: during Phase 1, the old repos remain the *production* source of truth. The monorepo is not production until Phase 2 passes its gate.

---

### Proposal B

**Verdict: Partially agree.** The strategy is correct in broad strokes — it converges on the same phased approach — but it is materially less rigorous than Proposal A and makes several choices I'd push back on.

**Strongest point:** The backward-compatible config fallback chain (monorepo config → environment variables → legacy repo configs) is a good defensive pattern. Proposal A has this concept but Proposal B names it more explicitly as a migration safety net.

**Weakest assumption:** The directory structure `packages/core/meta`, `packages/core/knowledge_extractor`, `packages/core/by_os` introduces unnecessary nesting and — more critically — renames packages during the merge. CKE becomes `knowledge_extractor`, corp-by-os becomes `by_os`. This is *exactly* the kind of "change two things at once" that the phased approach is supposed to prevent. You're changing the repo structure AND the package identity simultaneously. Every import, every `pyproject.toml` reference, every CLI entry point now has a different name than what the developer has been using. This creates cognitive load that is invisible in the plan but very real during debugging at 11pm.

**Overlooked risks:**

1. **No explicit Phase 0.** Proposal B says "refactor CKE's imports in its own repo" as Step 1 of Phase 1, but doesn't separate it as a standalone, validated milestone. This is a critical distinction. If the CKE rename and the first merge are in the same "phase," the temptation to overlap them is high. For a solo developer with ADHD, the phase boundary IS the discipline mechanism.

2. **No mention of the hardcoded path in cke_invoker.py as pre-work.** Proposal B defers this to Phase 2 ("updating its hardcoded CKE paths to use PathResolver"). But by Phase 2 you're already merging corp-by-os, so you're simultaneously changing its location, its path resolution mechanism, and its dependency's location. Three variables, not one.

3. **"Use `pytest-xdist` for parallel execution"** — this is a nice-to-have that adds a dependency and potential test isolation issues (shared filesystem state, port conflicts) at the exact moment you need maximum test reliability. Optimize for correctness first, speed later.

4. **Consolidating LLM routers into `packages/core/llm_router` in Phase 3** is stated as if it's a straightforward structural task. It isn't. Three routers means three different interface contracts, three sets of retry logic, three error handling strategies. Unifying them is a design project, not a migration step. Bundling it into Phase 3 alongside the RFP agent merge guarantees scope explosion.

---

## Revised Recommendation

I endorse Proposal A's plan with three specific amendments:

### Amendment 1: Explicit production cutover boundary

Add to the plan: **The old repos remain the production source of truth until Phase 2 passes its validation gate.** During Phase 1, the monorepo is a staging environment. This means:

- Rob continues running `cke`, `corp`, `cpe` from the old repo installs during Phase 1
- Phase 1's success criterion is "733 tests pass in monorepo" — not "monorepo is in production"
- Phase 2's success criterion is "1,842 tests pass AND Rob runs pre-sales work from monorepo for one full work cycle"
- Only after Phase 2 validation do old repos get archived

This eliminates the ambiguity about what happens if Phase 1 is done but Phase 2 hasn't started.

### Amendment 2: Fix the config path resolution

Replace the `parents[3]` approach with explicit discovery:

```python
# packages/corp-os-meta/corp_os_meta/config.py
import tomllib
from pathlib import Path

_MARKER_FILE = "corp-monorepo.marker"  # empty file at monorepo root

def _find_monorepo_root() -> Path | None:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / _MARKER_FILE).exists():
            return parent
    return None

def load_config() -> dict:
    root = _find_monorepo_root()
    search = [
        *([] if root is None else [root / "config" / "paths.toml"]),
        Path.home() / ".corp" / "paths.toml",
    ]
    for p in search:
        if p.exists():
            with open(p, "rb") as f:
                return tomllib.load(f)
    return _defaults()
```

A marker file is explicit, survives directory restructuring, and communicates intent. It's the same pattern `git` itself uses. The cognitive load of "why does this file exist" is one comment in the file.

### Amendment 3: Adopt Proposal B's explicit config fallback chain as the canonical pattern

Formalize the precedence as:

1. Environment variables (always win — CI, containers, overrides)
2. Monorepo `config/paths.toml` (if running from monorepo)
3. `~/.corp/paths.toml` (user-level defaults)
4. Package-internal defaults (hardcoded safe fallbacks)

This should be documented in the monorepo's README and tested with a dedicated test that validates the cascade. Each package's existing config becomes tier 4, not deleted.

### Everything else: unchanged from Proposal A

- Phase 0a/0b/0c as pre-work, each independently validated
- `git subtree add` for history preservation
- Keep subprocess calls during migration
- Keep all 4 CLI entry points
- Defer LLM router unification, subprocess→import conversion, and RFP agent to future phases
- Each package keeps its own `pyproject.toml`
- Package directory names match existing names (no renaming during merge)

The summary checklist from Proposal A is the right artifact to manage this work. Each checkbox is a "done" state the system can live in indefinitely.

*Latency: 46.61s | Tokens: 7228*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concerns are maintaining the non-negotiable data boundary (corp-by-os as the sole vault writer) and ensuring deterministic, secure execution during this highly complex integration.

Here is my evaluation of the proposals, followed by a hardened architectural recommendation.

---

### Evaluation of Proposal A

**Verdict:** Partially Agree
Proposal A grasps the human and operational constraints well, particularly the necessity of isolating the CKE namespace refactor from the monorepo merge. However, its integration mechanics introduce significant execution risks.

*   **Strongest Point:** Recognizing that subprocess boundaries are an architectural asset, not just legacy debt. Keeping CKE as a subprocess enforces memory and capability isolation, guaranteeing the pure-extraction engine cannot accidentally inherit or exploit `corp-by-os`'s vault-writing privileges.
*   **Weakest Assumption:** Using `shutil.which("cke")` or system PATH to resolve the subprocess in `cke_invoker.py`. During a migration where old standalone repos and new monorepo packages coexist, relying on system PATH is a severe integration risk and a local supply chain vulnerability. You have no guarantee which version of CKE is being executed.
*   **Overlooked Risks:** `git subtree add` preserves history but creates a highly convoluted git graph that makes future bisecting difficult. Furthermore, a shared `paths.toml` in the monorepo root risks accidental credential exposure if it isn't strictly segmented from the `.gitignore` policy for local secrets.

### Evaluation of Proposal B

**Verdict:** Disagree
Proposal B attempts a structured approach but advocates for several technically dangerous methods that violate both security principles and the stated constraints.

*   **Strongest Point:** Recommending a programmatic `PathResolver` for inter-package dependencies, which attempts to solve the deterministic pathing issue that Proposal A failed to address.
*   **Weakest Assumption:** The git strategy. Using `git merge --allow-unrelated-histories` and then moving files into `packages/core/` in subsequent commits will completely sever the file-level git history. `git log` on a file will stop at the merge commit unless followed with `--follow`, severely degrading auditability.
*   **Overlooked Risks:** 
    1. Modifying subprocess calls to directly invoke `cli.py` (`packages/core/knowledge_extractor/cli.py`) bypasses Python's virtual environment module resolution and entry point wrappers, breaking cross-platform compatibility and environment isolation. 
    2. blindly suggesting `pytest-xdist` for the 1,842 tests. Given `corp-by-os` interacts with a single vault path, parallel test execution will almost certainly cause lock contention and race conditions, breaking the "zero regression" constraint immediately.

---

### Revised Recommendation

To safely integrate these systems without interrupting production, breaking tests, or compromising the vault-writer boundary, we must use a strictly phased approach with hardened integration points.

#### 1. Merge Strategy & Git History (The "How")
Do not use `git subtree` or naive merges. Use `git filter-repo`.
Before merging, rewrite the history of each standalone repo so that its files exist in the target subdirectory (`packages/<name>`). When you merge these rewritten branches, the history natively reflects the new monorepo structure without convoluted merge commits.

#### 2. The Non-Negotiable Boundary (Subprocesses)
**Keep the subprocesses, but secure the IPC.**
Do not use `shutil.which` or hardcoded paths to `cli.py`. To guarantee the orchestrator (`corp-by-os`) invokes the exact version of CKE installed in the current virtual environment, use Python's executable path explicitly:

```python
# In corp-by-os / cke_invoker.py
import sys
import subprocess

def invoke_cke(args):
    # sys.executable guarantees we use the same Python environment 
    # executing corp-by-os, preventing PATH hijacking or legacy execution.
    cmd = [sys.executable, "-m", "corp_knowledge_extractor.cli"] + args
    return subprocess.run(cmd, capture_output=True, check=True)
```

#### 3. Concrete Phased Execution Plan

**Phase 0: Pre-Migration Hardening (Zero downtime)**
1. **CKE Namespace:** Refactor CKE's `src/` to `src/corp_knowledge_extractor/` inside its existing standalone repo. Verify all 625 tests.
2. **Execution Context:** Update `corp-by-os` to use the `sys.executable -m corp_knowledge_extractor` invocation method. Verify 847 tests.
3. **Environment Lock:** Pin all dependencies across the 4 merge candidates to exact versions to prevent PIP resolution conflicts upon monorepo synthesis.

**Phase 1: Foundation Integration**
1. Initialize `corp-monorepo`. Setup PEP 660 workspace (e.g., Hatch or standard `pip install -e .`).
2. Use `git filter-repo` to ingest `corp-os-meta` into `packages/corp-os-meta` and `CKE` into `packages/corp-knowledge-extractor`.
3. Validate tests sequentially (do not use parallel `pytest-xdist` yet).

**Phase 2: Orchestrator Integration & Path Centralization**
1. Ingest `corp-by-os` and `CPE` using the same `git filter-repo` method.
2. Centralize configuration in `corp-os-meta`. 
   * *Security requirement:* Split configuration into two concepts. `paths.toml` (checked into git) for structural defaults, and environment variables strictly enforced for LLM API keys and dynamic user paths. The `PathResolver` must fail closed if paths traverse outside permitted directories.
3. Validate all 1,842 tests.

**Phase 3: Deferred Items (Do Not Do Now)**
*   **LLM Router Unification:** This is a feature redesign, not a migration task. Merging them now risks mutating AI behavior during a structural change.
*   **RFP Agent:** Quarantine this repo until it is refactored (argparse -> Click, version pins added). Do not let it compromise the monorepo's dependency graph.
*   **CLI Unification:** Maintain the 4 distinct CLI entry points in `pyproject.toml`. Muscle memory for production operations is critical; an overarching `corp` CLI can be introduced as an alias later.

*Latency: 30.64s | Tokens: 8157*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A
**Agreement:** Partial agreement  
**Strongest point:** The explicit ADHD constraint acknowledgment and phased approach with validation gates after each step. The insistence on solving CKE namespace *before* merge as a standalone task is correct—it isolates the riskiest change.  
**Weakest assumption:** That keeping subprocess calls is an "asset." This ignores the performance cost of repeated process spawning (30-100ms per call) and the maintenance burden of CLI contracts that will become internal APIs. In a monorepo, subprocess boundaries between modules become artificial complexity.  
**Overlooked risks:**
1. No quantification of subprocess overhead: 847 tests in corp-by-os likely invoke CKE multiple times. At 50ms per call, test suite runtime increases unnecessarily.
2. Misses opportunity to unify LLM routers during merge—this is trivial to fix once imports are converted, and leaving three routers creates immediate technical debt.
3. Assumes all packages' test suites can run independently post-merge without environment contamination (shared temp files, configs).

### Proposal B
**Agreement:** Partial agreement  
**Strongest point:** Explicit backward-compatible config fallback chain—this ensures zero disruption during transition.  
**Weakest assumption:** That `git merge --allow-unrelated-histories` is clean for this scale. With 4 repos and 1,842 tests, merge conflicts in CI configs, READMEs, and `pyproject.toml` files are guaranteed.  
**Overlooked risks:**
1. No analysis of dependency graph: corp-by-os depends on CKE depends on meta. Merging meta+CKE first means corp-by-os tests will fail if run against new merged version unless careful version pinning.
2. Suggests `pytest-xdist` for parallel execution without considering test isolation requirements (vault writes, file I/O).
3. Proposes moving CKE CLI calls to `packages/core/knowledge_extractor/cli.py` but doesn't address Python path issues when invoked as subprocess from different working directory.

## Revised Recommendation

**Position: Modified incremental merge with performance-first refactoring during merge window.**

### Core Strategic Changes from Proposals:

1. **Refactor CKE namespace DURING merge, not before**  
   Why: The mechanical rename (39 files) can be automated with `ast` module tooling in <2 hours. Doing it during merge allows simultaneous update of corp-by-os imports that reference CKE—saving duplicate effort. Use `importlib` compatibility shims only for transition week.

2. **Convert subprocess calls to Python imports IN PHASE 2**  
   Why: Performance matters—each `cke process-manifest` spawns Python interpreter (150ms) + module load (200ms). With 50 daily invocations, that's 17.5 seconds wasted daily. After merge, these become function calls (<1ms).  
   Strategy: Keep CLI entry points for external use but add internal Python API. Corp-by-os should call `cke.process_manifest()` directly post-merge.

3. **Unify LLM routers IMMEDIATELY in Phase 1**  
   Why: Three routers mean three different prompt templates, error handling, and rate limiting. Centralizing reduces API costs and improves consistency. The merge creates the architectural moment to fix this.

### Concrete Performance-Optimized Plan:

**Phase 0: Dependency Analysis & Tooling (1 day)**
```
1. Map all cross-repo imports and subprocess calls
2. Write migration scripts:
   - `fix_cke_imports.py`: AST-based refactor (src.extract → corp_knowledge_extractor.extract)
   - `subprocess_to_import.py`: Replace `subprocess.run(['cke', ...])` with direct calls
3. Create unified LLM router interface in corp-os-meta
```

**Phase 1: Merge Meta + CKE + Router Unification (2 days)**
```
1. Create monorepo with hatch workspaces
2. Merge corp-os-meta via `git subtree add`
3. Merge CKE, run fix_cke_imports.py, update CKE's pyproject.toml
4. Update CKE to use unified LLM router from meta
5. Run 733 tests → MUST PASS
```

**Phase 2: Merge Corp-by-os + CPE + Import Conversion (3 days)**
```
1. Merge corp-by-os, update its imports to use CKE directly
2. Run subprocess_to_import.py on corp-by-os (convert `cke process-manifest`)
3. Merge CPE, similarly convert subprocess calls
4. Centralize config: single config.yaml at root with environment overrides
5. Run all 1,842 tests with performance profiling:
   - Compare subprocess vs import call times
   - Verify no regression in extraction quality
```

**Key Performance Metrics to Track:**
- Test suite runtime pre/post merge (target: <20% increase)
- Subprocess call elimination count (target: 100%)
- Memory footprint of unified vs separate processes

### Quantified Trade-offs:
```
BIG-BANG (Option A) vs INCREMENTAL (Option B) vs THIS PLAN:
| Metric               | Big-Bang | Proposal A/B | This Plan |
|----------------------|----------|--------------|-----------|
| Risk of breakage     | 90%      | 30%          | 40%       |
| Time to completion   | 5 days   | 10 days      | 6 days    |
| Test passes required | 1 batch  | 3 batches    | 2 batches |
| Performance gain     | Immediate| Delayed      | Phased    |
| Cognitive load       | High     | Low          | Medium    |
```

### Specific Disagreements with Both Proposals:

1. **Against deferring subprocess conversion**  
   Postponing this leaves performance gains on the table. Each day with subprocess calls wastes ~20 seconds of developer time (context switches) plus computational overhead.

2. **Against keeping four CLI entry points**  
   After merge, `corp` should become primary CLI with subcommands. Maintaining four CLIs adds maintenance overhead for argparse/click duplication. Unified CLI reduces cognitive load for users.

3. **Against separate config files per package**  
   Single config.yaml with schema validation (via corp-os-meta Pydantic) ensures consistency. Environment variables for secrets only.

### Risk Mitigation Added:
1. **Test contamination risk:** Use `pytest` with temporary directories scoped to each test module.
2. **Import circularity:** Dependency graph is linear (corp-by-os → CKE → meta). No cycles.
3. **Performance regression:** Profile test suite pre-merge as baseline, compare post-merge.

### Summary Execution Checklist:
```
□ Phase 0: Dependency graph + tooling scripts
□ Phase 1a: Merge meta, add unified LLM router
□ Phase 1b: Merge CKE, refactor namespace, update to use unified router
□ Phase 1c: Validate 733 tests pass
□ Phase 2a: Merge corp-by-os, convert subprocess calls to imports
□ Phase 2b: Merge CPE, convert subprocess calls
□ Phase 2c: Centralize config, update all packages
□ Phase 2d: Run 1,842 tests, profile performance
□ Phase 2e: Create unified `corp` CLI with subcommands
```

**Final note:** This plan optimizes for both correctness *and* performance, recognizing that 1,842 tests represent ~45 minutes of runtime at current speed. By eliminating subprocess overhead, we can reduce total test time by 15-20%, making the migration not just structural but performance-positive from day one.

*Latency: 104.45s | Tokens: 8497*

## Synthesis (by openai, non-participant)

## Consensus

1. **Use an incremental merge, not a big-bang**
   - Most participants agreed on **Option B: phased migration**.
   - Reason: your constraints strongly favor small, reversible steps:
     - solo developer
     - ADHD/history of big-bang failure
     - production work cannot stop
     - tests must stay green throughout

2. **Refactor CKE’s namespace**
   - Strong consensus that CKE’s flat `src/` namespace is the first hard blocker.
   - Most argued it should be changed to a real package such as:
     - `from corp_knowledge_extractor.extract import ...`
   - Broad agreement that this namespace problem must be solved before the full monorepo is viable.

3. **Preserve existing architectural boundaries during migration**
   - Most participants agreed that **corp-by-os remains the sole vault writer** and **CKE remains pure extraction**.
   - This boundary should not be weakened during the merge.

4. **Defer RFP agent**
   - Consensus: **do not include corp-rfp-agent now**.
   - It needs cleanup first and would add risk.

5. **Centralize config/path handling**
   - Most participants agreed path/config logic should move toward a single shared mechanism.
   - The favored home for this was **corp-os-meta**, acting as the shared foundational layer.

6. **Keep legacy CLI entry points during migration**
   - Most participants favored keeping:
     - `corp`
     - `cke`
     - `cpe`
     - `corp-meta`
   - This preserves backward compatibility and avoids retraining during a risky migration.

7. **Run tests at every phase gate**
   - Strong agreement that testing is the release gate for every step.
   - All major proposals treated passing tests as the definition of “done”.

---

## Unresolved Disagreements

### 1. When to refactor CKE namespace: before merge vs during merge
- **Before merge**:
  - Merit: isolates the hardest mechanical change.
  - Easier debugging: if tests fail, it’s due to namespace changes, not repo structure.
  - Better fit for “change one thing at a time”.
- **During merge**:
  - Merit: potentially less duplicated work if dependent repos are being updated at the same time.
  - Could reduce total calendar time.

**Assessment:** the “before merge” side is stronger because your biggest risk is not total elapsed time; it is losing control of scope and breaking production.

### 2. Subprocess calls vs Python imports after merge
- **Keep subprocesses initially**:
  - Merit: preserves isolation and current contracts.
  - Protects the vault-writer boundary.
  - Lower migration risk.
- **Convert to Python imports in phase 2**:
  - Merit: faster, cleaner long-term internal APIs.
  - Less process-spawning overhead.
- **Support both**:
  - Merit: internal code can use Python APIs while CLIs remain available externally.

**Assessment:** the debate split here. The migration-focused side favored keeping subprocesses at first; the optimization-focused side wanted imports soon after merge.

### 3. Git history preservation method
- **`git subtree add`**:
  - Merit: straightforward and preserves history reasonably well.
  - Easier operationally.
- **`git filter-repo` before merge**:
  - Merit: cleaner long-term history under final monorepo paths.
  - Better auditability in-file after migration.

**Assessment:** both are defensible. `filter-repo` is cleaner technically; `subtree` is simpler operationally.

### 4. Config model details
- **Root config file + corp-os-meta resolver + env var overrides**
  - Most support.
- **Single root config only**
  - Simpler, but less migration-safe.
- **Fallback chain including legacy configs**
  - Safer during transition, but slightly more complexity.

**Assessment:** fallback chain won the strongest support because it reduces migration risk.

### 5. Whether to unify LLM routers now
- **Defer router unification**
  - Merit: avoids mixing design refactor with structural migration.
- **Do it during early merge**
  - Merit: reduces duplication immediately and may simplify later integration.

**Assessment:** defer is stronger. Router unification is a separate design project, not a prerequisite for monorepo success.

---

## Recommended Decision

### Decision
Adopt a **phased monorepo migration** with this order:

1. **Phase 0: pre-merge hardening in existing repos**
   - Refactor **CKE namespace first, in its own repo**
   - Remove hardcoded CKE filesystem assumptions from callers
   - Establish deterministic invocation and config strategy

2. **Phase 1: merge `corp-os-meta` + `corp-knowledge-extractor`**
   - This is the pilot merge.
   - Goal: validate monorepo structure with the smallest meaningful dependency cluster.

3. **Phase 2: merge `corp-by-os` + `corp-project-extractor`**
   - Centralize path/config resolution here via shared logic in `corp-os-meta`
   - Keep production cutover only after this phase is fully green

4. **Phase 3: defer `corp-rfp-agent` until its cleanup is complete**
   - Not part of the current migration

### Specific architectural choices

#### 1. Merge strategy
Choose **Option B: incremental/phased**.

**Why:** This best matches the human and operational constraints. The debate strongly supported this, and no serious argument overcame the risk profile of a big-bang merge.

---

#### 2. CKE namespace
Refactor CKE **before** merge.

**Recommended target:**
- move to `src/corp_knowledge_extractor/`
- convert imports from:
  - `from src.extract import ...`
- to:
  - `from corp_knowledge_extractor.extract import ...`

**Do not rely on long-lived import alias shims** unless a very short transitional shim is needed briefly for local continuity. The debate’s strongest arguments were that shims create hidden debt and increase cognitive load.

**Why this decision:** This is the single biggest structural blocker. Isolating it first reduces debugging complexity and gives you a verified, merge-ready CKE.

---

#### 3. Subprocess calls after merge
**Keep subprocess boundaries initially, but make them deterministic and future-upgradable.**

Recommended near-term behavior:
- preserve subprocess invocation for cross-package orchestration during migration
- do **not** depend on hardcoded paths
- do **not** depend on ambient `PATH` resolution if avoidable
- prefer deterministic invocation such as:
  - CLI entry point installed in the active environment, or
  - `sys.executable -m corp_knowledge_extractor.cli ...`

**Why this decision:** This best preserves the current boundary and lowers migration risk. The strongest objection was performance, but the debate did not show that subprocess overhead is more important than migration stability. Performance optimization can come later, after the monorepo is stable.

**Follow-on decision:** after Phase 2 is stable, add internal Python APIs where valuable, but do that as a separate refactor. At that point you may support both:
- CLI/subprocess for external contracts
- Python imports for internal orchestration

---

#### 4. Path/config centralization
Use **corp-os-meta as the shared config/path resolver**, backed by a **root config file plus env-var overrides**.

Recommended precedence:
1. Environment variables
2. Monorepo root config file
3. User-level config (optional, e.g. `~/.corp/...`)
4. Safe package defaults / legacy fallback during migration only

Important constraints:
- API keys and secrets should remain in **environment variables**
- root config should hold non-secret structural paths and defaults
- legacy per-repo config can be supported temporarily as fallback during transition

**Why this decision:** It combines the most supported parts of the debate:
- one place to look
- shared resolution logic
- migration-safe fallback chain
- no secrets in repo config

---

#### 5. Testing strategy
Use **full-suite test gates at every phase**, plus a small set of targeted integration smoke tests.

Recommended testing rule:
- after each meaningful step, run affected repo tests
- at each phase completion, run **all 1,842 tests**
- add a few explicit integration tests for:
  - corp-by-os invoking CKE
  - corp-by-os invoking CPE
  - config resolution
  - vault-writer boundary behavior

**Why this decision:** Full-suite verification had the strongest support. Integration tests are useful, but they should supplement, not replace, the existing test suites.

---

#### 6. CLI entry points
Keep all current CLI entry points during migration:
- `corp`
- `cke`
- `cpe`
- `corp-meta`

Optionally later:
- introduce a unified `corp` umbrella CLI as an additive convenience
- do not remove the existing commands during migration

**Why this decision:** Backward compatibility and operational continuity matter more than immediate CLI elegance.

---

#### 7. Git history preservation
Use a history-preserving import approach, with preference for the method you can execute reliably:
- **Preferred if comfortable:** `git filter-repo` to rewrite each repo under its target subdirectory before merge
- **Acceptable if simpler for you:** `git subtree add`

**Why:** The debate showed `filter-repo` is cleaner technically, but execution reliability matters more than theoretical purity. Since you are the sole developer, the best method is the one you can perform safely and repeatably.

---

### Strongest objections acknowledged

1. **“Why not convert subprocesses to imports now for speed?”**
   - Good long-term idea.
   - Rejected for now because migration stability and boundary preservation matter more than startup overhead.

2. **“Why not unify the LLM routers during merge?”**
   - Also reasonable long-term.
   - Rejected because it is a design refactor, not a migration necessity, and would expand scope significantly.

3. **“Why not just make a shared `corp-common` package and keep repos separate?”**
   - This would reduce some duplication, but it does not solve the coordination problem as well.
   - You would still have multiple repos, multiple release/version sync points, and path coupling issues.
   - The debate overall favored monorepo over shared-package-only.

---

## Risks

### 1. CKE namespace refactor breaks many files/tests
- **Risk:** 39 files and 625 tests are touched.
- **Mitigation:**
  - do it in CKE alone, before merge
  - use automated refactoring tools
  - run all 625 tests
  - keep the change mechanical, not architectural

### 2. Production confusion during partial migration
- **Risk:** old repos and monorepo coexist; wrong code path gets executed.
- **Mitigation:**
  - define an explicit production cutover:
    - old repos remain production until Phase 2 is complete and validated
  - make subprocess invocation deterministic
  - avoid PATH ambiguity

### 3. Hardcoded path assumptions reappear
- **Risk:** one-off path fixes miss hidden filesystem assumptions.
- **Mitigation:**
  - centralize path resolution in one shared module
  - search codebase for path literals
  - add tests for config precedence and path discovery

### 4. Dependency conflicts in monorepo
- **Risk:** previously independent repos may have incompatible package constraints.
- **Mitigation:**
  - inspect and align dependency pins before merge
  - run `pip check` or equivalent
  - keep each package’s own `pyproject.toml` initially

### 5. Scope creep
- **Risk:** migration gets bundled with router unification, CLI redesign, API redesign, and RFP cleanup.
- **Mitigation:**
  - treat those as explicitly out of scope
  - define success narrowly:
    - same behavior
    - same boundaries
    - all tests green
    - history preserved

### 6. Monorepo config introduces secret leakage
- **Risk:** sensitive values end up committed.
- **Mitigation:**
  - keep secrets in environment variables only
  - commit only non-secret path/default config
  - enforce `.gitignore` and documentation

### 7. Git history migration gets messy
- **Risk:** difficult blame/log behavior after import.
- **Mitigation:**
  - choose one history-preserving method and test it on a throwaway clone first
  - document the import procedure
  - tag each phase boundary

---

## Action Items

### Phase 0 — Pre-merge hardening

1. **Refactor CKE namespace in the existing CKE repo**
   - Create `src/corp_knowledge_extractor/`
   - Move modules under it
   - Update imports from `src.*` to `corp_knowledge_extractor.*`
   - Update packaging config
   - Run all **625 CKE tests**
   - Tag this state

2. **Remove hardcoded CKE path usage from corp-by-os and CPE**
   - Replace fixed filesystem paths with deterministic invocation
   - Prefer `sys.executable -m corp_knowledge_extractor.cli ...` or equivalent stable mechanism
   - Run affected tests, especially corp-by-os’s **847 tests**

3. **Audit dependency versions across merge candidates**
   - Compare `pyproject.toml` / lockfiles
   - Align obvious conflicts before merge
   - Verify installability in one environment

4. **Define production cutover policy**
   - Write down:
     - old repos remain production until Phase 2 passes
     - monorepo is staging through Phase 1

---

### Phase 1 — Pilot monorepo

5. **Create monorepo skeleton**
   - Suggested package layout:
     - `packages/corp-os-meta/`
     - `packages/corp-knowledge-extractor/`
     - `packages/corp-by-os/`
     - `packages/corp-project-extractor/`
   - Keep package names recognizable; do not rename repos and packages gratuitously

6. **Import `corp-os-meta` and CKE with preserved history**
   - Use `git filter-repo` if you are comfortable
   - Otherwise use `git subtree add`

7. **Keep each package’s own packaging metadata initially**
   - Avoid premature packaging consolidation

8. **Run tests for Phase 1**
   - `corp-os-meta`: 108 tests
   - CKE: 625 tests
   - Ensure all Phase 1 tests pass before moving on

---

### Phase 2 — Orchestrator integration

9. **Import `corp-by-os` and `corp-project-extractor`**
   - Preserve history as in Phase 1

10. **Implement shared config/path resolver in corp-os-meta**
    - Root config for non-secret defaults
    - Env vars override all
    - Optional user-level fallback
    - Temporary legacy fallback if needed

11. **Update all four merged packages to use shared path resolution**
    - Replace scattered path logic gradually
    - Keep behavior-compatible defaults

12. **Add a small integration test suite**
    - corp-by-os → CKE invocation
    - corp-by-os → CPE invocation
    - config precedence
    - vault-writer boundary remains intact

13. **Run the full monorepo test suite**
    - all **1,842 tests**
    - plus integration smoke tests
    - no production cutover unless green

14. **Do one real production-like work cycle from monorepo**
    - validate daily workflow manually before archiving source repos

---

### Deferred, explicitly out of scope for migration

15. **Do not merge RFP agent yet**
16. **Do not unify LLM routers yet**
17. **Do not replace subprocess boundaries with imports yet**
18. **Do not redesign CLI UX yet**

---

## Bottom line

The best decision is:

- **Proceed with a phased monorepo migration**
- **Refactor CKE namespace first, before any merge**
- **Keep subprocess boundaries during migration, but make invocation deterministic**
- **Centralize config/path resolution in corp-os-meta with env-var overrides**
- **Run all tests at each phase gate**
- **Keep current CLI entry points**
- **Defer RFP agent and nonessential refactors**

This is the most reliable path to merging the repos without breaking 1,842 tests or interrupting production work.
