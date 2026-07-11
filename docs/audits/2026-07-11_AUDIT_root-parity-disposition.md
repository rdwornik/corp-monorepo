# Root-surface parity disposition — corp-monorepo

**Date:** 2026-07-11 · **Status:** applied · **Owner:** Rob
**Scope:** every root file/folder divergence of `corp-monorepo` vs the `.dev-knowledge` hub and the
reference consumer `ai-council` (rolled out on methodology **v1.3.1**). Evidence base: the
2026-07-08 fleet-consistency census + the 2026-07-11 fleet boundary matrix, **re-derived live**.

This is the committed evidence artifact for the v1.3.1 rollout's root-surface consolidation. Each row
carries one verdict — **CARRIED** (hub-owned; bring to parity now) / **LOCAL** (legitimately
project-specific; recorded in `.methodology.yaml` where it diverges from a fleet-generic expectation) /
**IGNORE** (caches; ensure gitignored, never committed).

## Disposition table

| # | Root entry | corp state (pre-rollout) | hub / ai-council expectation | Verdict | Action taken |
|---|---|---|---|---|---|
| 1 | `INSTALL.md` | absent | hub-canonical, deploy-carried (#315); ai-council carries verbatim | **CARRIED (interim manual copy)** | byte-identical manual copy from hub `plugins/tier1-lifecycle/INSTALL.md` (blob `68b9acd5`). Interim per the ai-council #315 pattern; the durable mechanism (manifest-carried doc artifact) is hub #315 — **until it lands, this file WILL drift on the next hub canonical change**. |
| 2 | `.pre-commit-config.yaml` hub block | `../.dev-knowledge` @ `v1.2.0`; toc-freshness + toc-generate only | GitHub URL @ `v1.3.1` + `backlog-id-on-close` + `block-ff-push` (ai-council) | **CARRIED** | repointed to `https://github.com/rdwornik/dev-knowledge` @ `v1.3.1`; added the two enforcement gates; removed the stale `69558c7` pin comment. |
| 3 | `CLAUDE.md` Form-A markers | none | inline `owner=hub/repo` markers per section | **CARRIED** | 11 marker regions grandfathered (marker-only, prose byte-identical) + a human-visible boundary note. owner=hub = first-read, conventions-commit-branch (§4 sub-span), session-start-protocol (§6 sub-span). |
| 4 | `.methodology.yaml` — codemap exclusion | documented only in a config comment | ai-council records a `hub-codemap-hooks` waiver | **LOCAL** | added `hub-codemap-hooks` sanctioned-divergence entry (machine-readable for the hub Informant), mirroring ai-council. |
| 5 | `.methodology.yaml` — `ruff-gate` | present (own ruff v0.15.8) | corp-only divergence | **LOCAL** | kept as-is (no change). |
| 6 | `assets/` | absent | ai-council tracks `assets/ruff-pre-commit.yaml` (referenced by INSTALL.md §2) | **LOCAL** | **not carried** — corp runs its own ruff gate (recorded divergence, row 5); a byte-copy would be unused. INSTALL.md §2's `assets/` reference is inert generic guidance for corp. |
| 7 | dot-caches (`.ruff_cache/`, `.pytest_cache/`, `.hypothesis/`) | gitignored, **untracked** | gitignore policy uniform; cache presence project-specific | **IGNORE** | verified gitignored + untracked (`git ls-files` on caches = empty). No removal needed; nothing tracked to report. |
| 8 | `.gitattributes` | present, correct (`* text=auto eol=lf`) | uniform fleet-wide | **LOCAL** (parity met) | no action — corp already conforms (ahead of most consumers). |
| 9 | `tach.toml` | present | project-specific (monorepo package boundaries) | **LOCAL** | no action. |
| 10 | `protocols/` | absent (references hub `../.dev-knowledge/protocols/`) | #314 ruled a methodology-mandated genre; not yet delivered to corp | **LOCAL** (deferred #314) | no action this rollout — pending hub #314 delivery; reported hub-side. corp references the hub protocols/ by design. |
| 11 | `.env` `.venv/` `logs/` `output/` `data/_outputs/` | gitignored | project-local ephemeral | **IGNORE** | no action — already gitignored. |
| 12 | 7 UPPERCASE living docs, `pyproject.toml`, `.corp-monorepo.code-workspace`, `.gitignore` | present, conform | methodology-generic core set | **LOCAL** (parity met) | no action — already conform. |

**No tracked caches** exist, so no tracked history was removed anywhere in this rollout.

## Locked operator decisions (2026-07-11)

1. **Hub pin form → GitHub URL** (row 2): one fleet convention; the relative path couples the gates to
   local disk layout + working-tree state rather than the published tag.
2. **Boundary note → "markers are the map"** (row 3): the inline `owner=` markers are the machine map;
   no second owner-map copy in `.methodology.yaml`.
3. **assets/ → LOCAL, don't carry** (row 6): an unused byte-copy is decorative parity; the divergence
   is already sanctioned and recorded.
4. **canonical_freshness A2**: any edit to a freshness-tracked canonical doc re-stamps its
   `last_reviewed` in the same commit (applied to ARCHITECTURE.md and CLAUDE.md).

## Applied on branch `chore/methodology-v1.3.1-rollout`

| commit | change |
|---|---|
| `efe5bd1` | W-A pre-commit carrier → v1.3.1 GitHub URL + block-ff-push + backlog-id-on-close |
| `21910a7` | W-B `.methodology.yaml` hub-codemap-hooks waiver |
| `d3dddfe` | W-C root INSTALL.md byte-identical carry (interim) |
| `2b84e4e` | W-D ARCHITECTURE.md §Authority ADR-31/Layer-2 citation split (D4) + re-stamp |
| `8ddf67b` | W-E CLAUDE.md Form-A markers + boundary note + §9 reconcile + v2.6 |

**Enforcement witnessed (v1.3.1 `block-ff-push`)** — in a disposable clone + throwaway bare remote
against the post-merge main state (real corp main/origin untouched): a direct-to-main non-merge push
was **REFUSED** (`block_ff_push: REFUSED — 1 non-merge commit(s) would land on main's first-parent
spine`, exit 1); a `--no-ff` merge push **passed** (exit 0). The gate resolves identically in corp
main and ai-council.

## Hub-side findings (reported, not applied from here — core-invariant #6)

- `deployed_methodology_version` for corp lives hub-side (`ecosystem/state.yaml`), not in corp — needs
  a bump to 1.3.1 there.
- `INSTALL.md` durable carrier is hub #315 — until it lands, corp's copy drifts on hub changes (row 1).
- `protocols/` delivery to corp is pending hub #314 (row 10).
- `/save` command is a genuine gap → route via hub BACKLOG (sibling to #280); do not improvise a local
  copy. `/handoff` absence is intentional (ADR-36).
- The hub's staged draft (`2026-07-12-…-rollout`) omitted INSTALL.md / root-surface / `.methodology`
  sections that the boundary matrix + census require — a draft gap to reconcile.
- Hub carriers now consumed by corp: #302 (`block-ff-push`), #309/commit-msg (`backlog-id-on-close`).
  #308 (gotchas half-adoption) not addressed this rollout.
