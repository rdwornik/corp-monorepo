# Codex sol — E5 registry foundation independent derivation (evidence)

> **What this is.** The verbatim output of the Codex **sol** independent second-derivation of the
> E5 registry foundation design, retained per Lane-B senior-review rider **LB-R1** (sol output
> retention is mandatory) so every ruling in the design doc's §7 adjudication traces to a
> witnessable source. **Immutable evidence artifact** (append-only per critical-rule 3).
>
> **Run parameters.**
> - Tool: `codex exec -s read-only` (Codex sandboxed read-only — committed/created **nothing**;
>   post-run `git status` showed only the executor's own intake doc untracked).
> - Model: Codex default · Version: codex-cli 0.144.5 · Tokens: ~62k.
> - Date: 2026-07-17 · Lane B `e5-registry-design` worktree · executor-architect (robdwornik).
> - Prompt: bounded independent-derivation prompt (sol was NOT shown the executor's design); same
>   read-first inputs (the two 2026-07-07 briefs, intake §5/§9, charter §3, BACKLOG [E5]); same
>   hard constraints (deterministic day-1, no PageRank, no microservices/mesh/bus,
>   reference-not-copy, hydration invariant, #35-before-#36).
> - Verdict: **usable derivation produced** (not barren). Adjudicated in the design doc §7.
>
> Consumed by: `docs/intake/2026-07-17-tech-e5-registry-foundation-design.md` §7.

---

## sol output (verbatim)

## 1. Registry data model + per-record contract

Use one operator-owned `source_registry.yaml` as the canonical target list. Store scout observations append-only in `ops.db`; they are derived state, never a second registry. Generated vault cards and shortcuts contain references only—never source bytes.

File-level fields: `schema_version`, `records`.

Per-record declaration fields:

- `id`
- `name`
- `site_id` — A1 permanent Graph site identity
- `drive_id` — A2 library identity
- `path_hint` — A3 drift-expected path below the drive
- `web_url` — regenerable display link
- `local_hint` — display-only sync-path text; forbidden as filesystem input
- `what_it_holds`
- `owner_team`
- `dims.industry[]`
- `dims.software[]`
- `topics[]`
- `phase` — `S0_RAW | S1_REGISTERED | S2_ESSENCE | S3_ARCHIVED`
- `added_by` — `operator | scout-promotion`
- `curation_level`
- `operator_prior` — `max | high | normal | low | exclude`
- `archive_pointer` — nullable reference; never implies SharePoint deletion

Materialized observation fields, joined by `id`:

- `last_verified`
- `liveness` — `LIVE | MOVED_CANDIDATE | LOST | STALE`
- `recovery_candidates[]`
- `yield`
- `value_score`
- `score_version`
- `score_as_of`
- `score_components`
- `observation_id`

Only operator-ratified changes modify YAML. The scout may append observations and proposals but cannot add, repin, or remove records.

## 2. Deterministic source-value scoring v1

All component values are in `[0,1]`, calculated from one frozen Graph-metadata snapshot at `score_as_of`.

`Y = (D + R + T + M + U) / 5`

`I = 0.60Y + 0.20C + 0.20O`

`value_score = round(100 × (0.85I + 0.15N))`

Components:

- `D — document density`: `(documents / (documents + folders)) × min(1, ln(1 + documents) / ln(64))`; zero for an empty listing.
- `R — recency`: mean of `2^(-age_days/180)` across directly listed documents; zero when none exist.
- `T — type value`: mean per-document weight: recording/audio/video `1.00`, PPTX `0.90`, DOCX/PDF `0.70`, XLSX `0.40`, other `0.20`.
- `M — dimension/topic match`: fraction of normalized `dims` and `topics` tokens found in the location name plus directly listed child names; neutral `0.50` when no terms are configured.
- `U — uniqueness`: `1 - observed_duplicate_rate`; neutral `0.50` until a legitimate sample supplies duplicate evidence.
- `C — curation`: operator golden source `1.00`, operator-ratified scout promotion `0.75`, unratified scout candidate `0.25`.
- `O — explicit operator prior`: `max=1.00`, `high=0.75`, `normal=0.50`, `low=0.25`, `exclude=0.00`.
- `N — neighbourhood prior`: computed only from intrinsic scores `I`, never from final scores. For a child candidate, `N = 0.70 × I(parent) + 0.30 × mean(top-three direct siblings by I)`. For a registry root, use the mean intrinsic score of its top-three direct children. Missing neighbourhood evidence gives neutral `0.50`.

“Neighbour” means an explicit one-hop Graph `parentReference` relationship within the same drive and snapshot. There is no link graph, recursion, eigenvector calculation, or repeated propagation: calculate every `I` once, calculate `N` once, then calculate the final score once. Ties sort by stable registry `id`.

Safety and policy gates override the score: `exclude`, credential blacklists, active-deal restrictions, and consent requirements cannot be outvoted numerically.

No bandit, hierarchical prior, Monte-Carlo estimate, or learned weight may affect v1. A learned v2 may be proposed only after at least three completed cycles, thirty operator-labelled candidate outcomes, and top-three precision below 70% for two consecutive cycles.

## 3. Three day-1 seed sources and resolution

Each seed receives `added_by: operator`, `curation_level: golden`, and `operator_prior: max`. No unresolved placeholder passes schema validation.

1. `_Cognitive Planning - Documents\General\6. TRAINING\COGNITIVE FRIDAYS`
   - Graph site search for `_Cognitive Planning`.
   - Enumerate that site's drives and match `Documents`.
   - Store the returned A1 `site_id` and A2 `drive_id`.
   - Probe A3 `General/6. TRAINING/COGNITIVE FRIDAYS` through drive-item metadata addressing.

2. `Blue Yonder Products - Product Documentation`
   - Graph site search for `Blue Yonder Products`.
   - Enumerate drives and match `Product Documentation`.
   - Store A1/A2; A3 is drive root unless Graph metadata proves a distinct subfolder.

3. `Blue Yonder Platform - Documents`
   - Graph site search for `Blue Yonder Platform`.
   - Enumerate drives and match `Documents`.
   - Store A1/A2; A3 is drive root.

Allowed resolution calls are site search, drive enumeration, drive-item metadata probes, and bounded direct-child metadata listings with selected fields such as `id`, `name`, `webUrl`, `parentReference`, `lastModifiedDateTime`, `file`, and `folder`. Content download, recursive enumeration, local `Test-Path`, directory listing, and every traversal under `OneDrive - Blue Yonder` are forbidden. `local_hint` is retained only as human-readable evidence. Ambiguous site or drive matches require operator ratification.

## 4. Registry seam contract tests

- `test_fr10_registry_schema_round_trip` — YAML declaration → validated record → canonical serialization; missing A1/A2 anchors or invalid enums fail closed.
- `test_graph_anchor_resolver_metadata_only` — seed hint → mocked Graph site/drive/item metadata calls; any filesystem or content-download call fails the test.
- `test_value_score_v1_golden_vector` — frozen record plus metadata fixture → exact component vector and integer score, identical across repeated runs.
- `test_neighbour_prior_is_single_pass` — intrinsic-score snapshot → one-hop `N`; final scores are never accepted as neighbourhood inputs.
- `test_scout_is_read_only_and_ratification_gated` — registry plus Graph metadata → observations and promotion proposals while the canonical YAML hash and Graph state remain unchanged.
- `test_magistrala_accepts_source_reference_only` — staged capture manifest carries `source_registry_id` and A1/A2/A3 provenance; magistrala neither fetches nor moves the SharePoint original.
- `test_registry_projection_contains_references_not_content` — registry plus latest observations → deterministic vault-card/shortcut projections containing links and metadata only.
- `test_source_provenance_survives_downstream` — registry ID and anchor tuple pass through capture manifest → CKE contract → vault citation without path rewriting.

## 5. Build order mapped to BACKLOG

`#35 → #38 → #40 → #36`

1. `#35 Registry-v4 gate`
   - Complete the magistrala routing-registry dry run above 80% and apply the approved zone mapping.
   - This routing registry is distinct from the FR-10 source registry.
   - **Blocked-on-operator:** final zone names.

2. `#38 Source-value scoring v1`
   - Build the FR-10 schema, observation model, deterministic scorer, golden vectors, and single-pass neighbourhood calculation.
   - **Not blocked-on-operator.**

3. `#40 Registry day-1 seed`
   - Resolve and ratify the three records above, then calculate their scores with maximum operator priors.
   - **Blocked-on-operator:** interactive Graph consent; ambiguous Graph matches also require ratification.

4. `#36 Scout pilot`
   - Starts only after `#35`, `#38`, and `#40`.
   - Run probe → bounded one-level forage → deterministic top-N queue → proposal report → heartbeat. The registry remains unchanged until operator ratification.
   - **Blocked-on-operator:** Graph consent. Candidate promotion is separately operator-ratified.
   - Day-1 ordering uses `value_score_v1`; the backlog’s active bandit clause must remain dormant until the measurable v2 trigger is met.

---

*Evidence artifact — verbatim Codex sol output, retained per LB-R1. Immutable (append-only).
The executor's design + the adjudication of these points live in
`docs/intake/2026-07-17-tech-e5-registry-foundation-design.md`. 2026-07-17.*
