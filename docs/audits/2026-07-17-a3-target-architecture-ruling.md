# A3 target-architecture ruling (ratified)

> **Status:** Ratified (Layer-1 operator ruling, en bloc). **Date:** 2026-07-17.
> **Scope:** first in-repo codification of the A3 target-architecture ruling (R1–R10),
> previously ratified off-repo. Resolves the "repo codification pending in the primary
> checkout" debt flagged by the SIGNED Arc-B deletion manifest
> (`docs/audits/2026-07-17-deletion-manifest-arc-b.md`, sign-off merge `1a014f0`).
> Doc-lane only — no `src/`/`tests/` change; this is a decision record, not an execution.
> **Governing evidence (extends, does not re-derive):** architecture ground-truth audit
> (`docs/audits/2026-07-16-architecture-ground-truth.md`) §6 D-1..D-8 + Addendum A;
> Codex edge-diff (`docs/audits/2026-07-16-codex-edge-diff.md`); code-quality audit
> (`docs/audits/2026-07-06-code-quality-audit.md`, RC-7/8/14/15); ADR-33..36
> (all Accepted 2026-07-17); intake DR-4 (`docs/audits/2026-07-06-technical-architect-intake.md`).

---

## 0. Headline — what this is

The **A3 target-architecture ruling** is the Layer-1 operator decision that fixes corp-monorepo's
*target* structure: what the foundation is, where the CKE boundary sits, how `rfp/` is rebuilt,
what dies, and where every stray responsibility gets a canonical home. Its rows are referenced
throughout the Arc-B work (as "A3-R4/R5") but — until this document — **existed nowhere in the
repo**. A whole-repo grep found `A3-R4`/`A3-R5` only in the signed manifest and the JOURNAL, both
explicitly labelling the ruling *"ratified off-repo 2026-07-17; repo codification pending in the
primary checkout."*

This document is that codification. R1–R10 were ratified **en bloc on 2026-07-17** as Layer-1
operator authority; they are recorded here verbatim in substance, with their witnessed evidence
base, and become the in-repo authority the manifest and the ADR pack point back to. Nothing is
re-derived — the ruling stands on the ground-truth audit, the Codex cross-derivation, the
code-quality audit, and the ratified ADR-33..36; this document *records the decision* those
inputs supported.

## 1. The rulings (R1–R10)

**R1 — Build-on foundation.** The foundation layer the target architecture builds on is:
`extraction`, `ops`, `retrieve`, `schema`, `vault_io`, `index_builder`. These are load-bearing
and kept; higher layers compose over them.

**R2 — CKE boundary.** CKE is a **subprocess with an explicit contract**. There is exactly
**ONE corp-side invoker** — merge `project/cke_invoker` + `overnight/cke_client` into a single
invoker. CKE summary-renderer isolation is a **follow-up** (does not block the boundary).

**R3 — `rfp/` is a composition-target rewrite.** `rfp/` is rewritten as a composition target in
phase R1. **Salvage**: the anonymization logic, the Excel/Word mechanics, and the selector
scoring. The **KB-JSON path is dead** (per ADR-33 + ground-truth §6 D-7).

**R4 — Kills follow the SIGNED manifest, not raw DR-4.** Deletions execute per the **SIGNED
Arc-B deletion manifest** (`docs/audits/2026-07-17-deletion-manifest-arc-b.md`, ratified/signed
and merged to `main` at sign-off merge **`1a014f0`**) — *not* per the raw intake DR-4 list. The
manifest is the deletion authority of record; this ruling defers to it. **`resolve_product_key`
is KEEP** — the T1-charter designated product-vocabulary owner (aspirational; charter-designated
even at 0 current runtime callers).

**R5 — Canonical homes.** Every stray responsibility gets one canonical home:
- `config` → the **PipelineConfig** family (migrate the `corp.config` importers).
- vocabulary → `schema`.
- models + pricing → **one registry**, to be **BUILT** from the live per-provider dicts
  (`ANTHROPIC_PRICING`, `GEMINI_PRICING`) — the registry does not exist yet.
- frontmatter → `vault_io`.
- LLM-JSON → `schema.utils`.
- OneDrive guards → `corp.safety` (**done**, landed as N1).
- CKE invoker → **one** (per R2).

**R6 — Accessor principle.** Production-path bindings (MyWork, vault, the databases) resolve
**through the config layer** — enforced **incrementally at refactor time**, not in a big-bang
pass (evidence: Codex Addendum A.3 records ~49 read touchpoints).

**R7 — Vault-writer invariant (TEXT).** The vault-writer invariant is rewritten under witnessed
reality: the `01_Knowledge` writer plus the `actions` whitelist are the sanctioned writers; the
scanner enforces it.

**R8 — Tach.** Un-exempt `src/corp/test_pipeline.py` from the tach layer exemptions.

**R9 — As-is docs rewritten ONCE, after Arc B+C.** The as-is descriptive docs (the
`ARCHITECTURE.md` codemap, the CLAUDE project layer) are rewritten **once**, **after** Arc-B
execution and Arc-C landing — **not before**. Rewriting them against the pre-execution tree would
document a structure about to change.

**R10 — Operator priority ruling (2026-07-17).** After the F0 / E1–E2 substrate is in place, the
**KNOWLEDGE LOOP (E5/E6) takes precedence over the RFP rewrite (E4)** — a conscious, recorded
deviation from intake §8's "R1 (FR-1 build) before R2 (coverage gap-fill)" order. The rebuilt
BACKLOG sequences themes accordingly (E1 → E2 → E3 → E5 → E6 → E4 → E7); theme *ids* keep their
identity, theme *sequence* carries the priority.

## 2. What this supersedes (quote-and-point — manifest left unedited)

Per critical-rule 3 (audits/manifests are immutable; supersede by a new file, never an in-place
edit), the following clause of the **signed** Arc-B manifest is resolved **by this document**;
the manifest itself is not touched.

- **`docs/audits/2026-07-17-deletion-manifest-arc-b.md` lines 9–11** — *"**Governing:** Layer-1
  operator ruling A3-R4/R5 (target-architecture ruling, ratified off-repo 2026-07-17; **repo
  codification pending in the primary checkout**)…"*
  → **Superseded (the "pending" clause only).** The A3 ruling is now codified in-repo by this
  document. A3-R4/R5 — and the full R1–R10 — have their authoritative in-repo home here; the
  manifest's citation resolves to this file. The manifest's KILL/KEEP decisions themselves are
  unchanged and remain the deletion authority (R4 defers to them). No amendment marker is added
  to the manifest — it is signed and immutable, and (per the ruling) none is needed: the pointer
  runs ruling → this doc → signed contract, closing the authority chain.

## 3. Evidence base

The ruling *records a decision*; it does not re-derive the evidence. The witnessed inputs it
rests on:

- **Architecture ground-truth audit** (`docs/audits/2026-07-16-architecture-ground-truth.md`) —
  the witnessed dependency + contract map (12 recon subagents, tach 0.34.0). §6 dead-weight
  ledger D-1..D-8 and headline #7 underwrite R1 (foundation), R3 (D-7 KB-JSON dead), and R4
  (the kill set). **Addendum A** (append-only Codex cross-derivation) carries the A.3
  read-binding table underwriting R6 (~49 read touchpoints).
- **Codex edge-diff** (`docs/audits/2026-07-16-codex-edge-diff.md`) — the independent
  `sol`-Codex derivation of `src/corp/` edges (89 static / 6 CLI / 32 data agreements); the
  data-binding cross-check that made "zero-caller ≠ zero-use" decidable for R4.
- **Code-quality audit** (`docs/audits/2026-07-06-code-quality-audit.md`) — RC-7 (product-vocab
  owner → R4 `resolve_product_key` KEEP), RC-8 (execute the DR-4 kills → R4), RC-14 (dead-code
  sweep → deferred as a future manifest), RC-15 (BatchJobRunner — re-grep flipped it to KEEP).
- **ADR-33..36** (corp `docs/decisions/`, all Accepted 2026-07-17) — ADR-33 RFP-KB federation via
  INDEX_EXTRA_ROOTS (supersedes ADR-22; underwrites R3 KB-JSON-dead + the E4 federation work);
  ADR-34 vault essence-layer operating model (R7, E6); ADR-35 corp-ops placement + dual-leg
  backup topology (E1 backup amendment); ADR-36 storage topology / estate roles (R6 accessor
  boundaries, tied to ADR-27 guards).
- **SIGNED Arc-B deletion manifest** (`docs/audits/2026-07-17-deletion-manifest-arc-b.md`, merge
  `1a014f0`) — the deletion authority R4 defers to.
- **Intake DR-4** (`docs/audits/2026-07-06-technical-architect-intake.md`) — the original kill
  register R4 supersedes (kills follow the signed manifest, not raw DR-4).

## 4. Sources

- `docs/audits/2026-07-16-architecture-ground-truth.md` (§6 D-1..D-8, headline #7, Addendum A.3)
- `docs/audits/2026-07-16-codex-edge-diff.md`
- `docs/audits/2026-07-06-code-quality-audit.md` (§1.4, RC-7/8/14/15)
- `docs/audits/2026-07-17-deletion-manifest-arc-b.md` (SIGNED; sign-off merge `1a014f0`)
- `docs/decisions/ADR-33-rfp-kb-federation-index-extra-roots.md`
- `docs/decisions/ADR-34-vault-essence-layer-operating-model.md`
- `docs/decisions/ADR-35-corp-ops-placement-backup-topology.md`
- `docs/decisions/ADR-36-storage-topology-estate-roles.md`
- `docs/audits/2026-07-06-technical-architect-intake.md` (DR-4, §8 derivation order)

---

*Codified 2026-07-17 · primary checkout · base HEAD `1a014f0` · Layer-1 ruling record (no code
change). The rebuilt `BACKLOG.md` is the product-axis execution surface for R1–R10.*
