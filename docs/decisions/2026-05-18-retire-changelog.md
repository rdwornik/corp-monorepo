# 2026-05-18 — Retire CHANGELOG.md

Type: Decision note (NOT a numbered ADR — ADR-numbering hygiene is a
later rollout step; corp-monorepo currently has two ADR-27 files).
Status: Accepted
Date: 2026-05-18
Branch: `docs/workstream-b-past-recording`
Authority: ADR-49 (`.dev-knowledge/docs/decisions/`) §"Decision";
2026-05-18 universalization-review audit §2.6;
universalization rollout step 3 (Workstream B).

## What

Retired the corp-monorepo-local change log:

- `CHANGELOG.md` (42 lines, semver lineage from `[1.0.0] 2026-03-28`;
  last entry 2026-04-22 ADR-27 drafting).

The repo's change record is now carried by two mechanisms that
already exist and were under-used while CHANGELOG.md was the
canonical source:

- Descriptive **Conventional-Commits** messages (`type(scope):
  summary` + body for non-trivial changes).
- The **`Changes:`** line in each JOURNAL.md entry (per the ADR-49
  per-entry shape: `Did / Result / Changes / Abandoned / Next`).

## Why

- ADR-49 retires CHANGELOG.md across the ecosystem. Maintaining a
  separate flat changelog alongside `git log` and JOURNAL produces
  three places to look for "what changed," with the changelog
  consistently the staler of the three.
- Commit messages have to carry the load CHANGELOG used to; the
  Conventional-Commits standard in `.dev-knowledge/protocols/ESSENTIALS.md`
  §"Commit message standard" exists to make that load tractable.
- The JOURNAL `Changes:` bullet provides a human-scannable
  per-session change record without duplicating commit messages
  verbatim.
- The two most recent CHANGELOG entries (2026-04-21 OneDrive hotfix,
  2026-04-22 ADR-27 drafting) were sourced into the JOURNAL
  catch-up commit on this branch before deletion, so no content was
  lost.

## Decommission

- `CHANGELOG.md` — removed via `git rm` on branch
  `docs/workstream-b-past-recording`. Last commit touching the file
  before removal: `d9c15a6` (2026-04-22, "docs(changelog): record
  ADR-27 drafting").
- `corp-monorepo.code-workspace` — `**/CHANGELOG.md` removed from
  the todo-tree exclude list (was line 74).

## What replaced it

- **Conventional Commits** as the primary change record. Standard
  defined in `.dev-knowledge/protocols/ESSENTIALS.md` §"Commit
  message standard": `type(scope): summary` (types `feat`, `fix`,
  `docs`, `refactor`, `test`, `chore`), imperative summary under
  ~72 chars, body required for any non-trivial change, one logical
  change per commit. Pre-commit and `/save` already enforce parts
  of this.
- **JOURNAL.md `Changes:` line.** The new ADR-49 per-entry shape
  makes this load-bearing — every session entry now lists the
  files/areas touched, providing a session-grained change record.
  JOURNAL.md intro updated in commit `237e1fa` on this branch.

## Out of scope (deferred)

- ADR-38 ↔ ADR-49 conflict: ADR-38's "Mandatory documentation"
  table still lists CHANGELOG.md. The ADR-38 amendment is a
  `.dev-knowledge`-side change and is operator-timed — out of scope
  for this corp-monorepo rollout. Proceeding here per ADR-49.
- ADR-numbering cleanup (duplicate ADR-27 files) — later rollout
  step (Workstream C).
- Historical CHANGELOG mentions inside `docs/archive/`,
  `docs/audits/`, and `docs/decisions/transcripts/` are intentionally
  left as-is (frozen / historical record).

## References

- ADR-49 (CHANGELOG retirement):
  `.dev-knowledge/docs/decisions/` — authority.
- Universalization-review audit (2026-05-18):
  `docs/audits/2026-05-18-universalization-review.md` §2.6.
- Commit message standard:
  `.dev-knowledge/protocols/ESSENTIALS.md` §"Commit message standard".
- Session-ending JOURNAL shape:
  `.dev-knowledge/protocols/ESSENTIALS.md` §"Ending a Session" + ADR-49.
- Companion decommission note:
  `docs/decisions/2026-05-18-retire-single-file-handoff.md`.
