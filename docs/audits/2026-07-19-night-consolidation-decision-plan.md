# Night consolidation + decision plan — 2026-07-19

> **Status:** informational consolidation (not a ruling). **Date:** 2026-07-19.
> **Purpose:** consolidate the 2026-07-18/19 distribution → ratification → S13 → #38 arc, map
> the live repo state, and lay out the decision plan for the next lane. Night-batch item **N1**.
> **Note:** the detailed N1 spec ("as previously ordered") was not in the executing session's
> context; this doc is derived from the one-line charter (consolidation + decision-plan, §2 =
> live-state asset map) plus the live tree at run time. §2 reflects `main` at the run instant.

---

## §1 Consolidation — what this arc landed

A single 2026-07-18/19 arc took the census-derived distribution plan through decomposition,
ratification, an archival sweep, and the first E5 developer story, each as a `--no-ff` merge:

- **BACKLOG distribution decomposition** — 14 tasks / 4 stories (`#55`–`#68`, `[S10]`–`[S13]`)
  across E3/E4/E5/E7 (`61fd554`).
- **intake-16 ratified** — E5 registry design flipped DRAFT → READY-FOR-TECHNICAL on the
  operator's D1/D3/D4/D5=A picks; D1 = `config/source_registry.yaml` (`770a804`).
- **Execution-channel discipline** — lesson recorded; the E5 lane preserved pending the channel
  pick (`2ee58f2`).
- **Traceability** — grep-witnessed `Consumed by:` lines on 28 July intake/brief artifacts
  (`6e28c32`).
- **S13 archival sweep** — signed ADR-38 deletion/relocation manifest (`59f29d8`), then executed:
  G4 relocate 8 audits + inventory.json → `docs/archive/` (`236de12`), G1 KILL 8 `.html`
  render-twins (`74ef46c`), G2 KILL 19 conformance digests (`af02a0c`); G3
  (`technical-architect-intake`) DEFERRED. `#66`/`#67`/`#68` closed.
- **E5 `#38` FR-10 source registry** — schema + observation model + deterministic scorer, built
  in the `epic/e5-registry` worktree lane (plan-then-auto), **terra-green after a 4-pass
  fix-and-rereview loop** (6 P1 fail-closed/design-invariant gaps fixed), merged `--no-ff`
  (`60b7367`).
- **Night batch** — N2 (`test_cke_paths_resolve` worktree-compat fix), N3 (`#69` ADR-archival
  task), N1 (this doc).

## §2 Asset map — live state (`main` at run time)

```
main HEAD          60b7367  (Merge epic/e5-registry — E5 #38, terra-green)
active branch      chore/2026-07-19-night-consolidation  (this night batch)
worktree           .claude/worktrees/epic-e5-registry @ db48093 [epic/e5-registry] — PRESERVED
                   (E5 developer lane; continues for #40/#36/#55; not torn down)
other branches     feat/arc4-leg1-ruff-equalization (pre-existing, unrelated)
BACKLOG            7 themes · 11 stories · 55 tasks (validate_backlog OK)
E5 open tasks      #35 #36 #37 #3 #4 #5 #6 #7 #38 #39 #40 #55
#38 status         MERGED as PRIMITIVES (scorer/schema/observation); stays OPEN — its
                   "every record carries a value_score / queue consumes" done-when completes
                   when #40 wires seeds + Graph snapshots
new code (main)    src/corp/ops/source_registry.py · source_value.py ·
                   source_observation_repo.py + source_observations table; tests/test_ops +82
immutable records  docs/audits/2026-07-19-deletion-manifest-s13-archival.md (SIGNED; G3 DEFER)
                   docs/intake/2026-07-17-tech-e5-registry-foundation-design.md (intake-16, READY)
E5 lane API        SourceDeclaration · validate/load_source_registry · score_record ·
                   compute_components · compose_score · neighbour_priors · rank_by_value_score ·
                   ScoredSource · SourceObservationRepository
```

## §3 Decision plan — next lanes

1. **E5 continuation (`#40` → `#36` → `#55`).** The `epic/e5-registry` lane continues from the
   new `main` (sync it forward first). `#40` seeds the three golden records + resolves + scores
   them; `#36` runs the scout pilot (day-1 = deterministic `rank_by_value_score`, bandit is
   cycle-3+); `#55` emits a draft Content-Manifest. The `#38` primitives are the substrate.
2. **Graph consent (decision G / auth D2)** — the one interactive gate. `#40` *record drafting*
   is consent-free, but *live resolution* to A1/A2 IDs and `#36`'s foraging **block on it**.
   Operator decision, not designed around (intake-16 §3/§6/§8).
3. **ADR-archival (`#69`, S13/G3)** — relocate the consumed+superseded
   `technical-architect-intake` via a forwarding-marker amendment arc on ADR-33/34/35/36
   (ref-integrity per ADR-38 / #68). Deferred, not dropped.
4. **Paper-only ADRs (`#63`/`#64`/`#65`)** — enforce-or-defer ADR-34/35/36 (census B-table 3).
5. **KE / RFP hardening (`[S10]` / `[S11]`)** — the SIM-1 acceptance gaps (C2/C3/C4/C6) + RFP
   body-FTS + cost observability; lane-scheduled per the 2026-07-18 focus ruling.
6. **E5 epic final return** — after `#40`/`#36`/`#55`; only then is the epic finalized and the
   `epic/e5-registry` worktree torn down.

## Open decisions (operator)

- **Graph consent** (gates `#40` live-resolve + `#36`) — the single interactive step.
- **Auth shape (D2)** — delegated (existing az/X1 consent) vs a dedicated app registration.
- **Final zone names (DR-6/7)** — gate `#35`'s zone renames.
- Whether to run `#69` (ADR-archival forwarding-marker arc) now or hold.

---

*Consolidation record — no `src/`/`tests/` change (night-batch N1). Derived from live `main`
state at run time; not a ruling.*
