# graphify Pilot — Security Review + Project-Scoped Evaluation (#88)

- **Date:** 2026-06-04
- **Author:** Rob (robdwornik)
- **Backlog ref:** [#88] (hub) — evaluate graphify for fleet adoption
- **Nature:** read-only pilot + findings; **no adopt/reject verdict pronounced** (operator's call)
- **Branch:** `chore/graphify-pilot` (unmerged; nothing on `main`)
- **Tool:** PyPI `graphifyy` v0.8.31 (CLI `graphify`); upstream `github.com/safishamsi/graphify`
- **Evidence bundle:** raw query+grep captures lived in `docs/audits/graphify-pilot-evidence/` on the (now-deleted) `chore/graphify-pilot` branch; regenerable from the commands in measurement (b)

---

## What this run was

Executed #88's project-scoped pilot of graphify in corp-monorepo only, gated on a
pre-install security review of its PreToolUse hook. Scope was kept **code-only**
(187 `.py` under `src/corp/`) via `.graphifyignore`, so extraction stayed 100%
local AST with **zero model calls** and nothing left the machine. All graph-build
and `graphify query` runs used a **clean env** (`GEMINI_API_KEY` unset — it IS set
ambiently here, the exact auto-detection #88's correction warned about).

Three measurements per #88: **(a)** graph quality vs the hand-curated
ARCHITECTURE.md codemap, **(b)** token cost of 3 navigation questions graph-query
vs grep, **(c)** maintenance overhead vs hub governance.

---

## Security review — verdict: **SAFE-TO-PILOT** (code is clean)

Source reviewed read-only at tag `v0.8.31` (= the installed PyPI release).

| Area | Finding |
|---|---|
| Package identity | `pyproject` name `graphifyy` v0.8.31; URLs → the GitHub repo; README pre-empts typosquats ("PyPI package is `graphifyy` (double-y)… others not affiliated"). PyPI maintainer handle `captainturbo` vs GitHub `safishamsi` — noted, not blocking. |
| Core deps | 100% local: `networkx`, `datasketch`, `rapidfuzz`, `tree-sitter` + 28 grammars. **All LLM clients (`openai`/`anthropic`/`boto3`) are optional extras** — a plain install has no LLM client (verified: `openai`/`anthropic` not importable in the pilot venv). |
| PreToolUse hook | **Benign.** Only `echo`s a JSON `additionalContext` text nudge ("run `graphify query`…") when `graphify-out/graph.json` exists. No code exec, no network; every branch fails open (`\|\| true`); parser is `python3`, no `shell=True`. |
| Git hook (`hooks.py`) | Not installed in pilot. Reviewed: python-path allowlist sanitized, `core.hooksPath` validated to stay in-repo, runs detached, "code only, no LLM." |
| SECURITY.md | Mature: no `eval`/`exec` (tree-sitter AST only), no `shell=True`, no creds stored; SSRF/path-traversal/XSS/prompt-injection mitigations. Network only on explicit `ingest`/`add` (unused here). |
| Local-AST claim | Confirmed for code; **caveat:** non-code files (.md/PDF/images) ARE sent to the model API per upstream docs. Code-only `.graphifyignore` neutralizes this — detect found 0 docs/papers/images, so the semantic/LLM stage was skipped entirely. |

**Install-path finding (gated the pilot; see measurement (c)):** v0.8.31 has **no
skill-only install path for Claude Code**. `graphify install --project` (Windows →
`windows` platform) routes `_project_install` → `claude_install` →
`_install_claude_hook`, which in one shot writes the skill **and** the PreToolUse
hook into `.claude/settings.json` **and** a `## graphify` section into the **root
`CLAUDE.md`**. Per #88's "do not install the always-on hook in the baseline," the
installer was **bypassed**; the skill file was placed manually. `.claude/settings.json`
and root `CLAUDE.md` were left untouched (verified clean).

---

## Measurement (a) — graph quality vs the hand-curated codemap

Code-only build: **3003 nodes / 6245 edges / 161 communities**, zero LLM tokens.
Benchmark (ARCHITECTURE.md): **10 nodes / 15 edges / 4 layers** (module-level).

**Altitude mismatch is the headline.** graphify produces a *symbol-level* call/type
graph (functions, classes, methods); the curated codemap is a *module/package-level*
architecture map. They answer different questions.

**Agreements (graph captured real structure):**
- God nodes are genuinely corp's core abstractions: `PipelineConfig` (75 edges),
  `OpsDB` (71, the ops facade), `SourceFile` (70), `get_config()` (49), `FileType`,
  `ContentRegistry`, `VaultZone`, `OvernightState`. This centrality view is a real,
  novel insight the codemap does **not** provide.
- The OneDrive safety-guard cluster is correctly grouped (communities 41/75:
  `_guard_onedrive`, `PathTraversalError`, `execute_moves`, `execute_plan`).
- Import cycles: "None detected" — consistent with Tach's 0-violation clean layering.
- The 5 CLIs are each discoverable as distinct nodes/communities
  (`corp` cli/__init__ c125, `cpe` project/cli c38, `com` opportunity/cli c45,
  `corp-meta` schema c89, `cke`/extractor).

**Misses (benchmark's organizing principles absent):**
- **No layer model.** The 4-layer interface>orchestration>core>foundation Tach
  model — the codemap's central concept — is entirely absent.
- **No package-dependency edges.** The 15 curated edges (cli→ingest, ingest→ops,
  ingest→extractor, …) are not represented as module edges. Closest signal:
  `imports`+`imports_from` = 138 symbol-level import edges, not the package graph.
- **The 5 CLIs are scattered, not framed as a set.** You must know to look.
- Over-fragmented: 161 communities for ~30 modules; low cohesion (many ~0.05–0.15).

**Noise / questionable edges:**
- **397 primitive-type nodes** (`str`,`bool`,`int`,`float`,`Path`,`bytes`,`object`,`Any`
  ≈13% of nodes) pollute centrality/clustering.
- 93 isolated nodes; "Surprising Connections" surfaced only trivial same-type edges
  (`StepResult --uses--> StepResult`). 21% of edges are INFERRED (avg conf 0.58) —
  heuristic, flagged by the tool itself as needing verification.

**Verdict (a):** **Worse than the curated codemap for architecture** (layers, package
deps, CLI set), **complementary at the symbol level** (god-node centrality is a
genuine new lens). Not a replacement for ARCHITECTURE.md.

---

## Measurement (b) — token cost, graph-query vs grep

Method: each question answered (i) via `graphify query` (local BFS traversal, clean
env, no LLM) and (ii) via grep — the **same session model interprets both sides**;
what differs is the retrieval mechanism. Cost = est-tokens (chars/4) of the context
each method forces into the model. grep figures include `.pyc` binary-match noise
(a real `rg` run would be smaller), so grep's advantage below is **conservative**.

```
Q  Question                                    graph-query        grep            cheaper   graph-query
   (no leading phrasing)                       chars / est-tok    chars / est-tok  method    answer quality
-- ------------------------------------------- -----------------  --------------- --------  ----------------------------
Q1 What writes to 02_sources/                  4923 / 1230        1231 / 307      grep 4.0x WRONG (keyword-matched
                                                                                            "writes"; missed vault_io/
                                                                                            ingest, the ADR-27 writer)
Q2 Where does the CLI register opportunity     6307 / 1576        1135 / 283      grep 5.6x PARTIAL (found opportunity/
   commands                                                                                 cli.py; mixed in project/cli
                                                                                            noise; no @cli.command detail)
Q3 What depends on naming_config               6277 / 1569        2547 / 636      grep 2.5x GOOD but INCOMPLETE (missed
                                                                                            cli/analytics.py importer)
-- ------------------------------------------- -----------------  --------------- --------  ----------------------------
   grep answer quality: Q1 correct trail · Q2 correct+clear · Q3 correct+complete (3/3)
```

**Findings:** At corp's scale, **grep is cheaper on tokens (2.5–5.6×) AND higher
quality (3/3) on all three questions** — the opposite of the #88 hypothesis. Two
mechanisms: (1) graphify query dumps ~34–42 nodes+edges incl. primitive noise
(~1.2–1.6k tok) where grep returns just matching lines (~0.3–0.6k tok);
(2) query selects start nodes by **keyword-matching node labels/docstrings**, so a
path-literal question ("02_sources/", not a node) collapsed to noise on Q1.

**Scale caveat (must read with the above):** the crossover variable is grep
result-set size. corp's three questions returned **16 / 21 / 29 grep lines** — far
below the point where grep's token cost would exceed graph-query's ~1.2–1.6k fixed
overhead. graph-query's bounded-context advantage is hypothesized to appear only
once grep result-sets are large enough to cross that line; corp's queries did not
reach it. (corp was historically declared *Project Scale: L* under the now-deprecated
tier system, but in absolute terms ~187 `.py` files / ~30 modules keep
single-symbol grep result-sets small.) **This pilot therefore shows graph
navigation does not pay off at corp's actual query sizes; it cannot prove the
large-result-set case either way.**

---

## Measurement (c) — maintenance vs hub governance

- **Freshness mechanism is outside the hub model.** graphify keeps the graph fresh
  via raw **git post-commit/post-checkout hooks** (`graphify hook install`) written
  directly into `.git/hooks/` — un-versioned, per-clone, not rev-pinned. ADR-71's
  governance model is hub-sourced tooling consumed via **rev-pinned
  `.pre-commit-config.yaml` stanzas** (single-source, no drift). graphify's hooks are
  *not* pre-commit-framework hooks and sit entirely outside that model. The
  alternative (manual `--update`) is a human step that drifts.
- **Installer mutates governed files (operator-mandated finding, verbatim):**
  "v0.8.31 has NO skill-only install path: the documented command force-bundles the
  PreToolUse hook, edits the governed root CLAUDE.md (ADR-53 contract) and
  .claude/settings.json. Adoption therefore means either accepting installer
  mutations of governed files, or maintaining a manual install procedure that drifts
  from upstream docs."
- **Repo weight:** `graphify-out/` = **7.1 MB / 190 files** — `graph.json` **3.06 MB**
  + `GRAPH_REPORT.md` 58 KB + `cache/` (187 per-file entries ≈ 4 MB). The post-commit
  hook rebuilds `graph.json` every commit → a 3 MB artifact churns git history if
  committed, or must be gitignored (then the graph isn't shared and each dev rebuilds).
- **Dependency footprint:** 30+ packages incl. 28 tree-sitter grammars + scipy/numpy
  for a Python-only repo (isolated in the venv; not a repo concern, but real install weight).

---

## Kill-criterion evaluation (evidence only — operator rules)

**Criterion (verbatim from #88):** *"adopt ONLY if token savings or navigation
quality are material AND maintenance fits the hub governance model"*

| Sub-claim | Evidence | 
|---|---|
| **Token savings material?** | No — at corp's query sizes graph-query cost **more** (1230/1576/1569 vs grep 307/283/636 est-tok; grep 2.5–5.6× cheaper). **Caveat:** corp's grep result-sets were small (16/21/29 lines), below the crossover where bounded graph context would win; the large-result-set case is untested. |
| **Navigation quality material?** | Mixed-negative for the tested navigation: graph Q1 wrong, Q2 partial, Q3 incomplete; grep 3/3 correct. Graph does **not** capture the codemap's layers/package-deps. **But** god-node centrality is a genuine new lens grep+codemap lack. |
| **Maintenance fits hub governance?** | Not as-shipped: freshness via un-versioned local git hooks (outside ADR-71 rev-pin model); installer force-mutates governed CLAUDE.md/settings.json (no skill-only path); 3 MB churning `graph.json`; 30+ deps. |

The criterion requires **(token savings OR navigation quality material) AND
(maintenance fits hub governance)**. Evidence on all three sub-claims is presented
above. **No verdict is pronounced here — that is the operator's ruling.**

---

## Disposition

Findings are proposals for operator triage. The pilot is complete and reproducible;
`chore/graphify-pilot` is **unmerged**. On the operator's ruling:
- **Adopt** → a follow-up session merges + wires docs (and must decide the
  governed-file/hook-governance questions in measurement (c)).
- **Reject** → delete the branch, `pip uninstall`/remove `.graphify-venv`; nothing
  remains on `main`.

---

## Operator Ruling

**Operator ruling 2026-06-04: REJECT** — kill criterion failed on both clauses
(grep cheaper 2.5–5.6x and higher quality 3/3; maintenance conflicts with hub
governance: unversioned local hooks, installer mutates governed files, 7.1MB
churning artifact). The symbol-level god-node lens remains available as an ad-hoc
analysis instrument from a temp clone — no adoption required.
