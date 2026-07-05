# Estate Recon Snapshot — 2026-07-05

> Read-only point-in-time snapshot. Part 1 (Wave-2 merge closure) + Part 2 (four-root reconnaissance). No fixes, no cleanup — metadata only. Produced on branch `docs/estate-recon`.

---

## Part 1 — Wave-2 merge closure (idempotent)

All six Wave-2 audits were **already merged** into `main` in the prior session (`77ca967`→`c73bd6c`, all `--no-ff`). This run confirmed state and did housekeeping only — no re-merges, no STOPs.

| Audit | Already merged? | Branch merged | Feature commits | Deliverables now on `main` | Leftovers / STOP |
|-------|:---:|---------------|:---:|----------------------------|------------------|
| rfp | ✅ | `worktree-cm-deep-rfp` ¹ | 2 | `2026-07-05-deep-rfp.md` + `.html` | — |
| vault | ✅ | `docs/deep-vault` | 3 | `2026-07-05-deep-vault-metadata.md` + `.html` ² | — |
| magistrala | ✅ | `docs/deep-magistrala` | 3 | `2026-07-05-deep-magistrala.md` + `.html` | — |
| extraction | ✅ | `docs/deep-extraction` | 3 | `2026-07-05-deep-extraction.md` + `.html` | — |
| dealloop | ✅ | `docs/deep-dealloop` | 2 | `2026-07-05-deep-dealloop.md` + `.html` | — |
| mywork | ✅ | `docs/deep-mywork` | 3 | `2026-07-05-deep-mywork.md` + `.html` | — |

**12 / 12 deliverable files present** (6 `.md` + 6 `.html`). All candidate branches (`docs/deep-*`, `worktree-cm-deep-*`) already deleted; no worktrees registered. No name had both candidates carrying commits → STOP rule never triggered.

¹ `docs/deep-rfp` never existed; only `worktree-cm-deep-rfp` carried the audit commits, so it was the deliverable.
² vault's files use the audit's own `-vault-metadata` suffix.

**Leftovers (cosmetic, out of scope for this snapshot):**
- `worktree-docs+deep-rfp` — empty non-candidate branch (0 commits vs `main`), left untouched (not one of the two named candidates).
- `.claude/worktrees/cm-deep-vault/` — orphaned directory: `git worktree remove` de-registered it from git, but the on-disk delete hits a Windows lock ("used by another process"). Gitignored, absent from `git worktree list`, no repo impact. Delete manually once the locking process (editor/indexer) releases it.

**Sanity:** `pytest -x -q` → **2588 passed, 5 skipped** (identical to prior session — docs-only merges stayed green). `git status` clean, `main` == `origin/main`.

### corp-ops spike
`docs/2026-07-05-x1-backup-proposal.md` is present on corp-ops `main` (`2653841`, `docs: merge X1 backup feasibility spike`); the `spike/x1-backup-feasibility` branch is already deleted. **Not pushed — corp-ops has no git remote configured.** The merge (and all corp-ops history) exists only on the local disk. Merging the proposal does not start the build (build waits on the two operator auth steps).

---

## Part 2 — Four-root reconnaissance

### Root A — `C:\Users\1028120\Documents\Dev` (repos)

| Repo | Git remote | Last commit | Working tree | Branch | Approx size |
|------|-----------|-------------|:---:|--------|------:|
| `ai-council` | ✅ origin (github rdwornik/ai-council) | 2026-07-05 | clean | main | 351 MB |
| `corp-monorepo` | ✅ origin (github rdwornik/corp-monorepo) | 2026-07-05 | clean | main | 18 GB ³ |
| `corp-ops` | ❌ **NONE** | 2026-07-05 | clean | main | 65 MB |
| `corp-sca-time-automation` | ✅ origin (github) | 2026-07-05 | clean | **feature/tenrox-loader** | 241 MB |
| `illustrated-book-gen` | — not a git repo | — | — | — | 678 MB |
| `overnight` | — not a git repo | — | — | — | 28 KB |
| `terminal-setup` | ✅ origin (github) | **2026-02-18** | clean | main | 112 KB |

³ Dominated by gitignored `data/_outputs` (~18 GB regenerable); tracked tree is a fraction of this.

### Root B — `C:\Users\1028120\Documents\MyWork` (vs deep-mywork baseline, same 2026-07-05 day)

| Zone | Files (now) | Size | Newest mtime | Δ vs deep-mywork census |
|------|:---:|------:|:---:|-------------------------|
| `00_Inbox` | 75 | 221 MB | 2026-04-10 | **= unchanged** (still frozen, inflow stopped) |
| `10_Projects` | 617 | 6.11 GB | 2026-07-03 | −3 (620→617) |
| `15_Extra_Inititives` | 63 | 84.4 MB | 2026-05-15 | = |
| `20_Workflows` | 29 | 217 MB | 2026-04-02 | −1 (30→29) |
| `30_Reference` | 1,354 | 3.54 GB | 2026-07-05 | −2 (1,356→1,354) |
| `70_Admin` | 17 | 0.8 MB | 2026-03-26 | — |
| `80_Compliance` | 29 | 13.7 MB | 2026-04-24 | — |
| `90_Archive` | 0 | 0 | n/a | = (empty shell) |
| `.corp` | 46 | 9.4 MB | 2026-03-30 | (config, not in zone census) |
| `.claude` | 2 | ~0 | 2026-03-22 | — |
| loose root | 2 | — | — | `CLAUDE.md`, `README.md` (= baseline) |

**Total ≈ 2,234 files vs baseline 2,236 (−2 net).** No new top-level dirs. Inbox count and newest-mtime identical to the deep-mywork audit — no material drift; the small negative deltas are transient (Office `~$` locks / same-day churn).

### Root C — `C:\Users\1028120\OneDrive - Blue Yonder\MyWork_OneDrive` (mirror)

**⚠️ Enumeration BLOCKED.** Live directory enumeration was refused at the tool layer by the fail-closed OneDrive-exclusion hook (P0 safety guard), even though the operator authorized the constrained read in chat. The machine guard overrides chat consent — working as designed. **No current L1/L2 dir listing or name-level diff is available this session.**

Cited from the **2026-06-16 current-state audit** (`--include-onedrive`, metadata-only, no hydration) — do not treat as live:

| Metric | Value |
|--------|------:|
| Files | 159,826 |
| Dirs | 30,233 |
| Size | 1.1 TB |
| Cloud-only | 153,547 (96%) |
| Max depth | 20 |
| No-convention filenames | 133,241 (83%) |
| Junk dirs | 274 |
| Names shared with local trees (by-name) | 986 |

For a live mirror snapshot, use the enumerated/authorized path — `python scripts/current_state_audit.py --include-onedrive` — not an ad-hoc `Get-ChildItem` (which the hook blocks).

### Root D — `C:\Users\1028120\Documents\ObsidianVault`

| Zone | Files | Newest mtime |
|------|:---:|:---:|
| `01_Knowledge` | 814 | 2026-03-27 |
| `_quarantine` | 23 | 2026-03-27 |
| `02_Navigate` | 18 | 2026-03-27 |
| `_assets` | 11 | 2026-03-27 |
| `99_System` | 5 | 2026-03-26 |
| `00_Home` | 1 | 2026-03-23 |
| `.obsidian` | 10 | 2026-06-16 |
| `.claude` | 2 | 2026-03-22 |
| loose root | 2 | — |

**Git state:** remote **NONE**; branch `master`; last commit **2026-03-26** (`1f75647` chore: quarantine 20 fragment-quality notes); **259 uncommitted changes**. The 814-note knowledge base matches the deep-vault audit's ~813 figure. Content mtimes are frozen at March 27 (matches deep-vault's read-only/dormant picture); the 259 uncommitted changes are the post-03-26 restructure state never committed.

---

## Anomaly list

1. **ObsidianVault is unbacked and uncommitted.** No git remote + last commit 2026-03-26 + **259 uncommitted changes** → the entire current 814-note vault exists only in a single-disk working tree. One disk failure = total loss of irreplaceable knowledge. This is precisely the X1 backup gap.
2. **corp-ops has no remote** → the X1 backup *proposal* (and all corp-ops history) is local-only and unpushable — the repo documenting the backup plan is itself unbacked.
3. **corp-sca-time-automation is on a WIP feature branch** (`feature/tenrox-loader`, not `main`; clean, last commit today) — active work in progress; worth a merge/ship decision.
4. **Root C recon blocked** — the fail-closed OneDrive hook overrode operator chat-authorization; ad-hoc `Get-ChildItem` cannot read the mirror. Future mirror recon must go through the enumerated audit tool. `terminal-setup` is also long-stale (last commit 2026-02-18) — likely fine, flagged for completeness.
5. **corp-monorepo housekeeping remnants** — orphaned gitignored dir `cm-deep-vault` (Windows lock, cosmetic) + empty non-candidate branch `worktree-docs+deep-rfp`. **MyWork is essentially unchanged** vs the same-day deep-mywork baseline (−2 files net, inbox frozen at 75, no new top-level dirs).
