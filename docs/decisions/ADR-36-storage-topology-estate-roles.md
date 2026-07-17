# ADR-36: Storage topology — estate roles

- **Status:** Accepted
- **Date:** 2026-07-17
- **Decision tier:** Technical-architect intake triage (Path A), 2026-07-06 decision register DR-12
- **Related:** ADR-34 (vault as essence layer — this ADR names the vault's role in the topology by reference to ADR-34's decision); ADR-27 (safety invariants — OneDrive guard centralization; the mechanical enforcement of this topology's write boundaries); ADR-35 (backup topology for the precious subset of this estate)
- **Intake:** `docs/audits/2026-07-06-technical-architect-intake.md`, DR-12
- **Decommission:** none — this ADR records a topology; it does not remove any existing file or folder. (The planned `Sharing_Files` folder under `MyWork_OneDrive` is a future addition, not a decommission.)
- **Source:** 2026-07-06 technical-architect intake decision register (ratified); evidence in `docs/audits/2026-07-05-estate-recon.md` §Part 2 and `docs/audits/2026-07-05-deep-mywork.md`

## Context

The estate spans four physical roots with no prior canonical statement of what each one is *for*. The 2026-07-05 estate recon's four-root reconnaissance (`docs/audits/2026-07-05-estate-recon.md` §Part 2) measured all four in one pass:

- **Root A — `Dev/`** (this repo and its siblings): `corp-monorepo` 18 GB (dominated by gitignored, regenerable `data/_outputs/`), clean, remote-backed on GitHub.
- **Root B — `MyWork/`** (local): 2,236 files / ~10.2 GB across the 7 declared zones plus `.corp` (`docs/audits/2026-07-05-deep-mywork.md` §1 one-line verdict); a same-day cross-check in the recon found 2,234 (−2 net, no material drift; inflow frozen, no new top-level dirs). Actively edited (`30_Reference` newest mtime same-day as the recon), and **no backup of any kind** for locally-authored content.
- **Root C — `OneDrive - Blue Yonder\MyWork_OneDrive`** (the synced mirror): live enumeration was **fail-closed BLOCKED** by the P0 OneDrive-exclusion hook even under operator chat-authorization — "the machine guard overrides chat consent, working as designed." Figures cited (not live) from the 2026-06-16 audit: 159,826 files / 1.1 TB, 96% cloud-only.
- **Root D — `ObsidianVault/`**: 814 files, git remote **NONE**, last commit 2026-03-26, 259 uncommitted changes.

The deep MyWork audit independently confirms the *functional* character of these roots (`docs/audits/2026-07-05-deep-mywork.md` §1, §5): `MyWork` is where actual deal work happens today — the declared "hot zone" `20_Workflows` is cold at 30 files while the real production studio lives 96%-undeclared inside `30_Reference/Training/…Warsaw/`. `MyWork/.corp` carries a live routing/registry config that has **diverged from its repo twin** (21.4 KB live vs 4.8 KB in `config/content_registry.yaml`, both stale since March) — a split-brain this topology surfaces but does not itself resolve. Operator ground truth (intake §6) confirms `MyWork_OneDrive` is actively used by the human as the SharePoint navigation hub even though **no code path touches it today** — zero msal/graph/office365 imports exist anywhere in `src/corp/` (`docs/audits/2026-07-05-functional-artifact-lifecycle.md` §2.2 S2 trace).

The OneDrive constraint map (`functional-artifact-lifecycle.md` §2.2) is the mechanical floor this topology sits on: `config/paths.toml [safety] excluded_paths = ["OneDrive - Blue Yonder"]`; fail-closed mutation guards predate this ADR (`cleanup/disk.py`, `cleanup/executor.py`, `actions/_helpers.py`, `project/renderer.py`); the only two sanctioned reads FROM the mirror are `corp-ops/scripts/sync-mywork.ps1` (one-way, cloud→local, no `/MIR`/`/PURGE`/`/MOVE`) and the current-state audit tool's opt-in `--include-onedrive`; and **no code writes TO the mirror anywhere, today.**

## Decision

Adopt the following as the canonical estate map — the roles below are load-bearing, and later work (naming kernels, backup scope, zone-rename decisions) references this map rather than re-deriving it:

| Root | Role | Notes |
|---|---|---|
| `Dev/` | **Engine** — the code/build surface | Repos (`corp-monorepo` and siblings); git-remote-backed |
| `MyWork/` (local) | **Local master workbench** — the working truth | Active deal work; local-only, currently unbacked for locally-authored content (see ADR-35) |
| `MyWork_OneDrive` (the synced mirror) | **Navigation hub** (Teams/SharePoint shortcuts) **+ sharing surface** (a planned `Sharing_Files` folder) | Explicitly **NOT a code surface** — code never writes there, today or by design |
| Wider SharePoint (beyond the mirror) | **Read-only source terrain** | Foraged from (scout intake), never written to |
| `ObsidianVault/` | **Essence** | Per ADR-34's operating model (S0–S3 lifecycle, generated link spine, scheduled promotion) |

The load-bearing property is: **"code never writes `MyWork_OneDrive` or wider SharePoint."** This is not a new rule invented here — it is the existing OneDrive-exclusion invariant (ARCHITECTURE.md "OneDrive exclusion", `config/paths.toml [safety]`), and its mechanical enforcement is the centralized guard module **`src/corp/safety/onedrive.py`** (ADR-27 Decision 1: `guard_path()` / `is_onedrive_path()`, unifying the four pre-existing mutation-guard sites plus the `project/cli.py --copy-to-vault` fix), backed by the AST scanner `tests/safety/test_no_unguarded_writes.py`. This ADR ties its "code never writes there" property to that existing mechanism rather than asserting a new one.

## Consequences

**Positive:**
- Gives every future decision (backup scope, zone-rename input, workspace-class carve-outs like `15_Extra_Inititives` / Warsaw) a single named map to reference instead of re-deriving root roles from scratch each time.
- Makes the `MyWork_OneDrive`-as-navigation-hub reality explicit and sanctioned, rather than an implicit, undocumented human workaround around a system that otherwise only "declares" the mirror as a read source.
- Ties the write-boundary property to a mechanically enforced, tested guard (ADR-27's `corp.safety.onedrive` plus AST scanner) rather than to documentation-only discipline — the exact class of gap that caused INCIDENT 2026-03-14.

**Negative / risks:**
- The AST scanner's current scope (`tests/safety/test_no_unguarded_writes.py`, its `ROOTS` list) covers `src/corp/project/cli.py` only — the specific D6 gap (`--copy-to-vault`) the architecture ground-truth recon flagged. Full repo-wide enforcement across all of `src/corp/` is ADR-27 PR-3 and remains unshipped; this ADR's "mechanically enforced" claim is accurate for the sites covered today (the four original guard sites plus the D6 fix) and should not be read as blanket repo-wide coverage until PR-3 lands.
- `MyWork_OneDrive`'s "sharing surface" role names a **planned** `Sharing_Files` folder that does not exist yet — this ADR records intent, not a built feature.
- The `MyWork/.corp` vs `config/content_registry.yaml` split-brain (live 21.4 KB vs repo 4.8 KB, both stale since March) is a known defect this topology surfaces but does not resolve; it remains open backlog (`deep-mywork.md` seed F-8).
- Root C (the live mirror) could not be enumerated live during the 2026-07-05 recon — the fail-closed guard blocked it even under operator chat authorization. This ADR's Root C figures are cited from the 2026-06-16 audit, not verified fresh; a live re-measurement requires the enumerated audit tool (`scripts/current_state_audit.py --include-onedrive`), never an ad-hoc directory read.

## Done-when

- This topology is recorded in `docs/decisions/` as the canonical estate map (this ADR, on ratification) and is the map later work (backup scoping, zone-rename decisions, workspace-class carve-outs) cites rather than re-deriving.
- No code path writes to `MyWork_OneDrive` or the wider SharePoint terrain — necessary condition: `tests/safety/test_no_unguarded_writes.py` passes green over its current scope, `rg -in onedrive src/corp` surfaces no new unguarded write site beyond the centralized guard call sites, and the negative-witness check (zero msal/graph/office365 imports) still holds until a sanctioned Graph-upload leg (ADR-35) is built.

## Alternatives considered

Not separately evaluated as competing designs in the intake — this ADR ratifies the estate's *measured, already-operating* role assignments (what each root is actually used for today, per the deep-mywork and estate-recon evidence) rather than choosing among topology alternatives. The one open design choice — whether `MyWork_OneDrive`'s sharing surface becomes a real `Sharing_Files` folder now or later — is left to a future increment, not decided here.

## References

- `docs/audits/2026-07-06-technical-architect-intake.md` §5 (DR-12 row)
- `docs/audits/2026-07-05-estate-recon.md` §Part 2 (four-root reconnaissance)
- `docs/audits/2026-07-05-deep-mywork.md` §1 (zone census) and §5 (live-config vs repo-config split)
- `docs/audits/2026-07-05-functional-artifact-lifecycle.md` §2.2 (OneDrive constraint map)
- `docs/decisions/ADR-27-safety-invariants.md` (OneDrive guard centralization mechanism referenced above); `src/corp/safety/onedrive.py`; `tests/safety/test_no_unguarded_writes.py`
