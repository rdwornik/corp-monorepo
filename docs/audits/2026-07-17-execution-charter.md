# Execution charter — corp-monorepo product execution (2026-07-17)

> **What this is.** The single first-read for a fresh **executor-architect** chat resuming
> product execution in corp-monorepo. It **consolidates by pointing** — every load-bearing
> fact lives in a canonical doc already in the repo; this charter orders those docs, records
> the standing rulings verbatim, and states the execution order. It restates **nothing** an
> audit already carries; where a section would restate, it points instead.
> Doc-lane only — no `src/`/`tests/` change.

---

## 1. System in one screen (current, witnessed 2026-07-17)

- **HEAD** `604fd80` (`main`, clean tree) — *Merge `docs/a3-codification-backlog-rebuild`*.
- **Tests** `2624 passed, 6 skipped, 0 failed` (`py -m pytest -q`, 146.86s, witnessed
  2026-07-17 at `604fd80`; 2629 collected). *Note:* an earlier note cited "2648/5" — the
  witnessed figure at this HEAD is 2624/6-skip; use the witnessed number.
- **BACKLOG** `7 themes / 9 stories / 51 tasks / 0 warnings` (`py scripts/validate_backlog.py` → OK).
- **What landed 2026-07-16/17.** The architecture recon closed and the plan was written into
  the repo. 2026-07-16: the architecture ground-truth audit (§6 D-1..D-8 + Addendum A) and the
  Codex edge-diff cross-derivation. 2026-07-17: the Arc-B deletion manifest was built PROPOSED
  (`78d5d1b`) then **SIGNED** and merged (`2690009`; sign-off merge `1a014f0`); ADR-33..36 were
  ratified (Accepted); the intake gained addenda §9 (FR-10..FR-19) and the FR-13 event-schema
  reconciliation + the T6 cross-repo-integration brief landed; then the **A3 target-architecture
  ruling was codified in-repo** for the first time (`5f210eb`) and **`BACKLOG.md` was rebuilt on
  the A3 product axis** (`cbee82f`; merge `604fd80`). The repo now encodes the plan; what a fresh
  chat lacks is this entry point.

## 2. Reading map (ordered — one line of "why" each)

Read in this order; each is authoritative for its slice, none is re-narrated here.

1. `docs/audits/2026-07-17-a3-target-architecture-ruling.md` — **the target architecture**
   (R1–R10); every execution decision defers to it.
2. `BACKLOG.md` — the **product-axis execution surface** for R1–R10 (7 themes E1–E7, 9 stories,
   51 tasks); the spec, items are tickets.
3. `docs/audits/2026-07-06-technical-architect-intake.md` (+ **§9** addenda FR-10..FR-19) —
   the functional requirements + decision register DR-4 the ruling rests on.
4. `docs/decisions/ADR-33..36` — RFP-KB federation (33), vault essence layer (34), corp-ops
   backup topology (35), storage/estate roles (36); all Accepted 2026-07-17.
5. `docs/audits/2026-07-17-deletion-manifest-arc-b.md` — **SIGNED**; the deletion authority of
   record (R4 defers to it); its §"Execution contract" governs the Arc-B batches.
6. `docs/audits/2026-07-17-brief-cross-repo-integration-t6.md` — the T6 Content-Manifest seam
   between corp and its consumers.
7. `docs/audits/2026-07-17-fr13-event-schema-reconciliation.md` — the FR-13 event-schema
   reconciliation feeding the seam-contract work (E3).
8. `docs/audits/2026-07-16-architecture-ground-truth.md` (+ **Addendum A** — the A.3
   read-binding table) — the witnessed dependency/contract map underwriting R1/R3/R4/R6.
9. `docs/audits/2026-07-06-code-quality-audit.md` — RC-7/8/14/15; the hygiene backlog behind
   Arc-C and the DEFER field.

## 3. Protocol ruling (senior-architect — recorded verbatim, do not re-derive)

The integration protocols are **already ratified**; the executor does not re-open them:

- **R2 — CKE is a subprocess with an explicit contract.** Exactly **one** corp-side invoker
  (merge `project/cke_invoker` + `overnight/cke_client`). Summary-renderer isolation is a
  follow-up, not a blocker.
- **R6 — accessor principle.** Production-path bindings (MyWork, vault, the databases) resolve
  **through the config layer**, enforced **incrementally at refactor time**, not big-bang
  (~49 read touchpoints, Codex Addendum A.3).
- **T6 Content Manifest** — the corp↔consumer seam is a versioned content manifest
  (`docs/audits/2026-07-17-brief-cross-repo-integration-t6.md`), not a shared import.
- **N2-class seam tests** — seam contracts are guarded by seam tests (the N2 codex-seam-contract
  audits), not by coupling the two sides.

**NOT-list (violations at solo-operator scale — 3 RFPs/month):** **no microservices, no service
mesh, no message bus.** The subprocess boundary (R2) + explicit contract (T6) + accessor
principle (R6) + seam tests (N2) are the whole integration architecture. Adding an
infrastructure tier is a NOT-list violation — stop and surface it, do not build it.

## 4. Execution order

Theme sequence (R10): **E1 → E2 → E3 → E5 → E6 → E4 → E7** — the knowledge loop (E5/E6) is
deliberately elevated ahead of the RFP rewrite (E4); theme *ids* are stable identities, the
*sequence* carries priority (BACKLOG "sequence vs identity" note).

**Hard `depends-on` edges (only three):**
- `#29` (config → PipelineConfig capstone) **after** `#19–#23` (the Arc-B batches — cut before unify).
- `#36` (scout) **after** `#35` (the registry-v4 gate).
- `#53` (Arc-E doc rewrite) **after** `#29` — the R9 "docs rewritten once, after Arc B+C" gate.

**First three moves:**
1. **Arc-B execution** — run the five signed batches. The prompt is
   `%USERPROFILE%\Downloads\2026-07-17_PROMPT_arc-b-execution.md` (BACKLOG #19–#23; one
   revertable commit per batch; Batch 2 repoint + `corp index rebuild`; Batch 3 witness the
   dead-lane boundary first; Batch 4 fires only on the recorded zero-use word).
2. **Arc-C wave 1** — the canonical-home unifications that don't depend on the config capstone:
   LLM-JSON → `schema.utils` (#27), frontmatter → `vault_io` (#26), the models+pricing
   registry BUILT from the live per-provider dicts (#25).
3. **E3 / E5** in disjoint worktrees where parallelizable (seam contracts vs knowledge loop).

## 5. Operator queue (open — verbatim, needs the operator, not the executor)

These are **not** executor work; they gate specific tasks and only the operator can close them:

- **Graph API consent** — unblocks the scout (#36) and the X1 build.
- **Vault git remote** — still absent; the vault has no backup remote.
- **4 credential rotations** — pending.
- **Final zone names** — the backup-topology zone names are not yet fixed.
- **ADR-35 amendment decision** — backup leg-2 → personal OneDrive (operator's second account)
  replacing the auth-blocked Google-Drive leg; routed through the sanctioned superseding/amending
  ADR mechanism, not a free edit (BACKLOG #18).
- **T6-D4 SharePoint confidentiality push** — the confidentiality classification for the T6
  content manifest.

## 6. Engagement contract (executor chat)

- Work `BACKLOG.md` **top-down**, honoring the three `depends-on` edges (§4).
- **Submit each arc's plan to the SENIOR architect** (Layer-1 browser, via the operator) for
  review **before** execution — the plan-review output contract applies (the browser emits
  exactly one of: the exact CC option to select / paste-ready feedback / `approve`).
- **Deletions ONLY per the signed manifest** — no deletion outside a signed row; the DEFER
  field and exclusions are off-limits.
- **Standing rules:** after a gates-green `--no-ff` merge to `main`, **push without asking**;
  evidence artifacts → `docs/audits/` (Downloads is transport/ephemeral only); **no new folders**
  without operator approval; every change branch → `--no-ff` merge, never direct to `main`.

---

## Done-when (this charter)

A fresh executor-architect reader can start the first Arc-B batch without asking anything that
is not already in the §5 operator queue.

---
*Codified 2026-07-17 · primary checkout · base HEAD `604fd80` · Layer-1 first-read record (no
code change). Consolidates by pointer — the canonical docs in §2 are authoritative.*
