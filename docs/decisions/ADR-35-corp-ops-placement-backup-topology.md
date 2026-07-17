# ADR-35: corp-ops repo placement and dual-leg backup topology

- **Status:** Proposed
- **Date:** 2026-07-17
- **Decision tier:** Technical-architect intake triage (Path A), 2026-07-06 decision register DR-10 + DR-11
- **Related:** DR-9 insurance actions — same intake register (`docs/audits/2026-07-06-technical-architect-intake.md` §5): vault git commit + X1 activation; ADR-27 (OneDrive-exclusion guard pattern this mechanism's Graph leg must respect)
- **Intake:** `docs/audits/2026-07-06-technical-architect-intake.md`, DR-10 and DR-11
- **Decommission:** none (repo scope). Operationally, the dead `MyWork GDrive Backup` Task Scheduler task is superseded by this mechanism and should be retired by the operator (see Context/Consequences) — not a repo file, so not tracked here as a formal Decommission item.
- **Source:** 2026-07-06 technical-architect intake decision register (ratified); evidence in `corp-ops` repo `docs/audits/2026-07-05-x1-backup-proposal.md` and corp-monorepo `docs/audits/2026-07-05-estate-recon.md` §Part 1

## Context

Two related gaps surfaced across the 2026-07-05 Wave-2 audits:

**Repo placement (DR-10).** `corp-ops` is a separate repository from `corp-monorepo` (65 MB, clean, branch `main`) but as of the 2026-07-05 estate recon carries **no git remote at all** (`docs/audits/2026-07-05-estate-recon.md` §Part 2 Root A). The X1 backup proposal itself — the very document describing how to back up the estate's precious data — exists only on local disk, in a repository that is itself unbacked. The corp-ops spike note in Part 1 confirms: "Not pushed — corp-ops has no git remote configured. The merge (and all corp-ops history) exists only on the local disk."

**Backup topology (DR-11).** The estate's precious set (~59.5 MB across the vault, RFP KB, `corp-by-os` DBs, and `MyWork/.corp`) has **zero backup** today. This is not a cold-start problem: a backup mechanism already existed and already rotted silently. Windows Task Scheduler's `MyWork GDrive Backup` task is still `Ready` and still fires daily, but has targeted a script (`C:\Users\1028120\Documents\Scripts\gdrive_backup.py`) that no longer exists — nearly four months of silent daily failure (`LastTaskResult = 0x80070002`, last successful run 2026-03-11), discovered only by the backup feasibility spike (`corp-ops/docs/audits/2026-07-05-x1-backup-proposal.md` §1). The companion `OneDrive to Local Sync` task also returns a nonzero result. The lesson the spike draws explicitly: **"the mechanism must be scheduled AND fail-loud. A schedule without alerting produced exactly the failure mode it was meant to prevent."** Separately, `ObsidianVault` itself has no git remote and 259 uncommitted changes as of the same recon (estate-recon.md Anomaly #1) — one disk failure from total loss, the single highest-consequence risk item across the whole estate (DR-9 addresses the git-commit half of this; DR-11 addresses the off-machine-copy half).

The feasibility spike (2026-07-05) proved both intended backup legs are technically reachable, each blocked on exactly one operator consent/auth step: the Blue Yonder OneDrive Graph API leg needs one interactive login with `Files.ReadWrite` scope (the default az CLI token carries no `Files.*` scope — confirmed via a live `AADSTS65002` consent error); the Google Drive leg needs one OAuth re-authorization (the existing `corp_ops.gdrive` refresh token is dead with `invalid_grant`, consistent with a Testing-mode consent screen expiring after 7 days).

## Decision

**DR-10 — corp-ops placement.** `corp-ops` **stays a separate repository** (not folded into `corp-monorepo`) and **gets a private remote**. No further restructuring of corp-ops is in scope of this decision.

**DR-11 — Backup topology.** Adopt a dual-leg, push-only, append-only backup mechanism for the estate's precious set:

1. **Snapshot stage (shared, local):** a nightly task stages one dated zip per precious-set member (`vault`, `rfp_kb`, `corp_by_os_db`, `mywork_corp`) under `%LOCALAPPDATA%\corp-ops\x1-backup\staging\` — never under any OneDrive-redirected path — plus a SHA-256 manifest.
2. **Leg A — Blue Yonder OneDrive, Graph API, upload-only.** HTTPS-only via Microsoft Graph to the operator's own drive (`/me/drive/root:/Backups/x1/...`), using a resumable upload session. This respects the OneDrive exclusion invariant: **no local synced-tree path is ever read from or written to** — the local OneDrive sync client is not involved at all; this is a pure cloud-side HTTPS push. Conflict behavior is `fail` (idempotent re-run only) — no overwrite, no delete, ever.
3. **Leg B — Google Drive, upload-only.** Reuse the existing `corp_ops.gdrive` module (OAuth + resumable `MediaFileUpload`, already implemented) after one re-authorization. Dated, create-only object names — never updated, never deleted.
4. **Both legs scheduled + heartbeat.** A success heartbeat file (`LAST_SUCCESS.txt`, UTC timestamp + manifest hash) is written on every green run; absence-of-success (not a failure flag) is the monitored condition, surfaced where the operator already looks (ecosystem health check) plus a desktop-visible failure artifact on any run failure. This directly answers the four-month silent-failure evidence in Context.
5. **Remotes are never pruned.** Retention is local-only (last 7 dated snapshot sets, deleted only inside the allowlisted staging root); both remote legs are strictly append-only forever.
6. **A restore drill is part of the done-contract, not an afterthought.** Downloading the latest vault zip from each leg, verifying its SHA-256 against the manifest, and confirming `git fsck --full` plus the expected HEAD on the unzipped vault (plus a DB integrity check) must succeed before the build counts as done, and repeats quarterly thereafter.
7. **Extension (not in this ADR's done-contract):** a MyWork delta backup leg (~10 GB of working deal documents) via the same Graph upload-only pattern, deferred as a later increment.

## Consequences

**Positive:**
- Closes the highest-consequence-to-effort-ratio risk in the estate: under 100 MB of genuinely irreplaceable data (vault, RFP KB, operational DBs, live `.corp` config) gains off-machine copies on two independent providers, while the 18.4 GB of regenerable extraction output is correctly left out of scope.
- The design is explicitly shaped by the prior failure: fail-loud heartbeat plus a mandatory restore drill directly target the exact failure mode (silent schedule death) that let the previous mechanism rot for four months undetected.
- corp-ops getting a remote also backs up the backup mechanism's own source and documentation — closing the "the proposal describing the backup plan is itself unbacked" anomaly.

**Negative / risks:**
- Two new external auth surfaces (Azure Graph scope consent, Google OAuth re-auth) are operator-gated prerequisites this ADR cannot execute itself — the build cannot start until the operator completes both interactive steps (x1 proposal §5).
- Google OAuth in Testing mode expires refresh tokens after 7 days — if the re-auth is not confirmed to run under a Production-mode consent screen, this leg will silently die again on the same schedule as before. This is an explicit gate on the done-contract, not assumed away.
- Nightly payload is small today (~60 MB) but unbounded growth over years is deferred ("revisit in a year") rather than solved now — an accepted scope limitation.
- MyWork delta backup (the ~10 GB of active, locally-authored deal documents that would also be lost entirely on disk failure — `docs/audits/2026-07-05-functional-artifact-lifecycle.md` §2.3 laptop-loss table) is explicitly deferred, not closed by this ADR.

## Done-when

- corp-ops has a configured private git remote — necessary condition: `git remote -v` in corp-ops shows a reachable private remote, and history has been pushed.
- Both backup legs (Graph/OneDrive upload-only, Google Drive upload-only) complete **one full scheduled** (not manually launched) cycle green, with the heartbeat file updating on each success and a forced-miss test proving the staleness alert fires (x1 proposal §3.5, §4 closure metric items 1 and 3).
- **A restore drill succeeds from each leg** — SHA-256 match, `git fsck --full` plus expected HEAD on the restored vault, spot-opened notes matching the manifest file count, and a DB integrity check — recorded in `JOURNAL.md` (x1 proposal §3.6, §4 closure metric item 2).

## Alternatives considered

- **rclone instead of the existing `corp_ops.gdrive` module for the Google Drive leg:** rejected in the source proposal — adds a second, separate OAuth surface for no functional gain over the already-implemented resumable-upload module (x1 proposal §3.3).
- **Fold corp-ops into corp-monorepo (reject DR-10's premise):** not adopted; the intake ratified separate-repo-with-remote as the outcome, and no evidence pointer in this decision's evidence set argues for consolidation.

## References

- `docs/audits/2026-07-06-technical-architect-intake.md` §5 (DR-10, DR-11 rows)
- `docs/audits/2026-07-05-estate-recon.md` §Part 1 (corp-ops spike state — no remote) and Anomaly list #1–#2
- `corp-ops` repo: `docs/audits/2026-07-05-x1-backup-proposal.md` §1 (feasibility verdicts + spike evidence), §2 (precious set), §3 (mechanism design incl. §3.5 fail-loud alerting, §3.6 restore drill), §4 (closure metric), §5 (operator prerequisites) — cross-repo evidence pointer; this file lives in `corp-ops`, not `corp-monorepo`
