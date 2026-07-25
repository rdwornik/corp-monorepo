# CORP_INTERFACE.md — Corporate OS external interface (thin index)

<!-- scope: meta -->
<!-- methodology:start id=corp-interface owner=repo -->

> Project-local, corp-domain interface doc (#314). **Thin index** — the
> authoritative structural detail lives in `ARCHITECTURE.md`; this file is a
> pointer, not a duplicate. **Genre (hub BACKLOG #327 — resolved by reference):**
> `protocols/` is the fleet's interface genre — *what other repos/agents must know
> to interact with THIS repo*. That wording is defined once at the hub
> (`../.dev-knowledge/protocols/README.md`) and is not restated here; this file is
> corp's interface doc under it.

## The five CLIs

Corporate OS's external interface is five console entry points (one
`pyproject.toml`; unified `src/corp/` namespace):

- `corp` — primary operator CLI (`corp.cli`): ingest / retrieve / vault operations
- `corp-meta` — schema & metadata CLI (`corp.schema.cli`)
- `cke` — Corporate Knowledge Extractor (`corp.extractor`) — pure extraction engine
- `cpe` — project-domain CLI (`corp.project.cli`)
- `com` — opportunity-domain CLI (`corp.opportunity.cli`)

See `ARCHITECTURE.md` for the module map, the 4-layer assignments (`interface >
orchestration > core > foundation`), and the per-CLI command surface.

## Interface contracts (authoritative detail in ARCHITECTURE.md / ADRs)

- **Vault-writer contract (ADR-27):** `ingest/` is the SOLE writer for
  `02_sources/` `.md` notes; `actions/*` may write DASHBOARDS / METADATA /
  BRIEFS directly; all others go via `vault_io.write_note()`.
- **CKE-staging contract:** CKE output must be staged in a
  `scope/client/package/` hierarchy **before** `corp ingest-extractions` — flat
  dirs ingest 0 notes.
- **CKE purity:** the extractor performs no vault writes and no database writes.

Detail deferred to `ARCHITECTURE.md`; this doc is the interface pointer only.
<!-- methodology:end id=corp-interface -->
