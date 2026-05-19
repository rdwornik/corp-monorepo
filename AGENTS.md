# AGENTS.md — corp-monorepo Codex Overlay

> The generic Codex reviewer config (role, review modes, checklist, output format) is global per ADR-54.
> See `~/.codex/AGENTS.md` for the global config.
> This file adds **corp-monorepo-specific review rules only**.

## Repo-Specific Critical Rules

- [ ] **Vault-writer invariant (ADR-27)** — actively flag any vault write that bypasses the vault-writer boundary. The boundary itself is defined in `ARCHITECTURE.md` / ADR-27 — do not restate it here.

## Repo-Specific Medium Rules

- [ ] **Stale package references** — no uses of old package names (`corp_by_os`, `corp_os_meta`, `corp_knowledge_extractor`) — all modules are now under `src/corp/`
