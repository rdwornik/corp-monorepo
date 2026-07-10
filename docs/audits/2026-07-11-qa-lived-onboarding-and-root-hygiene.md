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

**Scope.** Every top-level entry, in plain language, with evidence and a
**proposal-only** verdict. Findings skew **KEEP** because corp is a converged repo
— the value here is the three *permanent answers* (§3.2) + staleness flags, not
manufactured relocations. **No KILL proposals**: every entry traces to a live
consumer, ADR, or commit (checked). Nothing is deleted, moved, or renamed by this
run.

### 3.1 Full root inventory

Last-touched = `git log -1 --format=%as` on the path (worktree checkout date is
uniform 2026-07-10 and is *not* authorship — git dates below are the real signal).

| Entry | What it is (plain language) | Why it exists (evidence) | Last-touched | Verdict |
|---|---|---|---|---|
| `.claude/` | Agent-instruction config: methodology floor + sha256 guard, `settings.json` (SessionStart/Stop hooks), `commands/override.md`, gotchas skill | Methodology v1.2.0 adoption (`0cab8be`, #14); tracked-`.claude` convention via `.gitignore` negations | 2026-07-07 | **KEEP** |
| `.corp-monorepo.code-workspace` | VS Code multi-root workspace file (dot-prefixed, ADR-59 sort settings) | `8d11ca3` (ADR-59 sort settings) | 2026-05-28 | **KEEP** |
| `.gitattributes` | Line-ending policy (LF for py/yaml, CRLF for ps1) | `2202c25` | 2026-03-25 | **KEEP** |
| `.github/` | CI — `workflows/` (fail-closed nightly-triage Action) | `d7e8031` (nightly triage) | 2026-06-06 | **KEEP** |
| `.gitignore` | Ignore rules + corp-owned `.claude` re-include negations | `3b5fbe8` (post-deploy reconcile) | 2026-07-07 | **KEEP** |
| **`.methodology.yaml`** | **The standing-question YAML** — declares corp's sanctioned methodology divergences (currently: the ruff-gate, review 2026-10-07) | Read by hub Informant `enforcement_coverage.py`/`fleet_health.py` — see §3.2-A | 2026-07-07 | **KEEP-at-root** (§3.2-A) |
| `.pre-commit-config.yaml` | Enforcement config (ruff, tach, floor-hash, canonical_freshness, TOC) | Enforcement surface (Phase 1 §2.1) | 2026-07-07 | **KEEP** |
| `.ruff.toml` | Single ruff config (E/F/I), dot-prefixed (ADR-59) | `d3fa057`; the `.methodology.yaml`-sanctioned divergence | 2026-05-28 | **KEEP** |
| `ARCHITECTURE.md` | Canonical structural doc (`last_reviewed: 2026-06-04`) | ADR-51 (read before structural change) | 2026-06-04 | **KEEP** — D4 staleness deferred (§3.3) |
| `BACKLOG.md` | Canonical living backlog | 7-file canonical (ADR-38) | 2026-07-07 | **KEEP** |
| `CLAUDE.md` | Session contract (single canonical agent-instruction file, ADR-53) | ADR-53 | 2026-07-07 | **KEEP** |
| `config/` | Centralized runtime config: `paths.toml` (CWD>root>~/.corp), `naming_config.yaml`, `agents.yaml`, `audit.yaml`, per-domain subtrees (`extractor/ opportunity/ project/ rfp/`) | CLAUDE.md §4; `73631e3` (audit CLI scaffold) | 2026-06-16 | **KEEP** (minor clarify §3.2-C) |
| `CONTRIBUTING.md` | Canonical contributor guide | `4c54dd5` (7-file canonical) | 2026-06-02 | **KEEP** |
| `docs/` | `decisions/` (ADRs), `audits/`, `intake/`, `archive/`, `diagrams/` (Mermaid+SVG) | Doc tree | 2026-07-10 | **KEEP** |
| `eval/` | CLI `--help` regression snapshots (`cli_snapshot_2026-03-28/`, 54 files), `eval_history.jsonl`, `ontology_benchmark.md` — 58 tracked files | Consumed by `scripts/eval.py`, `check_doc_refs.py`; `294b425` | **2026-03-30 (stale)** | **KEEP + clarify** (§3.2-C); operator: confirm still a live baseline |
| `JOURNAL.md` | Canonical append-only session log | ADR-49 | 2026-07-10 | **KEEP** |
| `LESSONS.md` | Canonical lessons log | 7-file canonical | 2026-06-02 | **KEEP** |
| `models/` | **Confusing name** — classifier **train/test datasets** + CV report + eval results (`classifier_train/test.json`, `cv_report.txt`, `eval_results.json`, `hybrid_classifier.json`); 5 tracked files. NOT code models, NOT binaries | Consumed by `scripts/train_classifier.py`, `create_classifier_split.py`, `eval_classifier.py`; `271c919` | **2026-03-26 (stale)** | **KEEP + clarify/rename-proposal** (§3.2-C) |
| `pyproject.toml` | Single build/deps/pytest config | Monorepo consolidation (ADR-23) | 2026-07-10 | **KEEP** |
| `scripts/` | Dev/ops scripts (gates, audits, eval, training, session hooks) | Tooling | 2026-07-07 | **KEEP** |
| `src/` | The `corp/` package (single-package layout, `src/corp/`) | ADR-23 | 2026-06-06 | **KEEP** |
| `tach.toml` | 4-layer dependency config (interface>orchestration>core>foundation) | Enforcement (Phase 1 §2.4-c) | 2026-04-15 | **KEEP** |
| `tests/` | Test suite (+ `tests/qa_lived/` probe from this run) | Testing; probe = §4 keep/discard | 2026-07-10 | **KEEP** (probe → §4) |
| `VISION.md` | Canonical purpose/scope doc | ADR-38 | 2026-06-02 | **KEEP** |

### 3.2 The three standing questions — answered permanently

#### 3.2-A · The methodology/root YAML: `.methodology.yaml` — *why it is where it is*

**This is the file the operator has asked about repeatedly. Self-contained answer:**

- **Which YAML.** Exactly one methodology YAML sits at root: **`.methodology.yaml`**.
  (The other root `.yaml` is the standard `.pre-commit-config.yaml`; `.ruff.toml`
  and `tach.toml` are TOML, not YAML.)
- **What it is.** A tiny (13-line) declaration of corp's **sanctioned methodology
  divergences** — component id + a MANDATORY reason + a time-box. Today it holds
  exactly one: `ruff-gate` (corp runs its own ruff v0.15.8; review_date 2026-10-07).
- **What reads it (grep-verified consumers — all hub-side; corp code does NOT read it):**
  - `.dev-knowledge/scripts/enforcement_coverage.py` — `ALLOWLIST_REL = ".methodology.yaml"`
    (L169); reads `<root>/.methodology.yaml` `sanctioned_divergences` (L206); the
    per-consumer drift/fire-test consults it (L881).
  - `.dev-knowledge/scripts/fleet_health.py` — the divergence allowlist (contract 5,
    "no central exception registry"; L253/285/320).
  - `.dev-knowledge/deploy/release-v1.3.x-contract.md` — #276 `detect_prune` consults
    the consumer-declared allowlist (L98/109/123).
- **Why root, not `config/` (the crux of the recurring question).** The hub Informant
  looks it up at a **fixed, well-known path: the consumer repo ROOT** —
  `enforcement_coverage.py:161`: *"repo ROOT (`.methodology.yaml`), committed-by-default,
  so it is read from the SAME working tree."* It is a **cross-repo contract file**, the
  same class as `.pre-commit-config.yaml` / `.gitignore` / `.gitattributes`: tooling in
  *another* repo hard-codes `<root>/.methodology.yaml`. Moving it to `config/` would
  break `ALLOWLIST_REL` in two hub scripts. It is dot-prefixed precisely to satisfy
  ADR-59 root dot-prefix discipline — i.e. it is *correctly* a root dotfile.
- **Recommendation: KEEP at root (do not relocate).** Relocation has negative value
  (breaks the hub contract) and no upside. **To end the recurring question**, add one
  line to `CLAUDE.md` §4 (proposal text, §4 menu): *"`.methodology.yaml` (root) declares
  corp's sanctioned methodology divergences; read by the hub Informant at the fixed
  path `<repo-root>/.methodology.yaml` — keep at root, do not move to `config/`."*

#### 3.2-B · Mermaid inventory — every block, current-vs-stale, and the #262 doctrine

Five Mermaid blocks exist (2 fenced in ARCHITECTURE.md + 3 standalone `.mermaid` in
`docs/diagrams/`). None in `BACKLOG.md`. Plus `docs/diagrams/conventions.yaml`.

| # | Block | What it shows | Current vs stale (evidence) | Recommendation |
|---|---|---|---|---|
| M1 | `ARCHITECTURE.md:72` **codemap** (`CODEMAP:START/END`) | 10-node top-level package graph, 4 layer colors | **Current** — node layers (cli=interface, ingest=orchestration, extractor/retrieve/project/opportunity/rfp/ops=core, schema/extraction=foundation) match `tach.toml` exactly | **Keep hand-authored** — marker L120 "not generator-managed" (ADR-51 amdt). Folds into D4 *only when* hub #262 can model corp's layout |
| M2 | `ARCHITECTURE.md:275` **layer boundary** | 4-node interface→orchestration→core→foundation flow | **Current** — matches `tach.toml` layer order + the §Layer-Assignments lists | **Keep hand-authored** (trivially accurate) |
| M3 | `docs/diagrams/system-context.mermaid` (+`.svg`) | System-context view (referenced ARCHITECTURE.md L59) | **Stale** — last-touched **2026-03-30**; predates the ADR-30/31/38/53/54 governance churn | **Mark-stale → fold into D4 refresh** (re-render via `scripts/render-diagrams.ps1`) |
| M4 | `docs/diagrams/container-module.mermaid` (+`.svg`) | Container/module view | **Stale + superseded** — 2026-03-30; ARCHITECTURE.md L68 says the L72 codemap "supersedes the hand-drawn `container-module.svg` (retained only as a curated higher-level view)" | **Mark-stale → fold into D4** (or retire in favor of M1 — operator call) |
| M5 | `docs/diagrams/magistrala-pipeline.mermaid` (+`.svg`) | Ingest/pipeline flow | **Stale** — 2026-03-30 | **Mark-stale → fold into D4 refresh** |
| — | `docs/diagrams/conventions.yaml` | Diagram layer-name legend | **Stale + known drift** — 2026-03-30; the deferred "conventions.yaml layer-name drift" (JOURNAL 2026-05-18, gap-review §3-E) | **Fold into D4 refresh** (reconcile layer names to `tach.toml`) |

**How this squares with the hub codemap doctrine.** The hub's north star is a
**generator-managed** codemap (#262). For corp that is **BLOCKED** (G11 / intake
`2026-07-10-runbook-gap-notes.md`): the generator's node granularity is "top-level dir
under `src/`", corp has exactly one (`corp`), so it collapses to a **single orphan node,
0 edges, layer `-`**. Being tach-bearing does not rescue it. Therefore the two
ARCHITECTURE.md Mermaids **correctly stay hand-authored** (M1's L120 marker already says
so), and the pre-commit config **correctly does not consume the codemap hooks** (only the
TOC hooks). **Nothing here is a defect to fix now** — M1/M2 are current; M3/M4/M5 +
conventions.yaml are the *visual-diagram* set that needs a manual refresh, which belongs
to the D4 session (§3.3), gated on #262 only for the codemap sub-dimension.

#### 3.2-C · Folder names that don't self-explain

| Folder | What it actually holds | Proposed one-line clarification (proposal-only) |
|---|---|---|
| **`models/`** | Classifier **training/test datasets** + CV report + eval results (5 JSON/txt). **Not** code models (`src/corp/models.py`), **not** model binaries. Consumed by `scripts/train_classifier.py` etc. | Add `models/README.md`: *"Classifier training/test datasets + evaluation artifacts consumed by `scripts/*classifier*.py`. NOT code models (see `src/corp/models.py`), NOT binaries."* **Optional rename-proposal** (operator-gated, a move → not executed): `models/` → `classifier_data/`. |
| **`eval/`** | CLI `--help` regression snapshots (`cli_snapshot_2026-03-28/`), `eval_history.jsonl`, `ontology_benchmark.md`. Baseline for CLI/docs drift; consumed by `scripts/eval.py`. Stale (2026-03). | Add `eval/README.md`: *"CLI `--help` regression snapshots + eval history + ontology benchmark; baseline for CLI/doc drift (`scripts/eval.py`). Snapshots captured 2026-03-28 — re-capture before trusting as a live gate."* |
| `config/` | Centralized runtime config: `paths.toml` + per-domain subtrees. Clear-ish | Optional: one line in `config/` referenced from CLAUDE.md §4 (already documents `paths.toml`). Low priority. |

### 3.3 Cross-link — this audit is the INPUT PACKAGE for the D4 ARCHITECTURE.md refresh

This run **surfaces, does not resolve** the D4 finding (*"ARCHITECTURE.md 7+ weeks
stale / not in canonical generator-managed form"*; origin `docs/audits/2026-05-20-corp-monorepo-deep.md`,
re-surfaced in the B-S2 intake). Per the B-S2 operator ruling, the D4 refresh is a
**separate, dedicated `fix/`-scoped session — NOT started here.** This §3 is its
**input package**:
- **Staleness dimension** → the ADR-30/31/38/53/54 prose references in ARCHITECTURE.md
  (deferred; not edited by this run).
- **Codemap dimension** → M1 stays hand-authored; gate any generator adoption on hub
  **#262** (G11 requirement input: generator must model `src/<pkg>/<subpkg>/` granularity).
- **Visual diagrams** → M3/M4/M5 + `conventions.yaml` need a manual re-render
  (`render-diagrams.ps1`); fold into the same D4 pass.
- **Go/no-go** for that session is a §4 menu row.

---

## 4. MORNING ACTION MENU

_(filled in Phase 3 checkpoint)_
