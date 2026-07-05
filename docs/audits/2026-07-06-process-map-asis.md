# As-Is Process Map — Audit Snapshot

**Status:** operator-ratified as-is snapshot (2026-07-06). Not canonical — not `ARCHITECTURE.md`, not an ADR.
**Open inputs:** 5 operator inputs remain undecided, marked `[?n]` inline and listed below.
**Supersedes:** nothing.

```
━━━ DEAL LOOP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SALESFORCE (deal origin) → AM adds Rob to Opportunity Team
  → manual list-view copy-paste [manual]
  → PROJECT_CODES.XLSM = the "main" (MyWork/30_Reference)
      Raw tab → main tab: Stage (SF vocabulary) · col E = SF-URL key ·
      col M = folder link (empty 0/52)
  → DEAL HOME, two mirrors [?1][?2]:
      local MyWork/10_Projects/{Client} ⇄ SharePoint #1 (team site,
      shared with AM; local access via OneDrive shortcuts)
  → PRODUCTION (where the hours go):
      inputs: RFP Excel/Word (mail) · BRD/RFI (deal SharePoint) · ad-hoc Q&A
      ├─ RFP: parse → classify → RETRIEVE from knowledge → compose →
      │   validate → write back [today manual 2–5 days; vault effectively
      │   39 usable notes, 1,329-file KB unreachable — R1 target]
      ├─ DECKS: BRD → analysis → grounding → KM_v2 → python-pptx →
      │   render → verify [WORKS — Warsaw factory, 5 customers; fed by
      │   MANUAL synthesis, NOT the vault ← gap to close]
      └─ Q&A + security questionnaires (GDPR/NIS2)
  → DELIVERABLE returns to client/AM [?3 — mail or SharePoint? where does
      the submitted copy live? = style-store seed]
  → WIN/LOSS — status in xlsm (never timestamps)
      ├─ local → 90_Archive [mechanism exists; trigger MISSING]
      └─ SharePoint #1 → ??? [?4]

━━━ KNOWLEDGE LOOP (parallel; feeds BOTH productions: RFP and DECKS) ━━
SOURCES: SharePoint #2 corporate (enablement, trainings, _Cognitive
  Planning…; 1.1 TB chaos mp4+pptx+pdf) · Teams sessions/recordings ·
  deal residues · Rob's own material (Training Warsaw)
  → SCOUT: enter → look around cheaply (metadata) → assess → tag →
    shortlist → operator GO → copy out (source always read-only) [pilot ready]
  → STAGING %LOCALAPPDATA%/corp-ops/scout-staging + manual saves
  → MyWork/00_Inbox [frozen: 75 files since 04-10]
  → MAGISTRALA (W1): classify → rename (ADR-14) → route →
    record-before-move [sandbox 5/5 = works; restart gated on registry v4]
  → MyWork ZONES: 10_Projects=live deals · 30_Reference=library ·
    20_Workflows=work templates · 80_Compliance · 70_Admin ·
    15_Extra [disposition pending] · 90_Archive [empty]
  → EXTRACTION (W2, CKE): tiers LOCAL/Flash/Pro (cost: cents) →
    data/_outputs [18.4 GB one-shot artifacts = main disk eater; regenerable]
  → INGEST → VAULT ObsidianVault/01_Knowledge — .md note with frontmatter
    [frozen 03-27; 850 on disk / 488 indexed / 39 RFP-usable]
  → INDEX.DB (FTS5) → RETRIEVAL (corp retrieve/prep/rfp)
    ──▶ feeds PRODUCTION: RFP lane AND deck lane ▲
  → ESSENCE — the drill-down map (target, does not exist yet):
    ROOT ─ industry (retail·mfg·3PL) × software (planning·execution·platform)
         └─▶ topic (e.g. replenishment) ─▶ S2 notes [MOC spine to build]

━━━ MEMORY & BACKUP (why OneDrive) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRECIOUS <100 MB: vault 46 MB · rfp_kb 1.7 MB · 3×.db · .corp 9.4 MB
  → X1 — scheduled + heartbeat, never delete:
    ├─ BY OneDrive /Backups/x1 (Graph, upload-only) ← in-tenant compliance
    └─ Google Drive (corp-ops module) ← second leg
WORKING ~10 GB: MyWork [sync-mywork dead ~4 months → no copy] [?5]
JUNK 18+ GB: _outputs v2/v3 · twin pairs 756 MB → cleanup = disk management
DEAD: OneDrive/MyWork_OneDrive = pre-migration copy, code never touches [?5]
ENGINE: Dev/ (5 repos, GitHub) — recon exceptions: corp-ops and VAULT no remote
```

## Open operator inputs

- [?1] SharePoint #1 topology: one team site with per-deal folders, or per-client sites? Local access = "Add shortcut to OneDrive"?
- [?2] Master of deal documents: local 10_Projects or the SharePoint folder? Copy direction and timing?
- [?3] Deliverable path: mail or SharePoint? Where does the submitted RFP copy live (style-store seed)?
- [?4] Win/Loss on SharePoint: what should happen to the deal folder (nothing / move / tag)?
- [?5] Confirm MyWork_OneDrive = dead pre-migration copy (demote to cold archive); does working MyWork get its own backup leg, or does SharePoint presence suffice for deal docs?
