# Demo-Prep Recon Audit -- Capability x Intent x Use (read-only)

> **What this is.** A read-only reconnaissance of the `demo-prep` repo (the operator's
> actual deck pipeline), the last black box before the cross-repo integration brief (T6).
> Mirrors the Wave-2 deep-audit structure: for each capability, separate what the code CAN
> do (capability) from what the docs SAY it is for (intent) from what actually RAN (use), and
> close with a backlog-seed table. Every claim carries a `file:line` or a `git log` citation;
> gaps are declared NOT FOUND, never paraphrased around.
>
> **Contract.** Zero writes to any repo. Subject: `C:\Users\1028120\Documents\Dev\demo-prep`
> (audited at HEAD `79e4acc`, 2026-07-07). This report is the sole output; it lives in
> Downloads, not in any repo. Governance frame: corp-monorepo
> `docs/audits/2026-07-06-technical-architect-intake.md` FR-7 (deck lane), DR-12 (storage
> topology), DR-14 (process views). The merged deck-production brief is operator-held and was
> **NOT AVAILABLE** in context; findings rest on repo evidence alone.
>
> **Method.** Attribute + content inventory via Glob/Grep/Read + `git log`. Runtime-input
> tracing by grep for file-read call sites across `generators/` and `pipeline/`. OneDrive
> `Blue Yonder Platform - Documents` was **never traversed** -- its role is read from config
> and doc citations only (per the standing exclusion). Verdicts LIVE / DORMANT / DEAD are
> defined in Sec.3 (the repo is 2 days old, so "dormant" means built-but-not-wired or
> immutable-by-design, not aged-out).

---

## 0. Repo map (the use-recency baseline)

- **Age:** founded `2026-07-06 23:30` (`FIRST chore: bootstrap demo-prep skeleton`); HEAD
  `2026-07-07 19:50` (`Merge feat/handson-library -- Pass D`). **The entire repo is ~44
  hours old.** No capability is "dormant by age"; dormancy here is structural, not temporal.
- **Passes visible in git history:** Pass B (brand revamp: `by_brand_kit` + `verify_deck`
  v2), Pass C (canonical section library + `DECK_PRODUCTION_PROCESS.md`), Pass D (SharePoint
  library analysis + curated ingest). Bootstrap = Warsaw copy-only migration.
- **Structure (source, excl `.venv`/`.git`/`.claude/worktrees`/caches):**
  - `generators/` -- 21 `.py` (8 root `generate_*` + `by_brand_kit` + `_extract_phase1` +
    `extract_brand_theme` + per-customer `unilever/`, `wurth/`, `cortina/`)
  - `knowledge/` -- `sections/` (8 canonical + 13 `_inventory/`), `platform/` (5 QA
    syntheses), `training/` (syntheses + 15 `_extracted/` exercises), `sharepoint-blueyonder-platform/` (Pass D cards)
  - `pipeline/` -- `DECK_PRODUCTION_PROCESS.md` + 5 outlines + 1 runbook + `Files for
    Participants/` + `tools/extract_deck_text.py`
  - `brand/` -- `BRAND_SPEC_v2.md`, `_BY_editorial_spec.md`, `LAYOUT_CATALOG.md`,
    `corporate/`
  - `templates/` -- masters (disk-only pptx) + `_PPTX_TEMPLATE_KIT/`
  - `output/` -- 2 run-folders (ADR-002)
- **Tests:** 3 files (`test_brand_capability.py`, `test_extract_deck_text.py`,
  `test_repo_invariants.py`). Note the CLAUDE.md claim "Testing: none" (`CLAUDE.md:39`) is
  now stale -- Pass B/C added a real pytest harness.
- **Per-area last-touch (`git log -1`):** `generators` 07-07 14:46 (Pass B) ; `pipeline`
  07-07 14:02 (Pass C) ; `knowledge/sections` 07-07 14:15 (Pass C) ; `brand` 07-07 14:32
  (Pass B) ; `knowledge/sharepoint-blueyonder-platform` 07-07 18:53 (Pass D) ; `templates`
  07-06 23:32 (bootstrap, untouched since).

---

## 1. Capability pass -- what the pipeline CAN do

Evidence to `file:line`. "State" = build/pass status where a doc or code marker asserts it.

| # | Capability | Evidence (file:line) | State |
|---|---|---|---|
| C1 | **Brand kit + machine-verified brand gate.** `by_brand_kit.py` parses the palette from `BRAND_SPEC_v2.md` fenced blocks (`load_palette`, `by_brand_kit.py:102-115`) and runs `verify_deck` v2 -- a no-render structural assert (slide count, Arial title, no standalone `BY`, `00B7F1` present / `00B6F1` absent, product-term integrity, citation completeness) (`by_brand_kit.py:144-154`; asserts enumerated in `pipeline/DECK_PRODUCTION_PROCESS.md:100-108`). | Pass B, tested |
| C2 | **Section library (8 canonical sections).** `knowledge/sections/{AGENDA,PLATFORM,ARCHITECTURE,INTEGRATION,DATA_MANAGEMENT,SEMANTIC_NETWORK,SAAS,SECURITY}.md` -- each: narrative arc + grounded claims cited to `deck+slide` + overlap resolution + personalization slots (schema visible `AGENDA.md:15-85`). Backed by 13 per-deck `_inventory/` claim trails. AI-ML + REVERSIBILITY deferred (`BACKLOG.md:31` [#10]). | Pass C, 8 of 10 |
| C3 | **Deck-production algorithm (doc).** `pipeline/DECK_PRODUCTION_PROCESS.md` -- 7 stages discovery->personalize->select->divider->generate->verify->render, with a discovery questionnaire (`:26-51`) and the LIFT/ADAPT/NET-NEW slide taxonomy (`:88-92`). | Pass C, doc-only |
| C4 | **Native generators (in-repo paths).** `generate_platform_architecture_recap.py` (closure smoke test; every input in-repo, `:1-53`) + `generate_brand_capability_sample.py`. Both call `verify_deck`; recap emits a 12-slide deck + `--sample`/`--verify` modes (`:20-24`). | LIVE (ran) |
| C5 | **Migrated generators (pattern references).** 6 root `generate_*` (`recap_hour_1`, `recap_special`, `scpo_platform`, `supplement`, `tms_pitch`, `v6`) + `unilever/`, `wurth/`. Immutable copies with stale Warsaw-relative paths; `generate_v6.py` is "structural pattern only" (`CLAUDE.md:57`). Not runnable as-is until [#1] (`BACKLOG.md:17`). | Capability-only |
| C6 | **Cortina RFP-response pipeline.** `cortina/_rfp_retrieve.py` scores every canonical KB entry by query-term overlap, splits platform vs product_specific scope, emits `_rfp_mapping.json` (`:1-91`); feeds `_build_response(_v2).py` -> `_render(2).py` -> `_verify{,2,3}.py`. **Reads `RFP_Database_WMS_CANONICAL.json`** (`_rfp_retrieve.py:11`). | Capability-only |
| C7 | **SharePoint "Blue Yonder Platform" library ingest.** `knowledge/sharepoint-blueyonder-platform/` -- curated, confidential, disk-only binaries + tracked `.md` cards; 4 net-new delta guides, 5 demo videos + 16 recording links registered (`INDEX.md`, `README.md:29-40`). A1 invariant `test_confidential_roots_md_only` enforces md-only tracking (`README.md:15`). | Pass D, LIVE |
| C8 | **Deck-text extraction tooling.** `pipeline/tools/extract_deck_text.py` -- python-pptx per-slide inventory (title/body/table/notes/picture/hidden-flag), improves on the immutable `_extract_phase1.py` which misses table + grouped-shape text (`extract_deck_text.py:1-15`). Built to construct the Pass-C section library. | Pass C, LIVE |
| C9 | **Templates axis.** `templates/_BY_template_clean.pptx` (masters) opened read-only by every generator (`Presentation(str(TEMPLATE))`, e.g. `generate_platform_architecture_recap.py:716`). | LIVE (dependency) |

---

## 2. Intent pass -- what the docs SAY it is for

- **Mission.** "single home for Blue Yonder corporate presentation creation ... precursor to a
  corp-monorepo presentation module" (`CLAUDE.md:28`; `VISION.md:11`). **Succession path is
  explicit and matches FR-7's framing:** demo-prep content migrates into a corp-monorepo
  presentation module, then this repo archives (`VISION.md:37`; `ARCHITECTURE.md:37`).
- **Five axes.** brand kit . templates . knowledge base . deck-production process . generator
  patterns, + reference examples (`ARCHITECTURE.md:20-29`).
- **Grounding doctrine.** Every technical/customer claim cites the BRD or a `knowledge/` file;
  unciteable -> `[NEEDS INPUT]`, never invented (`CLAUDE.md:52`; `VISION.md:30`). This is the
  same "claim->cite, else abstain" contract FR-1 ratifies (intake `:38`).
- **Boundary.** Customer *deliverables* + pre-sales *domain intel* -> Obsidian vault / MyWork
  (Council #23); demo-prep holds the **capability** + reference examples
  (`ARCHITECTURE.md:35`). This is the DR-12 split (Dev = engine; vault = essence) applied to
  the deck lane.
- **What FR-7 says demo-prep proves.** "The Warsaw workspace proves the behavior manually (5
  customers, gated, cited); the target shares the grounded-content-manifest seam with FR-1
  (one compose mechanism, three output channels: Excel/Word/PPT)" (intake `:56`). demo-prep
  IS the migrated form of that Warsaw workspace -- so this repo is the evidence that the
  manual behavior exists. The 5 customers surface here as `unilever/`, `wurth/`, `cortina/`,
  and the SCPO/TMS pitch generators.

---

## 3. Use pass -- what actually RAN (LIVE / DORMANT / DEAD)

Verdict basis: **LIVE** = executed and produced a tracked artifact, or is read at runtime by
something that did. **DORMANT** = built and intact but not wired into an executed path
(includes immutable-by-design pattern references). **DEAD** = superseded / broken / no path
to execution.

| Cap | Verdict | Evidence of (non-)use |
|---|---|---|
| C1 Brand kit + `verify_deck` | **LIVE** | `by_brand_kit` imported + `verify_deck` called by both native generators; `BRAND_SPEC_v2.md` **read at runtime** (`by_brand_kit.py:105`). Tested (`tests/test_brand_capability.py`). |
| C2 Section library | **DORMANT (as pipeline input)** / LIVE (as doc) | The 8 files exist and are the richest asset in the repo -- but **no `.py` in `generators/` or `pipeline/` reads `knowledge/sections/` or any `knowledge/*.md` at runtime** (grep returned NONE, see Sec.5a). It is a human/LLM reference, not a machine input. |
| C3 Deck-production algorithm | **DORMANT (doc-only)** | No code executes the 7 stages; it is a written procedure a human/LLM follows. `AGENDA.md:86` even flags the bridge dependency as newly-landed. |
| C4 Native generators | **LIVE** | `output/2026-07-06_platform_architecture_recap/` holds a built 12-slide `.pptx` + `_SAMPLE.pptx` + 12 `_preview/*.png` + pdf; `output/2026-07-07_brand_capability_sample/` likewise. Both ran. |
| C5 Migrated generators | **DORMANT (by design)** | Immutable Warsaw copies; "stale Warsaw-relative paths until [#1]" (`CLAUDE.md:56`, `ARCHITECTURE.md:26`). No in-repo run possible; [#1] open (`BACKLOG.md:17`). Not dead -- they are the reuse patterns. |
| C6 Cortina RFP pipeline | **DORMANT** | Migrated; `_rfp_retrieve.py:11` + its write target `:89` are **absolute Warsaw/RFP-library paths** -- runs only against `MyWork\...\RFP_Library\...CANONICAL.json`, which is outside the repo. No in-repo output. The one grounded-*retrieval* path in the repo. |
| C7 SharePoint ingest | **LIVE** | Committed 07-07 18:53 (Pass D Phase 2); tracked cards present; A1 invariant guards md-only. Binaries disk-only + confidential -> **pending Rob push decision** (`README.md:15`). |
| C8 Extraction tooling | `extract_deck_text` **LIVE** (built + used for Pass C section extraction); `_extract_phase1` **DORMANT** (immutable, Warsaw glob `_extract_phase1.py:20`). |
| C9 Templates | **LIVE** | Read-only dependency of every generator run. |

**Net.** Two things actually execute end-to-end today: the **native generators** (C4) and the
**brand gate** (C1). Everything that would make generation *grounded* -- the section library
(C2), the process algorithm (C3), the RFP retriever (C6) -- is **built but unwired**. That gap
IS the T6 opportunity.

---

## 4. FIRST-CLASS FINDING -- the "dimensions" question (for T1 / T2)

**Operator claim:** dimensions were created here from the `Blue Yonder Platform - Documents`
source. **Verdict: PARTIALLY CONFIRMED, with two decoys that a naive `grep dimension` would
mis-surface.** Three distinct "dimension" artifacts exist; only one is derived from that
SharePoint library, and it is a *proposal*, not implemented.

| Candidate | What it is | Derived from `Blue Yonder Platform - Documents`? | Evidence | Status |
|---|---|---|---|---|
| **(A) Pass-D metadata schema** | ~11 classification **axes** for cataloguing the SharePoint library: `asset_type`, `source_site`, `source_path`, `cohort/date`, `product_area -> section`, `audience`, `depth`, `format`, `demo_usability`, `dedup_status`, `hydration`, `verdict`. Header: "Axes derived from what the library actually contains." | **YES -- this is the match.** | `docs/audits/2026-07-07-sharepoint-blueyonder-platform-analysis.md:100-120` | **DRAFT / PROPOSED for Gate C. NOT implemented per-asset.** Open question `:120`: tag only COPY + VIDEO assets. |
| (B) 8-section taxonomy | `PLATFORM . ARCHITECTURE . INTEGRATION . DATA_MANAGEMENT . SEMANTIC_NETWORK . SAAS . SECURITY . AI-ML` -- the deck-section classification. | **NO.** Synthesized in Pass C from the **reference decks** (S2-S7), before Pass D. | `knowledge/sections/AGENDA.md:3` ("Synthesized ... from the per-deck inventories"); sources table `:6-13` cites S4/S5/S6/S7/S2/S3 only. | LIVE as the library's spine. Pass D *maps against* it (`analysis.md:47`) but did not create it. |
| (C) SNA drill-down "Dimensions" | Domain content: Dimensions / Nodes / Measures / Data Leaf / CAD physical model. | **NO.** This is Semantic-Network *subject matter*, grounded in the S7 reference deck. | `knowledge/sections/SEMANTIC_NETWORK.md:38-43` (each cited `S7 s26-s30`). | LIVE as section content; a `grep dimension` decoy. |

**So:** the only dimension/axis *schema* provably built from `Blue Yonder Platform - Documents`
is **(A), the Pass-D per-asset metadata schema** -- and it sits as a Gate-C draft, not a wired
taxonomy. For T1/T2 this is the seed of a demo-asset catalog schema; it is **not** the
knowledge-organization taxonomy (that is (B), deck-derived) and **not** a planning-dimension
model (that is (C), SNA domain content). If the operator recalls "dimensions from the platform
docs," (A) is what was authored; its implementation is still open.

---

## 5. Integration seams -- the T6 questions, answered with evidence

### 5a. What does deck generation consume today -- manual synthesis or a grounded store?

**Manual synthesis, with two narrow exceptions.** Traced every runtime file-read call site in
`generators/` + `pipeline/`:

- **Every generator reads only two things at runtime:** the pptx **template** (`Presentation(str(TEMPLATE))`, e.g. `generate_platform_architecture_recap.py:716`, and the same call in all 8 root generators) and, via `by_brand_kit`, the **brand palette** (`load_palette` -> `BRAND_SPEC_v2.md`, `by_brand_kit.py:105`).
- **Slide content is hardcoded Python string literals**, authored by a human/LLM. `knowledge/` is a **citation target, not an input**: `KB = REPO / "knowledge"` is used only to *name* sources in speaker notes and to phrase `[NEEDS INPUT]` gaps (`generate_platform_architecture_recap.py:50, 432-445, 685`).
- **Proof of the negative:** `grep -rn "sections/|knowledge/.*\.md" generators/ pipeline/ --include=*.py` -> **NONE**. The section library never enters a generator.
- **The two exceptions** -- both grounded *retrieval*, neither in the deck path:
  1. **Brand:** the palette IS a grounded store, read not remembered (`by_brand_kit.py:102-115`) -- the one seam already done right.
  2. **RFP:** `cortina/_rfp_retrieve.py` genuinely retrieves from `RFP_Database_WMS_CANONICAL.json` (`:11-12`, scoring `:44-56`). This is the FR-1 style/truth store, reached from *inside demo-prep*.

**Conclusion for T6:** deck generation is where RFP answering was *before* FR-1 -- content
composed by hand, grounding enforced by discipline (`[NEEDS INPUT]`) and a verify gate, not by
retrieval. The Content Manifest is the missing input.

### 5b. Section library vs RFP style store -- one precedent store, two views?

- **Section library:** `knowledge/sections/*.md`, **8 files**, schema = narrative arc +
  grounded claims (cited `deck+slide`) + overlap resolution + **personalization slots** +
  `[NEEDS INPUT]` (`AGENDA.md:15-85`; template named in `BACKLOG.md:31`). Product-agnostic,
  reusable substrate; claims cite disk-only reference decks (ADR-001).
- **RFP style store (FR-1):** product-agnostic *precedent as form* + product-scoped *truth*,
  dual-retrieval, `source_hash`/`valid_to`/category-volatility reuse gate (intake `:38`).
  Reached in-repo by `cortina/_rfp_retrieve.py`.
- **Structural parallel (strong):** both are **grounded, cited, reusable claim stores with a
  reuse-vs-derive tension and personalization/composition on top.** A section "claim cited to
  S7 s28" is isomorphic to an RFP answer cited to a `kb_id`. Both carry a "form vs truth"
  split -- the section library's *narrative arc* (form) vs *grounded claims* (truth) mirrors
  FR-1's *precedent-as-form* vs *product-scoped-truth*.
- **Honest divergence:** granularity differs (a section = a multi-claim narrative block; an RFP
  entry = one Q/A pair), and the section library is doc-native `.md` while the RFP store is
  `json` with `rich_metadata`/`scope`/`subcategory` (`_rfp_retrieve.py:39-56`). "Two views of
  one store" is **plausible and worth an ADR**, but is a *design claim, not an existing fact* --
  today they are two stores with a parallel shape, unified only by the human who reads both.

### 5c. Where would a Content Manifest plug in -- the exact seams

The manifest is the object that replaces hardcoded slide content with retrieved, cited claims.
Concrete insertion points, by evidence:

- **Producer seam:** `pipeline/DECK_PRODUCTION_PROCESS.md` stage 2 (personalization mapping,
  `:55-61`) + stage 3 (section selection via `AGENDA.md` matrix, `:65-75`) already define the
  manifest's *content* -- `discovery answer -> section slot -> the claim/slide it customizes`.
  That mapping, today written by hand into `traceability.md`, IS the Content Manifest in prose.
- **Consumer seam (the code change):** the per-slide content blocks in each generator. In
  `generate_platform_architecture_recap.py` the slide-builder body (the `add_run` / `set_notes`
  literal blocks, e.g. `:432-445, 599, 685`) is exactly where a `manifest[slide_id] -> {claim,
  citation, [NEEDS INPUT]}` lookup would substitute for hardcoded strings. The function
  boundary already exists; only the data source changes.
- **Verify seam (already built):** `by_brand_kit.verify_deck(..., require_citations=True)`
  (`by_brand_kit.py:144`; `generate_platform_architecture_recap.py:697`) already asserts every
  technical slide carries a `knowledge/` citation or `[NEEDS INPUT]`. A manifest-fed deck would
  satisfy this gate *by construction* rather than by author discipline.
- **Shared-compose seam (FR-1 convergence):** FR-1's compose stage ("facts = content, precedent
  = form", intake `:38`) and this deck stage are the "one compose mechanism, three output
  channels" the intake names (`:56`). The manifest is the shared intermediate: same
  `{claim, citation, form-knob}` record, rendered to Excel/Word (FR-1) or pptx (FR-7).

### 5d. What would vault-fed grounding change, concretely?

- **Today's grounding source is disk-only reference decks + in-repo `knowledge/`**, cited by
  hand; unciteable -> `[NEEDS INPUT]` (`CLAUDE.md:52`). The reference decks (S2-S7) are
  disk-only (ADR-001) -- **not queryable, only readable by a human building a section file.**
- **Vault-fed grounding would:** (1) make claims *retrievable* (the section library becomes a
  query result, not a hand-maintained `.md`); (2) let `[NEEDS INPUT]` gaps trigger the same
  coverage-check/abstain loop FR-1 uses (intake `:38`) instead of a static flag; (3) unify the
  citation namespace -- a deck claim and an RFP answer could cite the *same* vault note, which
  is what DR-12 ("vault = essence") and FR-5 ("retrieval serves BOTH FR-1 and FR-7", intake
  `:50`) already anticipate.
- **What it would NOT change (do not over-claim):** the brand gate (C1) and template axis (C9)
  are orthogonal to grounding; the `[VISUAL]`/`[VIDEO]` diagram + demo content (`BACKLOG.md:32`
  [#11]) is not text-retrievable and stays a human/vision task regardless of vault feeding.

---

## 6. Backlog-seed table (T6 inputs)

Sizes are gut-feel, not estimates. "Done when" is a necessary, testable condition per the
operator's rule.

| Seed | What | Done when | Refs |
|---|---|---|---|
| T6-1 | **Define the Content Manifest record** as the shared FR-1/FR-7 compose intermediate (`{claim, citation, form-knob, [NEEDS INPUT]}`). | An ADR names the record schema and both a section-claim and an RFP `kb_id` serialize into it losslessly. | intake `:38,:56`; `_rfp_retrieve.py:70-74`; `AGENDA.md:22` |
| T6-2 | **Wire one native generator to read the manifest** instead of hardcoded strings (pilot: `generate_platform_architecture_recap.py`). | The recap deck rebuilds from a manifest file; `verify_deck(require_citations=True)` stays green; zero literal claim strings remain in the slide bodies. | `generate_platform_architecture_recap.py:432-697`; `by_brand_kit.py:144` |
| T6-3 | **Decide section-library <-> RFP-store unification** (one store, two views vs two stores, one manifest). | An ADR rules on it with the granularity + format divergence (5b) addressed; if unified, a migration path from `knowledge/sections/*.md` to the store is specified. | `knowledge/sections/`; `_rfp_retrieve.py:39-56`; intake FR-1/FR-5 |
| T6-4 | **Promote the Pass-D metadata schema (finding A) or retire it.** | The ~11 axes are either implemented as per-asset front-matter on COPY+VIDEO assets (its own open question) or explicitly marked deferred with a reason. | `2026-07-07-sharepoint-blueyonder-platform-analysis.md:100-120` |
| T6-5 | **Close [#1] (generator path refactor)** so the migrated + Cortina generators become runnable in-repo -- prerequisite for any manifest wiring beyond the two native generators. | Each `generate_*` + the Cortina pipeline resolve every input in-repo; a sample regeneration succeeds. | `BACKLOG.md:17`; `_rfp_retrieve.py:11,89` |
| T6-6 | **Resolve the SharePoint confidentiality push decision** before demo-prep content migrates to corp-monorepo (succession path). | Rob rules on whether `knowledge/sharepoint-blueyonder-platform/` + `brand/corporate/` `.md` may reach a remote; the target module inherits the ruling. | `README.md:15`; `VISION.md:37` |

---

## Verification

- **Five step-5 questions answered:** 5a (manual synthesis, grep-proven NONE), 5b (parallel,
  not-yet-one-store), 5c (producer/consumer/verify/shared-compose seams named to `file:line`),
  5d (vault-grounding deltas + explicit non-changes) -- all with evidence. [DONE]
- **Dimensions finding located:** finding (A) Pass-D metadata schema
  (`analysis.md:100-120`), with the two decoys (B deck-taxonomy, C SNA content) disambiguated.
  [DONE]
- **LIVE/DORMANT/DEAD verdict per capability:** Sec.3, C1-C9. [DONE]
- **NOT AVAILABLE declared:** the merged deck-production brief (operator-held) -- report rests
  on repo evidence alone. **NOT FOUND** where searched and empty: no runtime read of the
  section library (Sec.5a). **No DEAD capabilities** found (repo is 44h old).
- **Zero writes to any repo.** OneDrive `Blue Yonder Platform - Documents` never traversed --
  cited from config/docs only (`SOURCES.md:12`, `analysis.md`).
- **Report path:** `C:\Users\1028120\Downloads\2026-07-07_AUDIT_demo-prep-recon.md`

---
*Recon only -- design (the T6 brief) is out of scope by contract. ASCII-only. Read-only session.*
