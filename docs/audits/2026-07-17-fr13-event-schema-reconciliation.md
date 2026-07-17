# FR-13 event-schema reconciliation (ratified)

> **Status:** Ratified (Layer-1 ruling). **Date:** 2026-07-17.
> **Scope:** resolves the FR-13 `event_type` conflict named by the FA-campaign self-review (`2026-07-08_AUDIT_fa-campaign-self-review.md` §4-1 / §7 — "the only per-FR blocker"). Doc-lane only; supersedes specific lines of two briefs by quote-and-point (the briefs themselves are immutable and left unedited, per critical-rule 3).

---

## 1. The conflict

FR-13 (the telemetry spine) was born in the **algorithmic-adopt-map** brief and later amended by the **ontology-north-star** brief. The two briefs define the **same field** — `event_type` — two incompatible ways:

- **adopt-map (owner):** `event_type` is an **open** activity vocabulary — retrieval queries, scout cycles, extraction scores, liveness transitions, content-reuse — emitted "at minimum," no closed enum.
- **ontology (amendment):** `event_type` is a **closed** four-value enum equal to the kinetic action types (`ratify`, `prune`, `reuse`, `transition`), plus new `object_type`/`object_id` fields.

An open vocabulary and a closed four-value enum cannot both be the definition of one field. This is a content conflict on a single FR, not a numbering collision — the self-review's sole per-FR handover blocker.

## 2. The ruling — a two-level schema

`event_type` is not one flat enum. It is discriminated by a new outer field, **`event_class`**:

```
event_class ∈ { kinetic-action, observation }
event_type  = the enum/vocabulary scoped to that class
```

Both briefs were right about their own half; each mistook its half for the whole. The two-level schema keeps both intact:

- **`event_class = kinetic-action`** — `event_type` is the **closed** four-value enum from the ontology brief's §3.3 kinetics table: `ratify`, `prune`, `reuse`, `transition`. These are the governed, ontology-addressable "verbs"; the enum is closed because the ontology deliberately fixes the action vocabulary (a new action type is an ontology change, not a free string).
- **`event_class = observation`** — `event_type` keeps the adopt-map's **open** vocabulary: `retrieval` (queries + results + which result was used), `scout-cycle` (predicted vs realized yield), `extraction-score` (CKE), `liveness-transition` (registry), `content-reuse` (RFP/deck). Open because observation is ambient instrumentation — new observation types are expected as the learning roadmap grows, and adding one must not require an ontology amendment.

### 2.1 The carrier envelope

The adopt-map brief's envelope remains the carrier, **extended** with the discriminator and the ontology's addressing fields:

```
{
  ts,                      # adopt-map §5 — timestamp
  event_class,             # NEW (this ruling) — kinetic-action | observation
  event_type,             # scoped by event_class per §2
  subject_id,              # adopt-map §5 — the entity the event is about
  object_type, object_id,  # ontology §6 — ontology addressing (see §2.2)
  context{},               # adopt-map §5 — open bag
  outcome{}                # adopt-map §5 — open bag
}
```

### 2.2 Ruling on `object_type` / `object_id` applicability

The ontology brief added `object_type`/`object_id` "so every event is ontology-addressable," but the adopt-map envelope (which carries observation events) never had them. Ruling:

- **`event_class = kinetic-action`: `object_type`/`object_id` are REQUIRED.** A governed action always acts on an ontology object; that is what makes it a kinetic action. This is the "every event is ontology-addressable" intent, correctly scoped to the class where it holds.
- **`event_class = observation`: `object_type`/`object_id` are NULLABLE (optional).** An observation already identifies its target via `subject_id` (a query, a scout cycle, an extraction run need not be an ontology object). Requiring ontology addressing on ambient instrumentation would force every retrieval log to name an object it may not have — over-constraint. When an observation *does* concern an ontology object, the fields may be populated; they are never mandatory for this class.

### 2.3 One disambiguation the two-level schema buys for free

`reuse` appears on **both** sides — a kinetic **REUSE action** (`event_class=kinetic-action`, `event_type=reuse`) and an observation **content-reuse event** (`event_class=observation`, `event_type=content-reuse`). Under a single flat enum these would collide or be conflated. `event_class` disambiguates the shared token cleanly: the governed decision to reuse a ratified object is a different record from the ambient observation that an RFP/deck reused some content. Keep the tokens distinct (`reuse` vs `content-reuse`) and the class makes the intent unambiguous.

## 3. What this supersedes (quote-and-point — briefs left unedited)

Per critical-rule 3 (briefs are immutable), the following lines are superseded/refined **by this document**; the briefs are not touched.

- **`2026-07-07_BRIEF_ontology-north-star.md` line 73** — *"Amendment to FR-13: telemetry `event_type` enum = the four kinetic action types; schema gains `object_type`/`object_id` fields so every event is ontology-addressable."*
  → **Superseded.** The four kinetic types are the `event_type` enum **only within `event_class=kinetic-action`**, not the whole `event_type` field. `object_type`/`object_id` are added to the envelope but scoped per §2.2 (required for kinetic-action, nullable for observation) — not unconditionally on "every event."

- **`2026-07-07_BRIEF_ontology-north-star.md` line 48** — *"the telemetry spine's `event_type` enum IS the kinetic half of the ontology… FR-13 was already designed to log exactly these."*
  → **Refined.** True for the kinetic *class*, not the entire `event_type` field. The kinetic four are one half; the observation vocabulary is the other. The spine logs both.

- **`2026-07-07_BRIEF_algorithmic-adopt-map.md` line 84** — the open observation vocabulary + envelope *"`{ts, event_type, subject_id, context{}, outcome{}}`"* for retrieval / scout / extraction-score / liveness / content-reuse.
  → **Superseded (extended, not replaced).** This vocabulary is retained verbatim as the `event_class=observation` half; the envelope gains `event_class` (discriminator) and the nullable `object_type`/`object_id` fields per §2.1–2.2.

- **`2026-07-07_BRIEF_algorithmic-adopt-map.md` line 89** — *"FR-13 (new): Telemetry spine — §5 schema + emit points."*
  → **This document is the reconciled successor to that FR-13 charter.** FR-13's schema of record is §2 here, not either brief's §5/§6 in isolation.

## 4. Done-when

**One telemetry write path can validate BOTH a kinetic-action event and an observation event against a single schema definition** — i.e. one schema/validator (a `event_class`-discriminated union) accepts a well-formed `ratify` action *and* a well-formed `retrieval` observation, and rejects (a) a kinetic-action missing `object_type`/`object_id`, (b) a kinetic-action whose `event_type` is outside the closed four, and (c) any event missing `event_class`. This subsumes the adopt-map brief's own done-when (line 85: "the event log exists, a schema validator passes on every emit path, and one week of ambient use produces ≥1 event of ≥3 types") — the ≥3 types now span both classes.

## 5. Sources

- `2026-07-07_BRIEF_algorithmic-adopt-map.md` §5 (envelope + open vocabulary, line 84), §6 (FR-13 charter, line 89), inline done-when (line 85).
- `2026-07-07_BRIEF_ontology-north-star.md` §3.3 (four kinetic action types, lines 43–46), §6 (FR-13 amendment, line 73), unification claim (line 48).
- `2026-07-08_AUDIT_fa-campaign-self-review.md` §4-1, §7 (the conflict named as the sole per-FR handover blocker).
