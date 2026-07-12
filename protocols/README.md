# protocols/ — project-local corp-domain interface docs

<!-- scope: meta -->

**Scope marker (hub BACKLOG #314).** This folder holds **project-local,
corp-domain** interface / contract docs — the external-interface surface of
Corporate OS itself:

- `CORP_INTERFACE.md` — the five CLIs (`corp`, `corp-meta`, `cke`, `cpe`, `com`)
  + the vault-writer / CKE-staging contracts; a thin index into `ARCHITECTURE.md`

**Methodology protocols are NOT here.** The universal methodology protocols
(`ESSENTIALS.md`, `PLAYBOOK.md`, and the rest of the hub `protocols/` set) are
**hub-pointer only** — read them at `../.dev-knowledge/protocols/`, never copied
into this repo. `CLAUDE.md` §1 points at them directly by design (corp is a
consumer; the ADR-36 read-only contract holds).

This is the "marked/local" half of #314's hub-pointer-vs-local split: the folder
a reader lands in first now states, in-band, that it is intentionally
domain-scoped and carries no methodology-protocol copies. Full genre wording
lands with #327.
