# Deep Audit D — Vault + Metadata Chain (Wave 2)

**Date:** 2026-07-05 · **Branch:** `docs/deep-vault` · **Base:** `2753601` (main, post Phase-1 merge)
**Method:** read-only. All SQLite access via `sqlite3.connect("file:...?mode=ro", uri=True)`. No OneDrive path read or traversed (excluded-zone `source_path` values classified by string prefix only, never touched). No vault write, no index rebuild, no Obsidian app launch or CLI execution — Obsidian feasibility is file/version-metadata reads only. Census computed by a scratchpad script importing `corp.schema.validate` from this repo's source (validation logic exercised in-memory against on-disk frontmatter; nothing written).

**One-line verdict:** The metadata chain *works end-to-end for exactly six fields* — everything else is decoration, tombstone, or phantom; the vault fails its own written contract 813/813, the link tree is 0% built (all navigation is dataview, invisible to the link graph), and after the deprecated-filter the effective RFP-answerable corpus is **39 notes, not 182** — yet every major defect is mechanical, enumerated below, and ~87% of notes pass the contract after two deterministic fixes.

---

## 1. Step 1 — Metadata chain: field-survival trace

### 1.1 The chain as implemented (producer → consumer)

```
CKE extract (Gemini JSON)
  → extractor/post_process.py         normalize + validate (Pydantic QUARANTINE + schema.yaml warn)
  → config/extractor/templates/extract.md.j2   ← RENAMES source_file→source, DROPS summary to body
  → CKE package on disk (data/_outputs/...)
  → ingest/extractions.py             ← does NOT call validate_frontmatter; gates = title-present
                                        + quality_score≥25 only; injects trust_level=extracted;
                                        KNOWS client from projects/{client}/ staging path but DROPS it
  → vault_io.write_note → ObsidianVault/01_Knowledge/*.md  (flat, Council #7)
  → index_builder._index_cke_notes    ← 30 columns; `confidence` column stores trust_level;
                                        list fields stored as ", ".join(...); rfp_visible computed;
                                        source_hash dedup deletes 325 duplicate rows
  → index.db notes/notes_fts
  → retrieve/engine.py                ← filters client/products/domains/topics/source_type/type/
                                        rfp_visible; EXCLUDES confidence='deprecated' by default;
                                        re-reads frontmatter per hit for trust/overlays/key_facts
  → retrieve/prep.py + retrieve/rfp.py  answer context = title, client, source_type,
                                        topics[:5], products[:3], body content — nothing else
```

Three structural facts discovered in code (each verified at the cited line):

1. **The template betrays the validator** (`config/extractor/templates/extract.md.j2:2`): post_process validates a dict containing `source_file` (required field), then the Jinja template writes it out as `source:` and moves `summary` into the body. Every note on disk therefore fails the Pydantic contract it passed seconds earlier. Measured: 813/813 notes fail with `source_file: Field required`; `source` is flagged "unknown field" on 811.
2. **Ingest never validates** (`src/corp/ingest/extractions.py:152-164`): the vault gate is title-present + `quality_score ≥ 25`. `validate_frontmatter` has exactly two callers: CKE post_process (pre-render) and `corp schema` CLI. The "schema validation" stage of the chain is real code that the real path bypasses.
3. **Ingest discards the client it knows** (`src/corp/ingest/extractions.py:135` vs `:112`): `_collect_packages` extracts `client` from the `projects/{client}/` staging hierarchy, passes it to `_resolve_dest`, which ignores it (flat routing). Client survives only if the LLM put it in frontmatter. This is the origin of a large share of the 258 clientless indexed notes.

### 1.2 Field-survival table

Fill = non-empty count across the 813 `01_Knowledge` notes (disk truth). Verdicts: **LIVE** (produced → consumed on an answering/filtering path), **DEAD** (produced, never consumed downstream), **PHANTOM** (defined/expected, never produced), **BROKEN** (a transform loses or corrupts it).

| Field | Produced by (fill /813) | Validated? | Survives to vault? | Indexed? | Consumed by | Verdict |
|---|---|---|---|---|---|---|
| `title` | CKE (813) | Pydantic req | yes | col+FTS | FTS rank, citation, answer header | **LIVE** |
| `type` | CKE + ext-override (813) | enum — **80 fail** | yes | col+dedup… col | `type` filter; RetrievedNote.note_type | **LIVE** (enum drift) |
| `topics` | CKE (770) | max-8 warn | yes | col+FTS | topic filter, answer header [:5] | **LIVE** |
| `products` | CKE + alias normalize (688) | max-4 warn | yes | col+FTS | product filter (+`expand_product_query`), answer header [:3] | **LIVE** — but uncanonicalized (§4) and comma-join/comma-split round-trip splits embedded-comma terms |
| `client` | CKE/manifest (440) | — | yes | col+FTS | client filter (+alias variants), citation, answer header | **LIVE** — 258/488 indexed rows empty (§3.1) |
| `source_type` | CKE (813) | enum — **66 fail** | yes | col+FTS? (col) | `rfp_visible` rule, filter, citation | **LIVE** (enum drift: `presentation`×54 not in enum) |
| `trust_level` | **ingest injects** `extracted`; tag_legacy script wrote `deprecated` (813) | allowed-values — `deprecated` **not an allowed value** (321 warn) | yes | as `confidence` col | deprecated-filter, rank boost, vault_adapter min_trust, rfp_visible | **LIVE** — the single most load-bearing field, and its dominant value is outside the schema |
| `doc_type` | CKE classifier (773) | free-text | yes | col+FTS | rfp_visible rule, overlay selection (emit side), Products MOC dataview | **LIVE** (1 malformed literal, §3.4) |
| `source_hash` | CKE freshness (778) | — | yes | col | index dedup (deleted 325 rows), planned freshness | **LIVE** (load-bearing at index build) |
| `confidentiality` | defaulted `internal` (812) | enum | yes | col | rfp_visible rule (conf/restricted → never) | **LIVE** (weak — value is 99% default) |
| `project` | CKE/manifest (250) | — | yes | as `project_id` | project filter, query_engine | LIVE (weak) |
| `date` | CKE (812) | — | yes | col | query_engine timeline only | LIVE (weak) |
| `extracted_at` | CKE freshness (778) | — | yes | col | RetrievedNote.extracted_at (carried, not rendered into answers) | DEAD-ish (carried, unused) |
| `source_path` | CKE freshness (778) | — | yes | col | freshness/integrity scanners (N3, never run); not on answer path | **BROKEN data** — resolves today for only 69/488 indexed (§3.3) |
| `quality_score` | CKE (253) | **unknown field** per schema.yaml | yes | no | **ingest quality gate** (quarantined 2 notes) | **LIVE at ingest** — a load-bearing field the schema doesn't know exists |
| `key_facts` | CKE deep (592) | list[str] | yes | no | engine reads it into `meta`… then discards; `facts` table = 0 rows ever | **DEAD** — produced, read, thrown away every query |
| `entities_mentioned` | CKE deep (589) | — | yes | no | none | DEAD |
| `tags` | CKE generate_tags (445) | informational | yes | no | no code consumer; Obsidian tag pane only | DEAD (in-chain) |
| `*_overlay` (9 kinds) | CKE deep (434 total) | **unknown fields** | yes | no | engine collects into `overlay_data`, prep/rfp never read it | **DEAD** — the richest extraction output never reaches an answer |
| `summary` | CKE (all) | warn-if-missing | **NO — rendered into body only** (0 in frontmatter) | no | body content reaches answers, so content survives; the *field* doesn't | **BROKEN** (transform loses it; benign in practice) |
| `source_file` | post_process (pre-render) | Pydantic req | **NO — renamed to `source`** | (`source` col, unread) | none | **BROKEN** — contract-killing rename (813/813 fail) |
| `source` | template (811) | **unknown field** | yes | col | none | DEAD (and the rename's residue) |
| `schema_version` | template `2` (812) | — | yes | no | none | DEAD |
| `source_tool` | template (812) | Pydantic req | yes | no | none | DEAD (provenance only) |
| `layer` | defaulted (811) | enum | yes | col | none at query time | DEAD (indexed, unread) |
| `authority` | defaulted `tribal` (812) | enum | yes | **no column** | none | DEAD |
| `language` | CKE (812) | — | yes | col | none | DEAD |
| `quality` | CKE (811) | enum — **43 fail** (`medium`, `local`) | yes | col | none | DEAD (enum drift) |
| `model`, `tokens_used` | CKE (811) | — | yes | cols | none | DEAD (provenance) |
| `routing_reason`, `prompt_version` | CKE (445) | schema.yaml optional | yes | no | none | DEAD (provenance) |
| `extraction_cost_usd` | CKE (253) | unknown field | yes | no | none | DEAD |
| `tag_validation_warnings` | CKE (153) | unknown field | yes | no | none | DEAD |
| `extraction_version`, `depth` | CKE (812) | — | yes | cols | engine reads → discards | DEAD |
| `duration_min` | CKE video (137) | — | yes | no | none | DEAD |
| `valid_to` | normalize (release notes) (173) | — | yes | col | **none — no staleness gate exists** | DEAD (the reuse-vs-derive gate the target design wants would consume this) |
| `source_mtime` | CKE freshness (778) | — | yes | no | freshness scanner (never run) | DORMANT |
| `people` | CKE + role-filter (325) | max-3 warn | yes | col+FTS | FTS-searchable only; no filter, not in answers | DEAD-ish |
| `rebuild_status` | one-off `scripts/archive/tag_legacy_notes.py` (321) | unknown field | yes | no | none — tombstone marker only | DEAD (but the de-facto S3 marker, §2.4) |
| `needs_review` | never (0) | — | — | no | `cli/overnight` expects it | **PHANTOM** |
| `last_verified` | never (0) | schema optional | — | no | none | PHANTOM |
| `content_origin`, `source_category`, `source_locator`, `routing_confidence` | never (0) | schema v2.1 fields | — | 4 cols, all empty | none | **PHANTOM** (whole routing-provenance block: modeled, columned, never populated) |
| `tool_meta` | never (0) | schema field | — | no | none | PHANTOM |
| `confidence` (float 0-1) | never as float | schema field | — | col name hijacked to store trust_level | — | PHANTOM (its column is trust_level's carrier) |
| `rfp_visible` | *derived at index build* | n/a | n/a | col | `rfp_only` filter, vault_adapter | **LIVE** — but 143 of 182 visible rows are `deprecated` (§2.3) |

**Scorecard: 12 LIVE (6 strongly — title, topics, products, client, source_type, trust_level), ~20 DEAD, 8 PHANTOM, 3 BROKEN.** The answering context is built from exactly title + client + source_type + topics[:5] + products[:3] + body. Everything else in the 30+-field contract either dies before the index, dies in the index, or was never born. This is the load-bearing-vs-decoration map the architect asked for.

### 1.3 Handshake to Audit C (extraction quality)

Fields at the handshake boundary (emitted by CKE, judged here only for *survival*, not quality): `key_facts`, `*_overlay`, `quality_score`, `entities_mentioned`, `topics/products/people` content. Audit D's finding is transport-level: whatever their quality, `key_facts` and overlays are discarded at the answer layer, so extraction-quality investment in them currently buys nothing downstream.

---

## 2. Step 2 — Vault reality census

### 2.1 The 850 vs 488 delta — fully closed

850 `.md` on disk = 848 in the note universe + 2 agent-rules files under `.claude/`. Every one of the 848 is accounted for; there is **no** "below-quality-threshold" or mystery residue category:

| Category | Count | Detail |
|---|---|---|
| Indexed | **488** | `notes` rows (post source_hash dedup) |
| Dedup losers | **325** | on-disk notes sharing `source_hash` with an indexed winner — the physical residue of the v2/v3 double-extraction and the Council-#20 re-extraction; real duplicate *files*, deliberately collapsed only in the *index* |
| Quarantine | **22** | reasons: `quality_fragment` ×20, `quality_score 8 < 25`, `quality_score 18 < 25` (Phase-1's "23" = 22 `.md` + 1 non-md file) |
| Navigation / Home / System | **12** | 00_Home 1, 02_Navigate 9 (the MOCs), 99_System 2 |
| Frontmatter parse-fail | **1** | the vault's own `CLAUDE.md` at root (not a note) |
| **Total** | **848** | ✔ exact |

**Zone census vs Council #7:** conforms. 813/848 (96%) of notes sit flat in `01_Knowledge/`; no client subfolders; `_assets` holds 11 non-md covers; there is still no `02_sources/` zone (the ADR-27 invariant names a zone that does not exist on disk — Phase-1 finding re-confirmed).

### 2.2 S0–S3 mapping of the vault as it stands today

Contract for S1 taken from `schema/models.py` (Pydantic `NoteFrontmatter`) as the brief specifies; S2 from the brief's own definition (linked, 0 unresolved, owned by a MOC).

| Lifecycle state | Notes qualifying TODAY | Evidence |
|---|---|---|
| S0 RAW (<48h) | **0** | no capture since 2026-03-27 (extraction) / 2026-04-10 (inbox inflow) |
| S1 STRUCTURED — strict contract | **0 / 813 (0%)** | universal blocker: `source_file` required-but-renamed (813); then `type` enum drift (80), `source_type` enum drift (66: `presentation` ×54, `workshop` ×9…), `quality` enum drift (43: `medium` ×38, `local` ×5), cardinality >max (3), non-string `key_facts` (1) |
| S1 after two mechanical fixes (alias `source`→`source_file`; map off-enum `type`) | **704 / 813 (87%)** | measured by re-validating each note with those two patches applied in-memory |
| S1 after full enum-mapping table (add `source_type`, `quality` maps) | ~809 / 813 (99%+) | residual = cardinality + malformed key_facts singletons |
| S2 CONSOLIDATED | **0 / 813 (0%)** | see link graph below — no note is MOC-reachable, none has an incoming link |
| S3 ARCHIVED | **0 formally; 326 de-facto tombstones** | `trust_level: deprecated` + `rebuild_status` (291 `source_inaccessible`, 35 `source_missing`) sitting in-place in 01_Knowledge; never moved, never excluded from the folder |

### 2.3 Link-graph baseline (computed from files; app never opened)

| Metric | Value |
|---|---|
| Notes with ≥1 *resolved* outgoing wikilink | **5** / 848 |
| Notes with ≥1 incoming link (01_Knowledge) | **0** — orphan rate **813/813 (100%)** |
| Unresolved link instances | **8,262** across **787** distinct targets |
| Notes with zero unresolved links | 54 (mostly link-less) |
| Knowledge notes reachable from the MOC spine | **0** |

Two structural causes, both decisive for the operating model:

1. **The MOCs contain no links.** All 9 `02_Navigate` MOCs are **dataview queries** (`FROM "01_Knowledge" ... GROUP BY product`). They render as navigation in the app but contribute zero edges to the link graph — invisible to Obsidian's graph, to orphan/unresolved audits, and to any CLI link-integrity tooling. The proposed "tree lives in links" does not yet exist *at all*; what exists is a query-driven façade.
2. **The 8,262 dangling links are the taxonomy asking to be born.** Every note carries an auto-generated `**Links:** [[topic]] [[product]]` line (validate.py `generate_links_line`); the targets are concept pages that were never created. The top-30 targets (Supply Chain Planning 497, Demand Planning 478, API Integration 432, …) cover **6,417 of 8,262 instances (78%)**. Creating ~30–80 hub notes named for these targets would mechanically convert the orphan graph into a two-level tree — the cheapest possible spine bootstrap, and it is *already named* by the existing links.

### 2.4 Index-side lifecycle interaction (what the brief's S0–S3 must reconcile with)

`confidence`(=trust_level) × `rfp_visible` in index.db:

| trust_level | rfp_visible=1 | rfp_visible=0 | Total |
|---|---|---|---|
| extracted | **39** | 177 | 216 |
| deprecated | **143** | 129 | 272 |
| | 182 | 306 | 488 |

`_compute_rfp_visible` treats `deprecated` as neither draft nor verified, so deprecated notes fall through to the source_type/doc_type rules and get marked visible; only the retrieve-time `confidence != 'deprecated'` filter saves the answering path. **Net effective RFP corpus = 39 notes (8% of index, 21% of the nominal 182).** Phase-1's "182 rfp_visible" number is nominal, not effective. Any S3 design must set `rfp_visible=0` mechanically, not rely on a downstream filter.

---

## 3. Step 3 — Hygiene scope, quantified

Affected-note lists: Appendix A (paths only, no content). Sizes: XS <½ day, S ~1 day, M days, L week+.

### 3.1 H1 — Clientless indexed notes: 258/488 (53%)

Deterministic recoverability, measured (each clientless row probed in order: frontmatter `client/*` tag or `project` field → client-alias token in `source_path` → alias token in filename/title, using `naming_config.yaml` alias groups):

| Recovery route | Notes |
|---|---|
| Frontmatter tag (`client/x`) or `project` field | 31 |
| Client token in `source_path` | 63 |
| Client token in filename/title | 108 |
| **Deterministically recoverable** | **202 (78%)** |
| Not recoverable without content reading | 56 |

**Critical nuance** — clientless is not uniformly a defect. By source zone: `60_Source_Library` 141, no-source_path 35, other 30, `50_RFP` 19, `10_Projects` 18, `30_Templates` 15. Source-library and template notes are *legitimately* client-free product knowledge; the true defects are (a) the 18 `10_Projects` + 19 `50_RFP` notes whose client context existed and was dropped (§1.1 fact 3), and (b) the schema's inability to distinguish "no client by design" from "client unknown". Overlap warning: **210 of the 258 are also deprecated** (H3) — sequence the tombstone decision first or the backfill wastes 81% of its effort.
**Remediation candidates:** deterministic backfill script from the three probes above (S) + index rebuild; declare `client: null` valid for source-library/template zones (schema note, XS); re-extract only fixes the subset whose sources still exist (see H3).

### 3.2 H2 — Mojibake client variants: 2 index pairs, 6 notes on disk

Full list (this is the complete population, not a sample):

| Corrupt form | Rows | Clean form | Rows |
|---|---|---|---|
| `WÃ¼rth` | 1 | `Würth` | 2 |
| `Å»abka` | 1 | `Żabka` | 1 |

On disk, 6 notes carry a mojibake `client:` or `title:` value. All repair via the deterministic latin-1→UTF-8 round-trip (verified in the census: both forms recover their clean twin exactly). (`Coca-Cola İçecek` is *correct* Turkish, not mojibake — display-only issue in cp1252 consoles.)
**Remediation:** XS — 6 file edits + index rebuild; add the round-trip check to any future ingest gate so it can't regress.

### 3.3 H3 — Deprecated / source-lost notes: 326 on disk, 272 indexed

Producer: one-off `scripts/archive/tag_legacy_notes.py` after the 2026-03 MyWork restructure orphaned the recorded `source_path`s. Composition: `source_inaccessible` 291, `source_missing` 35. Does the recorded source resolve **today**: **0 of 326** (270 missing at recorded path, 21 point into the excluded OneDrive zone — unverifiable by policy, 35 have no path recorded). Basename-level probe against today's MyWork tree: **63** of the lost sources exist under a *new* path (re-linkable / re-extractable); **203** are locally gone for good.

| Sub-class | Count | Realistic remediation |
|---|---|---|
| Source findable by basename in MyWork | 63 | re-link `source_path` (deterministic-ish, S) or re-extract (only if W2 restarts) |
| Source gone locally | 203 | keep content, formalize as S3 tombstone (provenance honestly marked lost) — or delete; **operator decision** |
| Path in excluded zone | 21 | policy: treat as unverifiable; tombstone |
| No path recorded | 35 | tombstone |

Note the schema drift: `deprecated` — the value carried by 40% of the vault — is **not in `schema.yaml`'s `trust_level` allowed values** (verified/extracted/generated/draft). The most load-bearing state in the system is un-modeled.

### 3.4 H4 — Malformed / off-enum literals

- Malformed `type` literal: exactly **1** — `meeting|presentation|rfp|documentation` (index id 645, `lenzing_inventory.md`): the LLM returned the prompt's option list verbatim.
- Off-enum populations (schema-drift, not corruption): `type` 80 (incl. `unknown` ×37, `documentation` ×14, `questionnaire` ×9), `source_type` 66 (incl. `presentation` ×54), `quality` 43 (`medium` ×38, `local` ×5).
**Remediation:** one mapping table applied at a chosen seam (§4.3) fixes all four classes at once — this is the same fix as the S1 lenient→99% jump (§2.2). XS–S.

### 3.5 H5 — Source-path rot across the whole index (context for trust)

All 488 indexed notes: source exists 69 (14%) · missing 219 (45%) · excluded-zone path 165 (34%) · empty 35 (7%). Claim→cite verification against original sources is currently possible for 14% of the corpus. This is the "rotten provenance" floor under R1's verify stage.

---

## 4. Step 4 — Taxonomy canonicalization scope (W5)

### 4.1 Canonical list vs actual population

Canonical (`schema/data/products.yaml`): 22 top-level products + 36 sub-products, plus display-name/alias lookup; separately `extractor/data/product_aliases.yaml` (display-name normalizer) and the tag-side `_TAG_ALIASES` in post_process.py — **three disjoint normalization systems, none enforced in the pipeline** (`resolve_product_key` has zero call sites outside `schema/__init__` exports; only `expand_product_query` is used, at query time).

Population (813 notes, `products` frontmatter): **1,975 instances of 322 distinct terms.**

| | Instances | Distinct terms |
|---|---|---|
| Resolve through existing machinery (schema display-names/aliases; 48 only via extractor aliases) | 1,231 (62%) | 21 |
| Unresolved | **744 (38%)** | **301** |

### 4.2 Mapping-table size and shape

Top-40 unresolved terms cover 440/744 instances (59%); top-60 cover 65%; the tail is ~240 near-singletons. The unresolved set splits into three policy classes:

1. **Non-BY technology/competitor terms that leaked past the exclusion filter** — Azure (177), Snowflake (36), SAP\* (29 across variants), Power BI (7), Dynamics 365 (4)… ≈ **270 instances**. Per the products-field policy (post_process `filter_products`) these belong in `entities_mentioned`, not `products`. Mapping action: *move/drop*, not canonicalize. (They leaked because 253 of the notes predate the exclusion list's current coverage.)
2. **BY variants needing aliases** — Platform Data Cloud (34+5), Workforce Management (19), Demand-and-Supply-Planning family (~40 across a dozen spellings), IBP variants, JDA legacy names… ≈ **60–80 terms**. Note: `_TAG_ALIASES` already contains most of these mappings — for *tags*, where nothing consumes them. The knowledge exists in the codebase; it's wired to the dead surface.
3. **Ambiguous/junk singletons** (~240 terms, ~260 instances) — "Planning Engine", "CDP", "TENCEL" (client material, not a product)… Mapping action: review-or-drop list; do not hand-craft 240 aliases.

**Realistic mapping-table build: ~80 alias rows + a drop/move list — not 300.** Plus the comma-split repair: `IDSP (Integrated Demand, Supply & Inventory Planning)` splits into two garbage terms at the index's comma-join/comma-split round trip; storing JSON in `notes.products` (the reader already prefers JSON — `_parse_json_field` tries `json.loads` first) fixes it without touching the reader.

### 4.3 Enforcement seam — evidence per candidate

| Seam | Evidence for | Evidence against | Regression-proofness |
|---|---|---|---|
| (a) Extraction post-process | Machinery exists (`normalize_product_names`); fixes notes at birth | Already failed once — alias file too small vs unbounded LLM variance; fixes only *future* notes; CKE is the component Audit C owns | Weak — every new LLM phrasing regresses it |
| (b) Ingest (vault write) | Single writer (ADR-27) is the natural contract gate; would make *vault* canonical | Ingest currently validates nothing (§1.1); dormant process; doesn't fix 813 existing notes without a rewrite pass (vault writes — bigger blast radius) | Medium |
| (c) Index build (`_index_cke_notes`) | Single choke point every consumer reads through; fixes ALL 813 notes on next rebuild with zero vault writes; `resolve_product_key` importable right there; unknown terms loggable to `taxonomy_review.yaml` (mechanism exists) | Vault frontmatter stays raw — Obsidian dataview MOCs still see uncanonical terms | **Strong for retrieval** — cannot regress while rebuild applies it |

**Input to decision:** (c) now — it is the only seam that retro-fixes the whole corpus without touching a single note and cannot be bypassed by any producer; add (a)-side alias sync for cosmetic vault truth later; (b) becomes the gate when the S1 promotion job (operating model element 3) exists — at which point canonical-in-frontmatter becomes part of the S1 contract and (c) reduces to a safety net.

---

## 5. Step 5 — Operating-model evaluation (element-by-element, strict)

| # | Brief element | Evidence verdict | Grade (input, not decision) |
|---|---|---|---|
| 1 | Tree lives in links, not folders; flat folders stay; ROOT→domain→topic→notes ≤3 hops | Flat-folder half **HOLDS** (96% of notes in one flat zone; Council #7 conform). Link-tree half: **0% exists** — 100% orphans, 0 MOC-reachable notes, MOCs are dataview (contribute no edges, invisible to link audits). But feasibility is *good*: 78% of the 8,262 dangling links point at just 30 taxonomy hubs — the spine's node list is already named by the data | **AMEND**: (i) spine hubs must be *generated from the existing dangling-link taxonomy* (30–80 notes), not authored free-form; (ii) MOCs must become static-wikilink notes (or dual dataview+links) or every CLI/graph audit stays blind; (iii) "≤3 hops" is then achievable by construction: ROOT→hub→note = 2 |
| 2 | S0–S3 frontmatter state machine; S0 48h max age; S1 = valid contract | State machine maps cleanly onto real states (S3 already exists de-facto as 326 tombstones). BUT: S1-as-written = 0% pass — the contract itself is broken by the emitter (source_file rename), and its most load-bearing value (`deprecated`) isn't in the schema. 48h S0 SLA vs actual cadence: capture has been dead for 3 months (last ingest 2026-03-27, last inbox inflow 2026-04-10, 75-file backlog); an age-SLA with no running mechanism is a dead rule on arrival | **AMEND**: (i) contract-reconciliation is a *prerequisite* (decide: template emits `source_file`, or model renames to `source` — one line either way, plus enum-mapping table; measured yield 0%→87%→99%); (ii) add `deprecated`/S3 to the schema; (iii) 48h SLA only alongside a scheduled enforcement job (see #3), not as frontmatter aspiration |
| 3 | Promotion = CC job with hard validator gates, "held by mechanism, not memory" | Directionally the *best-supported* element: the estate's only living automation is the scheduled nightly conformance loop (N5), while every passive/event-driven surface died with 0 rows (routing_feedback, content_signatures, facts…). "Mechanism over memory" is precisely what the evidence prescribes — but the gate must run *scheduled*, and gates need the repaired contract or they reject 100% and get bypassed like validate_frontmatter was | **RATIFY with dependency** — blocked on element-2 amendment; specify scheduled (not on-demand) execution |
| 4 | Official Obsidian CLI (GA 1.12.4) as mechanical layer; Python for bulk | **Present on this machine**: app `1.12.4` at `%LOCALAPPDATA%\Programs\obsidian\Obsidian.exe`, CLI entry `Obsidian.com` on PATH (not executed — policy). Feasibility EXISTS-UNTESTED. Caveats from vault reality: CLI link-audits (orphans/unresolved/deadends) will report exactly what §2.3 found — and will *not* see dataview relationships, so they under-report navigation until element-1's amendment lands; CLI drives the running app (session dependency for automation). kepano/obsidian-skills: applicable as the CC-side skill layer over the same CLI, not installed in `~/.claude/skills` today — adopt after the CLI is validated, not before | **RATIFY** (with the dataview-blindness caveat; keep Python file-ops as the bulk path per the brief) |
| 5 | No big-bang: measure → author spine → gate new → backfill per domain slice | Shape matches the evidence (and this audit *is* the measure step). Missing from the brief: sizing and ordering. Backfill universe is NOT 850: subtract 325 dedup losers (disposition decision), 326 tombstones (S3 first), 22 quarantine → **~487 live notes** are the real S1/S2 backfill target, of which ~87% pass S1 after mechanical fixes | **AMEND**: insert "S3 triage + dedup-loser disposition" *before* backfill; without it, 81% of the clientless-backfill effort and 40% of all promotion effort is spent on tombstones |

**What the brief omits entirely (must-address list):**
1. **index.db is absent from the model.** The operating model describes the vault; every answering consumer reads index.db. The model must state the authority chain — frontmatter is truth, index.db is a derived cache rebuilt after every batch mutation, dataview/Bases are presentation — and make index-rebuild a mandatory post-step of every lifecycle transition. (Obsidian 1.12's native Bases could replace dataview MOCs, but nothing in the chain reads or writes Bases; treat as presentation-layer option only.)
2. **S0–S3 × `rfp_visible` × `trust_level` interplay.** Today S3-equivalent notes leak into rfp_visible=1 (143 rows) and are saved only by a retrieve-time filter (§2.4). The state machine must own these: S3 ⇒ `rfp_visible=0` at index build; S1/S2 ⇒ trust_level transitions (extracted→verified) rather than a parallel unmodeled axis.
3. **Migration cost quantified** (it wasn't in the brief): contract repair XS–S; client backfill S; mojibake XS; hub generation S–M; 326-tombstone sweep S plus one operator decision; dedup-loser disposition = decision + XS script; promotion job M. No single item is L; the risk is ordering, not size.

---

## 6. Backlog-seed table

| Seed | Goal (functional) | Evidence | Depends on | Size gut-feel | Decision required first? |
|---|---|---|---|---|---|
| V1 Contract reconciliation | S1 contract passable: template↔model agree on `source_file`; enum-mapping table for type/source_type/quality; add `deprecated` (S3) to schema | §1.1-1, §2.2 (0%→87%→99% measured) | — | XS–S | **Yes** — which side wins the rename (recommend: template emits `source_file`; keep `source` for compat one cycle) |
| V2 S3 tombstone sweep | 326 deprecated notes formally archived; `rfp_visible=0` forced at index build; effective-RFP corpus honest | §2.4 (143 leak), §3.3 | V1 (schema knows S3) | S | **Yes** — archive vs delete; and fate of 63 re-linkable sources |
| V3 Dedup-loser disposition | 325 duplicate files resolved (delete losers / move aside); disk truth matches index truth | §2.1 | — | XS script | **Yes** — deletion needs explicit approval (core invariant #3) |
| V4 Client backfill | 202 deterministically recoverable clients written back; `client: null` declared valid for source-library/template zones | §3.1 | V2 first (210/258 overlap) | S | No (script is deterministic; approve the mapping list) |
| V5 Mojibake repair | 2 pairs + 6 notes fixed via latin-1→UTF-8 round trip; regression check in future gate | §3.2 | — | XS | No |
| W5 Product canonicalization | ~80 alias rows + drop/move list; enforce at index build via `resolve_product_key`; JSON storage for list columns (comma-split fix) | §4 | — | M | **Yes** — seam ruling (evidence favors index-build now, ingest-gate later) |
| OM1 Spine generation | 30–80 hub notes generated from top dangling-link targets; MOCs gain static links; ≤3-hop tree real | §2.3 (78% coverage by top-30) | W5 helps (canonical hub names) | S–M | Ratify element 1 amendment |
| OM2 Promotion job | Scheduled CC job promoting S0→S1→S2 with validator gates; the *first* mechanism-held loop on the vault | §5 element 3, N5 precedent | V1, OM1 | M | Ratify elements 2+3 |
| OM3 Answer-layer uplift | Stop discarding `key_facts`/overlays at answer build (or stop paying to extract them) — join decision with Audit C | §1.2 (DEAD rows) | R1 design | M | Architect (R1 scope) |
| OM4 Index-in-the-model | Operating model names index.db as derived cache; rebuild wired into every lifecycle transition | §5 omission 1 | — | XS (doc) + S (wiring) | Ratification |

---

## Appendix A — affected-note lists

Lists carry paths/filenames only (no content excerpts; client names appear only as path tokens or recovery candidates, per Wave-2 rules). Full machine-readable census (all categories incl. 325 dedup-loser paths) reproducible via the read-only script preserved in the session record; the two decision-relevant lists follow inline.

<details>
<summary>A.1 Clientless indexed notes (258) with per-note recovery class — expand</summary>

| Note (filename) | Recovery | Recovered client candidate |
|---|---|---|
| 1_Demo2Win_Exercise_Packet.md | NOT RECOVERABLE | — |
| 20240304_CMFP_Intro.md | filename/title | Internal |
| 2026-03-22_blueyonderbrandguidelines202511_c4af.md | filename/title | Internal |
| 2026-03-22_index_fc7e.md | NOT RECOVERABLE | — |
| 2026-03-22_machinelearningdemandedgereality_9627.md | NOT RECOVERABLE | — |
| 2026-03-22_synthesis_356d.md | NOT RECOVERABLE | — |
| 2026-03-22_wmsbestpracticesguide_ffa0.md | NOT RECOVERABLE | — |
| 2026-03-23_pepsi_emea_discovery_call_832d.md | source_path | PepsiCo |
| 2026-03-27_20251003rossmanncybersecuritysession_52cc.md | project-field | vault_rebuild |
| 2026-03-27_230629_bsc_user_stories_3e9d.md | project-field | vault_rebuild |
| 2026-03-27_blue_yonder_cloud_services_standards_110_d89a.md | project-field | vault_rebuild |
| 2026-03-27_blue_yonder_general_reference_architecture_6e0c.md | project-field | vault_rebuild |
| 2026-03-27_blue_yonder_iso_2700127701_certificate_833e.md | project-field | vault_rebuild |
| 2026-03-27_blue_yonder_sap_integration_overview_5fda.md | project-field | vault_rebuild |
| 2026-03-27_cfsstatementsnoteslenzingar22_dd63.md | project-field | vault_rebuild |
| 2026-03-27_cgcorporategovernancereportlenzingar22_05aa.md | project-field | vault_rebuild |
| 2026-03-27_cpycompanylenzingar22_6600.md | project-field | vault_rebuild |
| 2026-03-27_cpycompanylenzingar23_6679.md | project-field | vault_rebuild |
| 2026-03-27_create_a_revenue_and_profit_chart_for_the_past_5_12cc.md | project-field | vault_rebuild |
| 2026-03-27_do_not_use_lenzingby_poc_sowop0276731_v10_b998.md | project-field | vault_rebuild |
| 2026-03-27_dspbaseeffortestimationplan_e6a2.md | project-field | vault_rebuild |
| 2026-03-27_entirelenzingar22_d638.md | project-field | vault_rebuild |
| 2026-03-27_entirelenzingar23_f9bf.md | project-field | vault_rebuild |
| 2026-03-27_entirelenzingar24_cfb8.md | project-field | vault_rebuild |
| 2026-03-27_factsheet_16cb.md | project-field | vault_rebuild |
| 2026-03-27_laginvestorpresentationhj2023_e143.md | project-field | vault_rebuild |
| 2026-03-27_lenzingby_poc_sowop0276731_v20_a753.md | project-field | vault_rebuild |
| 2026-03-27_lenzing_2022_4168.md | project-field | vault_rebuild |
| 2026-03-27_lenzing_ag_2024_annual_report_updated_summary_and_6f62.md | project-field | vault_rebuild |
| 2026-03-27_lenzing_ag_annual_report_2024en_0aa8.md | project-field | vault_rebuild |
| 2026-03-27_lenzing_ag_investorpresentationfy2024_5a9b.md | project-field | vault_rebuild |
| 2026-03-27_lenzing_bcg_analysis_d573.md | project-field | vault_rebuild |
| 2026-03-27_mgrmanagementreportlenzingar22_b335.md | project-field | vault_rebuild |
| 2026-03-27_mgrmanagementreportlenzingar23_b07c.md | project-field | vault_rebuild |
| 2026-03-27_neom_action_plan_to_finish_document_fd7c.md | project-field | vault_rebuild |
| 2026-03-27_not_use_blue_yonder_response_to_company_name_rfp_2026xxxx_202601_58e2.md | project-field | vault_rebuild |
| 2026-03-27_production_plants_0681.md | project-field | vault_rebuild |
| 2026-03-27_sprint_planning_8c71.md | project-field | vault_rebuild |
| 2026-03-27_stat_fcst_exercise_assessment_by_dbf2.md | project-field | vault_rebuild |
| 2_Demo2Win_Virtual_Reference_Cards.md | NOT RECOVERABLE | — |
| 3_Demo2Win_Student_Template.md | filename/title | Internal |
| 5_Takeways.md | filename/title | Internal |
| Actors_Procedures_Process_ProcedureMapping.Lighthouse_-_Cognitive_Shorts-20241017_073106-Meeting_Recording.md | source_path | Internal |
| Adeo_Data_Mappibg.md | filename/title | Internal |
| Adeo_Data_Mappings.md | filename/title | Internal |
| Adidas_Demo_-_12.4.23_FINAL.md | filename/title | Internal |
| AI_ML_Christian_Haag-Barcelona_2024_Presentation.md | NOT RECOVERABLE | — |
| ALM_Day#1_Lighthouse_-_Cognitive_Shorts-20250210_130230-Meeting_Recording.md | source_path | Internal |
| Andy.md | filename/title | Internal |
| Anishka.md | filename/title | Internal |
| API - BDM Ingestion.md | NOT RECOVERABLE | — |
| API_-_BDM_Ingestion.md | NOT RECOVERABLE | — |
| API_BDM_csv_data.md | NOT RECOVERABLE | — |
| ARB_Planning_Architecture_Reivew_(monthly)-20230801_110344-Meeting_Recording.md | filename/title | Internal |
| ARB_Review_-_MDAP_as_a_Service_(MaaS)-20220921_010854.md | filename/title | Internal |
| AutomationTestCases_Part_2_Lighthouse_-_Cognitive_Shorts-20250205_130157-Meeting_Recording.md | source_path | Internal |
| BDM_Day#1_Lighthouse_-_Cognitive_Shorts-20241024_073106-Meeting_Recording.md | source_path | Internal |
| BDM_Day#2_Lighthouse_-_Cognitive_Shorts-20241025_073106-Meeting_Recording.md | source_path | Internal |
| BDM_Day#3_Temporal_Curation_Lighthouse_-_Cognitive_Shorts-20241028_083109-Meeting_Recording.md | source_path | Internal |
| BH_Deep_Meta-Learning.md | filename/title | Internal |
| BH_Snowflake_Data_Story_(Storyboard).md | filename/title | Internal |
| Blue Yonder Brand Guidelines 2025.1.1.md | source_path | Internal |
| Blue Yonder Platform Services - Analytics.md | source_path | Internal |
| Blue Yonder Platform v3.0 Service Description.md | filename/title | Internal |
| BlueYonder-Powerpoint-Template_2025-ConfidentialFooter-usecases.md | source_path | Wurth |
| BlueYonder_StandardEntities.md | filename/title | Internal |
| Blue_Yonder_&_Snowflake_Data_Sharing_&_Architecture.md | filename/title | Internal |
| Blue_Yonder_(Cloud_Services)_-_2024_(July)_Type_2_SOC_1_-_Report.md | filename/title | Internal |
| Blue_Yonder_(Cloud_Services_&_Spectrum)_-_2025_Type_2_SOC_2_-_Report.md | filename/title | Internal |
| Blue_Yonder_(Heritage)_-_2025_(Oct)_Type_2_SOC_1_-_Report.md | filename/title | Internal |
| Blue_Yonder_-_SAP_Template_2.md | filename/title | Internal |
| Blue_Yonder_2023_SOC_1_Type_2_-_Report.md | filename/title | Internal |
| Blue_Yonder_2023_SOC_2_Type_2_-_Report.md | filename/title | Internal |
| Blue_Yonder_Brand_Guidelines_2025.1.1.md | NOT RECOVERABLE | — |
| Blue_Yonder_Corporate_Presentation_Deck.md | NOT RECOVERABLE | — |
| Blue_Yonder_Customer_Security_Measures_3.0.md | source_path | Rossmann |
| Blue_Yonder_ISO22301.md | filename/title | Internal |
| Blue_Yonder_ISO27001_and_ISO27701.md | filename/title | Internal |
| Blue_Yonder_Platform_Services_-_Analytics.md | filename/title | Internal |
| Blue_Yonder_Platform_Training_-_15-17_October_2025.md | filename/title | Internal |
| Blue_Yonder_Platform_v3.0_Service_Description.md | filename/title | Internal |
| Blue_Yonder_Responses_Lenzing_Forecast_Exercise.md | source_path | Lenzing |
| Blue_Yonder_Response_API_Checklist.md | NOT RECOVERABLE | — |
| Blue_Yonder_Response_to_SGDBF_Architecural_requirements.md | source_path | Saint-Gobain |
| Blue_Yonder_Security_Whitepaper.md | filename/title | Internal |
| Blue_Yonder_sustainability_Pierre_Farbre.md | filename/title | Internal |
| Blue_Yonder_Warehouse_Management_Architecture_v2.md | filename/title | Internal |
| BYPlatform-Architecture.md | filename/title | Internal |
| BY_SaaS_Migration_Questionnaire_SCPO_V1.3_Michelin.md | source_path | Michelin |
| CDAR-Logical_Model_-_Lighthouse_-_Cognitive_Shorts-20250605_123320-Meeting_Recording.md | NOT RECOVERABLE | — |
| CDAR_template_-_Lighthouse_-_Cognitive_Shorts-20250522_123057-Meeting_Recording.md | source_path | Internal |
| CDP_Architecture_Lighthouse_-_Cognitive_Shorts-20240927_073123-Meeting_Recording.md | filename/title | Internal |
| CDP_DataModelling_BYDM_WB_Lighthouse_-_Cognitive_Shorts-20241004_123036-Meeting_Recording_1.md | filename/title | Internal |
| CDP_Model_Algorithms_Lighthouse_-_Cognitive_Shorts-20250116_130108-Meeting_Recording.md | filename/title | Internal |
| CDP_PartialWeeks_Lighthouse_-_Cognitive_Shorts-20250109_073310-Meeting_Recording.md | source_path | Internal |
| CDP_Pre-Sales_Functional_Training.md | filename/title | Internal |
| Challenge_Yourself_Action_Book.md | NOT RECOVERABLE | — |
| chatgpt-prompt.md | NOT RECOVERABLE | — |
| Clicks_VAQuestionnaire_05282025.md | source_path | Clicks |
| Cloud_Services_Standards_9.0.md | filename/title | Internal |
| CMFP-April8th-Workshop-BYOrchestrator_Sample_Questions.md | filename/title | Internal |
| CMFP_Pre-Sales_Functional_Training.md | filename/title | Internal |
| CMFP_report._Lighthouse_-_Cognitive_Shorts-20250203_180322-Meeting_Recording.md | source_path | Internal |
| Cognitive Friday S4E1 - Journey to the Cloud.md | filename/title | Internal |
| Cognitive Friday S4E1 J2CC.md | filename/title | Internal |
| Cognitive Friday Season 2 - Product Analytics Program.md | filename/title | Internal |
| Cognitive_Demand_Data_Requirements.md | filename/title | Internal |
| Cognitive_Demand_Planning_Help.md | filename/title | Internal |
| Cognitive_Demand_Planning_Messaging_Guide_Final_August_2023_Challenger_Modified.md | filename/title | Internal |
| Cognitive_Demand_Planning_Questions.md | filename/title | Internal |
| Cognitive_Training_Attendee_List.md | filename/title | Internal |
| Consensus_Planning_Workflow_Lighthouse_-_Cognitive_Shorts-20250127_125052-Meeting_Recording.md | source_path | Internal |
| CPI.md | NOT RECOVERABLE | — |
| CPI8.csv.md | NOT RECOVERABLE | — |
| CPI88.md | NOT RECOVERABLE | — |
| Create_the_custom_entities_Lighthouse_-_Cognitive_Shorts-20241007_074701-Meeting_Recording.md | source_path | Internal |
| Customer_Discovery_Questions.md | NOT RECOVERABLE | — |
| Customer_Security_Measures.md | filename/title | Internal |
| Customer_Security_Measures_2_0_0_0.md | filename/title | Internal |
| Customer_Value_Proposition_Matrix.md | filename/title | Veronesi |
| Data Functions.md | NOT RECOVERABLE | — |
| Data_Functions.md | NOT RECOVERABLE | — |
| Data_Requirements.md | filename/title | Internal |
| Deep_Meta_Learning.md | filename/title | Internal |
| Demand and Supply Planning v1.2 Service Description.md | NOT RECOVERABLE | — |
| demandChannels_13022024_102953150506.md | filename/title | Internal |
| Demand_and_Supply_Planning_v1.2_Service_Description.md | filename/title | Internal |
| Demo_Environments.md | filename/title | Internal |
| DG_Demo_script_-_enablement.md | filename/title | Internal |
| DMS_-_Ingestion_Service.md | filename/title | Internal |
| DOTERRA_Demo_-_3.20.24_FINAL.md | filename/title | Internal |
| E2E-Automated-Deployment-Framework_Lighthouse_-_Cognitive_Shorts-20250206_130335-Meeting_Recording.md | source_path | Internal |
| Enterprise Data Orchestration Pitch Deck '25.md | NOT RECOVERABLE | — |
| Enterprise_Data_Orchestration_Pitch_Deck.md | filename/title | Internal |
| Enterprise_Data_Orchestration_Pitch_Deck_'25.md | NOT RECOVERABLE | — |
| Episode_1_-_Platform_Overview_and_Foundation_Services.md | filename/title | Internal |
| Evaluation_process_and_dashboards_Lighthouse_-_Cognitive_Shorts-20250117_125803-Meeting_Recording.md | source_path | Internal |
| ExplainabilityChartData.md | filename/title | Internal |
| ExploringIngestionServices.md | filename/title | Internal |
| extCausalConsumerPriceIndexesCityLevels_13022024_102954432172.md | NOT RECOVERABLE | — |
| extCausalEventses_13022024_102955030282.md | NOT RECOVERABLE | — |
| extCausalMedianIncomeses_13022024_102959996476.md | NOT RECOVERABLE | — |
| extCausalPopulationGrowthByCountries_13022024_103000252473.md | NOT RECOVERABLE | — |
| extCausalProductsByCountries_13022024_102958897770.md | NOT RECOVERABLE | — |
| extCausalTradePromotionses_13022024_102955503434.md | NOT RECOVERABLE | — |
| extCausalWeathers_13022024_102956012641.md | NOT RECOVERABLE | — |
| extCPICountries_1.md | NOT RECOVERABLE | — |
| Extension and Ingestion click Script (SCPO).md | NOT RECOVERABLE | — |
| Extension_and_Ingestion_click_Script_(SCPO).md | NOT RECOVERABLE | — |
| FAAS_Day#1_Lighthouse_-_Cognitive_Shorts-20250318_125743-Meeting_Recording.md | source_path | Internal |
| FAAS_Day#2_Lighthouse_-_Cognitive_Shorts-20250321_125946-Meeting_Recording.md | source_path | Internal |
| Financial_Questionnaire_Lenzing.md | source_path | Lenzing |
| Financial_Questionnaire_Lenzing_2025.md | source_path | Lenzing |
| gemini-prompt-v2.md | NOT RECOVERABLE | — |
| gemini-prompt.md | NOT RECOVERABLE | — |
| Generic_Cognitive_Planning_Reference_Material.md | filename/title | Internal |
| GRE_CMFP.md | filename/title | Internal |
| GTM_Cognitive_Training_v10.md | filename/title | Internal |
| GTM_Cognitive_Training_v10_-_Challenger_Slides.md | filename/title | Internal |
| histShipments_13022024_102956706377.md | NOT RECOVERABLE | — |
| Horizon_Web_-_How_To_Access.md | filename/title | Internal |
| Infrastructure_Recommendations_for_NEOM_WMS_OnPremise.md | source_path | NEOM |
| Introduction_to_CDP_Lighthouse_-_Cognitive_Shorts-20240925_073323-Meeting_Recording.md | source_path | Internal |
| itemLocationCustomers_13022024_102959395437.md | NOT RECOVERABLE | — |
| itemLocations_13022024_102959701502.md | filename/title | Internal |
| items_13022024_102953839045.md | filename/title | Internal |
| KYP_'23_Spring_Edition,_EP_#1_-_Platform_Overview_and_Foundation_Services.md | filename/title | Internal |
| KYP_'23_Spring_Edition,_EP_#2_-_Data_Services.md | filename/title | Internal |
| Lenzing_Platform_UseCase.md | source_path | Lenzing |
| LifeScience_session1v2.md | filename/title | Internal |
| Lighthouse_-_Cognitive_Shorts--Day#43-Process_Orchestration-Day#4-20241126_073116.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Copy_Inheritance-Day#1-20250212_133949-Meeting_Recording.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Copy_Inheritance-Day#2-20250213_125236-Meeting_Recording.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#10-Exploring_the_types_of_ingestion_service_and_Ingesting_data_into_Platform_Data_Cloud_-_Day#1-20241010_073249.md | filename/title | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#11-Exploring_the_types_of_ingestion_service_and_Ingesting_data_into_Platform_Data_Cloud_-_Day#2-20241014_073044.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#14-_Pre-Curation,_Post_Curation_and_Generic_Plugins_-20241023_073222-Meeting_Recording.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#36-Batch_Ingress-20241108_073125.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#38-_PDC-CDP_-_Batch_Scheduling_-20241112_073146.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#41-Process_Orchestration-Q&A-Day#2-20241119_073112.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#42-Process_Orchestration-Day#3-20241125_073112.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#44-Process_Orchestration-Day#5-20241127_073102.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#45-Exception_Workflow-20241209_073049.md | source_path | Internal |
| Lighthouse_-_Cognitive_Shorts-Day#47-MaaS-20241211_073132.md | source_path | Internal |
| Localhost_Architecural_requirements.md | source_path | Saint-Gobain |
| Localhost_Architecural_requirements_BY_RESPONSE.md | source_path | Saint-Gobain |
| Localhost_Oribco_IT_Questionnaire.md | source_path | Orbico |
| locations_13022024_102954078462.md | filename/title | Internal |
| Luminate_Portal_Day#1_Lighthouse_-_Cognitive_Shorts-20240930_073210-Meeting_Recording.md | source_path | Internal |
| Luminate_Portal_Day#2_Lighthouse_-_Cognitive_Shorts-20241001_073053-Meeting_Recording.md | source_path | Internal |
| Maas-Command_Center_Lighthouse_-_Cognitive_Shorts-Day#46-20241210_073123-Recording_2.md | source_path | Internal |
| MaaS_Guardrails_Lighthouse_-_Cognitive_Shorts-20250508_122803-Meeting_Recording.md | source_path | Internal |
| MaaS_HighLevelOverview_Lighthouse_-_Cognitive_Shorts-Day#46-20241210_073123-Recording_1.md | source_path | Internal |
| MachineLearning_DemandEdge_Reality.md | filename/title | Internal |
| MDAP_As_A_Service(MaaS)__Lighthouse_-_Cognitive_Shorts--Day#46-20241210_073123-Recording_3.md | source_path | Internal |
| MeetingNotes_Discovery_Workshop_2025-01.md | NOT RECOVERABLE | — |
| Mfg_Barcelona_Cognitive_Demand_Planning_Functional_Training.md | filename/title | Internal |
| MFG_Cognitive_-_ML_Studio___Workflow___RaaS-20240321_114221-Meeting_Recording.md | filename/title | Internal |
| Michelin_-_Post_Design_Thinking_-_IT_Session_29092025.md | source_path | Michelin |
| Michelin_DesignThinking_Deck_08072025.md | source_path | Michelin |
| Model_configuration_script.md | filename/title | Internal |
| MQV_Lighthouse_-_Cognitive_Shorts-20250121_125347-Meeting_Recording.md | source_path | Internal |
| Navigate_to_SNA_through_Luminate_portal_Logical_Data_Model_Lighthouse_-_Cognitive_Shorts-20241015_073130-Meeting_Recording.md | source_path | Internal |
| Nick.md | filename/title | Internal |
| Noatum_Tech_presentation_27oct2023.md | filename/title | Internal |
| ODA_Walkthrough_Lighthouse_-_Cognitive_Shorts-20250115_125935-Meeting_Recording.md | source_path | Internal |
| Oracle_Mapping_Matrix.md | filename/title | Internal |
| payload_Walmart.md | NOT RECOVERABLE | — |
| pepsi emea discovery call.md | NOT RECOVERABLE | — |
| pepsi_emea_discovery_call.md | NOT RECOVERABLE | — |
| pipeline_config.md | filename/title | Internal |
| Planning - WMS using BY Platform.md | filename/title | Internal |
| Planning_-_WMS_using_BY_Platform.md | filename/title | Internal |
| Platform Overview.md | filename/title | Internal |
| PlatformDataCloud_v2023.1_v3_BY_Training_Guide.md | filename/title | Internal |
| Platform_and_Cognitive_-_High_Level_Architecture.md | filename/title | Internal |
| Platform_Editedv2.md | filename/title | Internal |
| Platform_Overview.md | filename/title | Internal |
| Platform_Usage_by_Product.md | filename/title | Internal |
| PMC_Tool.md | filename/title | Internal |
| prep_SGDBF_20260316_131409.md | filename/title | Saint-Gobain |
| prep_SGDBF_20260320_210603.md | filename/title | Saint-Gobain |
| prep_SGDBF_20260320_210811.md | filename/title | Saint-Gobain |
| prep_SGDBF_20260320_235009.md | filename/title | Saint-Gobain |
| prodLocCustMeasures_13022024_102957700706.md | NOT RECOVERABLE | — |
| QATAR_DF.md | NOT RECOVERABLE | — |
| Quarterly_Review_Template.md | NOT RECOVERABLE | — |
| Racetrac_Cognitive_Feedback.md | NOT RECOVERABLE | — |
| RBAC-_Lighthouse_-_Cognitive_Shorts-20250401_122359-Meeting_Recording.md | source_path | Internal |
| Reporting_As_A_Service(RaaS)_Lighthouse_-_Cognitive_Shorts-20250129_130125-Meeting_Recording.md | source_path | Internal |
| sampe-chatgpt-data.md | filename/title | Internal |
| SAP_Mapping_Matrix.md | filename/title | Internal |
| SAP_Mapping_Matrix_2.md | filename/title | Internal |
| SCPO_Ingestion_data_payload.md | NOT RECOVERABLE | — |
| Security_Slides_Edited.md | filename/title | Internal |
| session_cognitive-friday-s4e1-j2cc.md | filename/title | Internal |
| session_cognitive-friday-season-2---product-analytics-with.md | filename/title | Internal |
| SGDBF-Architecural_requirements.md | source_path | Saint-Gobain |
| Sleep_Country_D&F_Demo_3.12.24.md | filename/title | Internal |
| Sleep_Country_Demo_Working.md | filename/title | Internal |
| Slides_for_Integration.md | NOT RECOVERABLE | — |
| Snowflake sharing click script.md | NOT RECOVERABLE | — |
| Snowflake-to-Snowflake.md | NOT RECOVERABLE | — |
| Snowflake_sharing_click_script.md | NOT RECOVERABLE | — |
| Training_Presenations_Skills_1.md | NOT RECOVERABLE | — |
| Training_Presentation_Skills-20231127_110402-Meeting_Recording.md | filename/title | Internal |
| Use_case_per_BY_Platform_service.md | filename/title | Internal |
| Veronesi - Tech Track - 10th of December.md | source_path | Veronesi |
| Veronesi_-_Minimum_Data_Requirements.md | source_path | Veronesi |
| Veronesi_-_Tech_Track_-_10th_of_December.md | filename/title | Veronesi |
| Veronesi_Template_PPT.md | source_path | Veronesi |
| WMS_-_PDC_-_Reference_Document.md | filename/title | Internal |
| WMS_Best_Practices_Guide.md | NOT RECOVERABLE | — |
| Wurth_Blue_Yonder_Platform_Service_Description.md | filename/title | Wurth |
| Wurth_Cloud_Approval_Application_Template.md | source_path | Wurth |
| _Blue Yonder Pitch Deck - April 2025.md | source_path | Internal |
| _Blue_Yonder_Pitch_Deck_-_April_2025.md | NOT RECOVERABLE | — |
| _OLD_FILES.md | NOT RECOVERABLE | — |
| _Training_Presentation_Skills.md | filename/title | Internal |

</details>

<details>
<summary>A.2 Deprecated / source-lost notes (326) with rebuild_status and source-path status today — expand</summary>

| Note (path under vault) | rebuild_status | source_path status |
|---|---|---|
| 01_Knowledge/1_Demo2Win_Exercise_Packet.md | source_inaccessible | missing |
| 01_Knowledge/202306_BSC_FRS_Questionnaire.md | source_inaccessible | missing |
| 01_Knowledge/2023_March_BY_WMS_HWSizing_ILS.md | source_inaccessible | missing |
| 01_Knowledge/20240304_CMFP_Intro.md | source_inaccessible | missing |
| 01_Knowledge/20250709 Michelin - Composable Journey IS Stream (Summary).md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_2023marchbywmshwsizingils_29a3.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_annex7tempdsi2481conventioncyberscuritv11en_c7bb.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_arbplanningarchitecturereivewmonthly20230801110344meetingrecordi_0df5.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_arbreviewmdapasaservicemaas20220921010854_2d09.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_blueyonderbrandguidelines202511_c4af.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_blueyondersaptemplate2_eaf6.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_blueyondersnowflakedatasharingarchitecture_c0d9.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_blueyonderstandardentities_4060.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_blueyonderwarehousemanagementarchitecturev2_829a.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_byplatformarchitecture_0a78.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_cognitivedemanddatarequirements_13cc.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_datarequirements_6d78.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_deepmetalearning_62fb.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_dmsingestionservice_fb7f.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_enterprisedataorchestrationpitchdeck_100b.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_episode1platformoverviewandfoundationservices_9e04.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_gabrielreycbinterop_3f30.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_genericcognitiveplanningreferencematerial_224c.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_index_fc7e.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_kyp23springeditionep1platformoverviewandfoundationservices_0df3.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_kyp23springeditionep2dataservices_c05d.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_lifesciencesession1v2_ca53.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_machinelearningdemandedgereality_9627.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_noatumtechpresentation27oct2023_2200.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_oraclemappingmatrix_fd51.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_platformandcognitivehighlevelarchitecture_4981.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_platformeditedv2_f4ad.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_platformusagebyproduct_520b.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_sapmappingmatrix2_9e10.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_sapmappingmatrix_7a90.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_securityslidesedited_9717.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_synthesis_356d.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_wfmrequerimientosacumplimentarenglishtranslationwip_6054.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_wmsbestpracticesguide_ffa0.md | source_inaccessible | missing |
| 01_Knowledge/2026-03-22_wmspdcreferencedocument_0597.md | source_inaccessible | missing |
| 01_Knowledge/2_Demo2Win_Virtual_Reference_Cards.md | source_inaccessible | missing |
| 01_Knowledge/3_Demo2Win_Student_Template.md | source_inaccessible | missing |
| 01_Knowledge/4_Demo2Win Observations.md | source_inaccessible | missing |
| 01_Knowledge/5_Takeways.md | source_inaccessible | missing |
| 01_Knowledge/[Internal]_My_Technology_Template.md | source_inaccessible | missing |
| 01_Knowledge/[Tech_Only]_Blue_Yonder_Response_to_Pure_Health-_RFP_Supply_Chain_Planning_Platform_&_Network-August_2025-v0.3.md | source_inaccessible | missing |
| 01_Knowledge/_Blue Yonder Pitch Deck - April 2025.md | source_inaccessible | missing |
| 01_Knowledge/_Blue_Yonder_Pitch_Deck_-_April_2025.md | source_missing | no source_path |
| 01_Knowledge/_OLD_FILES.md | source_missing | no source_path |
| 01_Knowledge/_Training_Presentation_Skills.md | source_inaccessible | missing |
| 01_Knowledge/Actors_Procedures_Process_ProcedureMapping.Lighthouse_-_Cognitive_Shorts-20241017_073106-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Adeo_Data_Mappibg.md | source_inaccessible | missing |
| 01_Knowledge/Adeo_Data_Mappings.md | source_inaccessible | missing |
| 01_Knowledge/Adidas_Demo_-_12.4.23_FINAL.md | source_inaccessible | missing |
| 01_Knowledge/AI_ML_Christian_Haag-Barcelona_2024_Presentation.md | source_inaccessible | missing |
| 01_Knowledge/ALM_Day#1_Lighthouse_-_Cognitive_Shorts-20250210_130230-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/ALM_Day#2_Lighthouse_-_Cognitive_Shorts-20250214_073129-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Almajdouie_WMS_RFP_Technical_Proposal_Draft_23.10.25.md | source_inaccessible | missing |
| 01_Knowledge/Andy.md | source_inaccessible | missing |
| 01_Knowledge/Anishka.md | source_inaccessible | missing |
| 01_Knowledge/Annex_7_-_TEMP_DSI_2481_Convention_Cybersécurité_-_v1.1_EN.md | source_inaccessible | missing |
| 01_Knowledge/API - BDM Ingestion.md | source_inaccessible | missing |
| 01_Knowledge/API_-_BDM_Ingestion.md | source_missing | no source_path |
| 01_Knowledge/API_BDM_csv_data.md | source_missing | no source_path |
| 01_Knowledge/ARB_Planning_Architecture_Reivew_(monthly)-20230801_110344-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/ARB_Review_-_MDAP_as_a_Service_(MaaS)-20220921_010854.md | source_inaccessible | missing |
| 01_Knowledge/Automation_-_Test_Cases_-_Part1_Lighthouse_-_Cognitive_Shorts-20250204_125321-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/AutomationTestCases_Part_2_Lighthouse_-_Cognitive_Shorts-20250205_130157-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Avon_Implementation_Lighthouse_-_Cognitive_Shorts-20250224_130206-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/BDM_Day#1_Lighthouse_-_Cognitive_Shorts-20241024_073106-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/BDM_Day#2_Lighthouse_-_Cognitive_Shorts-20241025_073106-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/BDM_Day#3_Temporal_Curation_Lighthouse_-_Cognitive_Shorts-20241028_083109-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/BH_Deep_Meta-Learning.md | source_inaccessible | missing |
| 01_Knowledge/BH_Snowflake_Data_Story_(Storyboard).md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder (Cloud Services & Spectrum) - 2025 Type 2 SOC 2 - Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder (Cloud Services) - 2023 Type 2 SOC 2 - Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder (Cloud Services) - 2024 (July) Type 2 SOC 1 - Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder (Heritage) - 2025 (Oct) Type 2 SOC 1 - Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder - ISO 22301 2023 Certificate.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder Brand Guidelines 2025.1.1.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder ISO27001 and ISO27701.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder Platform Services - Analytics.md | source_inaccessible | missing |
| 01_Knowledge/Blue Yonder Platform v3.0 Service Description.md | source_missing | no source_path |
| 01_Knowledge/Blue Yonder Security Whitepaper.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_&_Snowflake_Data_Sharing_&_Architecture.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_(Cloud_Services)_-_2024_(July)_Type_2_SOC_1_-_Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_(Cloud_Services_&_Spectrum)_-_2025_Type_2_SOC_2_-_Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_(Heritage)_-_2025_(Oct)_Type_2_SOC_1_-_Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_-_SAP_Template_2.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_2023_SOC_1_Type_2_-_Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_2023_SOC_2_Type_2_-_Report.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Brand_Guidelines_2025.1.1.md | source_missing | no source_path |
| 01_Knowledge/Blue_Yonder_Corporate_Presentation_Deck.md | source_missing | no source_path |
| 01_Knowledge/Blue_Yonder_ISO22301.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_ISO27001_and_ISO27701.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Platform_Services_-_Analytics.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Platform_Training_-_15-17_October_2025.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Platform_v3.0_Service_Description.md | source_missing | no source_path |
| 01_Knowledge/Blue_Yonder_Response_to_Alfa_Laval_RFP_November_2025.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Response_to_Coca-Cola_İçecek-_RFP_End-to-End_Supply_Chain_Planning_Platform-July_2025-V1.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Response_to_Greencore_RFP_20251403_-_FINAL.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Response_to_Pure_Health-_RFP_Supply_Chain_Planning_Platform_&_Network-August_2025-v0.3.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Response_to_Rolls_Royce_APS_RFP_18_July_2025.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Responses_BRC_RfP_SIOP_Commercials.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Responses_Lenzing_Forecast_Exercise.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Security_Whitepaper.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_sustainability_Pierre_Farbre.md | source_inaccessible | missing |
| 01_Knowledge/Blue_Yonder_Warehouse_Management_Architecture_v2.md | source_inaccessible | missing |
| 01_Knowledge/BlueYonder_StandardEntities.md | source_inaccessible | missing |
| 01_Knowledge/BRC_RfP_SIOP_Commercials.md | source_inaccessible | missing |
| 01_Knowledge/BY_Internal_Training_-_Asda_George_Presentation.md | source_inaccessible | missing |
| 01_Knowledge/BY_MS_Dynamics_Customer_logo_slide.md | source_inaccessible | missing |
| 01_Knowledge/BY_SaaS_Migration_Questionnaire_SCPO_V1.3_Michelin.md | source_inaccessible | missing |
| 01_Knowledge/BYPlatform-Architecture.md | source_inaccessible | missing |
| 01_Knowledge/CDAR-Logical Model - Lighthouse - Cognitive Shorts-20250605_123320-Meeting Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDAR-Logical_Model_-_Lighthouse_-_Cognitive_Shorts-20250605_123320-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDAR_template_-_Lighthouse_-_Cognitive_Shorts-20250522_123057-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDP_Architecture_Lighthouse_-_Cognitive_Shorts-20240927_073123-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDP_DataModelling_BYDM_WB_Lighthouse_-_Cognitive_Shorts-20241004_123036-Meeting_Recording_1.md | source_inaccessible | missing |
| 01_Knowledge/CDP_Model_Algorithms_Lighthouse_-_Cognitive_Shorts-20250116_130108-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDP_PartialWeeks_Lighthouse_-_Cognitive_Shorts-20250109_073310-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CDP_Pre-Sales_Functional_Training.md | source_inaccessible | missing |
| 01_Knowledge/Challenge_Yourself_Action_Book.md | source_inaccessible | missing |
| 01_Knowledge/chatgpt-prompt.md | source_inaccessible | missing |
| 01_Knowledge/CIBP_Nestle_Purnia_Demand_Classification_Segmentation_Lighthouse_-_Cognitive_Shorts-20250311_125917-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Clicks Agenda.md | source_inaccessible | missing |
| 01_Knowledge/Clicks Roadmap Workshop.md | source_inaccessible | missing |
| 01_Knowledge/Clicks_VAQuestionnaire_05282025.md | source_inaccessible | missing |
| 01_Knowledge/Cloud_Services_Standards_9.0.md | source_inaccessible | missing |
| 01_Knowledge/CMFP-April8th-Workshop-BYOrchestrator_Sample_Questions.md | source_inaccessible | missing |
| 01_Knowledge/CMFP_Pre-Sales_Functional_Training.md | source_inaccessible | missing |
| 01_Knowledge/CMFP_report._Lighthouse_-_Cognitive_Shorts-20250203_180322-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/CMFP_template_Day#1_Lighthouse_-_Cognitive_Shorts-20250227_125957-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive Friday S4E1 - Journey to the Cloud.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive Friday S4E1 J2CC.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive Friday Season 2 - Product Analytics Program.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive_Demand_Data_Requirements.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive_Demand_Planning_Help.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive_Demand_Planning_Messaging_Guide_Final_August_2023_Challenger_Modified.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive_Demand_Planning_Questions.md | source_inaccessible | missing |
| 01_Knowledge/Cognitive_Training_Attendee_List.md | source_inaccessible | missing |
| 01_Knowledge/Composable_Journey_Workshop_Slides_-_Clicks.md | source_inaccessible | missing |
| 01_Knowledge/Consensus_Planning_Workflow_Lighthouse_-_Cognitive_Shorts-20250127_125052-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Corning_-_Blue_Yonder_Differentiation_Summary.md | source_inaccessible | missing |
| 01_Knowledge/CP_Enablement_Macy's_v1.md | source_inaccessible | missing |
| 01_Knowledge/CPI.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/CPI8.csv.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/CPI8.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/CPI88.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Create_the_custom_entities_Lighthouse_-_Cognitive_Shorts-20241007_074701-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Customer_Discovery_Questions.md | source_missing | no source_path |
| 01_Knowledge/Customer_Security_Measures.md | source_inaccessible | missing |
| 01_Knowledge/Customer_Security_Measures_2_0_0_0.md | source_inaccessible | missing |
| 01_Knowledge/Customer_Value_Proposition_Matrix.md | source_missing | no source_path |
| 01_Knowledge/Data Functions.md | source_inaccessible | missing |
| 01_Knowledge/Data_Functions.md | source_missing | no source_path |
| 01_Knowledge/Data_mapping_Retail_from_Chalhoub_-_Lighthouse_-_Cognitive_Shorts-20250520_123138-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Data_quality_workflow_Lighthouse_-_Cognitive_Shorts-20250113_125215-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Data_Requirements.md | source_inaccessible | missing |
| 01_Knowledge/Deep_Meta_Learning.md | source_inaccessible | missing |
| 01_Knowledge/DeepML_Avni_Jain-Barcelona_2024_Presentation.md | source_inaccessible | missing |
| 01_Knowledge/Demand and Supply Planning v1.2 Service Description.md | source_inaccessible | missing |
| 01_Knowledge/Demand_and_Supply_Planning_v1.2_Service_Description.md | source_missing | no source_path |
| 01_Knowledge/demandChannels_13022024_102953150506.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Demo_Environments.md | source_inaccessible | missing |
| 01_Knowledge/DG_CMFP_-_Enablement_Presentation.md | source_inaccessible | missing |
| 01_Knowledge/DG_Demo_script_-_enablement.md | source_inaccessible | missing |
| 01_Knowledge/DMS_-_Ingestion_Service.md | source_inaccessible | missing |
| 01_Knowledge/DOTERRA_Demo_-_3.20.24_FINAL.md | source_inaccessible | missing |
| 01_Knowledge/E2E-Automated-Deployment-Framework_Lighthouse_-_Cognitive_Shorts-20250206_130335-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Enterprise Data Orchestration Pitch Deck '25.md | source_inaccessible | missing |
| 01_Knowledge/Enterprise_Data_Orchestration_Pitch_Deck.md | source_inaccessible | missing |
| 01_Knowledge/Enterprise_Data_Orchestration_Pitch_Deck_'25.md | source_missing | no source_path |
| 01_Knowledge/Episode_1_-_Platform_Overview_and_Foundation_Services.md | source_inaccessible | missing |
| 01_Knowledge/Evaluation_process_and_dashboards_Lighthouse_-_Cognitive_Shorts-20250117_125803-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/ExplainabilityChartData.md | source_inaccessible | missing |
| 01_Knowledge/ExploringIngestionServices.md | source_inaccessible | missing |
| 01_Knowledge/extCausalConsumerPriceIndexesCityLevels_13022024_102954432172.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalEventses_13022024_102955030282.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalMedianIncomeses_13022024_102959996476.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalPopulationGrowthByCountries_13022024_103000252473.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalProductsByCountries_13022024_102958897770.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalTradePromotionses_13022024_102955503434.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCausalWeathers_13022024_102956012641.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/extCPICountries_1.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Extension and Ingestion click Script (SCPO).md | source_inaccessible | missing |
| 01_Knowledge/Extension_and_Ingestion_click_Script_(SCPO).md | source_missing | no source_path |
| 01_Knowledge/FAAS_Day#1_Lighthouse_-_Cognitive_Shorts-20250318_125743-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/FAAS_Day#2_Lighthouse_-_Cognitive_Shorts-20250321_125946-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Financial_Questionnaire_Lenzing.md | source_inaccessible | missing |
| 01_Knowledge/Financial_Questionnaire_Lenzing_2025.md | source_inaccessible | missing |
| 01_Knowledge/Gabriel__Rey_CB-_Interop.md | source_inaccessible | missing |
| 01_Knowledge/Garrett.md | source_inaccessible | missing |
| 01_Knowledge/gemini-prompt-v2.md | source_inaccessible | missing |
| 01_Knowledge/gemini-prompt.md | source_inaccessible | missing |
| 01_Knowledge/Generic_Cognitive_Planning_Reference_Material.md | source_inaccessible | missing |
| 01_Knowledge/GRE_CMFP.md | source_inaccessible | missing |
| 01_Knowledge/GTM_Cognitive_Training_v10.md | source_inaccessible | missing |
| 01_Knowledge/GTM_Cognitive_Training_v10_-_Challenger_Slides.md | source_inaccessible | missing |
| 01_Knowledge/HEB_Deck.md | source_inaccessible | missing |
| 01_Knowledge/HEB_Deck_2.md | source_inaccessible | missing |
| 01_Knowledge/HEB_Deck_3.md | source_inaccessible | missing |
| 01_Knowledge/histShipments_13022024_102956706377.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Horizon_Web_-_How_To_Access.md | source_inaccessible | missing |
| 01_Knowledge/IBP-FEMSA-Lighthouse_-_Cognitive_Shorts-20250417_133602-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Intel-_Parallel_execution_of_Actors_and_Procedures-_Lighthouse_-_Cognitive_Shorts-20250515_183213-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/INTEL_CDP_Implementation_Journey_Lighthouse_-_Cognitive_Shorts-20250226_130222-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Introduction_to_CDP_Lighthouse_-_Cognitive_Shorts-20240925_073323-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/itemLocationCustomers_13022024_102959395437.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/itemLocations_13022024_102959701502.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/items_13022024_102953839045.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/KYP_'23_Spring_Edition,_EP_#1_-_Platform_Overview_and_Foundation_Services.md | source_inaccessible | missing |
| 01_Knowledge/KYP_'23_Spring_Edition,_EP_#2_-_Data_Services.md | source_inaccessible | missing |
| 01_Knowledge/LifeScience_session1v2.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts--Day#43-Process_Orchestration-Day#4-20241126_073116.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Copy_Inheritance-Day#1-20250212_133949-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Copy_Inheritance-Day#2-20250213_125236-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#10-Exploring_the_types_of_ingestion_service_and_Ingesting_data_into_Platform_Data_Cloud_-_Day#1-20241010_073249.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#11-Exploring_the_types_of_ingestion_service_and_Ingesting_data_into_Platform_Data_Cloud_-_Day#2-20241014_073044.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#12_-_Data_Curation_flow_-_Day#1_-_20241021_073146.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#13_-_Data_Curation_flow_-_Day#2_-_20241022_073047.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#14-_Pre-Curation,_Post_Curation_and_Generic_Plugins_-20241023_073222-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#36-Batch_Ingress-20241108_073125.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#37_-_Pre-curation_validation_actor-20241111_133302.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#38-_PDC-CDP_-_Batch_Scheduling_-20241112_073146.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#39_-_Outbound_Extracts-20241114_073128.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#40-Process_Orchestration-Day#1-20241118_073106.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#41-Process_Orchestration-Q&A-Day#2-20241119_073112.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#42-Process_Orchestration-Day#3-20241125_073112.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#44-Process_Orchestration-Day#5-20241127_073102.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#45-Exception_Workflow-20241209_073049.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#47-MaaS-20241211_073132.md | source_inaccessible | missing |
| 01_Knowledge/Lighthouse_-_Cognitive_Shorts-Day#9-Pre-Curation_Validations-20241009_080106.md | source_inaccessible | missing |
| 01_Knowledge/locations_13022024_102954078462.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Luminate_Portal_Day#1_Lighthouse_-_Cognitive_Shorts-20240930_073210-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Luminate_Portal_Day#2_Lighthouse_-_Cognitive_Shorts-20241001_073053-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Maas-Command_Center_Lighthouse_-_Cognitive_Shorts-Day#46-20241210_073123-Recording_2.md | source_inaccessible | missing |
| 01_Knowledge/MaaS_Guardrails_Lighthouse_-_Cognitive_Shorts-20250508_122803-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/MaaS_HighLevelOverview_Lighthouse_-_Cognitive_Shorts-Day#46-20241210_073123-Recording_1.md | source_inaccessible | missing |
| 01_Knowledge/MachineLearning_DemandEdge_Reality.md | source_inaccessible | missing |
| 01_Knowledge/Martin_Brower_POC__Day#2_Lighthouse_-_Cognitive_Shorts-20250303_124948-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Martin_Brower_POC_Lighthouse_-_Cognitive_Shorts-20250225_130503-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/MDAP_As_A_Service(MaaS)__Lighthouse_-_Cognitive_Shorts--Day#46-20241210_073123-Recording_3.md | source_inaccessible | missing |
| 01_Knowledge/MeetingNotes_Discovery_Workshop_2025-01.md | source_missing | no source_path |
| 01_Knowledge/Mfg_Barcelona_Cognitive_Demand_Planning_Functional_Training.md | source_inaccessible | missing |
| 01_Knowledge/MFG_Cognitive_-_ML_Studio___Workflow___RaaS-20240321_114221-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Michelin - Post Design Thinking - IT Session 04122025.md | source_inaccessible | missing |
| 01_Knowledge/Michelin - Post Design Thinking - IT Session 29092025.md | source_inaccessible | missing |
| 01_Knowledge/Michelin Tech 29092025.md | source_inaccessible | missing |
| 01_Knowledge/Michelin_DesignThinking_Deck_08072025_[Autosaved].md | source_inaccessible | missing |
| 01_Knowledge/MLR_Lighthouse_-_Cognitive_Shorts-20250305_130216-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Model_configuration_script.md | source_inaccessible | missing |
| 01_Knowledge/MQV_Lighthouse_-_Cognitive_Shorts-20250121_125347-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Navigate_to_SNA_through_Luminate_portal_Logical_Data_Model_Lighthouse_-_Cognitive_Shorts-20241015_073130-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Nick.md | source_inaccessible | missing |
| 01_Knowledge/Noatum_Tech_presentation_27oct2023.md | source_inaccessible | missing |
| 01_Knowledge/NPI_Day#1_Lighthouse_-_Cognitive_Shorts-20250218_130511-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/NPI_Day#2_Lighthouse_-_Cognitive_Shorts-20250219_130155-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/OBI_-_Cognitive_Training.md | source_inaccessible | missing |
| 01_Knowledge/ODA_Walkthrough_Lighthouse_-_Cognitive_Shorts-20250115_125935-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Oracle_Mapping_Matrix.md | source_inaccessible | missing |
| 01_Knowledge/payload_Walmart.md | source_missing | no source_path |
| 01_Knowledge/pepsi emea discovery call.md | source_missing | no source_path |
| 01_Knowledge/pepsi_emea_discovery_call.md | source_missing | no source_path |
| 01_Knowledge/pipeline_config.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Planning - WMS using BY Platform.md | source_inaccessible | missing |
| 01_Knowledge/Planning_-_WMS_using_BY_Platform.md | source_missing | no source_path |
| 01_Knowledge/Platform Overview.md | source_inaccessible | missing |
| 01_Knowledge/Platform_and_Cognitive_-_High_Level_Architecture.md | source_inaccessible | missing |
| 01_Knowledge/Platform_Editedv2.md | source_inaccessible | missing |
| 01_Knowledge/Platform_Overview.md | source_missing | no source_path |
| 01_Knowledge/Platform_Usage_by_Product.md | source_inaccessible | missing |
| 01_Knowledge/PlatformDataCloud_v2023.1_v3_BY_Training_Guide.md | source_inaccessible | missing |
| 01_Knowledge/PMC_Tool.md | source_inaccessible | missing |
| 01_Knowledge/prep_SGDBF_20260316_131409.md | source_missing | no source_path |
| 01_Knowledge/prep_SGDBF_20260320_210603.md | source_missing | no source_path |
| 01_Knowledge/prep_SGDBF_20260320_210811.md | source_missing | no source_path |
| 01_Knowledge/prep_SGDBF_20260320_235009.md | source_missing | no source_path |
| 01_Knowledge/prodLocCustMeasures_13022024_102957700706.md | source_inaccessible | excluded zone (unverifiable by policy) |
| 01_Knowledge/Prompt_Scripting.md | source_inaccessible | missing |
| 01_Knowledge/Quarterly_Review_Template.md | source_missing | no source_path |
| 01_Knowledge/Racetrac_Cognitive_Feedback.md | source_missing | no source_path |
| 01_Knowledge/Rack_Room_Shoes_-_4_11.md | source_inaccessible | missing |
| 01_Knowledge/RBAC-_Lighthouse_-_Cognitive_Shorts-20250401_122359-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Reporting_As_A_Service(RaaS)_Lighthouse_-_Cognitive_Shorts-20250129_130125-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/RFP_Database_AIML.md | source_inaccessible | missing |
| 01_Knowledge/RFP_Database_Cognitive_Planning.md | source_inaccessible | missing |
| 01_Knowledge/RFP_Database_Master.md | source_inaccessible | missing |
| 01_Knowledge/RFP_Database_Planning.md | source_inaccessible | missing |
| 01_Knowledge/RFP_Response_Final_2026-01-15_v02.md | source_inaccessible | missing |
| 01_Knowledge/Role_of_Assignments_Lighthouse_-_Cognitive_Shorts-20250217_130112-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/sampe-chatgpt-data.md | source_inaccessible | missing |
| 01_Knowledge/SAP_Mapping_Matrix.md | source_inaccessible | missing |
| 01_Knowledge/SAP_Mapping_Matrix_2.md | source_inaccessible | missing |
| 01_Knowledge/SCPO_Ingestion_data_payload.md | source_missing | no source_path |
| 01_Knowledge/Security_Slides_Edited.md | source_inaccessible | missing |
| 01_Knowledge/session_cognitive-friday-s4e1-j2cc.md | source_missing | no source_path |
| 01_Knowledge/session_cognitive-friday-season-2---product-analytics-with.md | source_missing | no source_path |
| 01_Knowledge/Sleep_Country_D&F_Demo_3.12.24.md | source_inaccessible | missing |
| 01_Knowledge/Sleep_Country_Demo_Working.md | source_inaccessible | missing |
| 01_Knowledge/Slides for Integration.md | source_inaccessible | missing |
| 01_Knowledge/Slides_for_Integration.md | source_missing | no source_path |
| 01_Knowledge/Snowflake sharing click script.md | source_inaccessible | missing |
| 01_Knowledge/Snowflake-to-Snowflake.md | source_missing | no source_path |
| 01_Knowledge/Snowflake_Day#1_Lighthouse_-_Cognitive_Shorts-20241029_083055-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Snowflake_sharing_click_script.md | source_missing | no source_path |
| 01_Knowledge/Team_Tesco.md | source_inaccessible | missing |
| 01_Knowledge/Technical Requirements - Table Questions.md | source_inaccessible | missing |
| 01_Knowledge/Technical_Requirements_for_Solution_Architectures_in_SaaS_v1.0.md | source_inaccessible | missing |
| 01_Knowledge/Testing_For_Customers_Lighthouse_-_Cognitive_Shorts-20250422_123239-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Training_Presenations_Skills_1.md | source_inaccessible | missing |
| 01_Knowledge/Training_Presentation_Skills-20231127_110402-Meeting_Recording.md | source_inaccessible | missing |
| 01_Knowledge/Use case per BY Platform service.md | source_inaccessible | missing |
| 01_Knowledge/Use_case_per_BY_Platform_service.md | source_inaccessible | missing |
| 01_Knowledge/Veronesi - Tech Track - 10th of December.md | source_inaccessible | missing |
| 01_Knowledge/Veronesi_-_Tech_Track_-_10th_of_December.md | source_missing | no source_path |
| 01_Knowledge/WFM_Requerimientos_a_cumplimentar_English_Translation_WIP.md | source_inaccessible | missing |
| 01_Knowledge/WMS_-_PDC_-_Reference_Document.md | source_inaccessible | missing |
| 01_Knowledge/WMS_Best_Practices_Guide.md | source_missing | no source_path |
| 01_Knowledge/WMS_RFP_Database_Master.md | source_inaccessible | missing |
| 01_Knowledge/Wurth_Blue_Yonder_Platform_Service_Description.md | source_missing | no source_path |

</details>

---

*Audit D complete. Read-only discipline held throughout: index.db opened `mode=ro` only; zero vault writes; zero OneDrive reads/traversal (excluded-zone paths classified by string, never touched); Obsidian never launched, CLI never executed.*
