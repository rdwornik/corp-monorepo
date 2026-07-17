# T6 · Cross-repo integration brief — the four surfaces as one system

> **Format:** June-brief (problem → evidence → converged recommendation → open decisions → success criteria → FR-addendum candidates → NOT-list), each recommendation carrying a done-when.
> **Date:** 2026-07-17. **Type:** architect brief (design). **Sizing law:** solo operator, ~3 RFPs/month — governs all ambition.
> **This is the T6 deliverable** the demo-prep recon (`2026-07-07_AUDIT_demo-prep-recon.md`) was the precursor to (BRAINSTORM-BACKLOG T6, "demo-prep recon report + an integration brief defining the shared contracts").

---

## 1. Problem

The operator senses the pieces don't connect — *"mam wrażenie, że mamy z tym problem"*: the RFP-answering agent (FR-1), the knowledge extractor (FR-4), the deck factory (`demo-prep`, FR-7) and the Obsidian vault (FR-5) behave as **four tools, not one system** (BRAINSTORM-BACKLOG `2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md` T6, lines 44–50).

The integration question is not "how do we build a platform" — it is **"what is the single contract these four surfaces meet at, and can one client's work thread through all of them with a testable condition at every seam?"** T6's expected output is exactly this brief, done-when: *the one-client thread is specified with testable conditions at every seam* (BRAINSTORM line 50).

## 2. Evidence

**The deck lane is where RFP answering was *before* FR-1.** The demo-prep recon proved (§3, §5a, grep-of-the-negative §5.154) that deck generation is **manual synthesis**: slide content is hardcoded Python string literals; `knowledge/sections/*.md` (the 8-file section library, the richest asset in the repo) is **built but unwired** — no generator reads it at runtime. Grounding is enforced by author discipline (`[NEEDS INPUT]`) and a verify gate, not by retrieval. *"The Content Manifest is the missing input."* (recon §5.161)

**Retrieval is already designed to serve both productions.** Intake FR-5 (`:50`): *"retrieval serves BOTH FR-1 and FR-7."* FR-7 (`:56`): the deck target *"shares the grounded-content-manifest seam with FR-1 (one compose mechanism, three output channels: Excel/Word/PPT)."* FR-1 (`:38`): *"facts = content, precedent = form."* DR-12 (`:88`): *"Dev = engine · vault = essence."* The convergence is already in the intake — it just has no contract object.

**The convergence object has a name and a shape.** Demo-prep recon §5c located the exact insertion seams for a **Content Manifest** — `{claim, citation, form-knob, [NEEDS INPUT]}` — to `file:line` (producer / consumer / verify / shared-compose). The recon's backlog seeds T6-1…T6-6 (recon §6) are the raw material this brief converges.

**One of the four seams is now proven; the rest are not.** Since the recon, night-batch **Arc N2** (merge `56e476e`) added `tests/rfp/test_vault_adapter_cli_seam.py` — an **unmocked, end-to-end integration test** that spawns a real `corp retrieve --format json` process and parses its real stdout through the real consumer `corp.rfp.vault_adapter._retrieve_via_cli`, with `subprocess.run` left intentionally unpatched. **The vault→retrieve producer↔consumer seam is NOW integration-tested** — it is no longer the "never integration-tested" gap the code ground-truth doc (`2026-07-16-architecture-ground-truth.md` §2, rows 231–232) had recorded. That test is the **reference pattern** for the seam class this brief cares about: drive the *real* crossing, patch away only environment steering, assert the wire contract. (The same Arc also seeded the CKE stdout contract, `tests/test_overnight/test_cke_client_stdout_contract.py`, partially covering the extractor producer boundary.) The remaining integration seams — **extractor→vault, retrieve→compose, manifest→render** — have no test of this class yet. That gap is what the one-client thread (§3.5) closes.

## 3. Converged recommendation

**The Content Manifest is the single integration contract all four surfaces meet at.** RFP answering (FR-1) and deck production (FR-7) *compose* through it; the extractor (FR-4) and the vault (FR-5) *feed* it. It is a **record contract, not a service** — no new repo, no runtime engine (see NOT-list §7).

### 3.1 Define the Content Manifest record (converges recon T6-1)

The manifest is the shared intermediate that replaces hardcoded content with retrieved, cited claims: **`{claim, citation, form-knob, [NEEDS INPUT]}`**. `claim` = the fact (product-scoped truth); `citation` = a vault-note reference (the unified citation namespace, §3.4); `form-knob` = length/formality/precedent-as-form; `[NEEDS INPUT]` = the honest-gap marker FR-1's coverage-check and demo-prep's verify gate both already understand.

- **Done-when:** an ADR names the record schema and **both** a section-library claim (cited `deck+slide`) **and** an RFP `kb_id` answer serialize into it **losslessly** — proven by a round-trip test (serialize → deserialize → structural equality) on one real instance of each.

### 3.2 One compose mechanism, three output channels (converges FR-1 ⟷ FR-7)

The manifest is rendered, not re-authored, per channel: the same `{claim, citation, form-knob}` record renders to **Excel/Word (FR-1)** or **pptx (FR-7)**. The compose stage is written once; the renderer is per-channel. Demo-prep's `by_brand_kit.verify_deck(..., require_citations=True)` (recon §5c) becomes satisfied **by construction** — a manifest-fed deck carries a citation on every technical slide because the record requires one.

- **Done-when:** one manifest instance renders to at least two channels (one FR-1 channel + pptx) and the existing `verify_deck(require_citations=True)` gate passes on the pptx **without hand-editing** — zero literal claim strings remain in the piloted generator's slide bodies.

### 3.3 Section library ⟷ RFP style store — rule it to an ADR, do not unify now (converges recon T6-3)

The structural parallel is **strong** (recon §5b): both are grounded, cited, reusable claim stores with a reuse-vs-derive tension and personalization/composition on top; a section claim cited to `S7 s28` is isomorphic to an RFP answer cited to a `kb_id`; both carry a form-vs-truth split. **But "two views of one store" is a design claim, not an existing fact** — today they are two stores (doc-native `.md` vs `json` with `rich_metadata`/`scope`), of different granularity (multi-claim narrative block vs one Q/A pair), unified only by the human who reads both. **This brief does not unify them.** It rules the question to a dedicated ADR so the manifest can be defined (§3.1) *without* prejudging store topology — the manifest is the interoperability layer whether the stores merge or not.

- **Done-when:** an ADR rules "one store, two views" vs "two stores, one manifest," explicitly addressing the granularity + format divergence (recon §5b); if it rules unify, it specifies a migration path from `knowledge/sections/*.md` to the store. Until that ADR lands, no store-merge code is written.

### 3.4 Demo-prep succession path — capability absorbs, deliverables archive (converges FR-7 framing + DR-12)

Per the recon (§2) and demo-prep's own `VISION.md:37` / `ARCHITECTURE.md:37`, demo-prep is *"a precursor to a corp-monorepo presentation module."* The DR-12 split ("Dev = engine · vault = essence") applied to the deck lane:

- **corp-monorepo's presentation lane ABSORBS the *capability*:** the brand kit (the one seam already done right — palette read-not-remembered), the section-library *substrate*, the deck-production algorithm (`DECK_PRODUCTION_PROCESS.md`), and the generator patterns.
- **What ARCHIVES:** the `demo-prep` repo itself, after migration. Customer *deliverables* and pre-sales *domain intel* go to the vault / MyWork (already the DR-12 rule), never into the code module.
- **What is GATED, not decided here:** confidential SharePoint binaries + `brand/corporate/` reaching a remote — pending Rob's push decision (recon T6-6). The target module inherits that ruling; it is **not** resolved in this brief.

- **Done-when:** the capability inventory above is confirmed against demo-prep HEAD by the operator, and the T6-6 confidentiality ruling is recorded, **before** any file migrates. Migration is not in this brief's scope — only the contract that governs it.

### 3.5 The one-client end-to-end thread — the headline deliverable

The smallest thread that proves integration (BRAINSTORM line 49): **one client → extract → vault → one cited RFP answer + one cited deck slide, both cited to the *same* vault note.** The "same vault note" is the proof of unification — it is what FR-5 ("retrieval serves BOTH") and DR-12 ("vault = essence") anticipate, and demo-prep §5d names as the payoff (*"a deck claim and an RFP answer could cite the same vault note"*).

Each seam carries a **testable condition of the N2 class** (drive the real crossing, assert the wire contract). Current status:

| Seam | Crossing | Testable condition (done-when) | Status |
|---|---|---|---|
| A · extract → vault | CKE stdout → `vault_io.write_note` EMIT contract (FR-4) | One real extraction of the client's source writes a vault note whose frontmatter + body satisfy the write contract, asserted unmocked | **Partial** — CKE stdout contract seeded by Arc N2 (`test_cke_client_stdout_contract.py`); the write-note leg still needs an N2-class test |
| B · vault → retrieve | `corp retrieve --format json` producer↔consumer | Real subprocess retrieve returns the client's note with `note_id`/`confidence`/`relevance_score`/`content` keys | **DONE** — pinned by `tests/rfp/test_vault_adapter_cli_seam.py` (Arc N2, `56e476e`). **Reference pattern for A/C/D.** |
| C · retrieve → RFP answer | consumer result → FR-1 compose → cited answer | One retrieved note composes into one RFP answer citing that note's id; the answer's citation resolves back to the vault note | **Needed** — no N2-class test yet |
| D · manifest → deck slide | manifest record → generator → pptx slide (recon T6-2) | The piloted generator rebuilds one slide from a manifest entry; `verify_deck(require_citations=True)` passes; the slide's citation resolves to the same vault note as the RFP answer | **Needed** — no N2-class test yet |
| E · shared-compose (losslessness) | §3.1 record ⟷ both channels | Same manifest instance round-trips to an FR-1 render and a pptx render with no claim/citation loss | **Needed** — depends on §3.1 ADR |

- **Done-when (thread-level):** all five seams above hold for **one** real client, and seams A, C, D, E each carry a test of the N2 class (real crossing, unmocked boundary, wire-contract assertion), modeled on seam B's existing test. The thread is "specified with testable conditions at every seam" the moment this table's done-when column is executable — which it now is.

## 4. Open decisions

- **D1 — Section-library ⟷ RFP-store topology.** One store two views, or two stores one manifest? → **ADR (recon T6-3).** Blocks §3.1's store-migration leg only, not the manifest definition.
- **D2 — Manifest citation namespace.** Does `citation` reference a vault-note id directly, or an intermediate `kb_id`/`deck+slide` that resolves to a note? Recommend **vault-note id as the canonical target** (it is what makes A/C/D cite the *same* note), with per-store adapters — but confirm against FR-1's existing `kb_id` scheme before ratifying.
- **D3 — Generator-path prerequisite.** Manifest wiring beyond the two native generators needs `[#1]` (generator path refactor, recon T6-5) closed first. Is the one-client pilot scoped to a native generator (no refactor needed) or a Cortina one (refactor needed)? Recommend **native generator** for the pilot to avoid coupling the thread to the refactor.
- **D4 — SharePoint confidentiality push (recon T6-6).** Gates §3.4 migration; **operator ruling required**, not decided here.
- **D5 — Manifest vs telemetry boundary.** The Content Manifest (this brief) and the FR-13 telemetry spine (`2026-07-17-fr13-event-schema-reconciliation.md`) are **separate contracts** — the manifest is the compose intermediate, the telemetry spine is the observation log. A `content-reuse` observation event *records* that a manifest entry was reused; it does not *carry* the manifest. Keep them distinct (recommended); confirm no one tries to fold one into the other.

## 5. Success criteria (brief-level)

- The one-client thread (§3.5) is specified with a **testable condition at every seam** — met: the §3.5 table's done-when column is executable, seam B already green as the pattern.
- The Content Manifest is defined as **one record contract** both FR-1 and FR-7 compose through (§3.1–3.2), with a losslessness done-when.
- The section↔RFP question is **ruled to an ADR** (§3.3), not unified unilaterally.
- The succession path names **what absorbs vs archives** and defers the confidentiality gate to the operator (§3.4).
- **NOT-list intact after technical-architect review** — any machinery creep beyond a record contract + one pilot generator + four N2-class tests means this brief failed.
- **Solo-sizing (3 RFPs/month) respected** throughout — no ambition that a one-person, 3-RFP/month cadence cannot sustain.

## 6. FR-addendum candidates

- **FR-20 (candidate, new): Content Manifest integration contract** — the `{claim, citation, form-knob, [NEEDS INPUT]}` record (§3.1) as the single compose intermediate FR-1 and FR-7 meet at; the one-compose-mechanism/three-channel renderer (§3.2); the one-client thread (§3.5) as its existence test. Consumes FR-4 (extraction), FR-5 (retrieval/vault), feeds FR-1 and FR-7.
- **Amendment to FR-7 (deck production):** the "grounded-content-manifest seam" it already names (intake `:56`) is **FR-20's record**; deck slides are rendered from the manifest, not authored, with `verify_deck` satisfied by construction.
- **Amendment to FR-1 (RFP answering):** the compose stage ("facts = content, precedent = form", intake `:38`) emits/consumes the FR-20 record so the RFP and deck lanes share one compose mechanism.
- **Cross-ref (no new number):** section-library ⟷ RFP-store unification is deferred to an ADR (§3.3 / recon T6-3), not an FR.

*(Candidates only — for the technical architect to ratify. This brief does not renumber existing FRs; FR-20 is the next free number after the FR-10…FR-19 addenda.)*

## 7. NOT-list (over-engineering is the documented #1 killer)

- **NO new repo, NO runtime engine, NO service.** The Content Manifest is a **record/serialization contract** — a schema + a round-trip test, not a platform. If it grows a daemon, this brief failed.
- **NO section-library ⟷ RFP-store merge before the D1 ADR.** The parallel is strong but unproven; unifying two stores on a design hunch is exactly the machinery creep the recon warned against. Manifest first, store topology later.
- **NO graph database, NO ML, NO retrieval re-architecture.** The manifest rides the *existing* retrieval seam (proven by Arc N2). Reuse-vs-derive stays rules-first (FR-1's `source_hash`/`valid_to`/volatility gate) — no learned ranker for the thread.
- **NO automation into the OneDrive synced tree.** Uploads stay manual (FR-6 / DR-12 rule); the manifest and its renders never write into `OneDrive - Blue Yonder`.
- **NO rebuild of demo-prep's generators beyond one pilot.** Wire **one** native generator (recon T6-2, `generate_platform_architecture_recap.py`) to prove seam D; the remaining generators wait on the `[#1]` refactor and on evidence the pilot worked.
- **NO manifest fields the one-client thread does not need.** The record is `{claim, citation, form-knob, [NEEDS INPUT]}` — resist adding metadata axes (the Pass-D 11-axis schema, recon T6-4) until a consuming FR needs them.
- **NO migration of demo-prep content in this brief.** §3.4 defines the *contract* for succession; the actual file moves wait on the T6-6 confidentiality ruling and are out of scope here.

---

**Sources:** `2026-07-07_AUDIT_demo-prep-recon.md` (§3 use-verdict, §5a–5d seams, §6 T6-1…6 seeds, §2 succession) · `2026-07-06-technical-architect-intake.md` (FR-1 `:38`, FR-5 `:50`, FR-7 `:56`, DR-12 `:88`) · `2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md` (T6 lines 44–50; June-brief-format + NOT-list/sizing rules, line 4/56) · `2026-07-16-architecture-ground-truth.md` §2 (seam rows 231–232, superseded status) · `tests/rfp/test_vault_adapter_cli_seam.py` + `tests/test_overnight/test_cke_client_stdout_contract.py` (Arc N2, merge `56e476e`) · `2026-07-17-fr13-event-schema-reconciliation.md` (D5 boundary).
