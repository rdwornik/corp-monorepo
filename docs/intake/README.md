# docs/intake/ — the requirements spine (corp-monorepo)

<!-- scope: meta -->

`docs/intake/` holds **forward-looking intake and functional-design artifacts** — the
"what to build / why" layer that precedes implementation. Distinct from `docs/audits/`
(retrospective evidence — "what is / what happened") and `docs/decisions/` (ratified ADRs).

Genre, frontmatter schema, and lifecycle are **fleet-canonical**, defined once at the hub
(`../.dev-knowledge/docs/intake/README.md`, ADR-98 Accepted 2026-07-07). This is the
corp-local **thin** pointer + a **hand-maintained** index — it does not restate the hub
governance and runs **no generator** (corp does not use the hub's `gen_intake_index.py` /
`INTAKE-INDEX` markers; the index below is edited by hand).

## Frontmatter schema

Going-forward intake docs open with the hub schema (hub README §3):

```yaml
---
intake-id: <N>       # stable integer, next free across all history (closed ids not reused)
status: <SEED | DRAFT | READY-FOR-TECHNICAL | CONSUMED | REJECTED>
origin: <one line: who / where / when>
consumed-by: <ADR/backlog ids — populate only when status: CONSUMED>
---
```

`intake-id` is the permanent join key the accepting ADR and resulting epic(s) cite back.
Naming (hub README §4): `YYYY-MM-DD-{func|tech}-slug.md`, origin-dated.

## Contents

Hand-maintained — no generator.

- `2026-07-10-runbook-gap-notes.md` — Wave-1 **n=2** onboarding runbook gap-notes /
  NEEDS-RULING items (routes to `.dev-knowledge` for filing; a gap-notes deliverable,
  not an ADR-98 intake doc — carries no intake frontmatter).
