# Deletion / relocation manifest — S13 archival sweep (SIGNED)

- **Status:** SIGNED — immutable audit (ADR-38; CLAUDE.md §5 rule 3). Do **not** edit in place; supersede via a new manifest.
- **Signed:** Rob (operator; git identity `robdwornik`) — 2026-07-19. *(Operator's signature message used the placeholder `[imię operatora]`; resolved to the known git operator identity. Correct via a superseding note if a different attribution is wanted.)*
- **Evidence HEAD:** `6e28c32` — every leg re-derived fresh at this sha (never quoted from an audit, per ADR-38).
- **Doctrine:** ADR-38 (three evidence legs per row) + the #68 relocation policy (§1 below, ratified as drafted).
- **Execution:** a **SEPARATE** operator-authorised session (zero deletes / moves in the drafting + signing session). One commit per group, independently revertable; `./scripts/run-all-tests.ps1` after each; GATED rows fire only on the recorded operator word.
- **Backlog:** completes #66 (this signed manifest) + #68 (policy ratified, §1); **#67** executes this manifest in the separate session.
- **First signed instance precedent:** `docs/audits/2026-07-17-deletion-manifest-arc-b.md`.

---

## §1 Governing relocation policy (#68 — RATIFIED as drafted, 2026-07-19)

**1. What qualifies (relocate → `docs/archive/`).** Both conditions required — neither alone qualifies:
- **(a) fully consumed** — content has flowed to its downstream consumer(s) (grep-witnessed `consumed-by`), **and**
- **(b) superseded** — a canonical successor now holds the live version (an ADR / newer living doc / ratified spec).
- consumed-but-not-superseded → **stays** (still the live reference); superseded-but-still-cited → **stays** until citations migrate.
- **LIVE specs never qualify until closure:** intake-16 archives at E5 epic closure; the SIM acceptance spec archives at deck-phase closure — **not before** (both drive open work).
- pure disposables (render-twins, superseded CI digests) route to **DELETE** (this manifest), not archive.

**2. Reference-integrity rule.**
- any relocation updates **every live citation** to the new `docs/archive/` path in the **same commit** (no dangling refs);
- **`JOURNAL.md` is NEVER edited** (append-only immutable history; its refs correctly record where the file *was*);
- immutable docs (ADRs / transcripts / audits) are not edited in place — a forwarding note via the sanctioned amendment marker, or the citation is left as historical; a move that would **strand** a live citation is **BLOCKED** until the citation can move with it.

**3. Manifest format (per ADR-38).** One signed manifest; three evidence legs per row (reference re-grep · live-binding cross-check · docs+config ref grep), re-derived fresh vs a named HEAD sha; ruling legend `PROPOSED-RELOCATE / KILL / GATED / KEEP / DEFER`; PROPOSED until operator signature; execution is a separate signed arc; signed instances are immutable audits.

---

## §2 Manifest rows — rulings 2026-07-19 (evidence @ `6e28c32`)

### G1 · `.html` render-twins — RULED **KILL** (gated) — 8 files
```
docs/audits/2026-07-05-deep-dealloop.html
docs/audits/2026-07-05-deep-extraction.html
docs/audits/2026-07-05-deep-magistrala.html
docs/audits/2026-07-05-deep-mywork.html
docs/audits/2026-07-05-deep-rfp.html
docs/audits/2026-07-05-deep-vault-metadata.html
docs/audits/2026-07-06-code-quality-audit.html
docs/audits/2026-07-06-process-map-asis.html
```
- **Leg 1 (caller re-grep):** no `src/` or `tests/` reads any `.html`; every `.md` twin is present + canonical (`git ls-files` confirms the `.md` alongside each).
- **Leg 2 (live-binding):** the `.md` is the authoritative artifact; the `.html` is a disposable render output (no generator reads it back; not served).
- **Leg 3 (docs/config ref grep):** references appear in `docs/audits/2026-06-16-current-state-architecture-audit-inventory.json` + several July briefs (`deep-extraction`, `estate-recon`, `technical-architect-intake`, `_HANDOFF_functional-architect`).
- **RULING (operator, 2026-07-19): KILL — GATED** on pre-execution verification that `inventory.json` + the briefs cite the `.md`/content, **not** the `.html` path. **Any `.html`-path citation → that row is GATED until the citation is fixed first.** (The `inventory.json` cross-reference is the live gate condition; note it also belongs to a G4 relocation target — resolve ordering at execution.)

### G2 · conformance digests — RULED **KILL** — 19 files (18 nightly + 1 baseline)
```
docs/audits/2026-06-04-conformance-baseline-digest.md
docs/audits/2026-06-06-conformance-nightly-digest.md
docs/audits/2026-06-07-conformance-nightly-digest.md
docs/audits/2026-06-08-conformance-nightly-digest.md
docs/audits/2026-06-09-conformance-nightly-digest.md
docs/audits/2026-06-10-conformance-nightly-digest.md
docs/audits/2026-06-11-conformance-nightly-digest.md
docs/audits/2026-06-12-conformance-nightly-digest.md
docs/audits/2026-06-14-conformance-nightly-digest.md
docs/audits/2026-06-15-conformance-nightly-digest.md
docs/audits/2026-06-16-conformance-nightly-digest.md
docs/audits/2026-06-17-conformance-nightly-digest.md
docs/audits/2026-06-18-conformance-nightly-digest.md
docs/audits/2026-06-19-conformance-nightly-digest.md
docs/audits/2026-06-20-conformance-nightly-digest.md
docs/audits/2026-06-21-conformance-nightly-digest.md
docs/audits/2026-06-22-conformance-nightly-digest.md
docs/audits/2026-06-23-conformance-nightly-digest.md
docs/audits/2026-06-27-conformance-nightly-digest.md
```
- **Leg 1 (caller re-grep):** `src/` does not read them; `tests/test_nightly_triage_parser.py` binds to its **own fixture copy** (`tests/fixtures/nightly-triage/2026-06-06-conformance-nightly-digest.md`), **not** the `docs/audits/` originals; the parser matches the naming **pattern**, not a specific `docs/audits/` file.
- **Leg 2 (live-binding):** nightly CI ephemera, superseded by later conformance state; no live consumer.
- **Leg 3 (docs/config ref grep):** the digests only cross-reference each other.
- **RULING (operator, 2026-07-19): KILL** — the full witnessed set (18 nightly `2026-06-06`→`06-27` + 1 baseline `06-04` = **19**). The `tests/fixtures/nightly-triage/` copy is a **test fixture, OUT OF SCOPE — stays.**

### G3 · `2026-07-06-technical-architect-intake.md` — RULED **DEFER**
- **Leg 1 (caller re-grep):** heavily cited (~13 docs); content fully consumed.
- **Leg 2 (live-binding):** fully consumed + superseded — the DR register decisions are canonicalised in ADR-33/34/35/36; no longer the live reference.
- **Leg 3 (docs/config ref grep):** cited by ADR-33/34/35/36 (`Intake:` / `Source:` lines) + the a3-ruling + many audits.
- **RULING (operator, 2026-07-19): DEFER** — 4 **immutable-ADR** citations would strand on a move; revisit **only** if a forwarding-marker arc becomes worth it. Not signable as RELOCATE/KILL under §1's reference-integrity rule.

### G4 · individually-unconsumed old audits — RULED **RELOCATE → `docs/archive/`** — all 8
```
docs/audits/2026-03-30-codex-full-audit.md
docs/audits/2026-04-15-tach-baseline-violations.md
docs/audits/2026-05-25-adr27-status.md
docs/audits/2026-06-03-codex-adr71-doctools-pilot.md
docs/audits/2026-06-04-graphify-pilot.md
docs/audits/2026-06-16-codex-current-state-audit-tool.md
docs/audits/2026-06-16-current-state-architecture-audit.md
docs/audits/2026-06-21-foundation-review.md
```
- **Leg 1 / Leg 3 (reference re-grep):** zero downstream refs in `docs/decisions/`, `docs/intake/`, `BACKLOG.md` @ `6e28c32`.
- **Leg 2 (live-binding):** superseded by current-state (`2026-07-16-architecture-ground-truth.md` / the a3-ruling); no live binding.
- **RULING (operator, 2026-07-19): RELOCATE** all 8 witnessed zero-ref candidates to `docs/archive/` per §1's reference-integrity rule.
- **Execution note:** `2026-06-16-current-state-architecture-audit.md` has a companion `…-inventory.json` that references the G1 `.html` targets — the relocation must carry / re-point that companion, and it interacts with the G1 gate (resolve ordering: fix/relocate the `inventory.json` refs before the dependent `.html` KILLs).

---

## §3 Execution contract (separate session, per ADR-38)

- Executes as a **separate operator-authorised session**; this drafting+signing session performs **zero** deletes/moves.
- **One commit per group** (G1 · G2 · G4), independently revertable; `./scripts/run-all-tests.ps1` green after each.
- **G1 gate:** before any `.html` KILL, re-grep the `inventory.json` + briefs; any `.html`-**path** citation holds that row until the citation is fixed.
- **G4 relocation** obeys §1 reference-integrity (citations move in the same commit; `JOURNAL.md` never edited; immutable-doc citations get a forwarding marker or stay historical).
- **G3** takes no action (DEFER).
- On completion: JOURNAL anchor (closes #67). This manifest is not re-opened — a changed disposition is a **new** superseding manifest.

## Signature

**SIGNED:** Rob (operator; git identity `robdwornik`) — 2026-07-19. Execution authorised as a separate session per ADR-38; this signed manifest is an immutable audit.
