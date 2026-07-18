# Ontology North Star — Architecture-First Draft (T2)

> **Consumed by:** `docs/audits/2026-07-06-technical-architect-intake.md` → BACKLOG #44 (FR-17 ontology).

**Repo:** cross-cutting (vault · registry · index · telemetry) · **Audience:** functional intake / technical architect
**Status:** brainstorm-phase blueprint, ARCHITECTURE-FIRST — evidence reconciliation pending (P2 tree → Product axis; P4/Path-A topics → Topic vocabulary)
**Date:** 2026-07-07 · **Session:** functional-architect sitting #4 · **Named north star:** Palantir Foundry Ontology (operator's explicit reference)

---

## 1. Problem

Hundreds of GB of chaotic material; the essence must be caught, connected, and navigable — hand-picked paths first, automation later. The operator named Palantir Ontology as the golden north star. The job of this brief: extract what Foundry gets RIGHT that transfers to a solo operator, refuse the machinery that doesn't, and define the 5–10 object types of Rob's world with a day-1 slice provable on existing data. The foundation brief's over-engineering warning applies with full force.

## 2. What Foundry actually is (research pass, sources §8)

Foundry's Ontology is a **digital twin**: semantic elements (object types, properties, link types) + **kinetic elements** (action types, functions, dynamic security) over integrated data. Object type = schema of a real-world **entity or event**; link type = relationship between object types; **action type = a governed, validated set of edits applied as one transaction, with side effects** — and crucially, **user decisions committed through actions become part of the data asset**: one user's captured insight feeds the next user's decision. Nouns must be paired with verbs — "semantics must be paired with kinetics."

**The transferable insight is NOT the object model — it's the kinetics.** Every PKM system has nouns (notes, tags, links). What makes Foundry operational is that *changes* are first-class, governed, and logged as data. Our estate has been designing only semantics; meanwhile the kinetic half already exists in our briefs unnamed: ratification, prune, reuse, phase transition. Naming them IS the ontology work.

## 3. Converged recommendation — the solo translation

### 3.1 Semantics: 7 object types (the nouns of Rob's world)

| Object type | What it is | Physical home (no new machinery) | Consuming FR (existence test) |
|---|---|---|---|
| **Client** | account/prospect | vault Client-MOC note (frontmatter contract) | FR-15 prep-view |
| **Product** | BY product/module — **axis expected ≡ the Product-Documentation folder tree (hypothesis; P2 verdict pending)** | tag vocabulary + registry `dims` | FR-10, T1 charter |
| **Deal** | a *reified relationship* Client↔Product[] with lifecycle D1–D5 — a thin object whose meaning lives in its links (provocation #1, refined: Foundry models events as objects, so Deal stays an object, but deliberately property-poor) | deal note frontmatter | deal-loop FRs, FR-13 |
| **Claim** | atomic, citable assertion with provenance — the real unit of essence (provocation #2) | S2 note section / extract record with source pointer | FR-14 pipeline, RFP grounding |
| **Document** | source container on terrain — demoted from first-class essence to Claim's provenance anchor | registry-known file (site/drive/path + S0–S3 phase) | FR-10/12 |
| **Location** | golden-URL registry record (three-tier anchor) | registry YAML | FR-10/11 |
| **Precedent** | reusable HOW — an answer or deck section with voice/layout | style store entry (RFP lane / demo-prep section library) | FR-7, T6 manifest |

**Shared-property contract** (Foundry "interface", solo edition): every object carries `id`, `dims` (industry × software), `phase`, `created`, `last_used` in one frontmatter/record schema — polymorphism by convention + validator, not by type system.

### 3.2 Link types with business meaning (the graph that matters)

`Deal→for→Client` · `Deal→concerns→Product[]` · `Claim→cited-from→Document` · `Document→lives-in→Location` · `Precedent→grounded-on→Claim[]` · `Note→about→Topic` · `Synthesis→consolidates→Claim[]`. Links live as wikilinks + frontmatter fields + registry columns — queryable via index; no graph layer.

### 3.3 Kinetics: 4 action types (the verbs — the actual Palantir steal)

| Action | Governed how | Logged as (FR-13 event_type) |
|---|---|---|
| **RATIFY** | propose→operator-approve gate (registry promotion, tag adoption, spine domain, re-pin) | `ratify` |
| **PRUNE** | manifest-first, evidence-cited proposal → operator sign-off → tombstone | `prune` |
| **REUSE** | a Claim/Precedent lands in a deliverable (RFP answer, slide) | `reuse` |
| **TRANSITION** | phase changes: Deal D1–D5, estate S0–S3 — fired by scheduled loops or operator | `transition` |

**Unification (the elegant part):** the telemetry spine's `event_type` enum **IS the kinetic half of the ontology**. FR-13 was already designed to log exactly these; T2 just names them as the ontology's verbs. Decisions become data — the Foundry property we can actually afford — and the learning components (bandit priors, rot scoring, P(stale)) read the kinetic log as their training table.

### 3.4 Where the ontology LIVES — the cheap seat

Frontmatter + registry YAML + SQLite index + JSONL telemetry. That's the whole engine. The vault note is the object instance; the validator is the schema enforcement; the index is the query layer; telemetry is the writeback dataset. **No graph database until a query class demonstrably fails on the index** (measurable trigger, adopt-map discipline).

### 3.5 Day-1 slice (provable on existing data, one thread)

One closed-won H1 client: instantiate Client + its Deal (reified, linked to Products) + 5 Claims extracted from its documents (each `cited-from` a Document `lives-in` a Location) + 1 Precedent `grounded-on` two of those Claims + 1 REUSE event logged. **Done when:** every §3.1/3.2 type is exercised at least once by this thread, the validator passes on all instances, and one query answers "what do we claim about this client's product fit, with sources" from the index alone.

## 4. Open decisions

D1 Claim granularity — per-assertion vs per-note-section (recommend per-assertion with a max-length guard; P4's extraction quality decides) · D2 does `Person` earn object-type status day-1 (recommend NO — CRM territory; revisit when a consuming FR appears) · D3 Product axis adoption — pending P2 verdict (adopt the corporate tree vs curate a mapping layer over it).

## 5. NOT-list (Palantir-scale machinery we refuse)

- No graph database, no Object-Storage-class engine — index + frontmatter carries it.
- No interface/polymorphism system — one shared-property contract + validator.
- No action *framework* — actions are conventions + gates + telemetry events, zero runtime code beyond what FR-10..16 already specify.
- No roles/security layer, no functions runtime, no digital-twin completeness ambition: **an object type exists only while a consuming FR needs it** (consumption test, §3.1 column 4).
- No ontology tooling/UI — Bases views over frontmatter ARE the ontology browser.

## 6. FR-addendum candidates

- **FR-17 (new): Ontology charter** — the object/link/action tables (§3.1–3.3) + shared-property contract as a versioned docs contract with validator enforcement.
- **Amendment to FR-13:** telemetry `event_type` enum = the four kinetic action types; schema gains `object_type`/`object_id` fields so every event is ontology-addressable.
- **Amendment to FR-14:** extraction target upgraded from note-summaries to **Claims with provenance** (pending D1 + P4 quality evidence).

## 7. Success criteria (brief-level)

Day-1 thread done-when (§3.5) holds · every object type passes the consumption test · Product-axis hypothesis resolved against P2 evidence (adopted, mapped, or rejected with reasons) · NOT-list intact after technical-architect review (any machinery creep = this brief failed).

## 8. Sources (research pass, 2026-07)

- Palantir Foundry docs: Ontology overview (semantic/kinetic elements, digital twin), Core concepts (object/property/link/action definitions), Action types (governed transactional edits; decisions become part of the data asset), Types reference (interfaces, value types), Architecture Center "The Ontology system" (nouns+verbs).
- Secondary syntheses: puppygraph.com Palantir Ontology analysis (2026-05); Leading-AI-IO palantir-ontology-strategy (semantics/kinetics split).
- Internal: adopt-map brief (FR-13/14, dims), golden-URL brief (Location/three-tier anchor), Obsidian v2 brief (shared frontmatter contract, Bases-as-browser), handoff §2 (deal loop D1–D5).
