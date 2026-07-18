# Deletion-Manifest Template (corp-monorepo)

> Reusable template + **binding doctrine** for producing an operator-signable deletion manifest.
> The manifest is a *contract*; execution is a **separate, operator-signed arc** (zero deletions in
> the session that produces the manifest — no `src/`, `tests/`, or `main` change). Copy this
> structure for each new manifest.
>
> **Living doc** — amend the doctrine here so the *next* manifest inherits it; never edit a signed
> manifest instance in place (audits are immutable, CLAUDE.md §5 rule 3). First signed instance:
> `docs/audits/2026-07-17-deletion-manifest-arc-b.md`.

## Doctrine (binding on every manifest)

**Standard method — three evidence legs per KILL/GATED row**, each re-derived *fresh* against a
named HEAD sha (never quoted from an audit):

1. whole-repo **caller re-grep** (source + tests), verbatim in a per-batch fence;
2. **data-binding cross-check** — a zero-caller module with a live data-READ binding is **not** zero-use;
3. **docs/ + config reference grep**.

A row missing any leg is stamped **UNVERIFIED** and cannot be signed.

**Ruling legend:** `PROPOSED-KILL` (re-grep supports deletion, awaiting signature) ·
`PROPOSED-GATED` (blocked until the operator's explicit confirmation — his word is the evidence) ·
`PROPOSED-KEEP` (re-grep contradicts deletion, exclusion) · `DEFER` (visibility-only, **not**
signable as KILL).

### Amendments — senior review 2026-07-17 (item 1); source AMD-1 + AMD-2

**A. Column-granularity enumeration before a column KILL.** A removal that drops a *column* (or a
model field) requires a verbatim consumer enumeration at **column granularity** — every
`path:line` that reads / writes / orders / aggregates the column — recorded *before* the row may be
ruled KILL. A module-granularity caller grep is insufficient for column removals.
*Precedent:* AMD-1 enumerated **31** `projects.facts_count` consumer sites
(`docs/audits/2026-07-17-amd1-facts-count-consumers.md`), and only the column-level pass surfaced
that the column is a **live vault-sourced scalar** (populated at `index_builder.py:389/:414` from
note frontmatter), *independent* of the dead facts loader — so a module-level grep would have
mis-ruled it KILL. Re-confirmed by the 2026-07-18 process audit (F7: `facts_count` reads 0
everywhere, yet is written from frontmatter, not the facts table).

**B. Runtime-claim kills default to PROPOSED-GATED.** When a row's deletion evidence is a **runtime
claim** ("this lane never fires", "0 rows ever") rather than a **caller grep** — i.e. the target is
still reachable in the import graph — the row defaults to **PROPOSED-GATED**, never PROPOSED-KILL.
Its exact dead boundary must be witnessed at execution, and it requires the operator's explicit word.
*Precedent:* Arc-B Batch 3 (`ingest/router.py` inbox-lane internals) — `_run_extraction` /
`_run_package_extraction` are **live in the import graph** (`router.py:295/:596`); "dead" rested on a
runtime write-never-completed claim, so the batch is boundary-gated, never a blanket `router.py`
delete.

## Structure (copy per manifest)

1. **Header** — purpose · governing authority (operator ruling + witnessed audits) · HEAD sha · "zero deletions this session".
2. **Freshness caveats** — already-resolved claims excluded; misleading figures corrected.
3. **Sign-off block** — per-batch `PROPOSED-* → signed` checkboxes · scope-hash · the operator's verbatim word for any GATED batch.
4. **Batches** — one table per batch, columns: `# · Target · Class · Evidence (file:line) · Callers re-grep · Data bindings · LOC · Risk · Revert plan · Ruling`; each with its verbatim re-grep fence.
5. **Exclusions (KEEP)** — with the re-grep that flips a proposed kill to KEEP.
6. **DEFER field** — visibility-only, not signable.
7. **Execution contract** — one commit per batch (independently revertable) · `./scripts/run-all-tests.ps1` after each · GATED rows fire only on the operator's recorded word.

---
*Template established 2026-07-18 · doctrine amendments A/B from senior review 2026-07-17 item 1 (source AMD-1 + AMD-2, Arc-B plan Addendum B) · first signed instance `docs/audits/2026-07-17-deletion-manifest-arc-b.md`.*
