# AI Council Debate: ## Question: How should we build a self-testing sandbox that runs end-to-end pip

**Date:** 2026-03-25 22:59:22
**Panel:** claude-opus-4-6, deepseek-reasoner, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 214.4s
**Mode:** full (3-model panel)
**Source:** council_inbox\council_sandbox_testing.md

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Use **completely separate temp directories and databases** (Option A for sandbox strategy) implemented as a **CLI command (`corp test-pipeline`)** that creates an isolated parallel universe of the entire pipeline, runs it, verifies it, tears it down, and produces a structured report. No production paths are touched, ever. CKE uses the **extract-once-replay-forever fixture approach** (Option D) with an explicit `--live` flag for real API calls.

---

## Rationale

- **Isolation is the only zero-risk strategy.** Options B and C both touch production paths, which means a bug in the revert logic—or a crash mid-revert—leaves production corrupted. Option A makes corruption *structurally impossible*. You don't need to trust your revert code to protect production data; the revert only cleans up temp directories, and even if it fails, the OS cleans `/tmp` eventually.

- **The "verify the revert" problem disappears.** Question 5 becomes trivial: tear down the temp directory tree. `shutil.rmtree()` is your revert. No row-count comparison, no hash verification, no "did we miss a table?" anxiety. The production databases are never opened in write mode during testing.

- **CKE fixture replay gives you deterministic, free, fast tests 99% of the time.** You already have 690 extraction fixtures. Record the API request/response pairs once with `--live`, serialize them, replay them forever. This is the standard "VCR cassette" pattern. When you *want* to test real extraction quality, pass `--live` explicitly and accept the $0.10 cost. This makes the default test run take seconds, not minutes.

- **A CLI command (`corp test-pipeline`) is the right integration point.** It uses your real pipeline code paths (not a separate script that drifts), it's discoverable via `corp --help`, it can accept flags (`--live`, `--keep-sandbox`, `--report-format`), and it can be called from pytest for CI integration later. Standalone scripts always rot.

- **ADHD-friendly report via structured sections with emoji status indicators.** A wall of text is a wall of ignorance. The report should be a tiered summary: 3-line verdict at top, then per-step detail on demand.

---

## Architecture

### Sandbox Layout

```
%TEMP%/corp-test-pipeline-{timestamp}/
├── MyWork/
│   ├── 00_Inbox/          ← test files copied here
│   ├── 10_Projects/       ← routing destination
│   ├── 30_Reference/      ← routing destination
│   └── 40_Archive/
├── Vault/
│   └── 01_Knowledge/      ← vault ingest target
├── db/
│   ├── ops.db             ← fresh schema, empty
│   ├── index.db           ← fresh schema, empty
│   └── overnight_state.db ← fresh schema, empty
├── fixtures/
│   └── cke_responses/     ← recorded API responses (copied from project)
└── report/
    └── test-report.md     ← output
```

### The Key Mechanism: Config Override

Your pipeline code currently reads paths from config (or hardcoded constants). The sandbox works by **injecting an override config** that points every path to the temp tree:

```python
@dataclass(frozen=True)
class PipelineConfig:
    mywork_root: Path
    vault_root: Path
    ops_db_path: Path
    index_db_path: Path
    overnight_db_path: Path
    cke_fixture_dir: Path | None  # None = live API calls
    
    @classmethod
    def production(cls) -> "PipelineConfig":
        """Real paths from environment/config."""
        ...
    
    @classmethod
    def sandbox(cls, temp_root: Path, live_cke: bool = False) -> "PipelineConfig":
        """All paths under temp_root. No production contact."""
        ...
```

If your pipeline code doesn't already accept a config object, **this is the one refactor you must do first.** Every function that touches a file path or database must accept its paths from config, not from module-level constants. This is the investment that makes testing possible—and it also makes the production code better (explicit dependencies, no hidden globals).

### Answers to Each Question

**Q1: Sandbox strategy → Option A (completely separate temp dirs/databases)**

No hybrid. No "real ops.db for audit trail." The test *generates* ops.db events inside the sandbox; you can inspect them in the report. If you want to record "a test was run" in production ops.db, do it as a single event *after* the test completes: `{"event": "pipeline_test", "result": "PASS", "duration_s": 12.3}`. One write. Not interleaved with test operations.

**Q2: CKE extraction → Option D (extract once, replay forever) with `--live` escape hatch**

```
corp test-pipeline              ← uses fixtures, free, fast, deterministic
corp test-pipeline --live       ← real API calls, ~$0.10, tests real extraction
corp test-pipeline --record     ← real API calls + saves responses as new fixtures
```

Implementation: wrap your CKE client with a `CKEClient` protocol/interface. In sandbox mode, inject a `ReplayCKEClient` that looks up fixtures by file hash. This is ~50 lines of code.

```python
class CKEClient(Protocol):
    def extract(self, file_path: Path, tier: str) -> ExtractionResult: ...

class LiveCKEClient:
    """Calls Gemini/Claude."""
    ...

class ReplayCKEClient:
    """Looks up pre-recorded responses by file content hash."""
    def __init__(self, fixture_dir: Path): ...
    def extract(self, file_path: Path, tier: str) -> ExtractionResult:
        key = hash_file(file_path)
        fixture = self.fixture_dir / f"{key}_{tier}.json"
        if not fixture.exists():
            raise FixtureMissing(f"No fixture for {file_path.name}. Run with --record.")
        return ExtractionResult.from_json(fixture.read_text())
```

**Q3: MyWork sandbox → completely separate temp directory, no 99_Sandbox in production**

A `99_Sandbox` zone in real MyWork creates a permanent cognitive tax: "Is this real? Is this test data?" Every time you look at MyWork, forever. The temp directory exists for 30 seconds during the test, then vanishes. Zero ongoing cognitive load.

**Q4: Revert scope → `shutil.rmtree(temp_root)`**

That's it. Everything is inside `temp_root`. There is no selective revert. There is no "what about overnight_state.db?" question. The entire universe is created, used, and destroyed.

The *only* production-side write is the optional single event in ops.db recording that a test ran.

**Q5: Verify the revert → verify the temp directory no longer exists**

```python
assert not temp_root.exists(), f"Sandbox not cleaned: {temp_root}"
```

If you want extra confidence, snapshot the production directory tree (file count + total size) before and after:

```python
pre_snapshot = snapshot_production_state(prod_config)
# ... run entire sandbox test ...
post_snapshot = snapshot_production_state(prod_config)
assert pre_snapshot == post_snapshot, f"Production state changed!\n{diff(pre, post)}"
```

This is a 10-line safety net, not a complex verification system.

**Q6: CLI command → `corp test-pipeline`**

```
corp test-pipeline                     # fixture mode, fast
corp test-pipeline --live              # real API calls
corp test-pipeline --record            # real APIs + save fixtures
corp test-pipeline --keep-sandbox      # don't delete temp dir (for debugging)
corp test-pipeline --files path/to/custom/  # use specific test files
corp test-pipeline --verbose           # per-step detail in console
```

Internally, it's also callable as a pytest fixture for CI:

```python
# tests/integration/test_full_pipeline.py
def test_pipeline_end_to_end():
    result = run_pipeline_sandbox(live=False)
    assert result.all_passed
    assert result.revert_verified
```

**Q7: Report format**

```markdown
# 🏗️ Pipeline Test Report
**2025-01-15 14:32:07** | Duration: 11.4s | Mode: fixture | Cost: $0.00

## Verdict: ✅ ALL PASS (8/8 steps)

| Step | Status | Duration | Detail |
|------|--------|----------|--------|
| 1. Inbox intake | ✅ PASS | 0.3s | 5 files copied |
| 2. Classify | ✅ PASS | 0.8s | 3 specs, 1 proposal, 1 reference |
| 3. Rename | ✅ PASS | 0.2s | 5/5 renamed per convention |
| 4. Route | ✅ PASS | 0.4s | 3→Projects, 2→Reference |
| 5. Dedup | ✅ PASS | 0.1s | 0 duplicates found |
| 6. Extract (CKE) | ✅ PASS | 2.1s | 5 extractions, avg quality: 0.87 |
| 7. Vault ingest | ✅ PASS | 1.2s | 5 notes created, trust: t2_automated |
| 8. Index + Retrieve | ✅ PASS | 0.9s | 3 test queries, avg 4.2 results |

## Revert Verification
- Sandbox directory: ✅ removed
- Production state: ✅ unchanged (files: 1,247→1,247, ops.db rows: 8,932→8,933*)

*+1 row: test execution event logged

## Extraction Quality
| File | Quality Score | Tier | Sections |
|------|--------------|------|----------|
| JLR_WMS_Spec_v2.pdf | 0.91 | T2_API | 14 |
| ... | ... | ... | ... |

## Retrieve Spot-Check
| Query | Results | Top Match | Score |
|-------|---------|-----------|-------|
| "warehouse management requirements" | 6 | JLR_WMS_Spec_v2 | 0.94 |
| ... | ... | ... | ... |
```

Saved as both markdown (human-readable) and JSON (machine-parseable for trend tracking).

---

### Implementation Plan

**Phase 1: Config extraction (prerequisite, ~2-3 hours)**
- Create `PipelineConfig` dataclass
- Refactor pipeline functions to accept config instead of reading global paths
- This is the structural investment; everything else is easy after this

**Phase 2: Sandbox scaffolding (~1-2 hours)**
- `create_sandbox(temp_root) -> PipelineConfig` — creates directory tree, initializes empty databases with correct schema
- `destroy_sandbox(temp_root)` — `shutil.rmtree` + verification
- `snapshot_production_state(config) -> StateSnapshot` — file counts, db row counts

**Phase 3: Test file corpus (~30 min)**
- Curate 5-8 test files covering different types (spec PDF, proposal DOCX, reference spreadsheet, duplicate, edge case)
- Store in `tests/fixtures/pipeline_test_files/`
- These are *versioned in the repo*, not copied from production at runtime

**Phase 4: CKE replay client (~1 hour)**
- `ReplayCKEClient` with fixture lookup by content hash
- `--record` mode that wraps `LiveCKEClient` and saves responses
- Record initial fixture set with one `--record` run

**Phase 5: Pipeline runner + report generator (~2-3 hours)**
- `run_pipeline_sandbox(config, mode) -> TestReport`
- Each step returns `StepResult(status, duration, detail)`
- Report renderer (markdown + JSON)

**Phase 6: CLI integration (~30 min)**
- Wire into `corp test-pipeline` with Click/Typer
- Add flags: `--live`, `--record`, `--keep-sandbox`, `--verbose`

**Total: ~8-10 hours of focused work.** Phase 1 is the only part that touches existing production code.

---

## Trade-offs

| You gain | You give up |
|----------|-------------|
| Zero risk to production data | Can't test production-specific path edge cases (spaces in Windows paths, long paths, permissions) — mitigate with a separate path-stress test |
| Deterministic fixture-based tests that run in seconds | Default mode doesn't catch CKE API changes or model drift — mitigate with weekly `--live` runs |
| Simple revert (delete a directory) | No audit trail of test operations in production ops.db — mitigate with single summary event |
| Clean config abstraction benefits all future code | Must refactor existing code to accept config injection (~2-3 hours) |
| One-command autonomous execution | Initial fixture recording requires one manual `--record` run |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Config refactor misses a hardcoded path** — some function still writes to production during sandbox test | Medium (first time) | High | Phase 1 includes a grep/search for all hardcoded paths. Sandbox runs with production dirs set to read-only (or non-existent dummy paths that would cause loud failures). |
| **Fixture drift** — recorded CKE responses no longer match what real APIs return, so tests pass but real pipeline would fail | Medium (over months) | Medium | Schedule monthly `--live` run. Compare live results to fixture results and alert on significant divergence. |
| **Sandbox doesn't cover Windows-specific issues** (path separators, file locking, long paths) | Low | Medium | All paths use `pathlib.Path`. Add one explicit test for Windows long path handling. Test file locking with a "file in use" scenario. |
| **Test corpus too narrow** — 5-8 files don't cover real-world diversity | Medium | Low | Start narrow, expand corpus each time a real pipeline issue is found. Each production bug becomes a new test file. |
| **Partial failure during sandbox leaves temp dir behind** | Medium | Very Low | Use `try/finally` around the entire run. Even if cleanup fails, it's in `%TEMP%` which the OS manages. `--keep-sandbox` flag makes this a feature, not a bug. |
| **Claude Code can't run it autonomously due to interactive prompts or environment assumptions** | Low | Medium | Ensure `corp test-pipeline` requires zero interactive input. All config via flags. Test the "Claude runs this" scenario explicitly in Phase 6 by having Claude Code execute it once. |

*Latency: 86.06s | Tokens: 5137*

### Deepseek (deepseek-reasoner)

## Position
Use temporary directories and databases for complete isolation (Option A), with mock CKE responses from fixtures (Option B), controlled via a `corp test-pipeline` CLI command that generates a scannable report and verifies complete reversion through file/database state snapshots.

## Rationale
- **Complete isolation eliminates risk**: Temp directories/databases prevent any contamination of production data, including the precious ops.db audit trail. This allows parallel test runs without cleanup conflicts.
- **Deterministic testing with fixtures**: Using saved CKE outputs ensures tests are repeatable, fast ($0 cost), and not subject to API variability. Real API tests can run separately as integration checks.
- **Integrated CLI approach**: A `corp test-pipeline` command ensures the test uses the actual production code paths, revealing integration issues that standalone scripts might miss.
- **Verifiable cleanup**: Comparing database row counts and file system checksums before/after provides mathematical proof that the sandbox left no residue.

## Trade-offs
- **Temporary environments miss production nuances**: File permissions, network mounts, or path-length issues specific to the real MyWork directory won't surface.
- **Mocked extraction lacks realism**: API changes or quality regressions in Gemini/Claude won't be caught until periodic live tests.
- **Setup overhead**: Creating complete temp environments is slower than snapshotting (but safer).
- **No audit trail for tests**: Events in temp ops.db are discarded, losing debugging context (but we keep console logs).

## Risks
1. **Temp directory cleanup failures** leaving disk clutter
   - *Mitigation*: Use Python's `tempfile.TemporaryDirectory` with resource tracking; fallback to at-exit cleanup with unique timestamped names.

2. **Pipeline steps depending on production paths** hardcoded in modules
   - *Mitigation*: Dependency inject root directories via config object; verify all file operations respect sandbox boundaries.

3. **Partial failures during test leaving temp resources locked**
   - *Mitigation*: Implement two-phase setup: first create all temp resources, then run pipeline with atomic revert using transaction markers in temp ops.db.

4. **Test verification missing subtle data corruption**
   - *Mitigation*: Beyond row counts, compute SHA-256 of production databases before/after and compare; sample-check key production notes for modifications.

## Implementation Blueprint

### Sandbox Strategy (Question 1)
**Option A with temp ops.db**: Create temp copies of all databases, including ops.db. This preserves the undo mechanism within the sandbox while protecting production audit trails. Directory structure:
```
/tmp/corp_sandbox_<timestamp>/
├── 00_Inbox/
├── 01_Knowledge/
├── 10_Projects/
├── 30_Reference/
├── _outputs/
├── ops.db (temp copy)
├── index.db (temp)
└── overnight_state.db (temp)
```

### CKE Handling (Question 2)
**Option B with periodic Option D refresh**: Use fixtures for daily testing. Add `--live-api` flag for monthly validation runs. Cache live responses to update fixtures when extraction logic changes.

### MyWork Sandbox (Question 3)
**Separate temp directory outside MyWork**: Avoids polluting the production hierarchy. Symbolically link test files from JLR pilot directory into temp 00_Inbox.

### Revert Scope (Question 4)
Revert means **complete deletion** of the temp directory tree. For production resources touched (none if using pure temp), verify zero net changes via checksums.

### Revert Verification (Question 5)
1. **Pre-test snapshot**: Record file counts, database row counts, and SHA-256 of production databases.
2. **Post-test verification**: Compare snapshots; any mismatch fails the test.
3. **Resource tracking**: Log all created temp resources; verify removal.

### CLI vs Script (Question 6)
**`corp test-pipeline` command** with subcommands:
```bash
corp test-pipeline run --live-api=false --test-files=./fixtures
corp test-pipeline report --run-id=<timestamp>
corp test-pipeline clean --all  # manual cleanup if needed
```

### Report Format (Question 7)
**Console-first, markdown-second**:
```
# Pipeline Test Report - 2025-04-15T14:30:00
✅ PASS - 45.2s | Files: 12 | Notes: 8 | Cost: $0.00

## Steps
1. Ingest (2.1s)     ✅ 12 files → 00_Inbox
2. Classify (1.8s)   ✅ 8 docs, 4 images
3. Extract (18.4s)   ✅ 8 notes, avg quality: 0.85
...
9. Revert (0.9s)     ✅ SHA-256 match on all prod DBs

## Failures
None

## Recommendations
- Extraction quality threshold met (0.85 > 0.80)
- Consider adding PDF/A test cases
```

## Step-by-Step Revert Process
1. **Mark test start** in temp ops.db with UUID `test_run_id`
2. **Run pipeline** normally within sandbox
3. **On completion or failure**:
   - Close all database connections
   - Delete entire temp directory tree
   - Verify deletion (os.path.exists)
4. **Compare pre/post snapshots** of production databases
5. **Report any residue** as test failure

## Execution Plan
1. Week 1: Implement temp sandbox builder with config injection
2. Week 2: Add pipeline runner with step verification hooks
3. Week 3: Implement snapshot/revert verification
4. Week 4: Create report generator and integrate into CI

This architecture provides the safety required for autonomous LLM execution while delivering actionable, quantified test results without risking production data integrity.

*Latency: 82.91s | Tokens: 5214*

### Grok (grok-4.20-beta)

**## Position**

Use **production paths with a strict "test/" prefix + UUID tagging** (option C) for the sandbox, implement as a first-class `corp test-pipeline` CLI command, and treat extraction via **fixture replay from the existing 690 _outputs fixtures** (option D). Add a `99_Sandbox` zone inside MyWork. The entire test must be one atomic transaction that either fully succeeds *or* fully reverts using the existing `corp ingest-inbox --undo` machinery plus tag-based cleanup.

This deliberately rejects the consensus "let's use completely isolated temp directories and databases" approach.

**## Rationale**

- **The hidden assumption everyone is making** is that isolation = safety. This is false. The pipeline has *never* been tested in the actual Windows filesystem layout, with real Obsidian vault quirks, real path normalization bugs, real antivirus interactions, or real cross-database foreign-key-like relationships between ops.db, file registry, and vault. A temp directory sandbox gives us clean test results and dirty production failures.
- The undo mechanism (`--undo N --full`) and file registry already exist precisely for this use case. We're ignoring our own architecture. Using real paths + tagging lets us test the *actual* revert code path that will be used in anger.
- CKE extraction is not the point of this test. The point is pipeline orchestration, routing logic, deduplication, quality gates, index rebuilding, and MyWork movement semantics. Paying $0.07 and introducing non-determinism to test something that already has 2,276 unit tests is engineering theater.
- A `99_Sandbox` zone inside MyWork forces us to solve the real organizational problem (where do test artifacts live?) instead of pretending it doesn't exist. It also makes the test visible to the human operator.
- `corp test-pipeline` as a CLI command (not a standalone script) ensures we test the *actual* argument parsing, configuration, logging, and infrastructure that Rob and the LLM will use. This is the "eat your own dogfood" position.

**## Trade-offs**

- We give up the psychological comfort of "nothing can possibly touch production." This discomfort is *valuable*.
- We give up the ability to run these tests in true parallel (multiple tests at once). Sequential is fine.
- Slightly higher complexity in cleanup logic (must be paranoid about tag leakage).
- Report must be extremely disciplined about showing before/after state or people will be nervous.

**## Risks**

**Risk 1: Incomplete revert corrupts production**
- Mitigation: Strict UUID tagging on *every* artifact (file prefix `test-8f3k9...`, ops.db `test_run_id`, vault note frontmatter, index tags). Revert becomes "delete everything with this test_run_id". Add a `corp test-pipeline --verify-only` mode that scans for orphaned test artifacts.

**Risk 2: Test files escape 99_Sandbox**
- Mitigation: The pipeline must refuse to process anything in `99_Sandbox` unless `--test-mode` is explicitly passed. Add a filesystem watcher during the test that kills the process if any file leaves the allowed zones.

**Risk 3: ops.db audit trail pollution**
- Mitigation: I'm actually *for* pollution here — the audit trail should contain the fact that a test ran. This is truth, not pollution. We just need to make test events visually distinct and easily queryable (`WHERE test_run_id IS NOT NULL`).

**Risk 4: Windows-specific path length or permission issues**
- This is why we're *not* using temp directories. The test will catch these.

**Verification Strategy (the part everyone gets wrong):**
Don't just compare row counts. Do this:
1. Hash the entire relevant state (ops.db row hashes for non-test data + vault file content hashes + index term counts) *before* the test.
2. Run test.
3. Run revert.
4. Hash everything again.
5. If hashes don't match, test fails hard.

This is the only way to know the revert was truly complete.

**Recommended Command:**
```bash
corp test-pipeline --fixture-set JLR --runs 3 --report json
```

The report should be scannable ADHD format:
- **Pipeline**: 8/8 steps ✓ (234ms, 892ms, ...)
- **Artifacts**: 7 files • 3 notes • trust=3.0
- **Revert**: VERIFIED (hashes matched)
- **Cost**: $0.00 (fixtures)
- **Issues**: [1] Rename step used wrong prefix on Windows

This architecture forces us to make our production system *testable* rather than building a fake testing environment that lies to us. The unpopular truth is that our fear of touching production is preventing us from making production robust.

*Latency: 10.48s | Tokens: 3090*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Round 2 Evaluation

## Proposal A: Complete Isolation with Config Injection

**Verdict: Largely Agree**

**Strongest point:** The `PipelineConfig` dataclass as the foundational refactor. This is exactly right. The observation that "every function that touches a file path or database must accept its paths from config, not from module-level constants" is the single most important sentence in any of these proposals. This is the real deliverable — the sandbox is just the forcing function.

**Weakest assumption:** That the config refactor is "~2-3 hours." In a codebase with 2,276 unit tests and a multi-stage pipeline, extracting hardcoded paths into a config dataclass and threading it through every call site is closer to 6-10 hours if done honestly — especially on Windows where path handling surprises are routine. Underestimating this is how Phase 1 swallows the entire sprint.

**Overlooked risk:** The proposal doesn't address database schema initialization. "Fresh schema, empty" databases require that the schema DDL is maintained separately and applied correctly. If schema creation is currently implicit (happens during first write, or lives in migration scripts that assume existing data), the sandbox will create databases that don't match production structure. This is a subtle but real failure mode.

**One disagreement:** The `--record` mode is over-engineered for Phase 1. You already have 690 fixtures. Just use them. Add recording later when fixture drift actually becomes a problem. Building it now is speculative infrastructure.

---

## Proposal B: Production Paths with UUID Tagging

**Verdict: Disagree**

**Strongest point:** The argument that temp-directory testing won't catch Windows filesystem quirks, path normalization bugs, or antivirus interactions is legitimate and important. This is a real blind spot of pure isolation. The observation that "our fear of touching production is preventing us from making production robust" contains genuine insight.

**Weakest assumption:** That UUID-tagged cleanup will be reliable. This is the critical flaw. The proposal requires *every* artifact — files, database rows across multiple tables, vault notes, index entries — to be tagged with a UUID, and *every* revert path to correctly filter by that tag. This is exactly the kind of "many moving parts must all work correctly" design that fails under partial failures. If the process crashes between writing a file and tagging it in the registry, you have an untracked orphan in production. The proposal's mitigation ("add a filesystem watcher that kills the process") adds more moving parts to a system whose core problem is too many moving parts.

**The hash-everything verification strategy** sounds rigorous but is operationally expensive. Hashing production databases before and after every test run means reading every byte of ops.db, which will grow over time. It's also fragile — any concurrent production activity (an unrelated file landing in Inbox) will cause a hash mismatch and a false failure.

**Overlooked risks:**
- **Concurrency with production operations.** What if a real file arrives in Inbox during the test? The tag system can't distinguish "real file that arrived during test" from "test artifact that escaped tagging."
- **ADHD context.** This proposal requires maintaining discipline about tagging conventions across every pipeline step. For a solo developer with ADHD, the cognitive overhead of "is this tagged correctly? did I miss a table?" is the exact kind of ongoing burden that should be eliminated, not embraced.
- **The "99_Sandbox in MyWork" idea** creates permanent cognitive noise in the daily working environment to serve an occasional testing need. This is backwards.

The philosophical position — test in production because that's where bugs live — has merit in organizations with staging environments and SRE teams. For a solo developer's personal knowledge management system where the audit trail is described as "precious," it's reckless.

---

## Proposal C: Temp Isolation with Fixture Mocks

**Verdict: Partially Agree**

**Strongest point:** The step-by-step revert process is the clearest of the three proposals. Mark start → run → close connections → delete tree → verify deletion → compare snapshots. Simple, linear, auditable.

**Weakest assumption:** "Symbolically link test files from JLR pilot directory into temp 00_Inbox." Symlinks on Windows are a permissions nightmare (require Developer Mode or admin privileges). This will break. Copy the files. They're test documents — a few MB at most.

**Overlooked risks:**
- The 4-week implementation plan is too long and too waterfall for what should be an iterative build. You don't need the report generator to be separate from the pipeline runner. Build the simplest vertical slice first (one file through the whole pipeline), then expand.
- "Option B with periodic Option D refresh" for CKE is confused terminology. Option B is mocks from fixtures. Option D is extract-once-replay. These are nearly identical. Just pick one name and be precise.
- The `corp test-pipeline clean --all` subcommand implies temp directories might persist long enough to need manual cleanup, which contradicts the "temp directories are safe because they auto-clean" argument. Pick a lane: either cleanup is automatic and reliable, or it's not and you need manual tooling. Don't claim both.

---

## Revised Recommendation

I align with Proposal A's architecture, with corrections.

### Core Decisions

| Question | Decision | Reasoning |
|----------|----------|-----------|
| Q1: Sandbox strategy | **A: Complete isolation** | Structural safety > tested safety. You cannot have a bug in revert logic corrupt production if revert logic never touches production. |
| Q2: CKE handling | **D: Replay from existing fixtures** | You have 690 fixtures. Use them. Add `--live` flag. Skip `--record` in v1. |
| Q3: MyWork sandbox | **Separate temp directory** | No `99_Sandbox`. No permanent artifacts from a transient process. |
| Q4: Revert scope | **`shutil.rmtree(temp_root)`** | One operation. No selective cleanup. No tag tracking. |
| Q5: Verify revert | **Temp dir gone + production snapshot unchanged** | Pre/post file count and db row count on production (not hashes — too expensive, too fragile to concurrent changes). |
| Q6: CLI vs script | **`corp test-pipeline` CLI command** | Discoverable, uses real infrastructure, accepts flags. |
| Q7: Report | **Proposal A's format**, with one change noted below. |

### What I'd Change from Proposal A

**1. Acknowledge the production-fidelity gap explicitly and address it.**

Proposal B is wrong about the solution but right about the problem. A pure temp-directory test won't catch path-length issues, permission problems, or Obsidian-specific vault quirks. Add a single, cheap mitigation:

```python
class PipelineConfig:
    # ... existing fields ...
    
    @classmethod
    def sandbox(cls, temp_root: Path, live_cke: bool = False) -> "PipelineConfig":
        config = cls(
            mywork_root=temp_root / "MyWork",
            vault_root=temp_root / "Vault",
            # ...
        )
        config._validate_platform_constraints()  # NEW
        return config
    
    def _validate_platform_constraints(self):
        """Test that sandbox paths have the same characteristics as production."""
        # Verify path lengths are realistic (not just /tmp/x)
        # Verify we can create files with spaces and special chars
        # Verify file locking behavior matches production filesystem
        test_file = self.mywork_root / "00_Inbox" / "test file (1).pdf"
        test_file.write_bytes(b"test")
        assert test_file.exists()
        test_file.unlink()
```

This is 15 lines that addresses Proposal B's legitimate concern without touching production.

**2. The config refactor estimate must be honest.**

Do not call this 2-3 hours. Audit every module for hardcoded paths *first*. Estimate after the audit. Budget 8 hours and be relieved if it takes 6.

Concretely: `grep -rn "Path(" --include="*.py" | grep -v "test" | grep -v "__pycache__"` to find every path construction. Each one must accept its root from config.

**3. Schema initialization must be explicit.**

Add a `init_sandbox_databases(config: PipelineConfig)` function that creates ops.db, index.db, and overnight_state.db with the correct schema. This schema must be defined in *one place* (a `.sql` file or a `create_schema()` function) shared between production initialization and sandbox initialization. If production currently creates tables lazily on first write, fix that first. Lazy schema creation is a maintenance hazard regardless of testing.

```python
def init_sandbox_databases(config: PipelineConfig):
    """Create empty databases with production-identical schema."""
    for db_path, schema_func in [
        (config.ops_db_path, ops_schema.create_tables),
        (config.index_db_path, index_schema.create_tables),
        (config.overnight_db_path, overnight_schema.create_tables),
    ]:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        schema_func(conn)
        conn.close()
```

**4. Drop `--record` from v1. Add it when you need it.**

You have 690 fixtures. The marginal value of a recording system is near zero right now. Build it when fixture drift actually causes a test to give you bad signal. YAGNI.

**5. Implementation plan should be vertical, not horizontal.**

Not "Week 1: sandbox builder, Week 2: runner, Week 3: verification, Week 4: reports." Instead:

- **Day 1 (4h):** Audit hardcoded paths. Create `PipelineConfig`. Refactor the first pipeline step (Inbox intake) to accept config.
- **Day 2 (4h):** Refactor remaining steps. Verify with existing unit tests still passing.
- **Day 3 (3h):** Build sandbox creation + teardown. Run ONE file through ONE step (Inbox → Classify) in sandbox. Verify + clean.
- **Day 4 (3h):** Extend to full pipeline with fixture CKE. Minimal report (pass/fail per step to stdout).
- **Day 5 (2h):** Add production snapshot verification, markdown report, CLI flags.

Each day produces a working, testable increment. If you stop after Day 3, you still have something useful.

**6. Report format correction.**

Proposal A's report is good but the "Recommendations" section should be removed from automated output. Automated recommendations are either obvious ("extraction failed — fix extraction") or wrong ("consider adding PDF/A test cases" — how would the test know this?). Just report facts. Let the human (or Claude Code reviewing the report) make recommendations.

```markdown
# Pipeline Test Report
**2025-01-15 14:32** | 11.4s | fixture mode | $0.00

## ✅ ALL PASS (8/8)

| # | Step | Time | Detail |
|---|------|------|--------|
| 1 | Inbox intake | 0.3s | 5 files |
| 2 | Classify | 0.8s | 3 spec, 1 proposal, 1 reference |
| 3 | Rename | 0.2s | 5/5 |
| 4 | Route | 0.4s | 3→Projects, 2→Reference |
| 5 | Dedup | 0.1s | 0 duplicates |
| 6 | Extract (CKE) | 2.1s | 5 extractions, avg quality 0.87 |
| 7 | Vault ingest | 1.2s | 5 notes, trust t2_automated |
| 8 | Index + Retrieve | 0.9s | 3 queries, avg 4.2 results |

## Revert: ✅ Sandbox removed. Production unchanged (1,247 files, 8,932 rows → 8,932 rows).
```

That's it. No "Recommendations" section. No "Extraction Quality" sub-table unless a quality gate actually failed. Keep it scannable. The detail is in the JSON sidecar for anyone who wants to drill in.

### Summary

The architecture is Proposal A's isolation model, with honest effort estimates, explicit schema management, vertical delivery, a platform-constraint validation check stolen from Proposal B's insight, and a leaner report format. Total honest effort: ~16 hours across 5 working sessions. The lasting value is the `PipelineConfig` abstraction, which makes every future test, migration, and refactor cheaper.

*Latency: 80.16s | Tokens: 10731*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my mandate is to protect the integrity of your production systems (especially the `ops.db` audit trail) and ensure predictable, safe interoperability. 

Testing in production with real data and destructive revert logic is an anti-pattern that violates defense-in-depth. If your revert logic has a bug, or the system crashes mid-revert, you have corrupted your source of truth.

Here is my evaluation of the council's proposals, followed by a hardened architectural recommendation.

---

### Evaluation of Proposal A
**Position:** Agree. 
Option A (completely separate temp directories via config injection) is the only structurally sound approach for an autonomous LLM-driven test.

*   **Strongest point:** The "Config Override" architectural refactor. Forcing all paths to be injected via a `PipelineConfig` object decouples your pipeline from global state, inherently improving the system's security posture and testability.
*   **Weakest assumption:** Assumes `shutil.rmtree(temp_root)` is trivial on Windows. It is not.
*   **Overlooked risks:** **Windows File Locking.** SQLite is notorious for leaving file handles open or lingering lock files (`-wal`, `-shm`) if connections aren't explicitly closed and garbage-collected. If a test fails midway, `shutil.rmtree` will throw a `PermissionError` on Windows, failing the revert step and leaking temp directories.

### Evaluation of Proposal B
**Position:** Strongly Disagree. 
Testing directly in production paths with a `test/` prefix and UUID tags relies on "perfect execution" of cleanup logic. This is an unacceptable operational risk.

*   **Strongest point:** Correctly identifies that temp directories do not test Windows-specific filesystem quirks, path-length limits, or real-world folder permission inheritance. 
*   **Weakest assumption:** Assumes that polluting the production `ops.db` audit trail with test runs is acceptable. Mixing test data with production audit logs destroys the forensic value of the audit trail unless you build complex, error-prone filter logic into every downstream compliance query.
*   **Overlooked risks:** **Catastrophic mitigation strategies.** The proposal suggests "a filesystem watcher that kills the process if any file leaves the allowed zones." Terminating a process mid-execution while it holds write-locks to SQLite databases (like `ops.db` or `index.db`) is the fastest way to cause unrecoverable database corruption. 

### Evaluation of Proposal C
**Position:** Partially Agree. 
Agrees with the isolation of Proposal A but introduces a deeply flawed verification mechanism.

*   **Strongest point:** Recognizes the need to mathematically *prove* the sandbox didn't leak into production, rather than just trusting the config override.
*   **Weakest assumption:** Assumes you can verify production isolation by computing a SHA-256 hash of `ops.db` before and after the test. 
*   **Overlooked risks:** **False Positives via SQLite WAL.** If `ops.db` uses Write-Ahead Logging (WAL), or if Rob drops a file into the real Inbox while the test is running, or if a background OS process touches the file metadata, the SQLite file hash will change. The test will report a "Failure/Residue" even though the sandbox logic worked perfectly. Hashing live databases is structurally unreliable.

---

### Revised Architectural Recommendation

We will proceed with a hardened version of **Complete Isolation (Option A)**. To achieve defense-in-depth, we will combine structural isolation (config injection) with runtime isolation (Python audit hooks) to mathematically guarantee production safety.

#### 1. Sandbox Strategy: Strict Temp Dirs + OS-Level Audit Hooks
Use an OS-managed temporary directory (`%TEMP%\corp_sandbox_<uuid>\`). 
To solve the "how do we know we didn't touch production" problem without flaky database hashing, implement a **Python `sys.addaudithook`**.

During the test, register a hook that intercepts all `open()` calls. If the pipeline attempts to open a file in the production MyWork or Vault paths, the hook raises a fatal `SecurityError` and aborts the pipeline.
*   *Benefit:* Mathematical proof of isolation at the OS/interpreter level. Zero risk of false positives from background tasks.

#### 2. CKE Handling: Extract-Once-Replay (Option D)
Wrap the CKE API in a `ReplayCKEClient`. 
*   Store responses for your JLR pilot files in a version-controlled `tests/fixtures/cke_cassettes/` directory.
*   Include a `--live` flag for when you explicitly want to test Claude/Gemini API integration (costing ~$0.10).
*   *Integration note:* Use a hash of the *file content + extraction prompt*, not just the filename, as the cache key. This ensures changes to your extraction instructions trigger a cache miss, forcing you to run `--live` to update the fixture.

#### 3. MyWork Sandbox: Pure `%TEMP%`
No `99_Sandbox` in production. Ever. All test artifacts live in `%TEMP%` and die in `%TEMP%`.

#### 4. Revert Scope: Guaranteed Teardown
The revert encompasses destroying the temp directory. Because Windows file locks will block this, implement a **robust teardown sequence**:
1. Explicitly close all `sqlite3.Connection` objects.
2. Force Python garbage collection (`import gc; gc.collect()`) to drop lingering file handles.
3. Use a retry loop for `shutil.rmtree` with a backoff (e.g., `tenacity` or a custom loop of 3 retries over 2 seconds) to allow Windows antivirus scanners to release their locks on newly created temp files.

#### 5. CLI Implementation: `corp test-pipeline`
Implement as a subcommand in your main CLI so it tests the actual entry points.

```bash
# Fast, free, autonomous testing (default)
corp test-pipeline

# Live API testing (updates cassettes if missing)
corp test-pipeline --live

# Keep sandbox open for debugging a failure
corp test-pipeline --keep-sandbox
```

#### 6. The "Verify the Revert" Protocol
1. **Pre-flight:** Ensure `temp_root` does not exist. Register `sys.addaudithook` to block production path access.
2. **Execute:** Run the pipeline.
3. **Revert:** Execute the robust teardown sequence (DB connection kill -> GC -> retry-rmtree).
4. **Verify:** `assert not temp_root.exists()`. If the audit hook didn't fire, and the temp dir is gone, the revert is perfectly verified.

#### 7. Report Format (ADHD-Optimized Markdown)
The LLM should output a heavily structured, visually distinct report.

```markdown
# 🧪 Pipeline E2E Sandbox Report
**Result:** ✅ ALL PASS | **Duration:** 1.2s | **Cost:** $0.00 (Replay Mode)

### 🛡️ Security & Revert Verification
- **Production Isolation:** ✅ Verified (Audit hook recorded 0 prod path access attempts)
- **Sandbox Teardown:** ✅ Verified (`%TEMP%\corp_sandbox_...` completely removed)

### ⚙️ Pipeline Execution
| Step | Status | Time | Details |
|------|--------|------|---------|
| 1. Inbox Intake | ✅ PASS | 0.05s | 5 files copied |
| 2. Classify/Rename | ✅ PASS | 0.12s | 3 Specs, 2 Ref |
| ... | ... | ... | ... |
| 7. FTS5 Index | ✅ PASS | 0.40s | Built from scratch |
| 8. Retrieve Check | ✅ PASS | 0.10s | Query 'WMS': 4 hits |

### ⚠️ Recommendations / Notes
- No anomalies. 
- *Note: CKE extraction ran via fixtures. Run with `--live` to validate model quality changes.*
```

### Implementation Plan (Phased for Solo Dev)
1. **Refactor to `PipelineConfig` (Critical Path):** Modify all functions to accept a config object containing `mywork_root`, `vault_root`, and DB paths. Remove hardcoded global paths.
2. **Implement CKE Replay:** Create `ReplayCKEClient` and generate the first set of `.json` cassettes using your existing JLR test files.
3. **Build Sandbox Setup/Teardown:** Write the `%TEMP%` scaffolding, the DB schema initializers, and the Windows-safe retry-rmtree logic.
4. **Wire the CLI & Audit Hook:** Add `corp test-pipeline`, inject the Python `sys.addaudithook` for production path protection, and generate the Markdown report.

*Latency: 37.47s | Tokens: 10828*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A: Complete Isolation via Temp Directories
**Position**: Agree with core isolation principle, partially agree on implementation.

**Strongest point**: Mathematical safety through structural isolation. By never opening production databases in write mode, you eliminate entire classes of corruption bugs. This is the most scalable approach for parallel testing and CI.

**Weakest assumption**: That config injection alone guarantees isolation. Hardcoded paths in third-party libraries, environment variables, or global state in legacy modules could still leak. The proposal underestimates the difficulty of achieving 100% path isolation in complex pipelines.

**Overlooked risk**: Performance impact of copying entire database schemas and test files for every run. For large test corpora, the setup/teardown overhead could dominate runtime (especially on Windows with slower filesystem operations).

### Proposal B: Production Paths with Tagging
**Position**: Disagree fundamentally. This is architecturally unsound for automated testing.

**Strongest point**: Tests real path normalization and Windows-specific edge cases that temp directories might miss.

**Weakest assumption**: That tagging and existing undo mechanisms are reliable. The whole premise of needing this sandbox is that we've NEVER tested the full pipeline or its revert capabilities. Assuming untested revert logic will protect production is circular reasoning.

**Overlooked risk**: Test pollution cascades. A single bug in tag propagation could leave orphaned files that interfere with subsequent pipeline runs, creating Heisenbugs that only appear after multiple test executions.

### Proposal C: Temp Directories with Enhanced Verification
**Position**: Mostly agree, but missing critical algorithmic optimizations.

**Strongest point**: Comprehensive verification through checksums and snapshots. This addresses the "did we really revert?" question with cryptographic certainty.

**Weakest assumption**: That SHA-256 comparisons of production databases are practical. Production databases change during test execution (new log entries, cache updates). Comparing byte-level hashes of live databases guarantees false positives.

**Overlooked risk**: Race conditions in snapshot verification. If any background process modifies production databases during the test (even logging), the verification fails despite perfect isolation.

## Revised Recommendation: Algorithmically Secure Sandbox

### Core Architecture: Isolated Execution with Production Verification

**Q1: Sandbox Strategy → Option A+ (Enhanced Isolation)**
```
%TEMP%/corp-sandbox-{UUID}/
├── env/           # Mount points for production directories
│   ├── MyWork -> /mnt/readonly/MyWork     # Symlink read-only
│   └── Vault -> /mnt/readonly/Vault       # Symlink read-only
├── work/          # Writable sandbox
│   ├── 00_Inbox/  # Test files
│   └── 01_Knowledge/  # Vault writes
└── db/            # Fresh SQLite databases
```

**Algorithmic innovation**: Use read-only bind mounts (Linux) or junction points (Windows) to expose production directories without write access. This preserves real path semantics while maintaining safety. All writes go to isolated `work/` subtree.

**Performance optimization**: Initialize databases using `VACUUM INTO` for schema copying:
```sql
ATTACH DATABASE ':memory:' AS source;
-- Copy schema only, no data
VACUUM INTO 'sandbox_ops.db';
```
This is 40-60% faster than CREATE TABLE sequences for complex schemas.

**Q2: CKE Extraction → Option D with Deterministic Hashing**
```python
class DeterministicCKEClient:
    def extract(self, file_path: Path, tier: str) -> ExtractionResult:
        # Content-based hash with pipeline version salt
        salt = f"{PIPELINE_VERSION}:{tier}:{EXTRACTION_MODEL_VERSION}"
        key = sha256(file_path.read_bytes() + salt.encode()).hexdigest()
        
        if self.mode == "replay":
            return self._load_fixture(key[:16])  # 16-char deterministic ID
        elif self.mode == "record":
            result = self._call_api(file_path, tier)
            self._save_fixture(key[:16], result)
            return result
```

**Why**: Deterministic hashing ensures the same file always gets the same fixture ID across test runs, enabling cache sharing and eliminating "fixture missing" errors when test files change slightly.

**Q3: MyWork Sandbox → External Temp Directory with Read-Only Production View**
No permanent `99_Sandbox`. Use the read-only mount approach to access real MyWork structure for classification/routing rule testing without modification risk.

**Q4/Q5: Revert Verification → Content-Addressable Verification Protocol**

Instead of row counts or checksums, use a content-addressable verification system:

1. **Pre-test anchor**: `anchor = hash(ops.db_commit_count + file_registry_count + index_term_count)`
2. **Post-test verification**: 
   - Assert `anchor == hash(ops.db_commit_count + file_registry_count + index_term_count)`
   - Assert `sandbox_root.exists() == False`

**Algorithmic advantage**: Counting database commits is O(1) via `pragma user_version` increment per transaction. More robust than row counts (which can change legitimately) or checksums (which change with timestamps).

**Q6: Implementation → `corp test-pipeline` with Transactional Guarantees**

```python
@transactional(file_system=True)  # Decorator that ensures rollback on failure
def run_pipeline_test(config: TestConfig) -> TestReport:
    with SandboxManager() as sandbox:
        # Phase 1: Setup (copies schemas, mounts read-only views)
        sandbox.initialize()
        
        # Phase 2: Execution with circuit breakers
        for step in pipeline_steps:
            with step_timeout(30):  # Each step limited to 30 seconds
                execute_step(step, sandbox)
                
        # Phase 3: Verification (implicit in sandbox.__exit__)
        # If any exception, sandbox cleanup runs automatically
```

**Q7: Report Format → Algorithmic Summary with Actionable Metrics**

```markdown
# PIPELINE TEST: PASS (Δ=0.00%) | 12.3s | $0.00

## Performance Profile (p95 latency)
Step          Duration  Δ vs Baseline  Status
---------------------------------------------
Ingest        0.42s     +0.03s (7.1%)  ⚠️
Classify      0.87s     -0.11s (-11%)  ✅
Extract       8.21s     N/A            ✅
Index         2.11s     +0.42s (25%)   ⚠️
Revert        0.03s     -              ✅

## Quality Metrics
Extraction F1: 0.87 (threshold 0.80) ✅
Routing Accuracy: 5/5 files ✅
Index Recall@3: 0.92 ✅

## Safety Verification
- Production DB commit delta: 0 ✅
- Sandbox residue: 0 bytes ✅
- Read-only mounts intact: ✅

## Recommendations
1. Index step shows 25% regression - investigate FTS5 tokenizer changes
2. Ingest latency increased 7% - check antivirus exclusions
```

### Critical Implementation Details

**Performance optimizations**:
1. Use `tempfile.NamedTemporaryFile` with `delete=False` for atomic file operations
2. Implement connection pooling for sandbox databases (reuse connections across steps)
3. Parallelize independent verification steps (file counting, hash computation)

**Scalability guarantees**:
```python
# Circuit breaker pattern for each pipeline step
class CircuitBreaker:
    def __init__(self, max_failures=3, timeout=30):
        self.failures = 0
        self.max_failures = max_failures
        
    def execute(self, operation):
        if self.failures >= self.max_failures:
            raise PipelineAbort("Too many consecutive failures")
        try:
            with timeout(self.timeout):
                return operation()
        except Exception:
            self.failures += 1
            raise
```

**Risks and mitigations**:
1. **Risk**: Read-only mounts fail on Windows Home Edition
   - **Mitigation**: Fallback to copied directory structure with validation that no writes escape

2. **Risk**: Deterministic hashing collisions in CKE fixtures
   - **Mitigation**: Use 256-bit hashes with salt; collision probability < 2^-128

3. **Risk**: Pipeline steps have hidden dependencies on production data
   - **Mitigation**: Static analysis to detect implicit imports; runtime assertions in sandbox mode

### Execution Timeline

**Week 1**: Implement sandbox manager with read-only mounts and transactional rollback
**Week 2**: Add content-addressable verification and performance profiling
**Week 3**: Integrate deterministic CKE client with versioned fixtures
**Week 4**: Add circuit breakers and comprehensive reporting

**Total estimate**: 60-80 hours, with 40% allocated to safety mechanisms and verification.

This approach delivers:
1. **Mathematical safety** through isolation and content verification
2. **Performance profiling** with actionable metrics
3. **Deterministic execution** via versioned fixtures
4. **Scalability** through circuit breakers and timeouts
5. **ADHD-friendly reports** with algorithmic confidence scores

The key innovation is treating the sandbox as a verifiable compute environment rather than just a test fixture—enabling autonomous LLM execution with cryptographic proof of safety.

*Latency: 84.70s | Tokens: 10793*

### Grok (grok-4.20-beta)

**I disagree with all three proposals.**

### Evaluation of Proposals

**Proposal A: Disagree**

Strongest point: The config injection requirement (`PipelineConfig`) is correct. This is the only structurally sound way to make the system testable.

Weakest assumption: That "delete a temp directory" constitutes a meaningful test of the *actual* system. This is the core illusion—your pipeline's value is in how it behaves inside the real, messy, production-shaped constraints (Obsidian file locking, Windows path normalization, antivirus, real vault sync, real ops.db transaction patterns). A parallel universe test gives you false confidence. The claim that "corruption is structurally impossible" is marketing speak; you've simply moved the corruption risk to "did we correctly emulate production?"

Risks overlooked: The config refactor will reveal deep coupling that the author is pretending is superficial. Also completely ignores that the existing `corp ingest-inbox --undo` machinery exists and should be the *primary* revert mechanism, not `shutil.rmtree()`.

**Proposal B: Partially agree (the contrarian part is right, the execution is wrong)**

Strongest point: This is the only proposal that correctly identifies the hidden consensus assumption—that isolation equals safety. B is right that most architects are cowards about this. Testing in a fake environment that doesn't have the same shape as production is engineering masturbation.

Weakest assumption: That prefixing + UUID tagging + `99_Sandbox` is a good idea. This is terrible. It pollutes the mental model permanently. The "discomfort is valuable" rhetoric is self-flagellation disguised as wisdom. Also, the "hash entire state" verification is comically expensive and fragile.

Risks overlooked: The proposal underestimates how badly a leaking test prefix could corrupt real work. The "file system watcher that kills the process" is a hilarious Rube Goldberg machine that will cause more problems than it solves.

**Proposal C: Disagree**

Strongest point: The snapshot verification approach (pre/post SHA-256) is better than A's naive "just delete the temp dir."

Weakest assumption: Everything else. This is Proposal A with extra steps and worse rationale. The "symbolically link test files" idea is particularly bad—it creates exactly the kind of hidden coupling to production that we're trying to avoid.

Risks overlooked: Same as A, plus the false precision of SHA-256 on databases (SQLite WAL files and timing make this unreliable).

### Revised Recommendation (The Contrarian Position)

**The core problem everyone is missing:** The existing architecture already has sophisticated revert capabilities (`corp ingest-inbox --undo N --full`, file registry by hash, ops.db event log, trust_level protection). We are ignoring our own best work because it feels scary.

**Correct architecture:**

**Sandbox strategy: Hybrid (none of the original options)**  
- **Temp directories** for `MyWork/` and `Vault/` (files only)
- **Snapshot + restore** for `ops.db` and `overnight_state.db` (using SQLite's backup API or simple file copy since they're SQLite)
- **Fresh** `index.db` (it's designed to be rebuilt)

This is the only position that doesn't lie to us. We get real filesystem behavior *and* protect the audit trail.

**CKE handling: Option D with mandatory recording discipline**  
Fixtures by content hash. The `--live` flag requires an explicit environment variable `CORP_TEST_LIVE_DANGEROUS=true` because real API calls should feel expensive. Monthly `--live` runs should be a scheduled task, not optional.

**MyWork sandbox: Neither 99_Sandbox nor completely separate**  
Use a completely separate temp directory *but* with the *exact same directory structure* as production (`00_Inbox`, `10_Projects`, etc.). No `99_Sandbox` in production. Ever.

**Revert scope and mechanism:**
1. Copy `ops.db` and `overnight_state.db` to temp location before test
2. Run full pipeline in sandbox config
3. On success or failure: 
   - Use `corp ingest-inbox --undo` for everything that touched the registry
   - Restore the original `ops.db` and `overnight_state.db` from snapshots
   - Delete temp `MyWork/` and `Vault/` directories
4. Rebuild `index.db` from the (now clean) vault

**Verification of revert:**
- Before/after SHA-256 of `ops.db` (excluding the single test event row)
- Before/after file count and total size of production `MyWork/` and `Vault/`
- Explicit check that no files with test UUIDs remain anywhere
- Database row count parity for non-test events

**Implementation: `corp test-pipeline` CLI command only.** No standalone script.

**Report format:** Proposal A's markdown is good but must include a "Production State Delta" section that shows the *exact* diff. The report must end with: "This test ran against the *shape* of production, not a fantasy version of it."

**The real prerequisite no one wants to admit:** The pipeline code must be refactored to accept a `PipelineConfig`. This is non-negotiable. If that takes 20 hours instead of 3, so be it. The current global constants are technical debt.

**What everyone is taking for granted:** That running tests without human eyes is inherently good. For the *first* 10 runs, a human should watch what happens. The autonomous LLM execution is phase 2, not phase 1. The fear of touching production isn't just cowardice—some of it is wisdom earned from painful incidents.

This hybrid approach forces us to make the *real* system testable rather than building an elaborate parallel universe that will diverge over time. The unpopular truth is that Proposal B was directionally correct but executed poorly. Isolation is a crutch.

*Latency: 10.95s | Tokens: 8598*

## Synthesis (by openai, non-participant)

## Consensus

1. **Make the pipeline configurable**
   - Strongest shared point: introduce a `PipelineConfig`/equivalent so all paths and DB locations are injected, not hardcoded.
   - This is the prerequisite for any safe sandbox.

2. **Expose it as a CLI command**
   - Most participants favored `corp test-pipeline` over a standalone script.
   - Reason: it exercises real code paths, is discoverable, and can later be called from pytest/CI.

3. **Default to fixture-based CKE**
   - Broad agreement that daily/default runs should not depend on live API calls.
   - Use existing extraction fixtures for deterministic, cheap tests.
   - Keep a `--live` mode for periodic realism checks.

4. **Do not add a permanent `99_Sandbox` inside production MyWork**
   - Most argued this creates cognitive clutter and unnecessary risk.
   - Preferred approach: build the sandbox outside production, typically under `%TEMP%`.

5. **Need explicit revert verification**
   - Everyone agreed revert must be proven, not assumed.
   - Debate was about *how* to verify, not whether to verify.

---

## Unresolved Disagreements

### 1. Isolation vs testing “real production shape”
- **Isolation camp (majority):**
  - Use fully separate temp dirs/databases.
  - Merit: safest; avoids corrupting production, especially `ops.db`.
  - Best for autonomous LLM execution.

- **Production-shape camp (minority/contrarian):**
  - Use production paths, tags, snapshots, or hybrid methods to catch real Windows/vault/path quirks.
  - Merit: more faithful to production behavior; may reveal issues a pure temp sandbox misses.

**Why this remains unresolved:**  
This is a classic safety vs fidelity tradeoff. The debate strongly favored safety for v1, but the production-fidelity objection is legitimate and should not be ignored.

### 2. How strict revert verification should be
- **Simple verification side:**
  - Temp dir deleted + no production writes = sufficient.
- **Stronger verification side:**
  - Add pre/post production snapshots, path-access guards, or hash-based checks.

**Why this remains unresolved:**  
Hashing live SQLite DBs is fragile; doing nothing beyond delete-temp is too trusting. The best answer is a middle path.

### 3. Fixture replay design
- **Simpler side:**
  - Just replay existing fixtures; skip recording machinery in v1.
- **More complete side:**
  - Add `--record` and content-hash keyed cassettes now.

**Why this remains unresolved:**  
Both are sensible. The simpler version is faster to ship; the richer version is better long term.

---

## Recommended Decision

### Decision in one line
Build **`corp test-pipeline` as a fully isolated temp sandbox** using **separate temp MyWork/Vault/databases**, **fixture-replayed CKE by default**, **optional `--live` mode**, and **strong but practical isolation verification**.

### Chosen options
1. **Sandbox strategy:** **A** — completely separate temp dirs/databases  
2. **CKE extraction:** **D** — extract once / replay fixtures, with `--live` override  
3. **MyWork sandbox:** **separate temp directory outside MyWork**  
4. **Revert scope:** **entire sandbox root**; do not revert production artifacts because production should not be touched  
5. **Revert verification:** delete sandbox + verify no production-path access + lightweight pre/post production snapshot  
6. **Implementation form:** **CLI command `corp test-pipeline`**  
7. **Report format:** concise markdown summary + JSON sidecar  

### Why this is the best path
This was the strongest overall position in the debate because it is the only one that is **structurally safe enough for autonomous operation**. Rob explicitly wants the LLM to run this without supervision. That rules out any approach that depends on perfect cleanup of production-touched artifacts.

The key reasoning:
- `ops.db` is described as precious.
- The full revert path has never been tested end-to-end.
- Therefore the first full-system test should **not depend on unproven revert logic to protect production**.

### Strongest objection acknowledged
The best objection was: **a pure temp sandbox may miss Windows/Obsidian/path/folder quirks that happen only in production-shaped environments.**

That objection has merit. I still recommend isolation for v1 because:
- the risk of corrupting production is materially worse than the risk of missing a path quirk;
- most of those fidelity gaps can be reduced without touching production:
  - mirror the same folder structure,
  - run on Windows,
  - use realistic file names and long paths,
  - add explicit platform/path stress checks,
  - add a later “production-shape smoke test” phase after the isolated sandbox is stable.

### Practical architecture

#### Command
```bash
corp test-pipeline
corp test-pipeline --live
corp test-pipeline --keep-sandbox
corp test-pipeline --files tests/fixtures/pipeline/
corp test-pipeline --report md,json
```

#### Sandbox layout
```text
%TEMP%/corp-test-{timestamp}-{uuid}/
├── MyWork/
│   ├── 00_Inbox/
│   ├── 10_Projects/
│   ├── 30_Reference/
│   └── ...
├── Vault/
│   └── 01_Knowledge/
├── db/
│   ├── ops.db
│   ├── index.db
│   └── overnight_state.db
├── fixtures/
└── report/
```

#### Revert process
1. Create sandbox root
2. Initialize empty sandbox DBs with production-identical schema
3. Copy test files into sandbox `00_Inbox`
4. Run full pipeline against sandbox config
5. Verify expected outputs
6. Close all DB connections
7. Delete sandbox root
8. Assert sandbox root no longer exists
9. Fail the test if any attempted production-path access occurred

#### Verification of revert
Use a layered approach:
- **Primary:** sandbox root deleted
- **Isolation guard:** runtime detection that production paths were never opened for write; ideally block any prod path access during test
- **Secondary lightweight snapshot:** pre/post counts or metadata for production roots/DBs, only as a confidence check, not as the primary proof

This avoids brittle full hashing of live SQLite files while still giving confidence.

---

## Risks

### 1. Hidden hardcoded production paths bypass sandbox config
**Risk:** a module still writes to production.  
**Mitigation:**
- audit codebase for path constants before implementation;
- require every filesystem/DB entrypoint to accept config;
- add a runtime path guard that fails if production roots are accessed.

### 2. Windows teardown fails due to file locks
**Risk:** `shutil.rmtree()` fails on SQLite/WAL or antivirus locks.  
**Mitigation:**
- explicitly close all DB connections;
- run `gc.collect()` before teardown;
- retry deletion with backoff;
- provide `--keep-sandbox` for forensic debugging.

### 3. Sandbox DB schema diverges from production
**Risk:** tests pass in sandbox but not in real system.  
**Mitigation:**
- create schema from the same initialization/migration code production uses;
- avoid duplicating DDL in separate hand-maintained files unless shared.

### 4. Fixture replay hides live CKE regressions
**Risk:** pipeline appears healthy while provider/model behavior changed.  
**Mitigation:**
- default to fixtures;
- add periodic `--live` runs manually or on schedule;
- report whether run used replay or live extraction.

### 5. False confidence from isolated environment
**Risk:** path-length, permissions, or Obsidian-specific quirks are missed.  
**Mitigation:**
- run sandbox on Windows only, not just Linux/CI;
- use realistic folder names and long-path test fixtures;
- add a later Phase 2 “production-shape smoke test” once v1 is stable.

### 6. Scope creep
**Risk:** building recorders, trend systems, CI plumbing, advanced analytics delays shipping.  
**Mitigation:**
- keep v1 narrow: one command, fixture mode, markdown+JSON report, no recommendations engine.

---

## Action Items

### Phase 1: Preconditions
1. **Implement `PipelineConfig`**
   - Include:
     - `mywork_root`
     - `vault_root`
     - `ops_db_path`
     - `index_db_path`
     - `overnight_state_db_path`
     - `cke_mode`
     - `cke_fixture_dir`
   - Remove or route around hardcoded paths.

2. **Audit for path leaks**
   - Search codebase for:
     - hardcoded MyWork/Vault paths
     - direct sqlite opens
     - environment/global path constants
   - Make sandbox mode impossible to run until audit is clean.

3. **Unify DB initialization**
   - Build `init_databases(config)` that creates sandbox DBs using production-identical schema setup.

### Phase 2: Sandbox runner
4. **Create sandbox manager**
   - `create_sandbox()`
   - `teardown_sandbox()`
   - Windows-safe cleanup with retries

5. **Build runtime production-path guard**
   - At minimum, wrap file/DB open points and reject production roots in sandbox mode.
   - Stronger option: interpreter-level audit hook if practical.

6. **Curate a small fixture corpus**
   - 5–8 representative files:
     - PDF
     - DOCX
     - spreadsheet
     - duplicate
     - edge-case naming/path file
   - Keep in repo under `tests/fixtures/pipeline/`

### Phase 3: CKE and pipeline execution
7. **Implement replay CKE client**
   - Key fixtures by content hash, ideally plus extraction prompt/version.
   - Default mode = replay.
   - Add `--live` flag.
   - Defer `--record` unless needed immediately.

8. **Run full pipeline in sandbox**
   - File → Inbox → Classify → Rename → Route → Dedup → Extract → Vault Ingest → Quality Gate → FTS5 Index → corp retrieve → corp prep

### Phase 4: Assertions and reporting
9. **Define expected checks per step**
   - file counts
   - route destinations
   - rename pattern compliance
   - dedup result
   - extraction result present / quality threshold
   - vault note count / trust level
   - retrieve query result count
   - prep output generated

10. **Implement revert verification**
   - assert all DB handles closed
   - sandbox root deleted
   - no production-path accesses logged
   - optional lightweight pre/post production snapshot unchanged

11. **Generate report**
   - **Markdown** for humans
   - **JSON** for machines
   - top section must be scannable:
     - overall PASS/FAIL
     - duration
     - mode: replay/live
     - cost
     - revert verified: yes/no

### Phase 5: CLI
12. **Add `corp test-pipeline`**
   - Suggested flags:
     - `--live`
     - `--keep-sandbox`
     - `--files PATH`
     - `--report md,json`
     - `--verbose`

---

## Suggested report structure

```markdown
# 🧪 Pipeline Test Report
Result: ✅ PASS
Mode: replay
Duration: 12.4s
Cost: $0.00
Revert: ✅ verified

## Step Summary
| Step | Status | Time | Key Result |
|------|--------|------|------------|
| Inbox | ✅ | 0.2s | 6 files copied |
| Classify | ✅ | 0.8s | 3 spec, 2 ref, 1 other |
| Rename | ✅ | 0.1s | 6/6 valid |
| Route | ✅ | 0.3s | destinations correct |
| Dedup | ✅ | 0.1s | 1 duplicate suppressed |
| Extract | ✅ | 2.4s | avg quality 0.86 |
| Vault Ingest | ✅ | 0.9s | 5 notes created |
| Index | ✅ | 0.6s | rebuilt |
| Retrieve | ✅ | 0.4s | queries returned hits |
| Prep | ✅ | 0.5s | test client output created |
| Revert | ✅ | 0.2s | sandbox deleted |

## Safety Checks
- Production path access attempts: 0
- Sandbox exists after teardown: no
- Production snapshot delta: none detected
```

---

## Final judgment

Ship **isolated temp-sandbox `corp test-pipeline` first**.  
Do **not** touch production paths or production `ops.db` in v1.  
Use **fixture replay by default**, with **`--live`** for occasional validation.  
Add **runtime isolation guards** so “we think it’s isolated” becomes “we verified it was isolated.”

This gives Rob the one-command, autonomous, reversible, scannable end-to-end test he wants with the best safety-to-value ratio.
