# BRAINSTORM BACKLOG — Unexhausted Topics (Functional Requirements)

> **Consumed by:** `docs/audits/2026-07-06-technical-architect-intake.md` §9 (FR-10–20 map) → BACKLOG E5/E6 (#35–#47, #55).

**Date:** 2026-07-07 · **For:** the next functional-architect chat (Fable) · **Companion:** `2026-07-07_HANDOFF_functional-architect.md`
**How to run:** one topic per sitting; output = an architect brief in the June-brief format (problem → evidence → converged recommendation → open decisions → success criteria), ending with **FR-addendum candidates** and a **done-when** per recommendation. Sequence below is by dependency, not calendar; the operator picks.

---

## T1 · Metadata & tagging — the complete fresh look (operator: "kluczowe")

**Why (operator's intent):** metadata is what makes drill-down AND drill-up possible; tagging is the algorithmic foundation for any future ontology. He will supply SharePoint links to internal documentation and relevant technologies — treat those as first-class inputs.
**What already exists (do not re-derive):** the field-survival chain (deep-vault-metadata audit — LIVE/DEAD/PHANTOM verdict per frontmatter field, CKE→schema→vault→index→retrieval); three disjoint normalization systems with `resolve_product_key` at zero call sites; canonicalization seam decided = index build (DR in register); 30+ CKE frontmatter fields, most discarded at ingest (DR-5 reverses that).
**Brainstorm questions:** What is the MINIMAL load-bearing metadata set per artifact class (note, deck, RFP answer, source file) vs decoration? Tag vocabulary: who owns it, how does it grow without grooming burden (the over-engineering trap is documented)? How do tags map to the two business dimensions (industry × software) + topic? Auto-tagging: deterministic-first (filename/zone/registry), LLM only for the residual? How does tagging serve BOTH retrieval filters and human navigation?
**Expected output:** a metadata charter brief — the canonical field set, the tag taxonomy governance rule, and the enforcement seam(s), each with done-when.

## T2 · Ontology north star (Palantir-class) — REQUIRES ONLINE RESEARCH

**Why:** the noise→essence problem at corporate scale — hundreds of GB of raw material, the essence must be caught, connected, and navigable. The operator can hand-pick paths initially; long-term it must be automated. Palantir Ontology named explicitly as the "golden north star — something to look up to."
**What already exists:** the drill-down target map (industry × software → topic → notes) = a proto-ontology; the MOC spine design (obsidian brief); the coverage matrix; taxonomy canonicalization.
**Research to do in the new chat (web):** Palantir Foundry Ontology core concepts (object types, link types, actions, object-backed provenance) and lighter-weight equivalents (knowledge graphs over markdown, typed wikilinks, schema-first PKM). Extract only what maps to a SOLO operator — the over-engineering warning from the foundation brief applies with full force here.
**Brainstorm questions:** What are the 5–10 object types of Rob's world (Client, Deal, Product, Topic, Document, Answer, Person…)? What link types carry business meaning (Deal→Product, Answer→SourceNote, Deck→Client)? Where does the ontology LIVE — frontmatter + index (cheap) vs a graph layer (expensive)? What is the day-1 slice provable on existing data?
**Expected output:** an ontology-north-star brief: target object/link model, the minimal day-1 implementation seam, and the explicit NOT-list (what Palantir-scale machinery we refuse to build).

## T3 · Obsidian second brain — deepen (operator: "za mało obsydiana")

**Why:** the operating-model brief got AMEND rulings from the deep-vault audit, but the operator is still not satisfied — he wants more creative Fable-grade ideas on the second-brain layer, and the vault is the layer his drill-down map lives in (DR-2 keeps it conditionally).
**What already exists:** the operating-model brief (S0–S3, MOC spine, Obsidian CLI division of labor, kepano skills) + the audit's element-by-element rulings: spine generatable from top-30 dangling-link hubs (78% coverage); MOCs are dataview-only (link-blind) and need static wikilinks; 48h S0 SLA works only with scheduled enforcement; contract reconciliation is prerequisite.
**Brainstorm questions:** What does the ROOT/Big-Picture note actually show a pre-sales engineer before a client meeting (the "prep view")? Synthesis-note production — what triggers it and what's the quality bar? Usage telemetry → rot scoring — what's the cheapest honest signal? How do Bases dashboards replace the graph view for daily navigation? What's the relationship between vault essence and the deck/RFP style stores?
**Expected output:** operating-model v2 brief folding in the audit amendments + the creative layer, with the consolidation plan's done-when unchanged (100% S2 ≤3 hops from ROOT, 0 orphans among S2).

## T4 · URL management — golden-URL registry (new capability)

**Why:** the operator holds a handful of GOLDEN URLs (SharePoint sites, documentation portals) that are the best entry points into corporate knowledge. SharePoint site NAMES are stable but LOCATIONS drift (content gets moved/reorganized) — today those links live in heads and scattered shortcuts.
**What already exists:** scout pilot design (foraging over terrain — a URL registry is its target list); `MyWork_OneDrive` as the human shortcut hub (DR-12); P4 heartbeat pattern; BY_Technical_Coordinates_Reference as a proto-example of a curated locations card.
**Brainstorm questions:** What is a golden-URL record (name, URL, what-it-holds, owner-team, last-verified, liveness)? Where does the registry live so BOTH the human and the scout consume it (a vault note class? `.corp` config? both via one source)? Liveness checking — scheduled ping/redirect detection with heartbeat (P4), never manual? How does a moved location get re-discovered (search-by-name fallback)? Relationship to the scout: registry = scout's crop rotation plan?
**Expected output:** a small, sharp brief — the registry contract + its scheduled verifier, done-when: every golden URL resolvable or flagged within one loop cycle.

## T5 · Open-source & local-model leverage (operator: underused)

**Why:** the operator's view — the system underuses the OSS ecosystem: Google's solvers (OR-Tools), predictive/ML libraries (TensorFlow/scikit-learn/XGBoost class), data-analytics stacks, and LOCAL models. Goal: predictive components, log-driven self-learning, and a cheap/local conversational interface — without API dependence where a local model suffices.
**What already exists (connect, don't duplicate):** the RFP brief's predictive control plane ALREADY specifies exactly this class — TF-IDF/SetFit classifier, gradient-boosted `P(stale)`, DeBERTa-NLI contradiction, LTR rerank — all deferred behind rules-first day-1; the advisory brief's **adopt-before-build heuristic** is ratified methodology; P1 names "cheap or local model" as the front-door target; every learning surface currently has 0 rows (the feedback loop from FR-1 stage 7 is the data prerequisite for ANY learning).
**Brainstorm questions:** Which local model class serves the front-door (intent routing + short Q&A) on the operator's hardware, and what's the honest quality bar vs CC? Which predictive components earn their keep at 3 RFPs/month (the Council-#10 sizing rule governs)? What OSS solvers/analytics have a REAL problem to solve here vs résumé-driven adoption? What telemetry must the system emit NOW so learning is possible LATER (logs as future training data)?
**Expected output:** an adopt-map brief: per capability — the OSS candidate, the trigger condition that justifies adopting it, and the NOT-yet list; plus the telemetry-to-emit-now spec.

## T6 · Cross-repo integration — RFP ⟷ Knowledge Extractor ⟷ demo-prep ⟷ Obsidian

**Why:** the operator senses the pieces don't connect ("mam wrażenie, że mamy z tym problem") — the answering agent, the extractor, the deck factory and the vault must form one system, not four tools.
**Known black box (from the handoff §7):** the **`demo-prep` repo was never audited this session** — the operator's actual deck-generation pipeline (branding ingest, reference decks, section library) lives there; the intake's FR-7 leans only on the Warsaw-workspace evidence. First move of this topic: a read-only recon of demo-prep (same method as Wave 2: capability × intent × use).
**What already exists:** the shared-seam insight — grounded content → Content Manifest → deterministic fill, one compose mechanism with three output channels (Excel/Word/PPT) — from the deck brief + intake FR-7; retrieval feeds BOTH productions (operator's correction, in the process map); the vault as the single truth store (DR-2), style stores per output lane.
**Brainstorm questions:** Is the Content Manifest the ONE integration contract all four repos meet at? What does demo-prep consume today (manual synthesis) and what would vault-fed grounding change? Where do the section library (demo-prep) and the style store (RFP) overlap — one precedent store with two views? What's the smallest end-to-end thread proving integration (one client: extract → vault → one RFP answer + one deck slide, both cited)?
**Expected output:** demo-prep recon report + an integration brief defining the shared contracts, done-when: the one-client thread is specified with testable conditions at every seam.

---

## Standing rules for every topic

Over-engineering is the documented #1 killer — every brief must carry a NOT-list. Every recommendation carries a done-when. Solo-operator sizing (3 RFPs/month) governs all ambition. Evidence pointers into `docs/audits/` replace re-derivation. Outputs are audit-space artifacts; canon (ARCHITECTURE/ADR/VISION) stays untouched until the technical architect's phase (DR-14).
