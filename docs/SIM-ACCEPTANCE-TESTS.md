# SIM-ACCEPTANCE-TESTS.md — knowledge-module phase acceptance conditions

> **Status: RATIFIED (as reconstructed) — 2026-07-18.**
> This file was reconstructed 2026-07-18 from the in-repo ruling record (the 2026-07-18 JOURNAL
> entry on the operator's SIM-2 ruling + the `docs/audits/2026-07-18-process-audit.md` F-findings)
> because the original artifact was absent from the handoff bundle (Session-1 A0-2 STOP). The
> operator ratified this reconstruction on 2026-07-18.
> **Supersede clause (retained):** the outgoing session may still re-emit the original — **if the
> original ever appears, it supersedes this reconstruction.**

## Scope & bar

- **Phase ruling (operator, 2026-07-18):** knowledge modules first, decks the next phase.
- **Phase bar:** **SIM-2** (the SIM-2 run itself is deferred to the deck phase, together with C5).
- **This window's acceptance:** a **green witnessed sandbox end-to-end run per focus module**
  (BACKLOG `#34` shape) satisfying **C1–C4 + C6** below. C5 is deferred (deck phase).
- **Focus streams:** metadata management · URL/source management · knowledge extractor · RFP agent.

## Acceptance conditions

| ID | Condition | Closes finding | This window |
|----|-----------|----------------|-------------|
| **C1** | **Fresh-env ingest** completes without crash when `<mywork>/.corp/content_registry.yaml` is absent at start | F1 | **REQUIRED** |
| **C2** | **Body-FTS retrieval** — a body-term query (not just title/metadata) returns the matching note | F6 | **REQUIRED** |
| **C3** | **Project ↔ vault client link** — an indexed note resolves to its project, and client propagates | F16 / F9 | **REQUIRED** |
| **C4** | **Index hygiene** — one source file yields exactly one indexed note (no duplicate/phantom rows) | F8 | **REQUIRED** |
| **C5** | **Slide bridge** — knowledge → deck hand-off produces a slide-ready artifact | — | **DEFERRED (deck phase)** |
| **C6** | **Single path/config resolution** — every lane (incl. AppConfig + `com`) resolves paths through one sandbox-honoring config; no real-asset leak | F18 / F26 | **REQUIRED** |

## Witnessed end-to-end steps (7)

Each focus-module acceptance run must witness these steps, in a **verified sandbox** (built via the
repo's own `SandboxManager`; a GO/NO-GO isolation gate asserts every env-resolved path under the
sandbox root before any live command — see the 2026-07-18 process-audit methodology):

1. **Fresh-env init** — sandbox with **no** `<mywork>/.corp/content_registry.yaml` present. (→ C1)
2. **Ingest** — drive `corp ingest` on ≥1 source file; it completes exit 0, no crash. (→ C1)
3. **Extract** — CKE produces a deep knowledge note into the vault. (→ C4)
4. **Index** — `corp index rebuild`; the source yields exactly **one** indexed note. (→ C4)
5. **Project link** — the note resolves to its project; client field propagates. (→ C3)
6. **Retrieve** — a **body-term** query (a phrase from the note body, not its title/metadata)
   returns the note. (→ C2)
7. **Draft + cite** — `corp rfp answer` (or module equivalent) produces a draft grounded in, and
   **citing, the vault note from step 3–6.** (→ end-to-end)

**Same-note invariant:** the retrieval output (step 6) and the draft citation (step 7) MUST cite
**the same vault note** produced in step 3. A run where the draft cites a different note than
retrieval surfaced does **not** pass.

## Isolation caveat (C6 basis)

The process audit disclosed two read-only real-MyWork leaks via lanes bypassing the sandbox env:
`project_resolver` AppConfig roots (F18) and `com` `project_codes.xlsx` (F26). C6 is not satisfied
until every lane resolves through one sandbox-honoring config. (No writes were observed; SHA-256
real-asset baseline held — but the leak is a correctness gap for a "witnessed sandbox" claim.)

## Progress (informational; not part of the ratified conditions)

- **C1 — CLOSED** by #35 (merge `6c36f61`, 2026-07-18): fresh-env ingest bootstraps the registry
  and completes; witnessed by the post-#35 SIM-1 diagnostic (sandbox e2e, real assets unchanged).

---

*Reconstructed 2026-07-18 · source: in-repo ruling record (JOURNAL 2026-07-18 SIM-2 ruling +
`docs/audits/2026-07-18-process-audit.md`) · RATIFIED (as reconstructed) 2026-07-18.*
