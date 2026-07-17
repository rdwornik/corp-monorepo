---
intake-id: 16
status: DRAFT
origin: 2026-07-17 · Lane B e5-registry-design worktree · executor-architect (robdwornik)
consumed-by:
---

# E5 Registry foundation — FR-10 URL/source registry + deterministic source-value scoring (design)

> **What this is.** The single design document the E5 build arc executes from, so the build
> re-decides nothing. It **consolidates by deciding**: the FR-10 registry and the FR-11/#38
> source-value score were sketched across two 2026-07-07 brainstorm briefs and a rebuilt BACKLOG;
> this doc fixes the day-1 data model, the deterministic scoring function, the seed set, the seam
> contracts (as skeletons), the phase-acceptance bar, and the build order. **Design-lane only — no
> `src/`/`tests/` change; skeletons are named on paper, not implemented.**
>
> **Audience:** the E5 executor-architect chat · **Status:** DRAFT (operator flips to
> READY-FOR-TECHNICAL on ratification) · **Date:** 2026-07-17.

---

## 0. Scope, framing, and what this is NOT

**In scope.** The *foundation stone*: a URL/source **registry** (logical layer over the physical
estate) and a **deterministic source-value score** attached to every registry record. These
underpin file management, directory management, the magistrala (capture pipeline), and every
downstream flow (scout, vault, RFP/deck grounding).

**Not-to-be-confused-with.** The existing `src/corp/ops/registry.py` `ContentRegistry`
(series→client→rules **file-routing** at ingest, backed by `config/content_registry.yaml`) is a
**different** registry. The FR-10 registry designed here is a **source/value registry** over
SharePoint/OneDrive terrain. They are disjoint; the FR-10 registry is a new artifact, not an
extension of `ContentRegistry`. (A later integration seam connects them — §4, seam C.) **This is
exactly the BACKLOG #35-vs-#38 distinction:** #35 "Registry v4 gate" is the `ContentRegistry`
routing gate (FR-3/DR-6/7); the FR-10 source registry is #38/#40 (§6, and §7 D8 for the
adjudication that corrected an earlier conflation).

**NOT-list honored (charter §3 + Arc-B plan §0 base-note union):**
- **No literal PageRank** — folders have no link graph; "neighbor propagation" here is a single
  bounded pass, defined precisely in §2.3, explicitly **not** an iterative eigenvector method.
- **No microservices, no service mesh, no message bus** — the registry is one YAML source + a
  generator + seam tests; adding an infrastructure tier is a NOT-list violation.
- **No self-amending registry** — the scout proposes, the operator ratifies (§4, seam A).
- **No local-tree crawling, ever** — Graph metadata only; the synced `OneDrive - Blue Yonder` tree
  is never traversed (§3, hydration invariant).
- **Reference-not-copy (DR-12)** — originals stay in place; the registry + generated shortcut hubs
  *organize*, they never relocate source material.

**Provenance (cite, don't restate — DR-12 reference discipline).** This design builds on:
`docs/audits/2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` (FR-10 record contract,
three-tier anchor, one-source-N-views, scout loop, S0–S3 lifecycle, seed list);
`docs/audits/2026-07-07_BRIEF_algorithmic-adopt-map.md` (yield-score v1, the learning-behind-
triggers map, telemetry-spine adopt-now); `docs/audits/2026-07-06-technical-architect-intake.md`
§5 (DR-12) + §9 (FR-10…FR-19); `docs/audits/2026-07-17-brief-cross-repo-integration-t6.md` §3.5 +
`docs/audits/2026-07-17-arc-b-execution-plan.md` §0/§3 (substrate acceptance bar);
`docs/audits/2026-07-17-execution-charter.md` §3; `docs/audits/2026-07-05-deep-magistrala.md`.

---

## 1. Registry data model

### 1.1 Logical over physical (reference-not-copy)

The registry is a **logical map** of where valuable knowledge lives. It never moves, copies, or
mutates source material (DR-12: wider SharePoint = read-only source terrain; MyWork_OneDrive =
navigation hub). Physical originals stay put; the registry and its generated projections are the
only things that "organize."

**One machine-readable source → N generated projections** (golden-url brief §3.2):
- **Source of truth:** one YAML file in the corp-monorepo config area (exact path is operator
  decision **D1**, §8). Hand-edited for operator entries; appended (on ratification only) for
  scout promotions.
- **Projection — vault card:** a generated "where to look" note (sentinel-marker sections, the
  same pattern as generated MOCs); successor to `BY_Technical_Coordinates_Reference`.
- **Projection — MyWork_OneDrive shortcuts:** optionally regenerated from the same source, making
  the DR-12 navigation hub a projection instead of a hand-tended artifact.
- **Projection — scout target list:** the registry *is* the scout's crop-rotation plan; no second
  list exists.

A hand-edit inside a generated sentinel block is detected and overwritten on next generation —
the source is authoritative, projections are disposable.

### 1.2 Three-tier anchor model (the record's spine)

Anchoring follows the golden-url brief's researched verdict (R1–R3): the SharePoint **site GUID**
is the only top-tier anchor worth trusting; document/folder identity is a trap.

| Tier | Anchor | Stability | Registry treatment |
|---|---|---|---|
| A1 | Site — composite Graph site ID (GUIDs) | Permanent across rename/URL change | Hard key; never expected to change |
| A2 | Drive / library — Graph drive ID | Stable while the library exists | Hard key; re-enumerable from A1 (`/sites/{id}/drives`) |
| A3 | Path below the drive | Drift-expected | Soft hint; auto-probed, recovered by name search, re-pinned only on operator ratification |

### 1.3 The record contract (FR-10)

Adopt the golden-url brief §3.1 contract, split into **declaration fields** (the hand-edited YAML
source of truth) and **observation fields** (derived state, computed and joined by `id`). *This
declaration/observation split is adopted from the sol derivation (§7 D1): derived, drift-prone
state does not belong in the hand-edited source — it invites staleness and merge noise, and it
keeps "the source is authoritative, projections/observations are disposable."* One record per
registered source (site/library granularity — never a per-document inventory of the 1.1 TB
terrain):

```
# --- declaration fields (in source_registry YAML; operator-ratified changes only) ---
id               # stable slug, permanent join key
name             # human, stable
site_id          # A1 — hard key
drive_id         # A2 — hard key
path_hint        # A3 — soft, drift-expected
web_url          # display/convenience, regenerable from IDs
local_hint       # OneDrive sync path — DISPLAY-ONLY, NEVER traversed
what_it_holds    # one line
owner_team
dims             # industry[] × software[] (the two business dimensions, T1 bridge)
topics[]
phase            # S0..S3 lifecycle (FR-12): RAW | REGISTERED | ESSENCE | ARCHIVED
curation_level   # curated-set membership
operator_prior   # enum: max | high | normal | low | exclude  (adopted from sol §7 D2)
archive_pointer  # nullable; an S3 tombstone reference — NEVER implies SharePoint deletion
added_by         # operator | scout-promotion

# --- observation fields (derived; append-only in ops.db, joined by id) ---
last_verified
liveness         # LIVE | MOVED-candidate | LOST | STALE
recovery_candidates[]
value_score      # §2 — deterministic; {score, components{}, score_version, score_as_of}
observation_id
```

`value_score` is stored as a struct (final score + its component breakdown + the weight-set
version + a snapshot timestamp), so a score is always explainable and reproducible from its
inputs. The scout may **append** observation rows and promotion **proposals**; it can never add,
re-pin, or remove a declaration record (that is operator-ratified only — §4 seam A).

**Done when (data model):** the three seed sources (§3) resolve to A1+A2 identities and store as
records passing a schema validator; resolving any record's `web_url` from its IDs round-trips to a
reachable location.

---

## 2. Source-value scoring v1 — DETERMINISTIC day-1

### 2.1 The contract: deterministic, explainable, learning-free on day 1

The day-1 score is a **pure deterministic function** of registry-visible signals: identical inputs
always produce an identical score; there is no randomness, no learned parameter, no model. This is
the A3-substance ruling (deterministic scoring day-1, learning later behind adopt-map triggers) as
carried by the adopt-map brief §2/§3 — *"any learning component before its data exists is barred;
the 0-rows rule beats all ambition."*

### 2.2 The v1 function

Per record, extending the adopt-map brief §3 yield-score v1 from a foraged-location score to a
registry-record score. All component values are in `[0,1]`, computed from **one frozen
Graph-metadata snapshot** at `score_as_of`. The composition is **two-level** (yield signals →
intrinsic → neighbourhood-adjusted final) — *adopted from the sol derivation (§7 D3), which
resolves a determinism defect in this design's first draft (see §2.3)*:

```
Y = (D + R + T + M + U) / 5                 # yield: equal-weighted metadata signals
I = 0.60·Y + 0.20·C + 0.20·O               # intrinsic: yield + curation + operator prior
value_score = round( 100 · (0.85·I + 0.15·N) )   # final: intrinsic + neighbourhood prior
```

Components (each in `[0,1]`, all from Graph metadata + registry state — no content hydration, no
local traversal):

- **D — document density:** `(docs / (docs + folders)) · min(1, ln(1+docs)/ln(64))`; `0` for an
  empty listing.
- **R — recency:** mean of `2^(-age_days/180)` over directly-listed documents (Graph
  `lastModifiedDateTime`); `0` when none.
- **T — type value:** mean per-document weight — recording/audio/video `1.00`, PPTX `0.90`,
  DOCX/PDF `0.70`, XLSX `0.40`, other `0.20`.
- **M — dim/topic match:** fraction of normalized `dims`/`topics` tokens found in the location
  name + directly-listed child names; neutral `0.50` when no terms configured.
- **U — uniqueness:** `1 − observed_duplicate_rate`; neutral `0.50` until a legitimate sample
  supplies duplicate evidence (MinHash is a *later* adopt — §2.4).
- **C — curation:** operator golden `1.00`, ratified scout promotion `0.75`, unratified candidate
  `0.25`.
- **O — operator prior:** `max=1.00 · high=0.75 · normal=0.50 · low=0.25 · exclude=0.00`.
- **N — neighbourhood prior:** §2.3.

**Equal weights at the yield level day-1** (golden-url brief D5); the fixed `0.60/0.20/0.20` and
`0.85/0.15` mixings are v1 constants. Every mixing carries a `score_version` so a recalibration is
a versioned, auditable change — never a silent edit. Ties sort by stable registry `id`.

**Safety/policy gates OVERRIDE the score numerically** *(adopted from sol §7 D5)*: `exclude`,
credential blacklists, active-deal restrictions, and consent requirements **cannot be outvoted by
a high numeric score**. A hard gate wins over any arithmetic — the OneDrive/consent invariants are
not tradeable against yield.

### 2.3 Neighbourhood prior — single-snapshot, single-pass (NOT PageRank)

**Fixed constraint:** folders have no link graph, so there is no eigenvector to solve. **N is
computed from the *intrinsic* score `I`, never from the final `value_score`, within one snapshot:**

```
N(child) = 0.70·I(parent) + 0.30·mean( top-3 direct siblings by I )
N(root)  = mean( top-3 direct children by I )
neighbours = explicit one-hop Graph parentReference within the same drive + snapshot
missing neighbourhood evidence → neutral N = 0.50
```

- **One snapshot, one pass:** compute every `I` once, compute `N` once, compute the final score
  once. No link graph, no recursion, no eigenvector, no repeated propagation.
- **Why this replaces the first draft.** This design's first draft computed the neighbour prior
  from the *previous cycle's final scores* — introducing cross-cycle temporal coupling (a score
  depended on run history, not just the current snapshot). sol's "N from intrinsic, single
  snapshot" removes that coupling entirely: the score is now a pure function of one metadata
  snapshot, strictly more deterministic and reproducible. **Adopted (§7 D3).**
- This still captures "valuable neighbourhoods lift their members" without PageRank's iterative
  machinery or its link-graph assumption.

### 2.4 Learning — LATER phase, behind adopt-map triggers (named, not designed in)

Per the adopt-map brief, everything below is deferred behind a **measurable trigger**; only the
telemetry spine is an unconditional adopt-now. This design **names** them so the build arc knows
the runway, and **does not design them in**:

| Later capability | Trigger (from adopt-map brief) | Status here |
|---|---|---|
| Telemetry spine (FR-13) | Unconditional — the 0-rows fact | Prerequisite; emit liveness/score events from day 1 (§4 seam D) |
| Bandit exploration queue (Thompson) | Scout loop exists + >1 cycle of yield data (cycle 3+) | Named only; day-1 queue is round-robin/deterministic-rank |
| Hierarchical / recalibrated weights | Realized-usage telemetry disagrees with equal weights | Named only; `weights_version` is the seam |
| Monte-Carlo terrain sampling (FR-14) | Cheapest high-information action once Graph access lands | Named only; feeds priors later |

**Quantified v2 trigger** *(adopted from sol §7 D4 — "measurable, not a vibe", adopt-map §7):* a
learned v2 scorer may be **proposed** only after **≥3 completed scout cycles**, **≥30
operator-labelled candidate outcomes**, and **top-3 precision below 70% for two consecutive
cycles**. Until all three hold, v1 deterministic scoring stands and the bandit clause stays
dormant.

**Done when (scoring v1):** every registry record carries a `value_score` with its component
breakdown; two consecutive deterministic rankings agree with the operator's spot-check of the
top-3/bottom-3 (adopt-map brief §3 done-when).

---

## 3. Seed sources (the #40 day-1 seed)

Three operator golden sources, entered with **maximum operator priors** (`operator_prior: max`,
`added_by: operator`, `curation_level: golden` — the §2.2 enums):

| Seed | Source (operator-supplied local hint) | Brief §8 ref |
|---|---|---|
| 1 | Blue Yonder **Platform** — Documents | seed 1 |
| 2 | Blue Yonder **Products** — Product Documentation | seed 5 |
| 3 | **Cognitive Fridays** (`_Cognitive Planning - Documents\General\6. TRAINING\COGNITIVE FRIDAYS`) | seed 3 |

**Hydration invariant (core-invariant #1 — absolute, restated for the executor):** these live under
the synced `OneDrive - Blue Yonder` tree. Resolution to A1/A2 identities is a **Graph METADATA
listing only** (`GET /sites?search=`, `/sites/{id}/drives`, path-addressing liveness probe). The
scout and the registry builder **NEVER filesystem-traverse the synced tree**. In OneDrive-guard
terms: only **T0** (hydration-free names/metadata enumeration) is used; **T1** (content
read/hydration) and **T2** (any write) are not invoked by any registry code path. `local_hint` is
stored display-only and is never opened.

**Allowed vs forbidden Graph calls** *(adopted from sol §7 D6 — turns the invariant into an
enforceable allowlist):*
- **Allowed:** site search (`GET /sites?search=`), drive enumeration (`/sites/{id}/drives`),
  drive-item metadata probes (path-addressing), and bounded **direct-child** metadata listings
  with `$select=id,name,webUrl,parentReference,lastModifiedDateTime,file,folder`.
- **Forbidden:** content download/hydration, **recursive** enumeration, local `Test-Path` /
  directory listing, and **every traversal under `OneDrive - Blue Yonder`**. Ambiguous site/drive
  matches are not auto-pinned — they require operator ratification.

**Graph-consent note:** the Graph read leg sits behind the same interactive consent gating X1's
upload leg (AADSTS65002). Seeding the *records* (names, priors, `local_hint`) needs no consent;
*resolving* them to live A1/A2 IDs does. The design does not work around this — it is an operator
gate (§6, §8).

**Done when (seed):** the three seeds are entered as records; on Graph consent they resolve via
metadata listing only and round-trip `web_url`; a `git`-diff of any registry code path shows zero
content-read/traverse of the synced tree.

---

## 4. Seam contracts — N2-class seam-test SKELETONS (named, not implemented)

The registry's boundaries, each guarded (later) by an **N2-class seam test**: drive the real
crossing, assert the wire contract, fail on a boundary violation (charter §3; the T6 reference
seam is `tests/rfp/test_vault_adapter_cli_seam.py`). **Skeletons only — named here, implemented in
the build arc, not in this design.**

| Seam | Crossing | Wire contract (asserted by the seam test) | Skeleton test name |
|---|---|---|---|
| A | registry → scout | The scout's target list IS the registry; the scout never self-amends — a promotion is a *proposal*, entering the source only on operator ratification | `test_registry_scout_targetlist_seam` |
| B | registry → vault-card generator | The generated card is a pure projection; a hand-edit inside a sentinel block is overwritten; no card content originates outside the source | `test_registry_vaultcard_projection_seam` |
| C | registry → magistrala / ingest | A registered source drop routes to the right zone via magistrala + `ContentRegistry`; the FR-10 registry supplies *provenance/value*, `ContentRegistry` supplies *routing* — the two do not overwrite each other | `test_registry_magistrala_routing_seam` |
| D | registry → telemetry (FR-13) | Every `liveness` transition and every `value_score` (re)computation emits one schema-valid observation event; absence of a cycle's success is itself the STALE signal | `test_registry_telemetry_event_seam` |
| E | Graph-resolver → registry | A1/A2 resolution is read-only metadata; the resolver returns IDs + `lastModifiedDateTime`, never hydrated content; a synced-tree traverse attempt fails the test | `test_graph_resolver_readonly_metadata_seam` |
| F | schema round-trip | YAML declaration → validated record → canonical serialization; missing A1/A2 anchors or an invalid enum fails **closed** | `test_fr10_registry_schema_round_trip` |
| G | scorer determinism | frozen record + metadata fixture → the exact component vector and integer score, identical across repeated runs (guards §2) | `test_value_score_v1_golden_vector` |
| H | single-pass neighbour | intrinsic-score snapshot → one-hop `N`; a *final* score offered as a neighbourhood input fails the test (guards §2.3) | `test_neighbour_prior_is_single_pass` |
| I | provenance survives downstream | registry `id` + anchor tuple pass through capture manifest → CKE contract → vault citation **without path rewriting** (guards the §5 T6 thread) | `test_source_provenance_survives_downstream` |

Seams **F–I are adopted from the sol derivation (§7 D7)** — they guard the exact invariants this
design asserts (schema validity, scorer determinism, single-pass neighbour, provenance-to-vault).
Seam **D (telemetry) is kept over sol**, which omitted it: telemetry is the unconditional
adopt-now (FR-13) and seam D closes the loop that makes the *later* learning phase (§2.4)
possible — a load-bearing seam, not optional.

---

## 5. Phase acceptance — the T6 substrate bar E5 feeds into

E5 is a **substrate** phase. Its closure is not "tests pass" — it is that the registry can ground
the **T6 one-client sandbox simulation**, the substrate-phase acceptance bar
(`2026-07-17-arc-b-execution-plan.md` §0/§3; T6 brief §3.5):

> **Project_Codes → magistrala → vault → Excel/Word answer + deck slide**, where the RFP answer
> and the deck slide both cite the **same** vault note (the proof of unification).

The registry's contribution to that thread is the grounded **"where the sources live"** input: the
one-client run draws its source material from registered sources whose `value_score` ordered what
was pulled first. E5 does not *own* the T6 bar (that is phase-level, post Arc-C), but E5 is "done"
for substrate purposes only when the registry can supply that input.

**Registry-specific done-when (E5's own bar, gating the T6 substrate bar):**
1. the three seeds resolve to A1/A2 records passing the schema validator;
2. a deliberately broken `path_hint` reports `MOVED-candidate` with the correct recovery candidate
   (the drift-recovery proof);
3. every record carries a deterministic `value_score` with its component breakdown;
4. seam tests A–E exist and fail on a boundary violation.

---

## 6. Build decomposition — mapped to BACKLOG

> **Task-identity correction (adopted from sol §7 D8).** BACKLOG **#35 "Registry v4 gate + zone
> renames (DR-6/7)" is the `ContentRegistry` *routing*-registry gate** (the magistrala
> series→client→rules matcher, `refs FR-3, DR-6/7`) — the >80% figure is the routing dry-run
> match-rate. It is **distinct from the FR-10 source registry** designed here. The FR-10 registry
> (schema + observation model + scorer) is built under **#38** and seeded by **#40**. This
> design's first-draft §6 conflated the two ("#35 = the FR-10 schema validator"); that was wrong —
> #35 is the routing substrate. This correction also resolves a first-draft internal tension
> (#40's done-when requires "records passing the schema validator", but the FR-10 schema is built
> in #38 — so #38 must precede #40).

Ordered execution (honoring the one hard `depends-on` edge, **#35 before #36**, and R10 theme
order E5 elevated above E4 — neither re-opened here). Corrected order **#35 → #38 → #40 → #36**:

| Order | Task | What | Gate |
|---|---|---|---|
| 1 | **#35** [P1][M] | `ContentRegistry` routing-registry v4 gate + zone renames — dry-run match-rate >80% (FR-3/DR-6/7); the magistrala routing substrate, **not** FR-10 | final zone names **operator-pending** (DR-6/7) |
| 1b | **#37** [P1][M] | Restart magistrala inbox-drop routing (§4 seam C) — pairs with #35's routing substrate | — |
| 2 | **#38** [P2][M] | **FR-10 source registry** — schema + observation model + deterministic scorer (§2) + single-pass neighbour + golden vectors; the scout's queue consumes `value_score` | **not** blocked |
| 3 | **#40** [P1][S] | Registry day-1 seed — draft the three golden records (§3) consent-free; **resolve + validate + score** them (needs the #38 schema + Graph consent) | live resolution **BLOCKED-on-operator** (Graph consent); ambiguous matches need ratification |
| 4 | **#36** [P1][L] | Scout foraging pilot — probe/forage/queue/promote; **after #35 + #38 + #40**; day-1 queue is deterministic `value_score` rank, bandit is the cycle-3+ upgrade (§2.4) | **BLOCKED-on-operator** (Graph consent); promotion separately ratified |

**Blocked-on-operator (flagged, NOT designed around):** #36 and the X1 build both gate on the one
interactive Graph consent; #40's live resolution needs it too (record *drafting* does not). This
design marks them blocked and stops there — it does not invent a workaround for the consent gate,
and it does not re-open the theme order or the depends-on edge.

Supporting E5 rows (#3 dedup wire, #4 session-id fix, #37) are ingest/loop work that consume the
registry but are not part of the foundation-stone data model or scoring; they are left to their
BACKLOG rows.

---

## 7. Adjudication — this design vs the sol independent derivation

The bounded `codex exec -s read-only` **sol** pass produced a **usable** independent derivation
(Codex committed nothing). Its verbatim output is retained per rider **LB-R1** at
**`docs/audits/2026-07-17-codex-sol-e5-registry-derivation.md`** — every ruling below references
that artifact's part (sol §1–§5).

**Independent convergence (sol reached these with no sight of this design — corroboration, not
divergence):** one operator-owned YAML canonical source; three-tier A1/A2/A3 anchor;
scout-proposes/operator-ratifies (no self-amending registry); deterministic, single-pass,
no-PageRank scoring with all learning deferred; the same three seeds at max priors resolved by
Graph metadata only; `#35`-before-`#36`; reference-not-copy projections. The core is
independently confirmed.

**Divergences — each ruled:**

| # | Divergence (this design ⟷ sol) | Ruling | One-line reason |
|---|---|---|---|
| D1 | Record shape: draft co-located `value_score`/liveness in the record ⟷ sol **splits declaration (YAML) vs observation (derived, ops.db, joined by id)** | **ADOPT sol** (§1.3 rewritten) | Derived, drift-prone state does not belong in the hand-edited source of truth — splitting it kills staleness/merge-noise and keeps "source authoritative, observations disposable". |
| D2 | `operator_prior` as `0..1` float ⟷ sol enum `max/high/normal/low/exclude` (+ `curation_level`, `archive_pointer`) | **ADOPT sol** (§1.3) | An operator-facing enum matches the ratification workflow better than a bare float; `archive_pointer`/`exclude` are useful and safety-aligned. |
| D3 | Neighbour prior from the **previous cycle's final score** (flat 1/5 weight) ⟷ sol **N from *intrinsic* I, single snapshot**, nested `Y→I→N` at `0.15` | **ADOPT sol** (§2.2–2.3 rewritten) | The draft's prior-cycle dependency introduced cross-cycle temporal coupling; sol's single-snapshot/intrinsic N makes the score a pure function of one metadata snapshot — strictly more deterministic. sol also supplies an executable formula where the draft had only a schema. |
| D4 | Learning triggers stated qualitatively (cycle 3+, "telemetry disagreement") ⟷ sol **quantified** (≥3 cycles, ≥30 labelled outcomes, top-3 precision <70% ×2) | **ADOPT sol** (§2.4) | "Measurable trigger, not a vibe" (adopt-map §7) — the quantified threshold is executable; the qualitative one is not. |
| D5 | No explicit safety-over-score rule ⟷ sol: **safety/policy gates cannot be numerically outvoted** | **ADOPT sol** (§2.2) | A high yield score must never override `exclude`/consent/OneDrive gates — the draft omitted this; it is safety-load-bearing. |
| D6 | Hydration invariant stated as principle ⟷ sol: **explicit allowed/forbidden Graph-call allowlist** (`$select` fields, no recursion) | **ADOPT sol** (§3) | Converts the invariant into an enforceable allowlist — strictly better for the executor and the seam test. |
| D7 | 5 seam skeletons (incl. **D telemetry**) ⟷ sol 8 skeletons (schema round-trip, golden-vector, single-pass, provenance-survives) but **no telemetry seam** | **MERGE** — adopt sol's F–I; **keep D over sol** (§4) | sol's four guard the exact invariants this design asserts (adopt). sol's omission of a telemetry-emit seam is a gap — FR-13 is the unconditional adopt-now, so D is kept as load-bearing. |
| D8 | Draft treated **#35 as the FR-10 schema-validator gate**; order `#40→#35→#38` ⟷ sol: **#35 is the `ContentRegistry` *routing* gate** (FR-3/DR-6/7), FR-10 is #38/#40; order `#35→#38→#40→#36` | **ADOPT sol** (§6 rewritten) | sol is correct: #35 `refs FR-3, DR-6/7` = routing registry, not FR-10; the draft conflated them and created an internal tension (#40's "passes schema validator" needs #38 first). sol's ordering resolves it. **The single highest-value catch of the pass.** |

**Net:** the core design is independently corroborated; sol's derivation is adopted on all eight
divergences **except** the telemetry seam (D7), where this design's seam D is kept because sol
omitted the FR-13 adopt-now. No divergence was rejected outright; D7 is a merge (superset). The
body sections above have been revised to reflect these rulings.

---

## 8. Education block — the so-what + operator decision points

**So-what.** This design turns the operator's scattered "golden URLs in my head + OneDrive
shortcuts" into **one machine-readable source of truth** with a **deterministic, explainable value
score** on every record. That single artifact is simultaneously: the human "where to look" card,
the scout's crop-rotation plan, and the grounding input for the one-client RFP/deck thread. It is
buildable **today** for everything except live Graph resolution — the records, the schema, and the
scoring are consent-free; only *resolving names to live IDs* waits on the operator.

**Decision points that need the operator (and nothing else):**

| # | Decision | Default this design assumes | Source |
|---|---|---|---|
| D1 | Registry YAML **home** (config path) | corp-monorepo config area; exact path needs sign-off (no new folders) | golden-url brief D1 |
| D2 | **Auth shape** — delegated (existing az/X1 consent) vs dedicated app registration | decide jointly with X1's ADR (DR-11 family) | golden-url brief D2 |
| D3 | **Ratification interface** — cycle-report paste-back vs vault-card checkbox | paste-back day-1 | golden-url brief D3 |
| D4 | **Archive trigger** (what qualifies a doc for S3) | explicit-pick day-1, policy later from telemetry | golden-url brief D4 |
| D5 | **Yield/score weights** | equal weights day-1, `weights_version` for later tuning | golden-url brief D5 |
| G | **Graph consent** — the one interactive step | gates #36 + X1; blocks live resolution | intake §5 / charter §5 |
| Z | **Final zone names** (DR-6/7) | pending; gates #35's zone renames | BACKLOG #35 |

None of these blocks writing the records, the schema, or the scoring; they gate specific downstream
steps as marked in §6.

---

## Sources / provenance

- `docs/audits/2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` — FR-10 record contract,
  three-tier anchor, one-source-N-views, scout loop, S0–S3 lifecycle, seed list, open decisions.
- `docs/audits/2026-07-07_BRIEF_algorithmic-adopt-map.md` — yield-score v1, learning-behind-
  triggers map, telemetry-spine adopt-now, neighbor/bandit/Monte-Carlo lineage.
- `docs/audits/2026-07-06-technical-architect-intake.md` — §5 DR-12 (storage topology /
  reference-not-copy), §9 FR-10…FR-19 map.
- `docs/audits/2026-07-17-brief-cross-repo-integration-t6.md` §3.5 · `2026-07-17-arc-b-execution-
  plan.md` §0/§3 — the T6 one-client substrate acceptance bar.
- `docs/audits/2026-07-17-execution-charter.md` §3 — NOT-list · `2026-07-05-deep-magistrala.md` —
  the capture pipeline the registry feeds.
- `BACKLOG.md` [E5] — #35/#36/#37/#38/#40 · core-invariant #1 (OneDrive exclusion / hydration).

---

*Design-lane record — no `src/`/`tests/` change. **terra** (codex-review) skipped: doc-only diff,
no code impact. Committed on `feat/e5-registry-design`; COMMIT-AND-STOP (never merged, `main`
untouched). 2026-07-17.*
