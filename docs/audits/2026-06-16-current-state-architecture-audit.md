---
last_reviewed: 2026-06-16
status: active
owner: Rob
type: audit
---

# Current-State Architecture Audit — Corporate-OS ecosystem

> **Measurement pass only.** This report measures the *real* folder / knowledge /
> automation architecture as it exists on 2026-06-16 and classifies it against a
> six-layer "night-shift pre-sales brain" ideal (L0–L5). It proposes **no**
> restructuring or taxonomy — that is a separate later phase.
>
> **Deterministic inventory:** `docs/audits/2026-06-16-current-state-architecture-audit-inventory.json`
> (1.3 MB), produced by `scripts/current_state_audit.py --include-onedrive`. This
> Markdown is the judgment layer authored over that inventory plus the repo
> architecture.
>
> **Read-only guarantee (verified in code):** the scanner's only write is the
> inventory JSON via one guarded sink; proven statically by
> `tests/safety/test_audit_readonly_invariant.py` (AST: no mutation primitive or
> shell-out except the whitelisted `write_text`) and at runtime by a `WriteLedger`
> assertion (`ledger.writes == [inventory.json]`, logged). No OneDrive file was
> hydrated (cloud-only files inventoried by metadata only; never hashed/opened).

## Executive summary — the five largest gaps

1. **The declared "sacred sources" zone does not physically exist.** `VaultZone.SOURCES = "02_sources"` is marked `IMMUTABLE` and is the target of the repo's flagship "sole-writer" invariant — yet the vault on disk has only `00_Home / 01_Knowledge / 02_Navigate / 99_System`. The ground-truth corpus (a **1.1 TB** OneDrive mirror, 96% cloud-only; **9.9 GB** MyWork; **17.1 GB** inside the *code* repo) is guarded against accidental mutation by convention + scattered guards, but is **not a sealed, declared read-only layer** (L0).
2. **Folders encode topic/access, not pipeline stages.** There is a real one-way ingest pipeline, but no `raw → desk → atoms → threads → express → briefings` refinement. CKE output lands flat in `01_Knowledge/`, and extraction byproducts sprawl (one filename appears in **161** directories; `synthesis.md` / `_meta.yaml` / `page_NNN.png` dominate the 1,216 by-name source-of-truth collisions) (L1).
3. **The deterministic spine is the strongest layer — but unscheduled.** Sole-writer invariant + AST tests, Tach 4-layer enforcement, `ops.db` record-before-move, code-owned write paths all hold. What's missing: **autonomous scheduling** (no in-repo cron; runs are manual or external cloud Routines) and **git-commit-per-run** (L2).
4. **Swarm and charter exist as ingredients, not as composed layers.** `ai-council` (multi-model debate) and tier-routing provide cheap-local + frontier judgment; `.dev-knowledge` holds ADRs, invariants and protocols. But there are **no explicit scout/cataloger/critic/editor roles**, and the charter is **mostly human-read prose, not machine-enforced** (L3/L4).
5. **Disorganization is the dominant tax.** Across the four roots, **44–83% of files match no clean naming convention**, 5–6 conventions coexist, **308 junk-drawer directories** hold >40 loose files each, and **2.5 GB** of exact-duplicate content sits in the local trees alone (L1/L5 friction).

## Headline inventory (read-only scan, 2026-06-16)

| Root | Files | Dirs | Size | Cloud-only | Max depth | No-convention | Junk dirs |
|------|------:|-----:|-----:|-----------:|----------:|--------------:|----------:|
| `Dev/corp-monorepo` | 4,312 | 408 | 17.1 GB | 0 | 9 | 1,931 (45%) | 20 |
| `Documents/MyWork` | 2,190 | 207 | 9.9 GB | 19 | 8 | 955 (44%) | 13 |
| `Documents/ObsidianVault` | 876 | 17 | 39.4 MB | 0 | 3 | 403 (46%) | 1 |
| `OneDrive…/MyWork_OneDrive` | 159,826 | 30,233 | 1.1 TB | 153,547 (96%) | 20 | 133,241 (83%) | 274 |

Supporting deterministic metrics: **550** exact-duplicate clusters wasting **2.5 GB** locally (447 files skipped as over the 50 MB hash cap; 153,579 cloud-only files never hashed); **986** filenames shared between local trees and the OneDrive mirror (by-name; hash-level overlap deferred to `--hash-onedrive` / `corp.cleanup.disk.find_onedrive_overlap`); **265** by-hash and **1,216** by-name source-of-truth collisions within the local trees.

---

## Layer-by-layer classification (L0–L5)

### L0 — Sacred ground truth (read-only sources) — **PARTIAL**

**Evidence**
- `src/corp/models.py:25` `VaultZone.SOURCES = "02_sources"` with `ZONE_MUTABILITY[SOURCES] = IMMUTABLE`, and CLAUDE.md critical rule #1 ("`corp` is SOLE writer for `02_sources/`") — a designed immutable-sources contract.
- OneDrive-exclusion guards exist and are enforced fail-closed: `src/corp/cleanup/disk.py:28 _guard_onedrive`, sibling guards in `cleanup/executor.py` / `actions/_helpers.py`, documented in `ARCHITECTURE.md` §"OneDrive safety guards".
- **Counter-evidence (verified on disk):** the vault has only `00_Home / 01_Knowledge / 02_Navigate / 99_System` — **no `02_sources/`**, no `03_playbooks`, `04_evergreen`, `dashboards`, `briefs`, or `metadata` zones the enum declares. The 1.1 TB raw corpus lives in the OneDrive mirror + MyWork, with no integrity seal (note `source_hash` tracks *extracted* sources, not originals).

**So what:** ground truth is protected from accidental mutation by convention and scattered guards, but the "immutable sources sanctuary" is aspirational — the zone the flagship invariant protects is a *phantom folder*, and the real corpus is an unsealed sprawl across MyWork + a 1.1 TB synced mirror.

### L1 — Refinement pipeline (folders = stages, not topics) — **PARTIAL (weak)**

**Evidence**
- A genuine one-way ingest pipeline exists: `src/corp/ingest/router.py` (`detect → match → route → record → move → extract`, record-before-move into `ops.db`), data-flow documented in `ARCHITECTURE.md` §Data Flow.
- **Counter-evidence:** folders are **topic/access**-oriented, not stage-oriented — MyWork (`10_Projects`, `20_Workflows`, `30_Reference`, plus the off-taxonomy, misspelled `15_Extra_Inititives`) and vault (`01_Knowledge`, `02_Navigate`). No `atoms`/`threads`/`desk`/`briefings` stages. CKE output lands flat in `01_Knowledge/`.
- Pipeline-byproduct sprawl is measurable: the by-name source-of-truth collisions are dominated by extraction artifacts (`synthesis.md`, `_meta.yaml`, `page_001.png`, `img_pNNN_*`), and by-hash collisions reach **161 copies of one content** across directories.

**So what:** the ingest→notes flow is real and crash-safe, but the *staged refinement* ideal (raw→atoms→threads→express→briefings, one artifact per stage) is absent; extraction output accumulates flat and duplicative rather than progressing through refinement stages.

### L2 — Deterministic spine — **EXISTS (with two gaps)**

**Evidence**
- Sole-vault-writer invariant: `src/corp/vault_io.py::write_note` + the AST enforcement test `tests/safety/test_vault_writer_invariant.py`.
- State + permissions: `ops.db` (immutable `ingest_events`, record-before-move, WAL), `src/corp/overnight/state.py` (resumable run state); 4-layer import enforcement via `tach.toml` + CI `.github/workflows/tach.yml`.
- Code-owned write paths: `scripts/render_conformance_digest.py` (recomputes a counts marker, fail-closed) feeding `.github/workflows/nightly-conformance-triage.yml`. Five CLIs (`corp`, `corp-meta`, `cke`, `cpe`, `com`).
- This audit tool is itself part of the spine: deterministic, read-only, with an AST-proven single write sink and a runtime write-ledger assertion.
- **Gaps (verified):** no GitHub-Actions `cron` on any workflow (scheduling is external cloud Routines or manual `corp overnight`); pipeline runs persist state to DB but there is **no git-commit-per-run** of run artifacts.

**So what:** the deterministic backbone is the most mature layer and genuinely enforces coverage/state/write-permissions — the remaining work is autonomous scheduling and versioning run outputs, not building the spine.

### L3 — Swarm / judgment layer — **PARTIAL**

**Evidence**
- `Dev/ai-council` (`VISION.md`, `ARCHITECTURE.md`): multi-model debate (5 debate + 5 research providers, blind-vote synthesis) — a real judgment engine.
- corp cost-tiered model use: `src/corp/extractor/tier_router.py` (LOCAL / TEXT_AI / MULTIMODAL) + `extractor/providers/{gemini,anthropic}_provider.py`; `intent_router.py` (keyword→LLM).
- Multi-agent automation: `.claude/workflows/conformance-corp.js` (corp) and `conformance-hub.js` (.dev-knowledge) — verifier→skeptic→digest role pipelines.
- **Counter-evidence:** no explicit, reusable scout/cataloger/cartographer/critic/editor **role interfaces** over the knowledge corpus; judgment is provider/model-based, not role-based; `ai-council` research is an isolated path that does not feed extraction or the vault.

**So what:** every ingredient of a swarm exists (cheap-local + frontier, debate, cost tiers, adversarial review) but they are not composed into a standing multi-role judgment layer operating on the corpus.

### L4 — Charter (machine-read operating constitution) — **PARTIAL**

**Evidence**
- `Dev/.dev-knowledge` is the governance hub: `VISION.md`, `docs/decisions/` ADRs, `protocols/ESSENTIALS.md` + `PLAYBOOK.md`; `~/.claude/rules/core-invariants.md` (5 invariants); per-repo `CLAUDE.md`.
- Parts of the charter *are* machine-enforced in code: the vault-writer invariant, OneDrive fail-closed guards, Tach layer rules, `models.py::ZONE_MUTABILITY`, and this audit's read-only AST proof.
- **Counter-evidence:** the bulk of the constitution is human-read prose. "No source, no claim" grounding is not machine-verified; never-delete→retired and stop-on-ambiguity are conventions, not gates; agent-write boundaries are enforced for the vault but not for decks/RFP/render outputs.

**So what:** a real, comprehensive constitution exists and is *partially* codified, but most of it governs behavior by being read, not by machine enforcement — the gap is turning prose invariants into loadable, checkable contracts.

### L5 — Expression / acceleration — **PARTIAL**

**Evidence**
- RFP answering: `src/corp/rfp/answer_selector.py` (5-stage selection, conservative "keep existing"), `src/corp/retrieve/rfp.py` (citations + confidence high/medium/low/insufficient), `rfp/rfp_excel_agent.py`; static capability matrices in `config/rfp/product_profiles/`.
- Client acceleration: `src/corp/retrieve/prep.py` (briefing synthesis); deck handling `src/corp/actions/deck_actions.py` + `com prep-deck`.
- Staleness detection exists: `src/corp/freshness_scanner.py` (fresh/stale/orphaned/review_due, 180-day threshold).
- **Counter-evidence:** staleness is **not wired into** RFP answer selection; deck assembly is template-copy, **not atoms→slides** synthesis; there is **no RFP-library mining** for recurring objections/capabilities; capability matrices are static config, not learned.

**So what:** the expression tooling is present but its parts are disconnected — grounding and staleness don't compose at answer time, and "assemble from atoms" / "mine the library" are unimplemented.

---

## Cross-cutting evidence (entropy & redundancy)

| Metric | corp-monorepo | MyWork | ObsidianVault | OneDrive mirror |
|--------|--------------:|-------:|--------------:|----------------:|
| Coexisting naming conventions | 5 | 5 | 5 | 6 |
| Files matching no clean convention | 1,931 (45%) | 955 (44%) | 403 (46%) | 133,241 (83%) |
| Junk-drawer dirs (>40 loose files) | 20 | 13 | 1 | 274 |
| Generic-named dirs ("New folder"…) | 0 | 0 | 0 | 20 |

- **Duplication (local trees):** 550 exact-duplicate clusters, **2.5 GB** wasted; largest single cluster wastes 141 MB (a 47 MB file copied 4×).
- **OneDrive overlap:** 986 filenames shared between local trees and the synced mirror (by-name; hashing of the mirror is opt-in via `--hash-onedrive`).
- **Source-of-truth collisions (local):** 265 by-hash (identical content in ≥2 directories, up to 161), 1,216 by-name (dominated by CKE per-page/synthesis artifacts).
- **Composition signal:** the `corp-monorepo` "code" repo is 17.1 GB and only 412 of 4,306 files are `.py` — it is dominated by `.md` (1,006), `.png` (560), `.pptx` (205), `.xlsx` (159), `.docx` (147); i.e., the repo doubles as an artifact store, blurring L0/L1/L2 boundaries.

## Method, scope & reproduction

- **Scanned (read-only):** `Dev/corp-monorepo`, `Documents/MyWork`, `Documents/ObsidianVault`, and (authorized, opt-in) the `…/MyWork_OneDrive` mirror. Automation inventory enumerated every directory under `Documents/Dev/` (the seven repos plus dot-config dirs `.claude` / `.settings` / `.archived`, which are config, not repos).
- **Hashing:** SHA-256 streamed for local files in `(0, 50 MB]` only; cloud-only placeholders detected via `st_file_attributes & (RECALL_ON_DATA_ACCESS | OFFLINE)` and never opened (no hydration); the OneDrive mirror is metadata-only by default.
- **Reproduce:** `python scripts/current_state_audit.py --include-onedrive` (re-run is idempotent; pass `--force` to overwrite the dated inventory JSON, `--hash-onedrive` to also hash hydrated mirror files). Config: `config/audit.yaml`. Tests: `pytest tests/safety -q`.
- **Read-only proof:** `ledger.writes == ['…/2026-06-16-current-state-architecture-audit-inventory.json']` (logged); AST invariant green; zero scanned-path mutations.

> **Not in scope (deliberately):** restructuring, taxonomy proposals, file moves, or any change to the scanned trees. The next phase (AI Council) decides the target taxonomy; this report is the matrix-before-experimenting baseline.
