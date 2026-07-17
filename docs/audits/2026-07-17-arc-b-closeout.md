# Arc-B closeout — signed-deletion execution (2026-07-17)

> Close-out record for the executor-architect Arc-B arc (signed deletion manifest execution).
> Arc-B is **MERGED + PUSHED** to `main` at merge `bf45d22`. This doc carries the closure-audit
> inputs (D1–D4), the CR-1..CR-6 review candidate dump (R4), and the amendment/queue status.
> The signed manifest (`docs/audits/2026-07-17-deletion-manifest-arc-b.md`) is untouched.

## 0. Outcome — one screen

- **Merge:** `bf45d22` on `main` (`1d8192d..bf45d22` pushed; block-ff-push passed).
- **Net collection:** 2629 → **2600** (every batch predicted==actual). Final suite **2595p / 6s / 0f**
  (pinned pytest 9.0.2 env). terra codex-review on the cumulative diff: **CLEAN**.
- **Post-merge `corp index rebuild`:** ran — 29 projects, **0 facts**, 488 notes → B2 facts residue cleared (D3).

| Batch | Ticket | SHA | Δcollection | Disposition |
|---|---|---|---|---|
| B1 cost_tracker | #19 | b8b958a | −2 → 2627 | KILL (0 src callers) |
| B2 facts repoint | #20 | 5bcf899 | −2 → 2625 | KILL (Option A narrow; `projects.facts_count` KEPT → AMD-1) |
| B3 inbox lane | #21 | 391d606 | 0 | **DROPPED** — premise falsified → AMD-2 |
| B4 task-mgr cascade | #22 | 8ffe8e5 | −25 → 2600 | KILL (recorded zero-use word) |
| B5 frames limbs | #23 | 9b7794a | 0 → 2600 | KILL (0 callers) |
| terra-fix orphaned workflows | (B4 completion) | d846c0d | 0 | fix (Option A, operator-authorized) |

## 1. Closure-audit inputs (D1–D4)

*Inputs supplied against the senior's D1–D4 closure-audit rubric; framing best-effort, evidence verbatim.*

- **D1 — every signed KILL row executed or resolved with disposition.** B1/B2/B4/B5 = signed KILLs
  executed (SHAs above). B3 = signed KILL **DROPPED** with recorded premise-falsification (AMD-2) —
  the row's "dead inbox lane" premise is contradicted by deep-magistrala §Step 1 (its own cited
  evidence): `_run_extraction`/`_run_package_extraction` are the shared CKE handoff for both live
  registered commands `corp ingest` + `corp ingest-inbox`. Exclusions KEPT: `resolve_product_key`,
  `move_to_vault`, `BatchJobRunner`. No DEFER-field row executed.
- **D2 — no deletion outside the signed row's real scope.** B2 narrowed to the dead facts-SEARCH
  pipeline (kept `projects.facts_count`, ~31 consumers → AMD-1). B4 removed only the cascade +
  necessary consequences (test-for-removed-action `test_built_in_actions:37-38`; the manifest-missed
  `cli/__init__:106`); the orphaned `intent_router:237`/`workflows.yaml` were the **only** out-of-row
  items, resolved by: terra-fix `d846c0d` (workflows.yaml — cascade completion, operator-authorized)
  + AMD-3 (intent_router NL-routing — PROPOSED, not executed).
- **D3 — residue cleared / verification run.** `corp index rebuild` RUN post-merge (not queued):
  0 facts, index.db rebuilt on the post-B2 schema (no `facts`/`facts_fts` tables recreated).
- **D4 — suite green + predicted==actual + terra clean.** Every batch: predicted collection Δ ==
  actual (collect-only, pinned env), full suite green after each (final 2595p/6s/0f). terra
  cumulative-diff review: 1 HIGH found + fixed (`d846c0d`) → re-run **CLEAN**.

**Arc-0 baseline pin (reference for all measurements):** HEAD 5a3de94, pytest 9.0.2, plugins
anyio/hypothesis/cov/xdist/tach; collection 2629; zero-remainder (2629 collected + 1 datasketch
collection-phase skip = 2630 outcomes = 2624p+6s). Standing gate R2: measurements in the pinned env.

## 2. Amendments queued (PROPOSED, operator queue, non-gating; signed manifest immutable)

- **AMD-1** — remove `projects.facts_count` (column) + `facts_count` model field. Gate: (a) verbatim
  consumer enumeration = **DONE** (`docs/audits/2026-07-17-amd1-facts-count-consumers.md`, Codex luna,
  31 sites) + (b) operator sign-off = **pending**. Recorded plan Addendum B.
- **AMD-2** — Batch-3 premise correction: `_run_extraction`/`_run_package_extraction` are live shared
  CKE infra; KEEP; fate re-opens only at the CKE-wiring decision (post-simulation). Recorded plan Addendum C.
- **AMD-3** — full add_task/my_tasks feature cleanup: `intent_router.py:237` NL-routing to the retired
  workflows (now degrades gracefully to the handled "unknown workflow" path). A design decision about
  the intent surface, not cascade hygiene. PROPOSED; operator queue.

## 3. CR-1..CR-6 — code-review candidate dump (for the R4 review; OUT of Arc-B)

*Per R4: the N1 review-findings night-batch does NOT enter authoring until the senior reviews this
list in detail and green-lights it (expected at Arc-B closure = now). Sequenced strictly AFTER Arc-B
so improvement never races the deletions on shared files.*

- **CR-1 — ADR-27 PR-3.** Extend the Decision-1 vault-writer AST scanner to full-repo coverage + run
  the `@onedrive_write_exempt` exemption sweep (deferred from night-batch Arc N1; scanner currently
  scoped to `project/cli.py` + the actions/ scanner). refs ADR-27, R7. (= BACKLOG #16.)
- **CR-2 — ADR-27 PR-4.** Confirm/ship the vault-writer narrowing coverage (`vault_io.write_note` sole
  writer for `02_sources/`; actions whitelist). refs ADR-27.
- **CR-3 — CKE summary-renderer isolation.** Isolate `extractor/scripts/run.py`'s summary renderer so a
  non-circular producer→consumer seam test is possible (the N2 fake-cke pins the corp-side parser only;
  CKE-side label drift needs this production refactor across the corp→CKE process boundary). refs R2
  follow-up, T6. (= BACKLOG #33.)
- **CR-4 — ADR-32 README row.** Add the ADR-32 (ruff lenient select) row to the relevant README. refs
  ADR-32. (= BACKLOG #54.)
- **CR-5 — N1 accepted boundaries.** (a) full CFG dominance analysis in the ADR-27 AST scanner
  (currently lexical dominance + top-level-halt detection); (b) directory-TOCTOU on the local
  `--copy-to-vault` CLI. Both documented as accepted design boundaries in the N1 codex rounds.
- **CR-6 — N2 boundary.** CKE-side stdout label drift across the corp→CKE subprocess contract (the
  fake-cke scope documented + accepted in N2; needs the CR-3 renderer isolation to close non-circularly).

**Note:** CR-1/CR-3/CR-4 already have BACKLOG homes (#16, #33, #54); CR-2/CR-5/CR-6 are review-surface
items for the senior's R4 green-light. Distinct from the manifest DEFER field (ChromaDB fallbacks,
rfp-KB D-7 orphan, RC-14 sweep) = a separate FUTURE DELETION manifest, not this review arc.

## 4. Pending (operator)

- AMD-1 operator sign-off (enumeration done); AMD-2 / AMD-3 acknowledgement.
- R4 green-light on the CR-1..CR-6 set before N1 authoring.
- Lane-prompt archival to the hub handoff carrier (routing rule v3): awaits the operator handing the
  two lane prompts + confirming the hub bundle path (ADR-36 — corp holds no `docs/handoffs/` surface;
  the hub is the carrier). The two Codex lane prompts authored this session (luna AMD-1 enumeration,
  terra Arc-B review) are retained in the session scratchpad pending that hand-off.
- Codex **sol** E5-registry-inputs lane (FR-10 + source-value scoring, NO literal PageRank) — queued
  read-only/off-tree, deliverable = an E5-plan input doc; not run this arc.

---
*Closeout 2026-07-17 · primary checkout · Arc-B MERGED+PUSHED at `bf45d22`. Signed manifest immutable
throughout; three amendments (AMD-1/2/3) recorded in the operator queue.*
