# ADR-30: Retire CHANGELOG.md

- **Status:** Accepted
- **Date:** 2026-05-18
- **Related:** ADR-49 (ecosystem-level CHANGELOG retirement, `.dev-knowledge/docs/decisions/`), ADR-31 (companion: retire single-file HANDOFF)
- **Decommission:** `CHANGELOG.md` (repo root); `**/CHANGELOG.md` entry in `corp-monorepo.code-workspace` todo-tree exclude list (was line 74)
- **Source:** 2026-05-18 universalization-review audit §2.6 (`docs/audits/2026-05-18-universalization-review.md`); rollout branch `docs/workstream-b-past-recording`

## Context

ADR-49 retires `CHANGELOG.md` across the ecosystem. corp-monorepo carried
a local change log (42 lines, semver lineage from `[1.0.0] 2026-03-28`;
last entry 2026-04-22 ADR-27 drafting). Maintaining a separate flat
changelog alongside `git log` and `JOURNAL.md` produced three places to
look for "what changed," with the changelog consistently the staler of
the three.

Commit messages have to carry the load `CHANGELOG.md` used to; the
Conventional-Commits standard in
`.dev-knowledge/protocols/ESSENTIALS.md` §"Commit message standard"
exists to make that load tractable.

The `Changes:` bullet in each `JOURNAL.md` entry (ADR-49 per-entry shape:
`Did / Result / Changes / Abandoned / Next`) provides a human-scannable
per-session change record without duplicating commit messages verbatim.

## Decision

Retire the corp-monorepo-local change log:

- Delete `CHANGELOG.md`. Last commit touching the file before removal:
  `d9c15a6` (2026-04-22, "docs(changelog): record ADR-27 drafting").
- Remove `**/CHANGELOG.md` from the
  `corp-monorepo.code-workspace` todo-tree exclude list.

The change record is now carried by two mechanisms:

- **Conventional Commits** as the primary change record. Standard
  defined in `.dev-knowledge/protocols/ESSENTIALS.md` §"Commit message
  standard": `type(scope): summary` (types `feat`, `fix`, `docs`,
  `refactor`, `test`, `chore`), imperative summary under ~72 chars,
  body required for any non-trivial change, one logical change per
  commit. Pre-commit and `/save` already enforce parts of this.
- **`JOURNAL.md` `Changes:` line.** The ADR-49 per-entry shape makes
  this load-bearing — every session entry now lists the files/areas
  touched, providing a session-grained change record.
  `JOURNAL.md` intro updated in commit `237e1fa`.

The two most recent `CHANGELOG.md` entries (2026-04-21 OneDrive hotfix,
2026-04-22 ADR-27 drafting) were sourced into the `JOURNAL.md` catch-up
commit on the rollout branch before deletion — no content lost.

## Consequences

### Positive
- One canonical place to look per change concern: `git log` for
  authoritative change record, `JOURNAL.md` for session narrative.
- No staleness drift between three sources.
- Aligns corp-monorepo with the ecosystem ADR-49 standard.

### Negative
- ADR-38's "Mandatory documentation" table still lists `CHANGELOG.md`
  as required at Tier M+. That conflict is `.dev-knowledge`-side and
  operator-timed; corp-monorepo proceeds per ADR-49 (the more recent
  decision) and an ADR-38 amendment is queued separately.
- Historical `CHANGELOG.md` mentions inside `docs/archive/`,
  `docs/audits/`, and `docs/decisions/transcripts/` are intentionally
  left as-is (frozen / historical record); readers must understand the
  context is pre-retirement.

## References

- ADR-49 (CHANGELOG retirement, ecosystem authority):
  `.dev-knowledge/docs/decisions/`.
- Universalization-review audit (2026-05-18):
  `docs/audits/2026-05-18-universalization-review.md` §2.6.
- Commit message standard:
  `.dev-knowledge/protocols/ESSENTIALS.md` §"Commit message standard".
- Session-ending JOURNAL shape:
  `.dev-knowledge/protocols/ESSENTIALS.md` §"Ending a Session" + ADR-49.
- Companion: ADR-31 (`ADR-31-retire-single-file-handoff.md`).
