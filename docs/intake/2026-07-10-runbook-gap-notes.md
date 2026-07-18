# Runbook gap-notes — corp-monorepo (Wave-1 **n=2**)

> **Consumed by:** `.dev-knowledge` repo-onboarding runbook — Wave-1 n=2 gap-notes (G10+), hub-filed. No corp ADR/BACKLOG consumer (cross-repo methodology deliverable).

> **Routing:** text artifact for the operator to file into `.dev-knowledge` — **no hub write was
> made from this consumer chat.** Every gap hit while EXECUTING
> `.dev-knowledge/docs/runbooks/repo-onboarding.md` (the #131 install sequence + the #215
> conformance verify) is the **n=2 gate's product** — a deliverable, not a failure.
>
> **G-series:** continues the global counter from the ai-council n=1 pilot (G1–G9) → **G10+**.
> **Baseline:** B-S1 (ai-council n=1), `ai-council/docs/intake/2026-07-08-runbook-gap-notes.md`.
> **Session:** B-S2, branch `chore/b-s2-corp-onboarding`, executed 2026-07-10.

---

## Context

corp-monorepo was **already substantially onboarded** at v1.2.0 (recorded n=2 in the runbook;
all 6 install layers present). B-S2 is therefore **verify-heavy**, not a fresh install. The
gaps below are the deviations/ambiguities the runbook surfaced on the first *structurally hard*
consumer (Scale-L, tach-bearing, single-package `src/corp/`, ADR-36 no-local-handoffs).

Two contract items were **amended by the operator** this session (ADR-81 architect prerogative):
- **Item 4** (leg-b seeder) → honest-partial: `--check` witnessed classification satisfies it.
- **Item 5** (#262 codemap) → BLOCKED/honest-partial: the premise (corp closes #262) was
  falsified by recon; the failure mode is a **requirement input** to the hub-side #262 fix.

---

## Gap-notes

### G10 — `seed_runbook.py` is not child-class-aware (NEEDS-RULING / HUB-DEFECT)
The leg-b seeder (`.dev-knowledge/scripts/seed_runbook.py`, #164 leg b) writes **only**
`<target>/docs/handoffs/README.md`, unconditionally. Run against corp (`--check`):
```
[seed-runbook] seeded: would write C:\Users\…\corp-monorepo\docs\handoffs\README.md   (exit 1)
```
But **ADR-36 makes corp a no-local-handoffs child** (corp CLAUDE.md §1/§6/§11: "corp carries no
local handoffs dir"; handoffs are generated in `.dev-knowledge` only). A real seed would create
`corp/docs/handoffs/` — the exact directory ADR-36 forbids. This is the **same class** as
ai-council's **G3** (census `docs/handoffs` target vs ADR-60/42), which the hub resolved for
ai-council by "create `docs/intake/` only, not `docs/handoffs/`". The seeder never absorbed that
ruling: it still assumes every consumer takes a local `docs/handoffs/`.
- **Operator ruling this session:** contract item 4 → **honest-partial**; the witnessed `--check`
  classification satisfies it. **No write was made** (corp/docs/handoffs/ confirmed still absent).
- **Impact (HUB DEFECT, not a corp quirk):** any ADR-36 child (corp-monorepo, and the class the
  #131 fan-out will hit) is mis-served by the leg-b seeder as-is. A literal run would violate ADR-36.
- **Candidate hub enhancement:** make `seed_runbook.py` **child-class-aware** — read the target's
  handoff-locality class (ADR-36 no-local-handoffs vs local) and either (a) seed `docs/intake/`
  guidance instead of `docs/handoffs/README.md`, or (b) skip + emit a documented "child is
  hub-handoff-only, nothing to seed" status. Encode the ADR-36 child class so the deferred #131
  fan-out (ADR-41) cannot silently create forbidden dirs.
- **Kill-candidate per backpressure:** if the leg-b seeder's audience is only *local-handoff*
  repos, gate it on that class and make ADR-36 children a first-class "skip" — no per-child
  handoff runbook copy for repos that have no local handoffs dir by contract.
- **Route:** file as a **hub intake candidate** (BACKLOG `[#…]`), paired with / cross-referencing
  the G3 census-amendment ruling (`docs/audits/2026-07-08-census-amendment-docs-handoffs-ruling.md`).

### G11 — #262 generator-managed codemap unreachable on a single-package layout (NAMED / requirement-input)
The plan-v3 premise was: *corp is tach-bearing (unlike ai-council's flat layout), so it can close
the generator-MANAGED codemap owe #295 blocked on (n≥1)*. **Recon + this witness falsify it.**
Running the generator (dry-run, no `--write`) against corp's `src/corp/` single-package layout:
```
warning: orphan modules (no edges): corp
| module | layer | path      | flags  |
| corp   | -     | src/corp/ | orphan |
Dependencies: (none)
```
The generator collapses corp's **13 subpackages** (cli, ingest, extractor, retrieve, project,
opportunity, rfp, ops, schema, extraction, cleanup, overnight, …) into a **single orphan `corp`
node, 0 edges, layer `-`**. corp's hand-authored Mermaid codemap (`ARCHITECTURE.md` L71-121) is
**10 nodes / ~17 edges / 4 layers**; `--write` would catastrophically regress it. So corp's config
correctly **does not consume the codemap hooks** (`.pre-commit-config.yaml` note).
- **Root cause:** the generator's module granularity is "top-level dir under `src/`". corp has ONE
  such dir (`corp`), and its `tach.toml` layers are keyed at `corp.<subpkg>` (dotted, one level
  BELOW the generator's node granularity), so every layer label is unassigned (`-`) and there are
  no inter-module edges to draw.
- **Same OUTCOME as ai-council G4/#295, different MECHANISM:** ai-council = flat, no `tach.toml`
  (2-orphan stub); corp = single-package WITH `tach.toml` (1-orphan). **Being tach-bearing does not
  rescue #262** — the blocker is node-granularity, not tach-presence. This is the key correction to
  the plan-v3 assumption.
- **Operator ruling this session:** contract item 5 → **BLOCKED / honest-partial**; the premise was
  falsified by recon. corp does NOT close #262 this session. **Nothing written** (ARCHITECTURE.md
  untouched; D4 codemap dimension stays deferred per the surface-only ruling — see below).
- **Requirement input to the hub-side #262 fix (the deliverable):** the generator must derive
  sub-module nodes from the package tree *below* the single `src/<pkg>/` root — i.e. treat
  `src/corp/<subpkg>/` as the node granularity and match `tach.toml` `corp.<subpkg>` layer keys —
  OR derive edges from the AST import graph (the existing `ast_walker`) at that sub-package
  granularity. Then a tach-bearing single-package repo (corp) can be the n≥1 close. File alongside
  ai-council's **#295** as the second concrete failing layout: **flat (ai-council)** AND
  **single-package-with-subpackages (corp)** both degenerate; the fix must handle both.
- **Kill-candidate per backpressure:** if generator-management is only ever pursued for genuinely
  multi-top-level-package repos, close #295/#262 for single-package + flat layouts and let them
  stay HAND-AUTHORED by policy (corp's L120 marker already says so). Decide before building the fix.

### G12 — runbook deploy command notation is wrong: `<consumer>` (path) vs required `<name>` (NAMED)
The runbook's install-sequence deploy command (`docs/runbooks/repo-onboarding.md` L40/L43)
reads `python deploy/tool.py <consumer> --target 1.2.0`. Its own notation key (L26) defines
`<consumer>` = **the consumer repo's filesystem path**. But `deploy/tool.py` takes the
consumer's **directory name** (the `ecosystem/deployed-versions.yaml` key; see `tool.py` L18,
L25). Passing the filesystem path aborts preflight:
`Error: preflight failed -- 'C:/Users/…/corp-monorepo' is not a registered consumer in
deployed-versions.yaml (known: …)`. The working invocation is `deploy/tool.py corp-monorepo
--target 1.2.0`.
- **Impact:** a literal-reading operator's very first runbook command fails. n=1 (ai-council)
  did not surface it — likely run from muscle memory with the name, not the path.
- **Candidate hub enhancement:** fix the runbook to `python deploy/tool.py <name> --target 1.2.0`
  (or make `tool.py` accept a path and resolve it to the registry key). One-line doc fix + an
  optional path-tolerance in the resolver.
- **Compounding — the toolchain's consumer-identifier is inconsistent across tools:** each names
  the consumer differently — `deploy/tool.py <name>` (positional registry name), `audit.py repo
  <name> --repo-path <path>` (BOTH), `enforcement_coverage --consumer <name>` (registry name),
  `floor_conformance --consumer <path>` (filesystem path), `seed_runbook --target-root <path>`.
  The runbook's uniform `<consumer>`/`<name>` notation cannot predict which form a command wants
  (of the #215 commands, three take a name, two take a path). A runbook notation table mapping
  each command → its actual arg form would prevent the class.
- **Kill-candidate per backpressure:** doc-only fix; no build. Trivial.

### G13 — runbook has no "already-onboarded / verify-only" re-run mode (NAMED)
corp is already fully converged (assess: `0 need apply, 5 already correct`). Yet the runbook's
only install path is the `deploy/tool.py … --execute` converge, which (a) requires a **clean
consumer tree** (aborts otherwise — so re-verifying a repo you're actively working in forces you
to stash/move your own files), and (b) on corp would hit the **prune sweep**: the methodology-
removed `ruff-gate` component is `present_modified` in corp, so `--execute` would REFUSE-to-prune
and demand confirmation. There is no "just re-verify an onboarded repo, write nothing" mode.
- **Impact:** the n=2 gate (and every future re-verify) is verify-heavy, but the runbook is
  written for greenfield install only; the operator must improvise the verify-only path.
- **Candidate hub enhancement:** a documented verify-only re-run (the assess + the #215 battery,
  no converge) for already-onboarded consumers; and let the read-only **assess** run on a dirty
  tree (it writes nothing — only `--execute` needs the clean-tree guard).
- **Kill-candidate per backpressure:** if re-verify is always the #215 battery anyway, this may
  be a doc note ("for re-verify, skip the converge, run #215"), not new code.

### G14 — #299 BACKLOG bookkeeping lags the merged fix (MINOR / hub bookkeeping)
The #299 (G8) release gate is satisfied on the code path — the corrected Layer-6 verify is merged
(`.dev-knowledge` `5ee7fb2`, HEAD) and the two-direction fire-test is GREEN — but hub `BACKLOG.md`
L86 still carries `[#299] … · DEFER — peg: post-Wave-1` (not flipped to closed). Presence of the
fix ≠ closure record.
- **Impact:** minor/bookkeeping — a reader gating on the BACKLOG (not the merge) would think #299
  is still open. Reconciliation is a `/review-closures` flip citing the fire-test evidence.
- **Bonus linkage (worth recording):** #299's own BACKLOG text predicted corp's fragility verbatim
  — *"corp-monorepo shares the latent fragility (`pre_commit` in its `.venv` but undeclared in
  pyproject → a fresh re-clone won't repopulate it)."* **This B-S2 session remediated exactly that**
  (Phase 3 / commit `5798598`: declared `pre-commit>=4.0` + `tach>=0.35`). So the fragility class
  #299 flagged is now closed on BOTH legs: hub-side (runbook verify, #299) + consumer-side (corp
  pyproject, B-S2). The #299 closure note can cite this.
- **Route:** hub bookkeeping (Tier-1 `/review-closures`); no new build.

### X-ref (not new) — G6/#296 reproduces on corp
`python scripts/audit.py repo corp-monorepo --repo-path <corp>` printed
`Report: …/docs/audits/2026-07-10-corp-monorepo-audit.md` (exit 0) but **the file was not
persisted** (absent on `ls`). Same defect ai-council filed as G6 → hub **#296**. floor_integrity
was still confirmed via exit 0 + the deploy assess (`floor present_correct`) + corp `state.yaml`
(`floor_integrity: pass … sha256 4d268f329a7e…`). Cross-reference only; no new id.

### X-ref (not new) — G7/#297 reproduces on corp (observe-arc env-constrained)
`PYTHONPATH=deploy python -m lived_sandbox.cli observe-arc --consumer <corp>` (#215 row 5) exited 1:
`consumer measurement could not run: ANTHROPIC_API_KEY not in env … the isolated child cannot
authenticate`. Same env constraint ai-council filed as G7 → hub **#297** (observe-arc needs a
billed authenticated child). Recorded as an honest-partial, matching the B-S1 attestation shape
(5 clean PASS/FIRED + observe-arc not-produced). The contract-item-3 bar (≥1 organ FIRED) is met
independently by `enforcement_coverage --fire` (2 organs enforcing-local) + `floor_conformance`
(9/9, incl. commit-time block + real gated merge). Cross-reference only; no new id.

### X-ref (not new) — #302/F1 branch-guard parity applies to corp
corp has the *behavioral* no-direct-to-main rule (floor L21) but **no enforcing guard**: its
pre-push stage is armed-but-empty (no `block_ff_push`), and corp has a private GitHub remote —
so a push-time guard is meaningful here. Already tracked as hub **#302** (PARITY-DEPLOY); listed
so the corp onboarding record names it. No new id.

---

## D4 surface (contract item 7 — surfaced as a decision, NOT resolved this session)

**What D4 is.** corp audit Finding **D4 (HIGH)** — *"ARCHITECTURE.md is 7+ weeks stale / not in
canonical generator-managed form."* Origin `corp-monorepo/docs/audits/2026-05-20-corp-monorepo-deep.md`
Finding D4; re-confirmed unremediated in the hub audit `2026-05-23-corp-monorepo-deep-audit.md`
(ADR-30/31 CHANGELOG+HANDOFF retirement, the ARCHITECTURE.md root move ADR-38 A4, AGENTS.md
retirement ADR-54, CLAUDE.md v2.1 rewrite ADR-53 — none reflected; "Last updated: 2026-03-30").
ARCHITECTURE.md is mandated session-start reading (corp CLAUDE.md §1/§3), so a stale canonical
doc misleads every fresh agent.

**Operator ruling this session: SURFACE-ONLY.** No `ARCHITECTURE.md` content edit was made during
onboarding (minimal-diff; "do not resolve D4 unilaterally"). Two of D4's dimensions were touched
only to the extent of *surfacing*:
- **Codemap dimension** — coupled to **G11 / #262**: generator-managed codemap is BLOCKED on corp's
  single-package layout, so the codemap cannot be brought to canonical generator-managed form until
  the hub-side #262 fix lands. Stays hand-authored (correct per corp's L120 marker).
- **Staleness dimension** — the ADR-30/31/38/53/54 references remain stale; unchanged here.

**Decision surfaced to the operator (for a future dedicated session, not this one):** do the D4
`ARCHITECTURE.md` refresh (staleness header + stale-ADR reconciliation) as its own scoped pass —
NOT folded into onboarding. The codemap sub-dimension should wait on the #262 generator fix (G11)
so the refresh and the generator-adoption land coherently rather than twice.
- **Route:** corp-local — D4 is a corp audit finding, tracked in corp's audit trail. Recommend a
  `fix/`-scoped ARCHITECTURE.md refresh session; gate the codemap portion on hub #262.
