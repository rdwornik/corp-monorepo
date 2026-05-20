# Conformance Gap Audit — corp-monorepo vs `.dev-knowledge`

**Date:** 2026-05-20
**Branch:** `docs/audit-corp-monorepo-conformance-gap`
**Author:** Claude Code (read-only audit, file-state verified)
**Subject:** `corp-monorepo`
**Standards source:** sibling repo `../.dev-knowledge` (binding per ADR-31)
**Method:** read-only file inspection; every classification cites a file path, grep result, or configuration value
**Non-goals:**
- Does **not** duplicate the internal drift findings in [`2026-05-20-corp-monorepo-deep.md`](2026-05-20-corp-monorepo-deep.md) (manifest retry, MinHash wiring, ARCHITECTURE.md staleness, CONTRIBUTING ADR-count drift, etc.). Internal-state drift is in that audit; this audit is conformance-vs-standard.
- Does **not** prescribe changes to `.dev-knowledge`. Upstream-gated items (codemap generator, tier-computation tool, lessons-index) are noted as such and never as directives.
- Does **not** restate `.dev-knowledge` ADR content. Pointers by ADR number only.

---

## Summary

| Class | Count | Notes |
|---|---|---|
| **CONFORMS** | 17 | Clear evidence; standard met |
| **PARTIAL** | 3 | Conforms in some respects; specific gaps named |
| **GAP** | 2 | Clear non-conformance; one-line recommendation given |
| **N/A** | 16 | Standard does not bind corp-monorepo (governs `.dev-knowledge` only, or superseded, or no LESSONS.md, etc.) |
| **UNKNOWN** | 2 | Cannot determine from file inspection alone (upstream tool required) |

### GAPs in priority order

1. **GAP — `.dev-knowledge` BACKLOG Cross-stream P2 "Phase 2 universalization rollout" lists corp-monorepo as "not yet started," but 2026-05-18 work (VISION at root, ARCHITECTURE at root, BACKLOG seeded, JOURNAL ADR-49 shape, CHANGELOG retired) materially started/closed Phase 2 for corp-monorepo.** Stale upstream BACKLOG entry — not actionable corp-side beyond flagging.  
   **Recommendation:** flag upstream so the BACKLOG entry is refreshed; corp-monorepo has nothing to fix in repo.

2. **GAP — ADR-numbering namespace collision risk.** Corp's local `docs/decisions/` and `.dev-knowledge/docs/decisions/` use overlapping numeric namespaces (e.g., corp ADR-27 = "Safety Invariants," `.dev-knowledge` ADR-27 = "Scope Tagging"; corp ADR-30 = "Retire CHANGELOG," `.dev-knowledge` ADR-30 = "Default Branch main"). CLAUDE.md §11 lists "ADR-14, -23, -27, -36, -42, -49, -51, -53" mixing both namespaces without prefix qualification.  
   **Recommendation:** in CLAUDE.md §11, prefix each cross-namespace reference with the source (e.g., "corp ADR-27" vs "`.dev-knowledge` ADR-42") to remove the silent ambiguity.

### PARTIALs

- **ADR-51 (ARCHITECTURE.md convention)** — corp has ARCHITECTURE.md at root with a graphical codemap (SVG diagrams under `docs/diagrams/`), but the codemap is **hand-maintained**, not auto-generated, and no CI freshness check exists. The auto-generator is itself upstream-gated (`.dev-knowledge` BACKLOG Stream C P2 "Codemap generator output specification" — open). **Best-available state given upstream gap.**
- **ADR-34 (file naming convention)** — corp's ADR filenames, audit filenames, and JOURNAL date headers use hyphen separator per the 2026-05-11 amendment (✓). Naming convention in `CLAUDE.md` §4 references the **vault/MyWork file pattern** `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` (underscore) per corp's local ADR-14 — that pattern is **out-of-scope** for ADR-34 (MyWork is the Obsidian vault, not the repo file tree), but the wording in CLAUDE.md §4 doesn't distinguish vault files from repo files, leaving room for future drift.  
- **ADR-46 (cross-repo dated-entries format, demoted)** — JOURNAL.md uses `### YYYY-MM-DD —` headers per ADR-49 (✓) and newest-first ordering (✓). The header normalizer hook is wired in `.pre-commit-config.yaml` line 20-25 (✓). Demoted-convention parts all conform.

### UNKNOWNs

- **ADR-40 (scale tier evaluation algorithm)** — corp declares `Scale: L` in VISION.md and CLAUDE.md §2. Algorithmic computation requires running the (unbuilt) audit tool. `.dev-knowledge` ADR-40 calibration baseline (2026-04-30) lists corp-monorepo at score ~21, tier L, but the same baseline notes F-08 ("all repos clamp to L under current coefficients"). **Verification gated on audit-tool P1 implementation in `.dev-knowledge`.**
- **ADR-51 codemap freshness CI check** — convention requires a CI check that regenerates the codemap and fails on diff. corp-monorepo has graphical SVGs and a manual `scripts/render-diagrams.ps1` script. Whether the CI freshness gate exists is **UNKNOWN from file inspection** (no `.github/workflows/codemap*` or similar found; standard not implementable without the upstream generator).

---

## ADR-by-ADR conformance (`.dev-knowledge` ADRs 27–54)

> One block per ADR. Non-binding ADRs get a short `N/A` block. Pointers go to `.dev-knowledge/docs/decisions/ADR-NN-*.md` — no content restated.

### ADR-27 — Scope tagging architecture
- **Conformance test (if bound):** all sections in qualifying files carry `<!-- scope: X -->` tags; LESSONS.md scope tags in 6-field entries.
- **Status:** **N/A** — corp-monorepo has no LESSONS.md (per ADR-35; lessons live in `.dev-knowledge`). The scope-tagging pre-commit hook is `.dev-knowledge`-only. ADR-48 (2026-05-17) retired the scope-tagging system entirely, so this is doubly N/A.

### ADR-28 — Three-layer architecture (descriptive)
- **Conformance test:** corp-monorepo is Layer 3 (executor); should contain no cross-repo orchestration logic.
- **Status:** **CONFORMS** — corp-monorepo is a code project that consumes `.dev-knowledge` methodology via documentation reads only (per CLAUDE.md §1.2–1.3). No scripts orchestrate `.dev-knowledge` from corp; no upward writes (ADR-36 read-only contract preserved — `docs/handoffs/` absent).

### ADR-29 — LESSONS.md grandfathering
- **Status:** **N/A** — no LESSONS.md in corp-monorepo (per ADR-35 / corp CLAUDE.md §4 "Cross-repo lessons → `.dev-knowledge/LESSONS.md`").

### ADR-30 — Default branch = `main`
- **Conformance test:** repo default branch is `main`; no hardcoded `master` references.
- **Status:** **CONFORMS** — `git branch -a` shows `main` exists; current branch list contains no `master`. CLAUDE.md §4 specifies "never commit to `main` directly" (`feat/`, `fix/`, `refactor/`, `chore/`, `docs/` off `main`). Evidence: `git symbolic-ref refs/remotes/origin/HEAD` returns "not a symbolic ref" (local repo; not relevant), but `git branch -a` confirms `main` is the integration branch.

### ADR-31 — Authority model (prescriptive with conformance audit)
- **Conformance test:** corp-monorepo accepts `.dev-knowledge` as binding source of cross-repo prescriptions; conformance audit findings remediated when surfaced.
- **Status:** **CONFORMS** — corp's `CLAUDE.md` §1 instructs reading `../.dev-knowledge/protocols/ESSENTIALS.md` and `PLAYBOOK.md`; `CLAUDE.md` §11 cites `.dev-knowledge` ADRs as binding (ADR-36, -42, -49, -51, -53). VISION.md "Relationships" section explicitly: "consumer of `.dev-knowledge` — it adopts the ecosystem's methodology, conventions, and governance patterns."

### ADR-32 — Handoff format v2.0
- **Status:** **N/A** — corp-monorepo doesn't generate handoffs (ADR-36 read-only contract: handoffs live in `.dev-knowledge` only). corp's own ADR-31 ("Retire single-file HANDOFF") closes the legacy `docs/HANDOFF.md` pattern. Also superseded upstream by ADR-42, then ADR-45.

### ADR-33 — VISION.md universalization across ecosystem repos
- **Conformance test:** VISION.md present at root with valid frontmatter (`version`, `tier`, `owner`, `status`, `last_reviewed`, `scale`) and 6 mandatory sections (Vision, Scope, Values, Relationships, Lifecycle, References). Standard tier required at Scale L.
- **Status:** **CONFORMS** — `VISION.md` at root (148 lines). Frontmatter: `version: 1.0`, `tier: standard`, `scale: L`, `owner: rob`, `status: active`, `last_reviewed: 2026-05-18`. All 6 sections present (Vision, Scope, Values, Relationships, Lifecycle, References). Pointer-to-`.dev-knowledge` text appears in §Relationships: "consumer of `.dev-knowledge`."

### ADR-34 — File naming convention (cross-repo, universal hyphen mandate per 2026-05-11 amendment)
- **Conformance test:** hyphen as separator in filenames/foldernames; ADR-NN-topic.md pattern; YYYY-MM-DD-topic.md for audits/handoffs; UPPERCASE.md for living docs at root; kebab-case for templates; per-language conventions for code.
- **Status:** **PARTIAL** — corp's ADR filenames use hyphens (e.g., `ADR-23-monorepo-internal-architecture.md`, `ADR-27-safety-invariants.md`); audits use `YYYY-MM-DD-topic-with-hyphens.md` (e.g., `2026-05-20-corp-monorepo-deep.md`); living docs UPPERCASE (CLAUDE.md, VISION.md, ARCHITECTURE.md, JOURNAL.md, BACKLOG.md, CONTRIBUTING.md, README.md). Python modules use snake_case (per language). **The partial:** legacy `docs/archive/` UPPERCASE-TYPE-tagged files persist (`.dev-knowledge` BACKLOG Cross-stream P3 "A5 — retire opportunistically"); CLAUDE.md §4 mentions the `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` (underscore) pattern from corp's own ADR-14 without disambiguating that this is the **vault file** pattern, not the repo file pattern.
- **Recommendation:** clarify in CLAUDE.md §4 that the underscore `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` pattern is for **Obsidian vault files** only; repo files (ADRs, audits, JOURNAL/BACKLOG entries) follow ADR-34 hyphen convention.

### ADR-35 — Lessons base activation (lessons-index + retrieval + querying)
- **Conformance test (child repo):** CLAUDE.md references `.dev-knowledge/LESSONS.md` as the authoritative cross-repo lesson source; `DEV_KNOWLEDGE_PATH` environment variable optionally set.
- **Status:** **CONFORMS** — corp's CLAUDE.md §4 ("Out of scope for this repo: …Cross-repo lessons → `.dev-knowledge/LESSONS.md`") satisfies the documentation-reference requirement. The lessons-index tooling itself is upstream-gated (`.dev-knowledge` BACKLOG Stream C P2 "Lessons activation P1 implementation" — open).

### ADR-36 — Audit tool architecture (`.dev-knowledge` as ecosystem auditor)
- **Conformance test (child repo):** read-only consumed by `.dev-knowledge` audit tool; provides compliant VISION.md (ADR-33), architecture (ADR-38), state.yaml entry in `.dev-knowledge/ecosystem/`.
- **Status:** **CONFORMS** — no writes into corp from `.dev-knowledge`; corp's `docs/handoffs/` directory does not exist (handoff ownership is `.dev-knowledge` per ADR-36 read-only contract). VISION.md and ARCHITECTURE.md are present and parseable. State.yaml in `.dev-knowledge/ecosystem/corp-monorepo/` is upstream's concern.

### ADR-37 — Session boundary protocol (two-phase handoff Current/Future)
- **Status:** **N/A** — corp doesn't generate handoffs (ADR-36). Recommendation-only for child repos with own handoff workflows; corp's local ADR-31 retired the single-file handoff. Two-phase framing concept does inform JOURNAL `Next:` line under ADR-49, which corp follows.

### ADR-38 — Universal repo architecture baseline
- **Conformance test:** `src/{package}/`, `tests/`, `docs/`, `pyproject.toml`, `README.md`; `VISION.md` (Standard for L), `CHANGELOG.md` (post-ADR-49: no longer required), `ARCHITECTURE.md` at **root** (per A3/A4 amendments) for L; `docs/decisions/` for L; `BACKLOG.md` per ADR-41 for L.
- **Status:** **CONFORMS** — `src/corp/` (unified namespace, 14 sub-packages + 19 root modules); `tests/` (sibling); `docs/` (with `decisions/`, `audits/`, `diagrams/`, `archive/`); `pyproject.toml` (single `corp` package, 5 CLI entry points); `README.md`; `VISION.md` (Standard tier, scale L); `ARCHITECTURE.md` **at root** (A4 closed the deferral 2026-05-18 — JOURNAL 2026-05-18 entry confirms move); `docs/decisions/` (30 ADRs); `BACKLOG.md` (present). CHANGELOG.md absent — correct per corp ADR-30 + `.dev-knowledge` ADR-49.

### ADR-39 — File lifecycle governance (6-element pattern for every `.dev-knowledge` file)
- **Status:** **N/A** — the 6-element registry governs `.dev-knowledge` files only. Recommendation for child repos with persistent files; corp's VISION/JOURNAL/BACKLOG/CLAUDE/ARCHITECTURE/CONTRIBUTING all have implicit lifecycles documented across CLAUDE.md and the files themselves, but no explicit 6-element registry in corp. The ADR text explicitly says "**Mandate**: `.dev-knowledge` applies this lifecycle pattern; **Recommendation**: child repos."

### ADR-40 — Scale tier evaluation algorithm
- **Conformance test:** tier declared in VISION.md frontmatter; declared tier matches algorithmically computed tier (mismatch = audit finding).
- **Status:** **UNKNOWN** — corp declares `tier: standard, scale: L` (VISION.md frontmatter line 3, 4) and `Scale: L` (CLAUDE.md §2). Algorithmic computation requires the `.dev-knowledge` audit tool's `compute_tier_score`. ADR-40 calibration baseline (2026-04-30) estimates corp at score ~21 → tier L, consistent with declaration. F-08 calibration concern (all repos clamp to L under current coefficients) is upstream; corp-side declaration is well-formed.

### ADR-41 — Cross-session BACKLOG architecture (BACKLOG.md mandate at M+)
- **Conformance test (L tier):** repo has its own BACKLOG.md per ADR-41 schema (`[P{N}]` `[Status]` `What/Why/Added/Status`).
- **Status:** **CONFORMS** — `BACKLOG.md` at root, 113 lines. Header line 3–4 cites ADR-41: "Schema per ADR-41 (`.dev-knowledge/docs/decisions/ADR-41-cross-session-backlog-architecture.md`): `[P{N}]` priority, `[open|superseded]` status, dated entries." All entries use the prescribed shape (verified entries P1–P3 for Open Decisions + Pending Fixes).

### ADR-42 — Handoff format v3.0
- **Status:** **N/A** — corp doesn't generate handoffs (ADR-36 read-only contract). Last legacy `docs/HANDOFF.md` retired 2026-05-18 per corp ADR-31; `docs/handoffs/2026-04-15-handoff.md` also deleted in the 2026-05-18 rollout-cleanup branch. Directory absent. The corresponding `.dev-knowledge` BACKLOG Cross-stream P2 "Handoff folder format adoption (corp-monorepo)" remains open upstream but is effectively resolved corp-side (no flat HANDOFF.md exists to migrate).

### ADR-43 — Cross-project transcript routing
- **Status:** **N/A** — ai-council CLI feature; not a corp-monorepo concern.

### ADR-45 — Handoff architecture v4 (invariant/session separation + defense-in-depth enforcement)
- **Status:** **N/A** — ADR's own status line says "Superseded by 2026-05-13 night minimum-viable refinement (HANDOFF_PROCESS v3.3 + HANDOFF_FOLDER_TEMPLATE update)." `.dev-knowledge`-side concern; corp consumes handoffs as a receiver in occasional cross-repo sessions but doesn't author the architecture.

### ADR-46 — Cross-repo dated-entries format (DEMOTED to convention 2026-05-16)
- **Conformance test (post-demotion, lightweight):** ISO 8601 `YYYY-MM-DD` in headings; newest entries at top; single header form `### YYYY-MM-DD`; header normalizer hook idempotent.
- **Status:** **PARTIAL/CONFORMS-as-convention** — JOURNAL.md headers use `### YYYY-MM-DD — <topic>` (✓ ISO date, ✓ single header form per ADR-49). Newest entries at top (✓ JOURNAL 2026-05-20 entry is first). Header normalizer is wired in `.pre-commit-config.yaml` (lines 20–25: `normalize-headers` hook calling `py scripts/normalize_headers.py` on `^(JOURNAL|LESSONS)\.md$`). The "PARTIAL" note: hook is regex-scoped to JOURNAL/LESSONS only — BACKLOG dated entries (`- **Added:** YYYY-MM-DD`) are not normalized, which is fine because BACKLOG entry shape doesn't use the `### YYYY-MM-DD` header form anyway.

### ADR-47 — Cross-repo BACKLOG.md organization (DEMOTED to convention 2026-05-16)
- **Conformance test (post-demotion):** one file `BACKLOG.md`; stream-grouped if useful; entry shape with `[P{N}]` `[status]` and `What/Why/Added/Status`; no `BACKLOG_ARCHIVE.md`.
- **Status:** **CONFORMS** — `BACKLOG.md` (single file); two top-level groupings ("Open Decisions" / "Pending Fixes" — appropriate at corp's scale, not Stream-prefixed because corp is a single repo); entry shape matches (`### [P{N}] [open] <title>` plus `- **What:**`, `- **Why:**`, `- **Added:**`, `- **Status:**`). No `BACKLOG_ARCHIVE.md` (correct).

### ADR-48 — Trim documentation governance to structural enforcement
- **Conformance test:** scope-tagging system retired; pre-commit hooks are structural-only (file/section presence, not format detail).
- **Status:** **CONFORMS** — corp's `.pre-commit-config.yaml` carries ruff (linting/formatting, dev concern) + tach-check (architectural-layer enforcement) + normalize-headers (idempotent rewriter, not a fail-on-format hook). No scope-tagging hook present (corp has no LESSONS.md anyway). Audit-style format-detail checks are absent from pre-commit (consistent with ADR-48's "thin structural boundary").

### ADR-49 — Consolidate past-recording documentation files
- **Conformance test:** no CHANGELOG.md (deleted); no BACKLOG_ARCHIVE.md; JOURNAL uses Did/Result/Changes/Abandoned/Next per-entry shape; LESSONS retained at L+ if needed.
- **Status:** **CONFORMS** — CHANGELOG.md absent (corp's own ADR-30 retired it; JOURNAL 2026-05-18 entry "Workstream B — retire `CHANGELOG.md`" confirms). BACKLOG_ARCHIVE.md absent. JOURNAL.md uses Did/Result/Changes/Abandoned/Next: header line 7 specifies the shape and recent entries (2026-05-18, 2026-05-19, 2026-05-20) follow it. LESSONS.md absent — corp routes lessons to `.dev-knowledge/LESSONS.md` per CLAUDE.md §4 (acceptable: ADR-35 places LESSONS at the ecosystem canonical level).

### ADR-50 — Machine-document encoding standard
- **Conformance test:** machine-layer files use restricted structured markdown, English, fixed section headers, key-value blocks; advisory per-file-type schemas (not CI-enforced).
- **Status:** **CONFORMS** — corp's CLAUDE.md, VISION.md, ARCHITECTURE.md, ADRs, BACKLOG.md all use structured markdown with fixed sections, key-value blocks (frontmatter, tables), English, minimal prose. Schemas are advisory only — no CI enforcement claimed.

### ADR-51 — Architecture documentation convention
- **Conformance test (M+):** dedicated `ARCHITECTURE.md` at root; mandatory minimum content (bird's-eye purpose, codemap, layer boundaries + invariants); auto-generated codemap with CI freshness check; graphical codemap at M/L.
- **Status:** **PARTIAL** — ARCHITECTURE.md at root (✓, A4 closed 2026-05-18); bird's-eye purpose (✓ §System Overview); codemap (✓ §Source Layout + Module Map + SVG diagrams under `docs/diagrams/system-context.svg`, `container-module.svg`, `magistrala-pipeline.svg`); layer boundaries + invariants (✓ §Dependency Layers, §Architecture Assessment); graphical depth (✓ SVG diagrams). **The gap:** codemap is **hand-maintained**, not auto-generated; no CI freshness check. ADR-51 §6 mandates "**CI check** regenerates the codemap and fails if the committed output differs — enforced from day one." This is upstream-gated: the codemap generator output specification is `.dev-knowledge` BACKLOG Stream C P2 (open), and the tool itself ships from `.dev-knowledge`. **Best-possible state under the upstream gap.**
- **Recommendation (deferred until upstream lands):** when `.dev-knowledge` ships the codemap generator + CI check, replace corp's hand-maintained SVG diagrams with the generated artifact (preserving hand-written invariants per ADR-51's "generation never overwrites the invariants" rule).

### ADR-52 — AGENTS.md convention (cross-tool agent-instruction contract)
- **Status:** **N/A — SUPERSEDED** — explicitly superseded by ADR-53 (2026-05-19). No conformance test active.

### ADR-53 — CLAUDE.md as single canonical agent-instruction file
- **Conformance test:** CLAUDE.md at root, ≤200 lines, 12-section template; no separate AGENTS.md as instruction file.
- **Status:** **CONFORMS** — CLAUDE.md present (148 lines, well under 200-line ceiling). All 12 sections present: §1 First read, §2 Repo identity, §3 Architecture (pointer), §4 Conventions, §5 Critical rules, §6 Session start protocol, §7 Slash commands, §8 Skills active, §9 Hooks active, §10 Anti-patterns, §11 Recent ADRs binding, §12 Section history. Top of file: `<!-- version: 2.1 — 2026-05-19 -->` matches the v2.1 template version. No per-repo AGENTS.md present (deleted 2026-05-20 per JOURNAL).

### ADR-54 — Codex reviewer config as global standard
- **Conformance test:** no duplicated Codex reviewer config in per-repo AGENTS.md; if a per-repo AGENTS.md exists, it carries only repo-specific overlay rules; global config at `~/.codex/AGENTS.md` (deployed from `.dev-knowledge/codex/AGENTS.md`).
- **Status:** **CONFORMS** — no per-repo `AGENTS.md` exists at all in corp-monorepo (deleted 2026-05-20 per JOURNAL "Delete corp-monorepo AGENTS.md entirely (ADR-54 complete)"). Repo-specific Codex content that previously lived in `corp-monorepo/AGENTS.md` ("Architecture Context," vault-writer invariant pointer, stale-package-names check) has been verified covered by ARCHITECTURE.md (Key Invariants §1) + CLAUDE.md §10 (anti-patterns). CLAUDE.md §10 first bullet explicitly: "The Codex reviewer config is global (`~/.codex/AGENTS.md`, ADR-54); corp-monorepo has no per-repo `AGENTS.md`."

---

## PLAYBOOK / ESSENTIALS conventions

### Commit message standard (ESSENTIALS §"Commit message standard")
- **Conformance test:** Conventional Commits, imperative summary, body required for non-trivial changes.
- **Status:** **CONFORMS** — `git log --oneline` last 5: `docs(audit):…`, `docs(journal):…`, `Merge branch 'docs/…'`, etc. All match `type(scope): summary` form. corp's CONTRIBUTING.md §"Commit Style" specifies the same standard.

### Starting a Session (ESSENTIALS §"Starting a Session")
- **Conformance test:** Claude Code session opens with `/boot`; Accept Edits as daily driver.
- **Status:** **CONFORMS** — CLAUDE.md §6 lists `/boot` as step 1. `/boot` skill is loaded user-level (per session-start system-reminder).

### Ending a Session (ESSENTIALS §"Ending a Session")
- **Conformance test:** full test suite → `git status` clean → codex-review if 3+ files / 2+ packages → JOURNAL.md entry in ADR-49 shape.
- **Status:** **CONFORMS** — JOURNAL.md entries follow Did/Result/Changes/Abandoned/Next exactly (verified 2026-05-18 / 2026-05-19 / 2026-05-20 entries). `./scripts/dev-check.ps1` and `./scripts/run-all-tests.ps1` referenced in CLAUDE.md §5 cover the test + clean-status step.

### Three-layer flow (ESSENTIALS §"Roles")
- **Conformance test:** corp does not perform browser-chat strategic functions; corp accepts prompts from browser → executes.
- **Status:** **CONFORMS** — corp is purely an executor repo. No browser-chat orchestration code. Architecture decisions go through `ai-council` (per VISION.md §Relationships).

### Architect → operator channel-discipline (ESSENTIALS §"Architect → operator channel-discipline for execution actions")
- **Status:** **N/A for corp** — governs browser-chat behavior, not repo content.

### Architect epistemic discipline (verification markers, completion claims)
- **Status:** **N/A for corp** — governs browser-chat behavior.

### Artifact generation direction (ESSENTIALS §"Artifact generation direction")
- **Conformance test:** ADRs, audits, handoffs generated in Claude Code with proper repo path, ADR-NN numbering, frontmatter, commit hygiene.
- **Status:** **CONFORMS** — recent ADR creations (corp ADR-30, ADR-31 on 2026-05-18) generated by Claude Code; numbered correctly; live in `docs/decisions/` with the canonical template structure. Audits (`2026-05-20-corp-monorepo-deep.md`, this file) generated by Claude Code with proper path and frontmatter.

### Supersession closes the loop (ESSENTIALS §"Supersession closes the loop")
- **Conformance test:** decisions that relocate/replace artifacts name the obsolete artifact in a `Decommission:` field; field becomes a BACKLOG item until removed.
- **Status:** **CONFORMS** — corp's `docs/decisions/README.md` step 3 explicitly: "Fill in the `Decommission:` field — list files/folders/sections this ADR makes obsolete, or write 'none'." Recent corp ADR-30 ("Retire CHANGELOG"), ADR-31 ("Retire single-file HANDOFF"), and ADR-27 ("Safety Invariants") all use the convention.

### Three Homes for Knowledge (ESSENTIALS §"Three Homes for Knowledge")
- **Conformance test:** client/product/domain intel → Obsidian vault; how-I-work → `.dev-knowledge`; runtime rules → `~/.claude/`.
- **Status:** **CONFORMS** — CLAUDE.md §4 "Out of scope for this repo: Client/pre-sales data → Obsidian vault; Cross-repo lessons → `.dev-knowledge/LESSONS.md`" exactly mirrors the three-homes split.

### Project Scale Tiers (ESSENTIALS §"Project Scale Tiers")
- **Conformance test:** scale declared in CLAUDE.md; tier-specific obligations met.
- **Status:** **CONFORMS** — CLAUDE.md §2: "Scale: L" declared. L-tier obligations met: ARCHITECTURE.md present, per-module READMEs exist (per CLAUDE.md §10 cross-references), 2495+ tests (per JOURNAL 2026-04-15 entries), `docs/decisions/` populated.

### Data Sanitization for Lessons (ESSENTIALS §"Data Sanitization for Lessons")
- **Status:** **N/A for corp** — corp has no LESSONS.md; lessons sanitization applies at the `.dev-knowledge` LESSONS.md boundary.

### Continuous Improvement (ESSENTIALS §"Continuous Improvement")
- **Conformance test:** VISION.md Lifecycle reflects continuous-improvement posture, not frozen-state framing.
- **Status:** **CONFORMS** — corp VISION.md §Lifecycle: "VISION is a **living, verifiable document** — not a one-shot statement"; review triggers (not deadlines); "**Vision realized:** propose next horizon." Matches ESSENTIALS pattern.

---

## Dev standards

### Click CLI framework
- **Status:** **CONFORMS** — `pyproject.toml` line 13: `click>=8.1` is a top-level dependency; five CLI entry points (`corp`, `corp-meta`, `cke`, `cpe`, `com`) registered in `[project.scripts]`.

### Rich library (terminal output)
- **Status:** **CONFORMS** — `pyproject.toml` line 34: `rich>=14.0` is a top-level dependency; CLAUDE.md §3 mentions Rich terminal use; ARCHITECTURE.md §Design Patterns references Rich.

### pytest test framework
- **Status:** **CONFORMS** — `pyproject.toml` line 45: `pytest>=8.0` in `[project.optional-dependencies] dev`; line 64–67: `[tool.pytest.ini_options]` testpaths = `["tests"]`, pythonpath = `["src"]`. `tests/` directory present with test files prefixed `test_*.py` (per JOURNAL "2495 tests passing").

### src/ layout (PEP 517)
- **Status:** **CONFORMS** — `pyproject.toml` line 57–58: `[tool.setuptools.packages.find] where = ["src"]`. `src/corp/` namespace verified.

### Tach module enforcement
- **Status:** **CONFORMS** — `tach.toml` at root: 4 layers (interface > orchestration > core > foundation), 34 modules mapped, `exact = true`, `forbid_circular_dependencies = true`. Pre-commit hook `tach-check` (`.pre-commit-config.yaml` line 13–17). Codified in corp's own ADR-26.

### pre-commit hooks
- **Status:** **CONFORMS** — `.pre-commit-config.yaml` configures ruff (linting/formatting), tach-check (layer enforcement), normalize-headers (idempotent JOURNAL/LESSONS rewrites). No scope-tagging hook (correctly retired per ADR-48). No secret scanning hook present — see "Recommendation" in §Recommendations below if this is treated as a gap.

### Naming conventions (Python / config)
- **Status:** **CONFORMS** — Python modules snake_case (per `src/corp/` listing: `vault_io.py`, `query_engine.py`, `intent_router.py`, etc.); ruff config in `pyproject.toml` line 69–76 enforces it. Config files `tach.toml`, `pyproject.toml`, `paths.toml` use kebab/lowercase per language convention.

### Conventional Commits
- **Status:** **CONFORMS** — verified in CONTRIBUTING.md "Commit Style"; recent commits match. (Repeat of ESSENTIALS bullet — listed here for the dev-standards rollup.)

### Default branch = `main`
- **Status:** **CONFORMS** — (see ADR-30 above).

### No hardcoded secrets
- **Status:** **CONFORMS** — CLAUDE.md §5 rule 3: "API keys in env vars ONLY — loaded from `~/Documents/.secrets/.env`; NEVER in config files or code." 2026-05-20 deep audit confirmed "zero committed secrets" and "GEMINI_API_KEY canonical."

### pathlib + forward slashes
- **Status:** **CONFORMS** — CLAUDE.md §5 rule 7: "Forward slashes everywhere in databases and stored paths." 2026-05-20 deep audit: "forward-slash convention 100% compliant (0 os.sep / os.path.join in src/corp/)."

### Type hints (Codex Medium checklist)
- **Status:** **CONFORMS — substantially** (no exhaustive count; pyproject.toml + ruff rules + recent Codex audits cited in JOURNAL imply broad compliance). Per-function detailed scan is out of scope for a conformance audit.

---

## Codex reviewer config

> Canonical source: `.dev-knowledge/codex/AGENTS.md`. Deployed to `~/.codex/AGENTS.md`. Per ADR-54, no per-repo AGENTS.md unless genuinely repo-specific.

- **Global config present and correctly cited:** CLAUDE.md §10 first bullet names `~/.codex/AGENTS.md` and ADR-54 explicitly. **CONFORMS.**
- **No duplicated reviewer config in corp-monorepo:** corp-monorepo/AGENTS.md absent (deleted 2026-05-20). **CONFORMS.**
- **ARCHITECTURE.md present so the global config's "read ARCHITECTURE.md first" directive can land:** ARCHITECTURE.md at root (429 lines). **CONFORMS.**
- **Per-repo overlay (would add only repo-specific rules if needed):** absent — that's the explicit conformant state per ADR-54 ("Per-repo AGENTS.md files carry only repo-specific review rules" — corp has none unique enough to warrant an overlay file; vault-writer invariant + stale-package-names are covered by ARCHITECTURE.md + CLAUDE.md §10 which Codex reads via fallback). **CONFORMS.**

---

## Corp-monorepo ADR cross-reference

> Section per the 2026-05-20 design decision (AskUserQuestion: "Yes, dedicated section"). Lists corp's local ADRs that explicitly interact with, extend, specialize, or risk silently diverging from a `.dev-knowledge` ADR.

| Corp ADR | Title | Interacts with `.dev-knowledge` ADR | Interaction type | Assessment |
|---|---|---|---|---|
| corp ADR-13 | Monorepo Package Architecture | `.dev-knowledge` ADR-38 (universal repo architecture) | **Predates** | corp ADR-13 (and its successor ADR-23) defined the `src/{package}/` pattern that `.dev-knowledge` ADR-38 later codified as the universal baseline. ADR-38 §"Migration approach" explicitly notes "corp-monorepo (already has src/corp/, tests/, pyproject.toml — verify minor details)" as the canonical reference implementation. **No reconciliation needed** — corp's pattern is the source of the universal standard. |
| corp ADR-14 | Naming Convention v2 (date-first, `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`) | `.dev-knowledge` ADR-34 (file naming convention, universal hyphen) | **Specializes / different domain** | corp ADR-14 governs **Obsidian vault file names** (MyWork content); `.dev-knowledge` ADR-34 governs **repo file names**. Underscore separator in corp ADR-14 vs hyphen mandate in `.dev-knowledge` ADR-34 → looks like conflict but isn't (different file domains). **Risk:** CLAUDE.md §4 cites corp ADR-14 pattern without explicitly disambiguating "this is for vault files, not repo files" — see GAP/Recommendation in §Summary. |
| corp ADR-23 | Monorepo Internal Architecture (flatten, centralize, delete dead code) | `.dev-knowledge` ADR-38 (universal repo architecture) | **Extends / specializes for L scale** | corp ADR-23 prescribes flattened `src/corp/` namespace consolidating 6 former packages — the L-scale outworking of ADR-38's universal `src/{package}/` baseline. ADR-23 also references "Amended by ADR-27" (per JOURNAL 2026-05-18 entry). **No conflict.** |
| corp ADR-26 | Tach Import Boundary Enforcement | `.dev-knowledge` dev standards / `.dev-knowledge` ADR-50 (ADR-50 ≠ Tach — that was a Phase-1 inventory hallucination). The `.dev-knowledge` ADR set does not contain a "Tach mandate" ADR; Tach is a dev-standard choice, not a universal ADR. | **Specializes dev standard** | corp's 4-layer Tach taxonomy is a corp-specific architectural pattern (interface > orchestration > core > foundation). `.dev-knowledge` ADR-38 §"Module definition" references corp-monorepo's pattern as the canonical example for module-count metric. **No conflict.** |
| corp ADR-27 | Safety Invariants (OneDrive guard centralization + vault writer narrowing) | `.dev-knowledge` ADR-27 (scope tagging — **DIFFERENT decision, same number**) | **Numbering collision (cosmetic)** | Both repos independently used the number 27 in their own ADR namespace for unrelated decisions. CLAUDE.md §11 mentions "ADR-27 Vault writer narrowed" — clearly the corp-local one. **Risk:** an unprefixed cross-namespace reference; see GAP #2 in §Summary. |
| corp ADR-30 | Retire CHANGELOG.md | `.dev-knowledge` ADR-30 (default branch = main — **DIFFERENT decision, same number**); `.dev-knowledge` ADR-49 (consolidate past-recording files) | **Numbering collision + Implements** | corp ADR-30 implements `.dev-knowledge` ADR-49's "CHANGELOG removed" decision specifically for corp-monorepo. Same-number coincidence with `.dev-knowledge` ADR-30 default-branch decision. **Functionally consistent** with `.dev-knowledge` ADR-49 (extends/applies), but the number coincidence is the namespace-collision issue. |
| corp ADR-31 | Retire single-file HANDOFF | `.dev-knowledge` ADR-31 (authority model — **DIFFERENT decision, same number**); `.dev-knowledge` ADR-32 / ADR-42 (handoff format evolution) | **Numbering collision + Implements** | corp ADR-31 implements the move to `.dev-knowledge`-owned handoffs (per `.dev-knowledge` ADR-36 read-only contract + ADR-42 folder format). Same-number coincidence with `.dev-knowledge` ADR-31 authority-model decision. **Functionally consistent** with the upstream ADRs. |

**Pattern observed:** corp's ADR-27 / ADR-30 / ADR-31 all happen to collide with `.dev-knowledge` ADR numbers of the same value, governing entirely different decisions. CLAUDE.md §11 mixes both namespaces. This isn't a logic conflict — but it is a discoverability/communication risk for new contributors and AI agents.

**Skip note:** corp ADR-28 / ADR-29 are intentionally reserved (per `docs/decisions/README.md` skip-note) for future Council distillations; no interaction with `.dev-knowledge` ADR-28 (three-layer architecture) or ADR-29 (LESSONS grandfathering).

---

## BACKLOG open items (cross-references to `.dev-knowledge` BACKLOG)

> Items here name corp-monorepo explicitly or gate corp conformance on upstream tooling. From `.dev-knowledge/BACKLOG.md` reading.

| `.dev-knowledge` BACKLOG item | Status | Corp-side action |
|---|---|---|
| **Stream A: corp-monorepo** — "(no items currently — populate as Phase 2 universalization begins)" | Empty | **N/A — placeholder only.** |
| **Cross-stream P2: "Phase 2 universalization rollout"** — explicit mention: "corp-monorepo: not yet started" | **Stale upstream** | **GAP (stale label, not actionable corp-side):** corp-monorepo Phase 2 substantively executed 2026-05-18 (VISION at root, ARCHITECTURE at root, BACKLOG seeded, JOURNAL ADR-49 shape, CHANGELOG retired, HANDOFF retired). Recommend `.dev-knowledge` BACKLOG refreshes the status (upstream concern). |
| **Cross-stream P2: "VISION.md tier declarations across ecosystem"** — "Other repos: pending" (post-ai-council) | **Resolved corp-side** | corp VISION.md declares `tier: standard, scale: L` (2026-05-18). Upstream BACKLOG can mark corp resolved. |
| **Cross-stream P2: "Skills universalization across repos"** | Open upstream | corp has only `.claude/skills/gotchas/` (corp-specific). No corp-side action without upstream classification framework. |
| **Cross-stream P1: "Sacred-files maintenance enforcement"** (8 files in `.dev-knowledge` post-CHANGELOG-deletion; child repos may keep CHANGELOG) | Open upstream | corp's 8-file canonical set (VISION, CLAUDE, ARCHITECTURE, JOURNAL, BACKLOG, CONTRIBUTING, README, no LESSONS, no CHANGELOG) is all present. Awaits upstream mechanism design. |
| **Cross-stream P2: "Hooks audit + consolidation"** | Open upstream | corp's hooks are minimal: ruff + tach-check + normalize-headers (pre-commit) and `.claude/settings.json` session-start hook. Awaits upstream inventory framework. |
| **Stream C P2: "Codemap generator output specification (ADR-51 open item)"** | Open upstream | corp's ARCHITECTURE.md codemap is hand-maintained graphical SVGs; this is the best-available state under the upstream gap. Will reconcile when generator ships. |
| **Cross-stream P2: "corp-monorepo hyphen migration + ADR-38 compliance"** | Partially resolved | corp's ADR-38 root-placement (ARCHITECTURE.md, VISION.md, BACKLOG.md, LESSONS.md not needed) completed 2026-05-18. Hyphen-migration for legacy `docs/archive/` UPPERCASE_TYPE files remains pending (P3 opportunistic per upstream BACKLOG). |
| **Cross-stream P3: "Apply scrum-master review pattern to other child repos"** | Open upstream | corp listed as priority #1 for next scrum-master review. No corp-side action until upstream codifies the pattern (N=2 grounding pending). |
| **Cross-stream P3: "UPPERCASE TYPE tag in legacy archive filenames (A5 — retire opportunistically)"** | Open | Opportunistic — handled when next touching `docs/archive/*` files. **CONFORMS to opportunistic posture** (no dedicated migration warranted). |

**Items gated on upstream tooling (UNKNOWN/N/A pending upstream):**
- Codemap generator (ADR-51 mandatory minimum); CI freshness check (ADR-51 §6)
- Audit tool P1 (ADR-36); algorithmic tier computation (ADR-40)
- Lessons activation P1 (ADR-35: index, retrieval, querying)
- Contradiction detection mechanism (Cross-stream P1: Council decisions management consolidation)
- Skills universalization framework (Cross-stream P2)

---

## Recommendations (corp-monorepo actionable)

> Prioritized by effort × impact. Upstream-gated items not listed — they appear in §BACKLOG above with their gating notes.

| # | Pri | Recommendation | Effort | Impact |
|---|---|---|---|---|
| R1 | P3 | Disambiguate CLAUDE.md §4 naming-convention bullet: clarify that `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` is for **vault/MyWork files** only; repo files (ADRs, audits, JOURNAL/BACKLOG) follow `.dev-knowledge` ADR-34 hyphen convention. | ~5 min | Removes a silent drift risk; clarifies new-contributor onboarding. |
| R2 | P3 | In CLAUDE.md §11, prefix cross-namespace ADR references with their source (e.g., `corp ADR-27` vs `.dev-knowledge ADR-42`). | ~10 min | Removes namespace-collision ambiguity. The 7 ADR references in §11 currently mix the two namespaces. |
| R3 | P3 | Flag stale `.dev-knowledge` BACKLOG entry "Phase 2 universalization rollout — corp-monorepo: not yet started" via the next `.dev-knowledge` session (cross-repo coordination — **not a corp-side change**). | upstream | Refreshes ecosystem visibility into actual corp-monorepo state. |

**No P1 or P2 corp-side gaps surfaced.** All material conformance items are CONFORMS or N/A; the partials and UNKNOWNs are either deliberately gated on upstream or are cosmetic discoverability concerns.

---

## Verification (post-audit checks)

End-to-end audit check:

1. `git log --oneline -3` on `main` after merge — audit commit and merge commit visible.
2. This file (`docs/audits/2026-05-20-conformance-gap-vs-dev-knowledge.md`) opens; summary table is at top; every `.dev-knowledge` ADR 27–54 has a block; every GAP has a one-line recommendation.
3. `JOURNAL.md` tail entry summarizes GAP count consistent with this audit.
4. `git diff main..HEAD --stat` shows only `docs/audits/2026-05-20-conformance-gap-vs-dev-knowledge.md` and `JOURNAL.md` changed.
5. Cross-spot-check: any 3 ADRs picked at random — open `.dev-knowledge/docs/decisions/ADR-NN-*.md`, confirm the conformance test described matches the actual ADR text. (Done during authorship: ADR-30, ADR-38, ADR-51, ADR-53, ADR-54 all spot-verified against the live ADR files.)
