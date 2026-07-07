# Golden-URL Registry & Knowledge-Flow — Architect Brief (T4+)

**Repo:** corp-monorepo (registry + scout) · vault (human view) · **Audience:** functional intake / technical architect
**Status:** brainstorm-phase blueprint (nothing implemented; audit-space artifact per DR-14)
**Date:** 2026-07-07 · **Session:** functional-architect sitting #1 (backlog T4, expanded per operator vision)

---

## 1. Problem

The operator holds a handful of GOLDEN entry points into corporate knowledge — SharePoint sites/libraries dense with recordings, decks, and documentation (six seeds supplied, §8). Today these live in his head and scattered OneDrive shortcuts. Three compounding failures:

1. **Location drift.** SharePoint names are stable; locations are not — content gets reorganized, sites renamed, folders moved. Links rot silently.
2. **No cascade.** Golden URLs are static bookmarks, not roots of exploration. The 1.1 TB terrain never narrows itself; every new discovery is a manual act. Golden URLs will keep arriving — the set must grow itself.
3. **No downstream flow.** Once material is found, there is no defined path from "found on SharePoint" through "essence in vault" to "archived to Google Drive." Queueing, prioritization, and archiving are undefined.

Constraint that shapes everything: the six seeds were supplied as **local OneDrive sync paths**, and the hard invariant bans any traverse-with-hydration under `OneDrive - Blue Yonder`. Whatever consumes these locations must operate **server-side (Graph), read-only** — never against the synced tree.

## 2. Evidence (research pass, 2026-07; sources §9)

**R1 — Site identity is permanent; URLs are not.** The Graph site ID is a composite of hostname + site-collection GUID + site GUID. The GUIDs survive site rename and URL change; renames create redirects, sharing links auto-redirect, and OneDrive sync transparently re-targets. Caveat: hard-coded URLs in web parts and custom solutions can still break, and some tooling ignores redirects. **Verdict: the site GUID is the only anchor worth trusting at the top tier.**

**R2 — Document-level permanence is a trap.** SharePoint's Document ID / durable-link machinery holds only *within one library*: a cross-library or cross-site move mints a new DocID and breaks the old link. **Folders get no durable link at all** — confirmed unsupported. Additionally, enabling the DocID service is a site-collection-admin action the operator does not control on corporate sites. **Verdict: do NOT anchor the registry on document or folder identity. Anchor on site + drive (library); treat everything below as drift-expected.**

**R3 — Re-discovery by name is a first-class API capability.** `GET /sites?search={name}` finds sites by name; `GET /sites/{siteId}/drive/root/search(q=…)` and the Microsoft Search API (`POST /search/query`, entityTypes `driveItem`/`list`, with `path:` / `isDocument` / date filters) find moved folders and files across the tenant. Path-addressing (`/drive/root:/{path}`) gives a cheap liveness probe. **Verdict: "name stable, location drifts" is solvable mechanically — probe by path, recover by name search.**

**Prior-evidence pointers (not re-derived):** scout pilot design (registry = its target list); DR-12 storage topology (MyWork_OneDrive = human hub); P4 scheduled-loops + heartbeat pillar; BY_Technical_Coordinates_Reference as proto-registry card; X1 proposal auth findings — the Graph leg is blocked on interactive consent (AADSTS65002); the tenant blocks Graph deletes (upload/read only) — irrelevant to a read-only scout, protective by construction.

## 3. Converged recommendation

### 3.1 Three-tier anchor model (the registry's spine)

| Tier | Anchor | Stability | Registry treatment |
|---|---|---|---|
| A1 | **Site** — composite Graph site ID (GUIDs) | Permanent across rename/URL change (R1) | Hard key. Never expected to change. |
| A2 | **Drive / library** — Graph drive ID | Stable while the library exists | Hard key, re-enumerable from A1 (`/sites/{id}/drives`). |
| A3 | **Path below drive** | Drift-expected (R2) | Soft hint, not truth. Auto-probed; on failure, recovered by name search (R3) and re-pinned only with operator ratification. |

**Golden-URL record (contract):** `id` · `name` (human, stable) · `site_id` (A1) · `drive_id` (A2) · `path_hint` (A3) · `web_url` (display/convenience, regenerable) · `local_hint` (OneDrive sync path, display-only, NEVER traversed) · `what_it_holds` (one line) · `owner_team` · `dims` (industry[] × software[] — the two business dimensions, T1 bridge) · `topics[]` · `phase` (lifecycle, §3.4) · `last_verified` · `liveness` (LIVE / MOVED-candidate / LOST / STALE) · `yield` (§3.3 score) · `added_by` (operator / scout-promotion).

**Done when:** the six seed paths are resolved to A1+A2 identities and stored as records passing a schema validator; resolving any record's `web_url` from its IDs round-trips to a reachable location.

### 3.2 One source, N generated views

The registry is **one machine-readable source** (YAML in corp-monorepo config, per dev standards) with generated projections — never hand-maintained copies:

- **Vault card** — a generated note (sentinel-marker sections, same pattern as generated MOCs) rendering the registry as the human "where to look" card; successor to BY_Technical_Coordinates_Reference.
- **MyWork_OneDrive shortcuts** — optionally regenerated from the same source, making the DR-12 hub a projection instead of a hand-tended artifact.
- **Scout target list** — the registry *is* the scout's crop-rotation plan; no second list exists.

**Done when:** editing the YAML and running the generator updates the vault card with zero manual edits; a hand-edit inside a sentinel block is detected and overwritten on next generation.

### 3.3 Cascading discovery — the foraging economy

Golden URLs are **roots, not bookmarks**. A scheduled scout loop (P4: scheduled + heartbeat; server-side Graph, read-only):

1. **Probe** every record: A1 resolve → A2 resolve → A3 path probe. Statuses: LIVE; MOVED (probe failed, name search found ≥1 candidate — candidate attached); LOST (no candidate); STALE (not verified within one cycle → heartbeat alarm, absence-of-success is the signal).
2. **Forage** one level below each LIVE root per cycle (bounded — never recursive slurps): enumerate children, compute a **yield score** per child folder/library from cheap signals — document density, `lastModifiedDateTime` recency, type mix (recordings/pptx/docx), name match against `dims` and `topics`.
3. **Queue** — exploration is budgeted: top-N unexplored candidates by yield per cycle (crop rotation). This is the operator's "kolejkowanie/priorytetyzacja" made mechanical.
4. **Promote** — children clearing a yield threshold become *golden candidates* in the cycle report. **The operator only ratifies**; the scout never self-amends the registry. Ratified candidates enter as records with `added_by: scout-promotion`.

**Done when:** one full cycle on the six seeds produces a report with per-record liveness, a scored candidate list, and a heartbeat success marker; a deliberately-broken `path_hint` is reported as MOVED with the correct recovery candidate.

### 3.4 Unified lifecycle — files join the S0–S3 machine

The vault operating model's S0–S3 state machine generalizes to the whole estate; **files and notes share one lifecycle, phase is metadata**:

- **S0 RAW** — exists on SharePoint terrain; known only as terrain.
- **S1 REGISTERED** — covered by a registry record / pulled to inbox; the system knows it exists and what it's about (`dims`, `topics` at ingest — the T1 bridge).
- **S2 ESSENCE** — CKE-extracted; a vault note cites it (Note→cites→Document).
- **S3 ARCHIVED** — copied to Google Drive archive leg; registry record carries the archive pointer as tombstone. **Archiving is copy + record — the SharePoint side is never deleted** (tenant blocks Graph deletes anyway; invariant-aligned by construction).

This also seeds T2's day-1 ontology slice with three object types (Location, Document, Note) and two link types (Document→lives-in→Location, Note→cites→Document) proven on live data — no graph layer, just frontmatter + registry + index.

**Done when:** one document from one seed location traverses S0→S3 with its registry/vault trail intact: registered with dims, extracted to a citing note, archived to GDrive with tombstone pointer resolvable.

### 3.5 Auth synergy (sequencing note, no timeline)

The scout's Graph read access sits behind the **same interactive Graph consent** already gating X1's upload leg (AADSTS65002). One operator consent action unblocks both lanes. Sequence accordingly; the consent is an operator-only step.

## 4. Open decisions (operator ratification, none blocking the blueprint)

D1 **Registry home** — proposed `corp-monorepo` config area; exact path needs approval (no new folders without sign-off).
D2 **Auth shape** — delegated flow via the existing az/X1 consent vs. dedicated app registration; recommend deciding jointly with X1's ADR (DR-11 family) at technical-architect phase.
D3 **Ratification interface** — cycle report with paste-back approvals (recommended day-1) vs. checkbox section in the vault card.
D4 **Archive trigger policy** — what qualifies a document for S3: age? superseded? explicit pick? Recommend explicit-pick day-1, policy later from usage telemetry.
D5 **Yield-score weights** — start with equal weights, tune from cycle reports; contested only if evidence disagrees.

## 5. NOT-list (over-engineering guards; Council-#10 sizing governs)

- **No per-document registry.** Site/library granularity + name search; never an item-ID inventory of 1.1 TB.
- **No DocID-service dependency** — needs site-collection admin the operator doesn't have, and breaks cross-library anyway (R2).
- **No local-tree crawling, ever** — hydration invariant; Graph-only.
- **No self-amending registry** — scout proposes, operator ratifies. No exceptions.
- **No webhooks/delta subscriptions day-1** — a scheduled loop suffices at solo scale; delta queries are a later optimization with a trigger condition (cycle runtime exceeding budget).
- **No graph database / Palantir machinery** — the ontology slice lives in frontmatter + YAML + index (T2's NOT-list applies in advance).
- **No SharePoint-side deletion in the archive lane** — copy + tombstone only.

## 6. FR-addendum candidates

- **FR-10 (new): Golden-URL registry** — the record contract (§3.1), one-source-N-views generation (§3.2), schema validation as the enforcement seam.
- **FR-11 (new): Scout foraging loop** — probe/forage/queue/promote cycle (§3.3) under P4 heartbeat; registry as sole target list; ratification-gated growth.
- **FR-12 (new): Unified estate lifecycle** — S0–S3 phase field spanning files and notes (§3.4); amends DR-2's vault operating model upward to the whole estate; defines the archive leg's contract with X1/DR-11.
- **Amendment to FR-7 lane inputs:** deck production gains the registry as a grounded "where sources live" input (cross-ref T6).

## 7. Success criteria (brief-level)

Every golden URL resolvable or flagged within one loop cycle (backlog contract) **and**: the six seeds live as validated records; one MOVED-recovery proven; one full S0→S3 traversal proven; heartbeat alarm proven by a forced-failure test. Closure is declared on these, not on "tests pass."

## 8. Seed list (operator-supplied, to be resolved to A1/A2 identities)

1. `Blue Yonder Platform - Documents`
2. `_Architecture Review Board - Documents\Recordings`
3. `_Cognitive Planning - Documents\General\6. TRAINING\COGNITIVE FRIDAYS`
4. `Integration Compliance Committee - Documents\Artifacts`
5. `Blue Yonder Products - Product Documentation`
6. `The Lighthouse Program - Documents\Cognitive Short`

(Local sync paths as supplied; stored as `local_hint` display-only. Resolution to site/drive IDs is a Graph lookup, not a local traversal.)

## 9. Sources (research pass)

- Site ID composite & permanence: learn.microsoft.com Graph `site` resource; ShortPoint site-ID guide; Microsoft Q&A on composite site IDs.
- Site rename behavior (redirects, sharing-link redirect, sync re-target, web-part caveats): learn.microsoft.com "Change a site address"; handsontek.net (2026-02).
- DocID fragility cross-library & no folder durable links: Microsoft Tech Community durable-links thread; Microsoft Q&A durable folder links (unsupported); cognillo.com broken-links analysis.
- Re-discovery APIs: Graph `sites?search=`, `driveItem-search`, Microsoft Search API `search/query` (learn.microsoft.com).
