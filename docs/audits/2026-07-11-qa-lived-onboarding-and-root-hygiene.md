---
title: QA lived-onboarding arc + root hygiene audit — corp-monorepo
date: 2026-07-11
type: AUDIT
status: proposal-only (operator rules dispositions)
branch: worktree-lane-q-qa-lived-audit
base_head: af3a793 (B-S2 merge)
hub_ref: 47f31b5 (read-only, untouched by this run)
---

# QA lived-onboarding arc + root hygiene audit — corp-monorepo

> **Night run, unattended.** Lane branch `worktree-lane-q-qa-lived-audit`; `main`
> untouched; hub `.dev-knowledge` @ `47f31b5` read-only and verified clean before
> and after every step. All hygiene verdicts are **proposal-only** — the operator
> rules keep/relocate/kill in the morning (see §4 MORNING ACTION MENU).
> Every claim is anchored to a SHA, `file:line`, or verbatim tool output.

---

## 1. Executive so-what

_(filled in Phase 3 — see MORNING ACTION MENU §4 for the one-word decisions)_

**Headline (Phase 1):** the freshly onboarded (n=2) repo **held under a lived agent
arc**. Every enforcement organ that *exists* fired exactly when it should
(floor-hash-verify, tach-check, ruff, canonical_freshness) and passed when it
should. Two **absences** (not breakages) surfaced and are already hub-tracked or
discipline-only: **no commit-msg conventional-commit gate** and **no `block_ff_push`
pre-push guard** (hub **#302**). **P1 count (broken/failed-to-fire gates): 0.**
Two enforcement **coverage gaps** flagged for an operator ruling (commit-msg,
pre-push) — neither is a broken gate; both are "guard absent by current config."

---

## 2. Phase 1 — QA lived agent arc (scorecard)

**Method.** A scripted "day in the life": task → code → file writes → dependency
use → tests → commit through every gate → negative gate-trips → push-block →
closing organ battery. Not a presence check — each organ was made to **fire in a
lived workflow**, exactly as a working agent would hit it. Probe artifacts live
under `tests/qa_lived/` (the sanctioned test location per the prompt; no dedicated
scratch dir exists — recon confirmed). Probe commit: **`bb2e16e`**.

### 2.1 Enforcement map (recon)

From `.pre-commit-config.yaml`, the installed `.git/hooks/*` shims, and a full-repo
grep:

| Stage | Wired hooks | Notes |
|---|---|---|
| **pre-commit** | ruff (v0.15.8 `--fix`), tach-check (`^src/corp/.*\.py$`), normalize-headers (`^(JOURNAL\|LESSONS)\.md$`), floor-hash-verify (`^\.claude/CLAUDE-FLOOR\.md(\.sha256)?$`), canonical_freshness (`always_run`), toc-freshness (hub@v1.2.0, `^ARCHITECTURE\.md$`) | The live enforcement surface |
| **commit-msg** | **(none)** — shim installed by `default_install_hook_types`, zero stage hooks | No conventional-commit gate anywhere (no commitizen/gitlint). Discipline-only. |
| **pre-push** | **(none)** — shim installed, zero stage hooks | No `block_ff_push`. Known hub **#302** (PARITY-DEPLOY). |

`default_stages: [pre-commit]` scopes stage-less hooks to commit time (the ADR-14 /
methodology-adoption fix). Floor sidecar `4d268f3…111f` == `sha256(.claude/CLAUDE-FLOOR.md)`.

### 2.2 Skills / config load — what fired and steered the session

| Loaded surface | Evidence it *steered* the run |
|---|---|
| `CLAUDE-FLOOR.md` @-include (branch→merge `--no-ff`, never commit to `main`) | Session executed entirely on the lane branch; `main` @ `af3a793` untouched (`git log --first-parent`). |
| SessionStart arm-leg (`pre-commit install`) | Startup output: *"pre-commit installed at …/pre-commit, …/commit-msg, …/pre-push"* — 3 stages armed (verified present in `.git/hooks/`). |
| gotcha: here-string commit body leaks delimiters | **Every** commit used `git commit -F <tmpfile>` (never inline `-m` for multi-line). |
| gotcha: `dev-check.ps1` mutates the tree (`ruff format src/`) | Deliberately **not** run; used `pytest` + `ruff check` directly to keep probe commits clean. |
| gotcha: codemap hooks NOT consumed (single-package layout) | Directly informs the Phase 2 Mermaid answer (§3). |
| core-invariants (OneDrive exclusion, no-delete, no hub writes) | Negative-push probe used a bare remote **outside** the repo tree; every negative probe reverted; hub verified clean before/after each organ. |

### 2.3 Dependency flow — B-S2 item-6, lived

| Check | Result |
|---|---|
| `tach --version` | `tach 0.35.0` — from `…/corp-monorepo/.venv/Scripts/tach.exe` |
| `python -c "import pre_commit"` | `pre_commit 4.6.0` → `…/.venv/Lib/site-packages/pre_commit/__init__.py` |
| Both declared in `pyproject.toml` `[project.optional-dependencies].dev` | `pre-commit>=4.0`, `tach>=0.35` (commit `5798598`) — the item-6 fix |
| Lived use | tach-check **fired** in negative-(c); pre-commit orchestrated **every** commit in the arc. Both resolved from corp's `.venv`, not a global. |

### 2.4 Per-gate scorecard (positive + negative trips)

**Rule:** a gate that cannot go red is not enforcement. `PASS-FIRED` = the gate
blocked exactly when it should. `PASS-GREEN` = passed a legitimate commit.
`GAP` = the gate the prompt expected does not exist (absence, not breakage).

| # | Gate | Expected | Observed | Verbatim evidence | Verdict |
|---|---|---|---|---|---|
| P | ruff | pass clean probe | Passed | `ruff (legacy alias)…Passed` (commit `bb2e16e`) | **PASS-GREEN** |
| P | tach-check | skip (no `src/corp` staged) | Skipped | `tach (import boundaries)…(no files to check)Skipped` | **PASS-GREEN** (scope-correct) |
| P | canonical_freshness | pass (no stale canonical edit) | Passed | `canonical_freshness…Passed` (ran `always_run` on every commit) | **PASS-GREEN** |
| a | floor-hash-verify | BLOCK on floor mutation | Failed, exit 1, commit aborted | `floor hash drift: d6bfba336936 != sidecar 4d268f329a7e -- …restore with git checkout HEAD…` | **PASS-FIRED** |
| b | commit-msg gate | reject non-conventional msg | **commit SUCCEEDED (exit 0)**; msg landed verbatim (`6e6a1d3`, soft-undone) | `git commit --allow-empty -m "QANEGB this is NOT a conventional commit message !!! nonsense"` → exit 0 | **GAP** (no gate; discipline-only) |
| c | tach-check | BLOCK illegal cross-layer import | Failed, exit 1, commit aborted | `[FAIL] src\corp\cleanup\_qa_tach_probe.py:11: Cannot use 'corp.cli.cli'. Layer 'core' ('corp.cleanup') is lower than layer 'interface' ('corp.cli').` | **PASS-FIRED** |
| d | pre-push `block_ff_push` | BLOCK non-ff push | **no pre-push hook fired** (empty stage); git-native non-ff **rejected** the push | push: `! [rejected] qa-ff-b -> shared (non-fast-forward)` exit 1; no hook lines on either push | **GAP-hook** (#302) / **PASS-git-native** |

**Reverts confirmed.** After each negative probe: floor `sha256` back to `4d268f3…111f`
and tree clean (a); bad-message commit soft-undone to `bb2e16e` (b); tach probe
deleted + `tach check → [OK] All modules validated!` (c); lane branch never moved
from `bb2e16e`, throwaway remote + branches removed, only `origin` remains, tree
clean (d).

**On (b)/(d).** Neither is a broken gate — each is a **guard that does not exist in
corp's current config**. (d) is already hub-tracked (**#302**, PARITY-DEPLOY;
corp has a private GitHub remote, so a push-time guard is meaningful — a `--force`
push has no corp hook to stop it). (b) has no tracking item yet; conventional
commits are enforced by agent discipline + the floor, not machinery. Both are
put to the operator in §4. Cross-confirmation: the hub Informant reports corp's T2
`precommit` carrier as **`present-not-wired`** (§2.5 row 4) — consistent with the
commit-msg + pre-push stages being armed-but-empty (needs-confirmation of the exact
carrier criterion; not over-claimed).

### 2.5 Closing organ battery (#215 seven-row, re-run as the closing baseline)

Hub `.dev-knowledge` @ `47f31b5` verified **clean before and after every row**;
zero hub writes. Runnable organs were vetted to write only to `tempfile.mkdtemp`
clones (or nothing); hub-write-capable organs were **held as honest-partials**
under the NO-hub-writes hard rule (not a coverage regression — the authoritative
result is B-S2's, cited).

| # | Organ | Invocation | Observed | Verdict |
|---|---|---|---|---|
| 1 | audit repo | `audit.py repo corp-monorepo --repo-path …` | **NOT run** — writes to hub `AUDITS_DIR`/`ECOSYSTEM_INDEX`; unattended NO-hub-writes | **honest-partial** (B-S2 = G6/**#296**: prints report path exit 0, file not persisted) |
| 2 | health | `audit.py health` (docstring: *"No file writes"*) | `health: OK` exit 0; hub self-audit 22/37 pass (warns are hub-internal); repos registered incl. `corp-monorepo` | **PASS** |
| 3 | floor-hash | `python .claude/check_floor_hash.py` (corp-local) | exit 0 (floor == sidecar) | **PASS** |
| 4 | enforcement_coverage `--fire` | `enforcement_coverage.py --consumer corp-monorepo --fire --no-write --run-date 2026-07-11` | `2 enforcing-local`: `session_end_backpressure` + `canonical_freshness` **FIRED**; T2 `precommit present-not-wired`; exit 0 | **PASS (2 organs FIRED)** |
| 5 | observe-arc | `PYTHONPATH=deploy python -m lived_sandbox.cli observe-arc --consumer …` | `consumer measurement could not run: ANTHROPIC_API_KEY not in env … the isolated child cannot authenticate` exit 1 | **honest-partial** (G7/**#297**, env-limited by design) |
| 6 | floor_conformance | `deploy/floor_conformance.py --consumer <corp main>` | `CONFORMANCE PASS (9 properties)` exit 0 (incl. commit-time floor-block + real gated `--no-ff` merge) | **PASS (9/9)** |
| 7 | fleet_health | `scripts/fleet_health.py` | **NOT run** — writes hub `logs/`; unattended NO-hub-writes | **honest-partial** (B-S2 authoritative) |

**Battery shape:** 4 clean PASS (health, floor-hash, enforcement_coverage 2-FIRED,
floor_conformance 9/9) + 3 honest-partials (audit-repo hub-write, observe-arc env,
fleet_health hub-write). Matches the B-S2 attestation shape; the two enforcing-local
organs FIRED identically → **the lived arc did not perturb the onboarded posture.**

### 2.6 Phase 1 verdict

**The onboarded repo held.** 0 P1 findings (no gate that exists failed to fire).
Every real gate went red on cue and green on a clean commit. The only gaps are two
**absent** guards (commit-msg, pre-push/#302), surfaced for an operator ruling.

---

## 3. Phase 2 — Root hygiene audit

_(filled in Phase 2 checkpoint)_

---

## 4. MORNING ACTION MENU

_(filled in Phase 3 checkpoint)_
