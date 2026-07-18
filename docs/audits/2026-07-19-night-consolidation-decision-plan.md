# Night consolidation + decision plan — 2026-07-19

> **Status:** informational consolidation (not a ruling). **Date:** 2026-07-19.
> **Purpose:** consolidate the 2026-07-18/19 distribution → ratification → S13 → #38 arc, map
> the live repo state, and lay out the decision plan for the next lane. Night-batch item **N1**.
> **Note:** the detailed N1 spec ("as previously ordered") was not in the executing session's
> context; this doc is derived from the one-line charter (consolidation + decision-plan, §2 =
> live-state asset map) plus the live tree at run time. §2 reflects `main` at the run instant.

---

## §1 Consolidation — what this arc landed

A single 2026-07-18/19 arc took the census-derived distribution plan through decomposition,
ratification, an archival sweep, and the first E5 developer story, each as a `--no-ff` merge:

- **BACKLOG distribution decomposition** — 14 tasks / 4 stories (`#55`–`#68`, `[S10]`–`[S13]`)
  across E3/E4/E5/E7 (`61fd554`).
- **intake-16 ratified** — E5 registry design flipped DRAFT → READY-FOR-TECHNICAL on the
  operator's D1/D3/D4/D5=A picks; D1 = `config/source_registry.yaml` (`770a804`).
- **Execution-channel discipline** — lesson recorded; the E5 lane preserved pending the channel
  pick (`2ee58f2`).
- **Traceability** — grep-witnessed `Consumed by:` lines on 28 July intake/brief artifacts
  (`6e28c32`).
- **S13 archival sweep** — signed ADR-38 deletion/relocation manifest (`59f29d8`), then executed:
  G4 relocate 8 audits + inventory.json → `docs/archive/` (`236de12`), G1 KILL 8 `.html`
  render-twins (`74ef46c`), G2 KILL 19 conformance digests (`af02a0c`); G3
  (`technical-architect-intake`) DEFERRED. `#66`/`#67`/`#68` closed.
- **E5 `#38` FR-10 source registry** — schema + observation model + deterministic scorer, built
  in the `epic/e5-registry` worktree lane (plan-then-auto), **terra-green after a 4-pass
  fix-and-rereview loop** (6 P1 fail-closed/design-invariant gaps fixed), merged `--no-ff`
  (`60b7367`).
- **Night batch** — N2 (`test_cke_paths_resolve` worktree-compat fix), N3 (`#69` ADR-archival
  task), N1 (this doc).

## §2 Asset map — live state (`main` at run time)

```
main HEAD          60b7367  (Merge epic/e5-registry — E5 #38, terra-green)
active branch      chore/2026-07-19-night-consolidation  (this night batch)
worktree           .claude/worktrees/epic-e5-registry @ db48093 [epic/e5-registry] — PRESERVED
                   (E5 developer lane; continues for #40/#36/#55; not torn down)
other branches     feat/arc4-leg1-ruff-equalization (pre-existing, unrelated)
BACKLOG            7 themes · 11 stories · 55 tasks (validate_backlog OK)
E5 open tasks      #35 #36 #37 #3 #4 #5 #6 #7 #38 #39 #40 #55
#38 status         MERGED as PRIMITIVES (scorer/schema/observation); stays OPEN — its
                   "every record carries a value_score / queue consumes" done-when completes
                   when #40 wires seeds + Graph snapshots
new code (main)    src/corp/ops/source_registry.py · source_value.py ·
                   source_observation_repo.py + source_observations table; tests/test_ops +82
immutable records  docs/audits/2026-07-19-deletion-manifest-s13-archival.md (SIGNED; G3 DEFER)
                   docs/intake/2026-07-17-tech-e5-registry-foundation-design.md (intake-16, READY)
E5 lane API        SourceDeclaration · validate/load_source_registry · score_record ·
                   compute_components · compose_score · neighbour_priors · rank_by_value_score ·
                   ScoredSource · SourceObservationRepository
```

## §3 Decision plan — next lanes

1. **E5 continuation (`#40` → `#36` → `#55`).** The `epic/e5-registry` lane continues from the
   new `main` (sync it forward first). `#40` seeds the three golden records + resolves + scores
   them; `#36` runs the scout pilot (day-1 = deterministic `rank_by_value_score`, bandit is
   cycle-3+); `#55` emits a draft Content-Manifest. The `#38` primitives are the substrate.
2. **Graph consent (decision G / auth D2)** — the one interactive gate. `#40` *record drafting*
   is consent-free, but *live resolution* to A1/A2 IDs and `#36`'s foraging **block on it**.
   Operator decision, not designed around (intake-16 §3/§6/§8).
3. **ADR-archival (`#69`, S13/G3)** — relocate the consumed+superseded
   `technical-architect-intake` via a forwarding-marker amendment arc on ADR-33/34/35/36
   (ref-integrity per ADR-38 / #68). Deferred, not dropped.
4. **Paper-only ADRs (`#63`/`#64`/`#65`)** — enforce-or-defer ADR-34/35/36 (census B-table 3).
5. **KE / RFP hardening (`[S10]` / `[S11]`)** — the SIM-1 acceptance gaps (C2/C3/C4/C6) + RFP
   body-FTS + cost observability; lane-scheduled per the 2026-07-18 focus ruling.
6. **E5 epic final return** — after `#40`/`#36`/`#55`; only then is the epic finalized and the
   `epic/e5-registry` worktree torn down.

## Open decisions (operator)

- **Graph consent** (gates `#40` live-resolve + `#36`) — the single interactive step.
- **Auth shape (D2)** — delegated (existing az/X1 consent) vs a dedicated app registration.
- **Final zone names (DR-6/7)** — gate `#35`'s zone renames.
- Whether to run `#69` (ADR-archival forwarding-marker arc) now or hold.

---

*Consolidation record — no `src/`/`tests/` change (night-batch N1). Derived from live `main`
state at run time; not a ruling.*

<!-- ============================================================================
     AMENDMENT MARKER — everything ABOVE this line is the byte-identical N1
     night-batch record and is NOT edited in place. Per CLAUDE.md §5 rule 3
     ("ADRs, transcripts, handoffs, and audits are immutable — supersede with a
     new file or an in-file amendment marker; never edit in place"), and because
     a new file was out of scope for this lane, this extension uses the sanctioned
     in-file amendment-marker mechanism. The ADR-94 in-place exception is
     ADR-specific (status line only) and does not apply to an audit.
     ============================================================================ -->

---

# AMENDMENT — 2026-07-19 · Module connection map, adjudication, freshness verdict

> **Lane:** `audit-module-map` (branch `docs/2026-07-19-module-connection-map`, off `main`@`2c48fd5`).
> **Relationship to the N1 body:** §1–§4 and the record above are **untouched**. This amendment
> *supplements* them (completing the thin N1 §1–§4) and adds the new §5–§8. Where it revises a
> live-state fact the N1 body recorded (notably: `main`'s HEAD has advanced past N1's `60b7367`),
> it says so explicitly rather than editing the original.
>
> **Method (no audit re-run — the evidence corpus already existed).** Wave 1: 8 read-only module
> probes (Sonnet) + 4 evidence-corpus legs + an asset-map leg + an ARCHITECTURE-claim extraction
> (Haiku). Wave 2 (parallel, independent tool): a `gpt-5.6-sol` derivation given **only** `src/`,
> blind to the audits and to Wave 1. Wave 3: this orchestrator adjudicated divergence-by-divergence.
> Wave 4: a cold-reader comprehension probe (§8). **Every §5 cell carries a witnessing command or a
> cited `file:line`.** Subagents wrote nothing (working tree verified clean before commit).

## §1-EXT — Decisions register (completes §1: what is in force, and what each forbids)

| Decision | In force | Core ruling | What it FORBIDS |
|---|---|---|---|
| **corp ADR-37** — metadata canonical layer + facts disposition | Accepted 2026-07-18 | Canonical layer = **note frontmatter**; `index.db` is a derived, disposable projection (**no dual-write, ever**). F7 facts pipeline **stays dead**; add exactly **one** projection leg `projects.facts_count := Σ len(key_facts-from-frontmatter)` (post-scan UPDATE, guarded, package-note-excluded, source-hash-deduped). Re-open a `key_facts` retrieval surface **only** on witnessed **post-F6** real-RFP grounding failure. | Dual-write; reviving `facts`/`facts_fts` tables/loader/FTS; a speculative `key_facts` index; a DB field not derived from a source file being treated as source of truth. |
| **corp ADR-38** — deletion-manifest doctrine | Accepted 2026-07-18 | **Three fresh evidence legs per KILL/GATED row** vs a named HEAD sha: (1) whole-repo caller re-grep, (2) data-binding cross-check, (3) docs/config grep. Missing a leg → **UNVERIFIED**, unsignable. Legend KILL/GATED/KEEP/DEFER. **Amendment A:** column-granularity enumeration before a *column* KILL (precedent: `facts_count` 29 sites — a live vault-sourced scalar a module-grep would have mis-killed). **Amendment B:** runtime-claim kills default to **PROPOSED-GATED**. First signed instance: `2026-07-17-deletion-manifest-arc-b.md`. | Signing a KILL on a module-level grep alone; a blanket delete on a runtime "never fires" claim; editing a signed manifest in place. |
| **intake-16** — E5 registry foundation | Ratified 2026-07-18 (DRAFT→READY) | Operator picks **D1=A** (`config/source_registry.yaml`), **D3=A** (paste-back ratification day-1), **D4=A** (explicit operator-pick archive trigger), **D5=A** (equal weights day-1; `weights_version` = the tuning seam). sol-adopted design: split declaration(YAML)/observation(ops.db, derived); `operator_prior` enum `max/high/normal/low/exclude`; neighbour-prior from **intrinsic single-snapshot** (nested Y→I→N); quantified learning trigger (≥3 cycles, ≥30 labelled, top-3 precision <70% ×2); **safety/policy gates numerically override the score**. | Derived/drift-prone state in the hand-edited source of truth; a yield score outvoting `exclude`/consent/OneDrive gates. |
| **#38 build rulings** (witnessed in code) | Merged 2026-07-19 (`60b7367`) | **F1** — single `weights_version` field (`ops/source_value.py:22` `WEIGHTS_VERSION="v1"`, `:166`). **F2** — **round-half-UP**, not banker's (`:19` `ROUND_HALF_UP`, `:178-179`). `operator_prior=exclude` → prior `0.00` **and** score **forced to 0 when gated** (`:171`) = the "exclude = gated" semantics. `MetadataSnapshot` frozen; **zero live Graph calls this story** (`source_value.py:6`). | Multiple version fields; banker's rounding; a gated source carrying a nonzero score; live Graph calls in #38 (deferred to #40/#36). |
| **S13 archival rulings G1–G4** | Signed `2026-07-19-deletion-manifest-s13-archival.md` | **G1** KILL 8 `.html` render-twins; **G2** KILL 19 conformance digests; **G4** relocate 8 audits + `inventory.json` → `docs/archive/`; **G3** (`technical-architect-intake`) **DEFERRED** → #69. | (G1) regenerating render-twins; (G3) deleting the intake before the forwarding-marker arc. |
| **Operator philosophy** (recorded across intake-16 + the focus ruling) | Standing | **Manual-first** (paste-back before vault-card; explicit-pick before telemetry-policy; deterministic rank before bandit); **safety gates are load-bearing** and cannot be outvoted by a score; **source-authoritative, observations-disposable**. | Automating a step before it has run manually; letting a computed score override a safety gate. |

*(The N1 charter also listed an "E4=WARN routed to primary" #38 validation ruling; it could **not** be witnessed anywhere in `src/`, `config/`, or intake-16, so it is **omitted here** rather than asserted from memory — flagged for the operator to confirm or drop.)*

## §2-EXT — Asset map (supplements N1 §2 with this-lane live state)

- **`main` has advanced** since N1 recorded `60b7367`: → `334da4e` (night-batch merge N1/N2/N3) → **`2c48fd5`** (ARC-4 leg 1, ruff/pytest floor equalization). This lane branched off `2c48fd5`. **The N1 §2 "main HEAD 60b7367" line is therefore stale — read this line as the correction (§2 above is not edited).**
- **Worktrees:** `corp-monorepo` @`2c48fd5` [main] · `audit-module-map` @`2c48fd5` [`docs/2026-07-19-module-connection-map`] (this lane, locked) · `epic-e5-registry` @`db48093` [`epic/e5-registry`] (E5 dev lane, locked, **behind** main).
- **BACKLOG:** 7 themes (E1 E2 E3 E5 E6 E4 E7, R10 priority) · 11 stories · 55 tasks · `validate_backlog` **OK** · **next-free task id = #70** (highest is #69).
- **Intakes (all LIVE, none DEFERRED):** `2026-07-10-runbook-gap-notes` (READY) · `2026-07-17-tech-e5-registry-foundation-design` (READY-FOR-TECHNICAL = intake-16) · `2026-07-18-func-sim-acceptance-tests` (RATIFIED).
- **ADR ledger:** 38 corp-local ADRs (ADR-01…38; 28/29 reserved). Superseded (retained as record): ADR-03→08a · ADR-04→07 · ADR-10→14 · ADR-22→33. Latest in force: **ADR-37, ADR-38**.
- **`docs/archive/`:** 44 files post-S13 sweep (includes the 8 G4-relocated audits + `inventory.json`).
- **Developer-bundle:** removed by the methodology hub — **confirmed absent** (0 references); do not recreate.
- **New #38 code on main:** `ops/source_registry.py` · `source_value.py` · `source_observation_repo.py` + `source_observations` table; `tests/test_ops` +82.

## §3-EXT — Start-here plan (ordered; supplements N1 §3)

1. **Sync the E5 lane forward** — fast-forward the `epic/e5-registry` worktree (`db48093`) to `main`'s tip **`2c48fd5`** before resuming. *(N1 §3 said `60b7397`/`60b7367`; main advanced twice — sync to `2c48fd5`.)*
2. **#40** — seed the three golden records + resolve to A1/A2 Graph IDs + score them. **Graph consent GRANTED**; **auth D2 = delegated SSO user token + refresh** (corp-ops precedent) — *per the operator's charter for this lane*, which **resolves** the intake-16 **D2** and **decision-G** items that the N1 body (and its "Open decisions") still listed as operator-pending. Record drafting is consent-free; live resolution uses the granted consent.
3. **#36** — scout pilot. Day-1 = deterministic `rank_by_value_score`; bandit is **cycle-3+**.
4. **#55** — draft the **Content-Manifest** (`{claim, citation, form-knob, [NEEDS INPUT]}`; "the single integration contract all four surfaces meet at… a record contract, not a service" — T6 brief, §3.1–3.2).
5. **S10 KE (#56–#60)** — seam-contract / knowledge-extractor hardening.
6. **RFP intake (S11)** — inputs: **terrain-recon return** — **branch `docs/rfp-terrain-recon` is ABSENT in this repo** (`git branch -a` finds no `*terrain*`/`*rfp*` branch); **locate it elsewhere or treat the return as not-yet-produced before relying on it.** Plus retrospection: RFP-KB = **real answers submitted BY us**, mixed quality, **Planning-heavy (894/1329)**, gold ratification **pending per product family**; `com` **stalled-by-misconfig** (~5-line / 4-env revival, **CONFIRMED** by the module-7 probe — not abandoned); `INDEX_EXTRA_ROOTS` federation is **built + tested** (`config.py:100`, `schema/pipeline_config.py:77`) vs ADR-22 (ratified-but-never-built, superseded by ADR-33) — **activation ratification NOT witnessed**.
7. **S12 (#63–#65)** — paper-only ADR enforce-or-defer (ADR-34/35/36).
8. **#69 ADR archival** — relocate the consumed+superseded `technical-architect-intake` via forwarding-marker amendments on ADR-33/34/35/36 (S13/G3; ref-integrity per ADR-38 / #68).

## §4-EXT — Open questions

- **Operator:** final zone names (DR-6/7) gate #35's zone renames · run #69 now or hold · **the ADR-27 §Decision-2 doc-drift + the `copy_to_vault` invariant hole (see §5, module 3) — enforce-fix now or schedule to the A3 R9 arc?**
- **Hub:** none surfaced this lane (developer-bundle removal already absorbed).
- **Execution-status:** where is the terrain-recon return if not on a branch? · who ratifies RFP-KB gold per product family? · is Graph auth D2 (delegated-SSO) now fully resolved by the charter grant, or still a joint dependency on X1's ADR (DR-11 family)?

## §5 — MODULE CONNECTION MAP

### §5.1 Adjudication — CC module probes (Wave 1A) ↔ `sol` derivation (Wave 2)

Two derivations were run blind to each other; the prior `2026-07-16` ground-truth audit is a third
witness (B1). Divergences resolved divergence-by-divergence:

| # | Divergence | CC (Wave 1A) | sol (Wave 2) | Verdict | Reason |
|---|---|---|---|---|---|
| 1 | **`com` coupling to index/vault** | Import-**siloed** — grep `corp.opportunity` outside the package → 0 hits; "no vault/index/registry coupling" | **Filesystem-coupled** — `folder_manager.py:57,111-112` writes `$PROJECTS_ROOT/<project>/_knowledge/project-info.yaml` that `index_builder.py:290-311` scans → `com → index` FILE edge; `com → vault` via `vault_io.py:336-338` | **MERGE** | Both cited and both true. `com` is import-siloed **and** filesystem-coupled through `project-info.yaml` under shared `$PROJECTS_ROOT`. The truth is "coupled by disk, not by import" — the classic data-READ edge import-analysis misses (the `2026-07-16` codex found 39 such). The edge exists in code but is **dormant** (com config-stalled; today `project-info.yaml` is populated via ingest/project, not com). |
| 2 | **`RFP → demo-prep` helper reuse** | Not surfaced (probe focused on retrieval inputs) | `retrieve/rfp.py:101` imports `_call_llm` + `build_notes_context` from `prep.py`; calls `:128,144` | **adopt-sol** (add edge) | Cited import+call; a real intra-`retrieve` coupling CC's RFP probe missed. |
| 3 | **`demo-prep ↔ com` filesystem edges** | demo-prep probe found `demo-prep → index`; not the com edges | `demo-prep → com` (prep writes `prep_*.md` into the com-managed `_corp_prep/`, read by `folder_standards.py:167-174`) + `com → demo-prep` (deck destination `_helpers.py:93-96`→`deck_actions.py:104-117`) | **adopt-sol** (add edges) | Cited file paths; prep output and deck both land in the com-owned project folder. |
| 4 | **Vault-writer invariant hole** (`copy_to_vault` → `02_sources/`) | **Surfaced** — false-green ADR-27 test (see module 3) | Not surfaced (its filename filter forbade reading `brief_actions.py`; `vault_actions` out of focus) | **adopt-CC** | CC's finding is cited and material; sol was structurally blind to it. |
| 5 | **Source registry connectivity** | PARTIAL — SEAM **NONE**, no callers outside tests, no scout runtime | **ISOLATED** — nobody imports it, nobody reads `source_observations` | **AGREE** (no divergence) | Strongest triangulation: two independent derivations both find it unwired. |
| 6 | **`inbox → vault` mechanism label** | "CKE output → vault direct file move" (`move_to_vault` = `shutil.move`) | "`inbox → vault` **DIRECT**" (import+call of `move_to_vault`) | **MERGE** | Same edge: an **in-process call** (`move_to_vault`) that **lands files on disk**. Existence agreed; label is "in-process call, filesystem data". |

### §5.2 The connection map — 8 modules, adjudicated, each verdict witnessed

**Legend:** WIRED = real exercised connection · PARTIAL = plumbing exists, end-to-end not completed/exercised · UNWIRED = no connecting mechanism.

**1 · inbox / routing — WIRED.**
- *Consumes:* files dropped in `00_Inbox/` (FS drop — `ingest/router.py:101` `scan_inbox`, `inbox_ops.py:27`); ContentRegistry rules (`ops/registry.py`); `naming_config.yaml`.
- *Produces:* a CKE `manifest.json` + `cke process-manifest` subprocess; extracted packages moved to `01_Knowledge/`; ops.db rows (`assets`, `ingest_events`, `file_registry`, `routing_feedback`).
- *Seam:* **SUBPROCESS** → CKE (`router.py:743`→`:784`; `overnight/cke_client.py:162-175,225-265`) **+** in-process `move_to_vault` landing files on disk (`router.py:792-795` → `extraction/vault_writer.py:57-71`) **+** DIRECT `rebuild_index()` post-ingest (`inbox.py:550-553`).
- *Witness:* `tests/test_ingest/test_inbox.py:394-441` patches `router._run_extraction` and drives `inbox._trigger_extraction` — the inbox→router→CKE call is live/exercised.
- *Cost if broken:* — (WIRED). *Caveat:* the **classify→finalize** secondary path (`router.py:841-893 finalize_file`) does **not** call `_run_extraction` — files routed that way are **not auto-extracted**. *Disambiguation:* `intent_router.py`/`routing_types.py` is a **separate** chat-intent subsystem, not file-inbox routing (no code path into `ingest/`).

**2 · CKE knowledge extractor — WIRED.**
- *Consumes:* a `cke_manifest.json` path (built by `extraction/manifest_emitter.py`) + CLI flags. No Python objects cross the boundary.
- *Produces:* per-file package dirs under `output_dir` (`extractor/batch.py:202-306`) + a stdout summary (regex-parsed by `overnight/cke_client._parse_summary:109-159`).
- *Seam:* **SUBPROCESS both ways** (`project/cke_invoker.py:50-96`, `overnight/cke_client.py:178-316`). **Zero** `import corp.extractor` outside the package; **zero** vault/db writes (`extractor/README.md:7-8` + 0 code matches) — the pure-extraction invariant holds. Two file-drop paths to vault: `corp extract`→`move_to_vault` (`shutil.move`) and `corp ingest-extractions`→`write_note`.
- *Cost if broken:* — (WIRED).

**3 · vault + metadata — WIRED (+ a cited safety gap).**
- *Consumes:* CKE `output_v2/{scope}/{client}/extract/*.md` staging via `corp ingest-extractions` → `ingest/extractions.py:199-322`.
- *Produces:* `.md` notes with `trust_level` frontmatter written **flat into `01_Knowledge/`** (sole writer `write_note`; sole call site `extractions.py:288`); failures → `_quarantine/`.
- *Seam:* file-drop (staging → vault) + in-process call (`cli/ingest.py:553`).
- *Findings (both cited):* **(a) doc-drift** — ADR-27 prose names `02_sources/` as canonical ingest output, but `_resolve_dest` routes **all** notes to `01_Knowledge/` per "Council Decision #7" (`extractions.py:102-112`); `index_builder` scans `01_Knowledge` first, `02_sources` is commented "# Legacy paths (pre-restructure)". Functional path OK; **ADR-27 §Decision-2 prose is stale**. **(b) live invariant hole** — the `copy_to_vault` action (`actions/vault_actions.py:106-134`, wired into the `extract_project` workflow `config/workflows.yaml:48`) → `vault_io.copy_to_vault` → direct `shutil.copy2` into `02_sources/{project_id}/`, **bypassing `write_note`** (no frontmatter, no quality gate, no conflict protection). The ADR-27 safety test `tests/safety/test_vault_writer_invariant.py` **false-greens** — its AST scanner only flags raw mutation primitives textually in `actions/*.py`, not mutations inside a called helper (`copy_to_vault` is an `ast.Name` call it doesn't match; the `shutil.copy2` lives in `vault_io.py`, outside `ACTIONS_DIR` scan scope).
- *Cost if broken:* notes can land in the protected `02_sources/` zone unvalidated and **undetected by the safety net**.

**4 · index + retrieval — WIRED.**
- *Consumes:* YAML frontmatter of notes under `01_Knowledge/` (+ `02_sources/`, `04_evergreen/_generated/`, legacy `knowledge/`, `INDEX_EXTRA_ROOTS` e.g. rfp_kb) via `vault_io.read_frontmatter` (`index_builder.py:488-593`); project `project-info.yaml`.
- *Produces:* SQLite `index.db` (`%LOCALAPPDATA%/corp-by-os/index.db`), tables `projects`/`notes`/`notes_fts` (FTS5, content=notes). `retrieve.engine.retrieve` is **the** single retrieval function ("All workflows call this").
- *Seam:* **shared SQLite `index.db`** (read by `query_engine`, `retrieve.engine`, `rfp.vault_adapter`, `knowledge_actions`) + subprocess for the RFP-agent path. Populated by a file-drop rescan (`rebuild_index`; no push/webhook); auto-triggered post-ingest.
- *Witness:* `pytest tests/rfp/test_vault_adapter_cli_seam.py tests/test_index_builder.py tests/test_retrieve/test_engine.py` → **82 passed**. Write site `index_builder.py:543-589`; read sites `query_engine.py:220-238`, `retrieve/engine.py:216-238`.
- *Cost if broken:* — (WIRED). *Live gap it carries:* FTS indexes **metadata only** (title/topics/products), **not note body** (F6) — body-phrased queries return 0.

**5 · RFP agent — WIRED.**
- *Consumes:* two live retrieval paths to vault/index: (1) `corp rfp answer` → `retrieve.rfp.answer_rfp` → **in-process** `retrieve.engine.retrieve` (`retrieve/rfp.py:109-115`); (2) Word/Excel tools → `rfp/vault_adapter.py` → **subprocess** `corp retrieve --format json --rfp-only` (`:117-157`) with a direct-SQLite `notes_fts` fallback (`:165-210`). A **vestigial** ChromaDB + `data/kb/canonical/RFP_Database_UNIFIED_CANONICAL.json` fallback remains (phased-out; only reached if vault retrieval returns nothing). Separate curation store `data/kb/{verified,drafts,rejected}` (`rfp_feedback.py`, `answer_selector.py`) — **not** the answer seam.
- *Produces:* answer text + citations + confidence (console); Word `.docx`; Excel `.xlsx`; all through `anonymization.AnonymizationMiddleware`.
- *Seam:* subprocess (`vault_adapter._retrieve_via_cli`) + in-process (`retrieve.engine.retrieve`); guarded by `tests/rfp/test_vault_adapter_cli_seam.py` (unmocked subprocess). Also reuses demo-prep helpers (`retrieve/rfp.py:101,128,144`).
- *Cost if broken:* — (WIRED). **Refines process-audit F11:** the "orphan `RFP_Database_UNIFIED_CANONICAL.json` with no producer" is the **vestigial fallback**, not the primary lane — the Word/Excel lane **is** vault-wired via `vault_adapter`.

**6 · source registry + scout (#38) — PARTIAL (primitives only; wiring is #40/#36).**
- *Consumes:* `config/source_registry.yaml` (**absent** → `load_source_registry()` returns `[]`); a caller-supplied `MetadataSnapshot` (no live Graph calls — deferred to #40/#36 per docstring).
- *Produces:* in-memory `SourceDeclaration`/`ValueScore`/`ScoredSource` only; `source_observations` table DDL exists (`ops/database.py:174`) but is **never written outside tests**.
- *Seam:* **NONE.** `grep -rn "score_record|rank_by_value_score|SourceObservationRepository|validate_source_registry" src/` → only self-definitions in `src/corp/ops/{source_registry,source_value,source_observation_repo}.py`, **zero external callers**. `grep -ril "scout" src/` → **0 files** (no scout runtime). `ls config/source_registry.yaml` → no such file. `sol` **independently confirms ISOLATED**.
- *Cost if broken:* nothing observable breaks today (nothing consumes it) — but the **"forage → rank → surface new sources" loop does not exist**: no source can be scored, observed, or ranked outside pytest.

**7 · deal loop `com` — PARTIAL (config-stalled; filesystem-coupled, import-siloed).**
- *Consumes:* `config/opportunity/default.yaml` + env `PROJECTS_ROOT`/`ARCHIVE_ROOT`/`TEMPLATES_ROOT`/`PROJECT_CODES_EXCEL` (**all unset** in this env) + `project_codes.xlsx` rows + Gemini (chat intent). Does **not** import `vault_io`/`index_builder`/registry.
- *Produces:* opportunity folder tree + `_knowledge/project-info.yaml` + `notes.md` + copied `.pptx` + a folder-link cell written back to `project_codes.xlsx`. Never calls `write_note`; nothing into `02_sources/`.
- *Seam:* entry point `com = corp.opportunity.cli:cli` (`pyproject.toml:58`). **Import-siloed** (`grep corp.opportunity` outside package → 0) **but subprocess-reachable** — `workflow_engine.py:236-268` runs `com new` as step 1 of the `new_opportunity` workflow (`config/workflows.yaml:5-26`), reachable from chat (`chat.py:159`) + `corp workflow` CLI — **and filesystem-coupled** (sol): `folder_manager.py:57,111-112` writes `$PROJECTS_ROOT/<project>/_knowledge/project-info.yaml` that `index_builder.py:290-311` scans → a **dormant `com → index` FILE edge**.
- *Cost if broken:* `com new/list/show/prep-deck/chat` non-functional against real data (defaults to a stray repo `test_projects/`); the chat-triggered `new_opportunity` workflow stalls at step 1. **Fix is config-only: 4 env vars in a root `.env` + one template-filename correction in `config/opportunity/default.yaml` — no code change** (the top-level `corp/config.py` already defaults the same env names to real MyWork paths).

**8 · demo-prep external surface — WIRED (inherits upstream gaps).**
- *Consumes:* the FTS5 index via `retrieve.prep.generate_prep` → `retrieve.engine.retrieve` (`prep.py:126-143`); project files (`project-info.yaml`, `facts.yaml`) for briefs; the template registry for decks.
- *Produces:* (1) `corp prep <client>` → LLM-synthesized `prep_{client}_{ts}.md` into the project `_corp_prep/` folder; (2) `generate_project_brief` → `brief.md` in the vault project dir; (3) `prep_deck` → a **copied template** file.
- *Seam:* DIRECT `retrieve.engine.retrieve` (shared index) + LLM API + FS read/write via the `@register_action` registry (`workflow_engine._execute_python_step:284-308`). **sol adds** `demo-prep → com` FILE (prep writes into the com-managed `_corp_prep/`) and `com → demo-prep` FILE (deck destination).
- *Witness:* `tests/test_retrieve/test_prep.py`, `tests/test_built_in_actions.py:196-208`.
- *Cost if broken:* — (WIRED; soft-degrades to notes-only if `google-genai` absent). **Inherits:** the body-FTS gap (F6); brief `facts.yaml` is starved (F7); `prep_deck` is template-copy, **not** LLM authoring (F27).

### §5.3 THE UNWIRED SEAMS — what is not connected, and what it costs

1. **Source registry / scout → the system (UNWIRED).** No CLI, no pipeline hook, no scout runtime; `config/source_registry.yaml` absent. *Cost:* the entire source-foraging/ranking loop does not exist yet. (By design — #40/#36.) *Two-witness confirmed (CC + sol).*
2. **Note body → search index (MISSING — F6).** FTS covers metadata only. *Cost:* body-phrased queries return 0; RFP/demo-prep grounding degrades at scale. **The biggest live gap inside the otherwise-WIRED spine.**
3. **Project → its own vault notes (MISSING — F16/F9).** ingest writes no `project-info.yaml` for ingested knowledge; `corp project list` shows `Vault=-`; routing key → note `client=''`. *Cost:* project view/analytics/briefs can't see the notes or the client. (`com` *can* write this file but is stalled — see #5.)
4. **`com` deal loop (PARTIAL — config-stalled).** Subprocess-reachable + filesystem-coupled, but 4 env vars unset. *Cost:* com non-functional against real data; `new_opportunity` stalls at step 1. ~5-line/4-env fix.
5. **classify→finalize → CKE (MISSING).** The secondary inbox path (`finalize_file`) does not trigger extraction. *Cost:* files routed via classify→finalize land without a knowledge note.
6. **synthesize → vault (NOT WIRED — F25).** `synthesize.build_package` is internal-only; `synthesis.md` never becomes a first-class note. *Cost:* no user-facing synthesis surface.
7. **Content-Manifest → deck (UNBUILT — F27).** `prep_deck`/deck actions copy a template; no LLM slide authoring. *Cost:* "deck production" yields an empty template, not content — the FR-7 deck seam is unbuilt (#55 Content-Manifest is its precursor).
8. **Vault-writer invariant (HOLE — module 3).** `copy_to_vault` writes `02_sources/` bypassing `write_note`; the ADR-27 test false-greens. *Cost:* unvalidated notes can enter the protected zone undetected.
9. **ingest cold-start (BRITTLE — F1).** `corp ingest` raises `FileNotFoundError` if `<mywork>/.corp/content_registry.yaml` is absent (no fallback to shipped config). *Cost:* cold-start ingest crashes.

## §6 — IMPROVEMENT OPTIONS (options, not decisions; each sized; NOT-list-bounded)

> Bounded by the A3 NOT-list: **no service / mesh / message-bus / literal-PageRank.** These are options for the operator to pick from, **not** a recommendation-as-decision.

| # | Seam | Cheapest credible closure | Unblocks | Size |
|---|---|---|---|---|
| O1 | Body-FTS (F6) | Extend the existing `notes_fts` projection to include note **body** at rebuild (one column + one populate site) — no new table, no query surface. | Body-phrased retrieval → RFP + demo-prep grounding at scale. | **M** |
| O2 | ingest cold-start (F1) | Fall back to the shipped `config/content_registry.yaml` (or bootstrap `.corp/…`) when the per-MyWork file is absent. | `corp ingest` on a fresh environment. | **S** |
| O3 | project↔vault link (F16/F9) | Have ingest/project write a per-project `project-info.yaml` — the field `index_builder` **already scans**. | `project list` shows notes; analytics/briefs get the client. | **S–M** |
| O4 | `com` revival | Set the 4 env vars in a root `.env` + correct one template filename in `config/opportunity/default.yaml`. | `com` CLI + `new_opportunity` workflow; activates the dormant `com→index` edge. | **S** (no code) |
| O5 | #38 registry wiring | #40 seeds+resolves+scores the golden records; #36 runs the deterministic scout pilot (`rank_by_value_score` day-1). | Source foraging/ranking. Gated on Graph consent (granted per charter) + auth D2. **NOT:** no bandit day-1 (cycle-3+); no literal PageRank (neighbour-prior is the bounded form). | **M–L** |
| O6 | Vault-writer hole | Route `copy_to_vault` through `write_note`, **or** extend the AST scanner to follow the helper call / scan `vault_io.copy_to_vault`'s target zone. | Closes the false-green; restores ADR-27 §Decision-2 enforcement. | **S–M** |
| O7 | synthesize → vault (F25) | Surface `synthesize.build_package` output as a first-class note via a user-facing command (reuse `write_note`). **NOT:** no new pipeline. | A user-facing synthesis surface. | **M** |
| O8 | Content-Manifest → deck (F27) | Build the FR-7 deck lane on the `{claim, citation, form-knob}` record (#55 first). **NOT:** record contract, not a service (T6). | Cited deck slides, losslessly shared with the RFP channel. | **L** |
| O9 | ADR-27 doc drift | Amend ADR-27 prose (via an in-file amendment marker) to name `01_Knowledge/` as canonical ingest output. Doc-only. | Removes the stale-doc trap. | **S** |
| — | key_facts retrieval surface | **PARKED per ADR-37 (iii)** — do **not** build until a witnessed post-F6 real-RFP grounding failure. Listed as an explicit non-option. | — | — |

## §7 — FRESHNESS VERDICT

### §7.1 `validate_backlog`
`python scripts/validate_backlog.py BACKLOG.md` → **`validate_backlog: OK (7 themes, 11 stories, 55 tasks, 0 warning(s))`**. Next-free task id = **#70**.

### §7.2 ARCHITECTURE.md drift — item by item (vs §5; **ARCHITECTURE.md is untouched**)
Codemap = the Tach import-layer edge list (`ARCHITECTURE.md:34-41`). Checked against the witnessed map and the prior `2026-07-16` ground-truth (B1):

| ARCHITECTURE codemap claim | Status | Witness |
|---|---|---|
| `cli → extractor` | **PHANTOM** | `cli` does not import `extractor`; `cke` is a sibling entry point. B1: `grep corp.extractor src/corp/cli/*.py` → 0. |
| `cli → project` | **PHANTOM** | `cpe` is a sibling entry point; no import. |
| `cli → opportunity` | **PHANTOM** | `com` is a sibling entry point; no import. |
| `cli → rfp` | **PHANTOM** | `corp rfp answer` uses `corp.retrieve.rfp`, not `corp.rfp`; no `cli→rfp` import. |
| `rfp → retrieve` | **WRONG KIND** | Drawn as an import; actually a **subprocess** edge (`vault_adapter`→`corp retrieve`), and the in-process path is `corp.retrieve.rfp`. |
| `cli → ingest`, `cli → retrieve`, `ingest → ops`, `ingest → schema`, `ops → schema` | **CORRECT** | B1 confirms these are correct-as-drawn. |
| **All runtime data-flow seams** (inbox→CKE subprocess; CKE→vault file; vault→index file-scan; index→retrieval shared-DB; com→index `project-info.yaml`; demo-prep↔com file; RFP subprocess) | **MISSING** | None appear in the codemap — it is an **import-layer graph, not a connection map**. |
| `ops/source_registry`, `source_value`, `source_observation_repo` (#38 code, on main) | **MISSING** | Not reflected anywhere in ARCHITECTURE.md. |

**Headline (already witnessed 2026-07-16, B1):** *"the codemap is ~90% wrong or missing — 90 static unit-edges vs 8 drawn; of the 8, 3 correct-as-drawn, 1 wrong kind, 7 phantom targets."*

### §7.3 Proposed rewrite scope (NOT executed here — the A3 R9 rewrite arc, unscheduled)
Doc-only, no code: **(a)** remove the 4 phantom `cli→{extractor,project,opportunity,rfp}` edges and relabel `rfp→retrieve` as subprocess; **(b)** add a distinct **"runtime connection map"** section (or explicitly label the codemap "import-layer only") carrying the §5 subprocess/file/DB-table seams; **(c)** add the #38 `ops/source_registry` module; **(d)** reconcile the `01_Knowledge` vs `02_sources` canonical-output statement with ADR-27 (see §6 O9). Bounded: no `src/`/`tests/` change.

## §8 — COMPREHENSION PROBE (Wave 4)

*(Pending — cold-reader probe runs next; results and any gap-closures land in the second commit.)*

---

*Amendment record (lane `audit-module-map`) — no `src/`/`tests/` change. §5 cells are witnessed;
the CC↔sol adjudication is §5.1; ARCHITECTURE.md is untouched (drift listed in §7.2, rewrite
deferred to A3 R9). Extends the N1 record above via the CLAUDE.md §5 in-file amendment-marker
mechanism; §1–§4 and the N1 body are byte-identical.*
