# Corporate OS — New Chat Handoff (2026-03-23)

Przeczytaj ten dokument w CAŁOŚCI zanim odpowiesz. To jest konsolidacja 2 tygodni pracy (30+ godzin, 3 czaty, 12 Council decisions). Plik MASTER_HANDOFF.md w .ecosystem/ ma więcej szczegółów — przeczytaj go przez Claude Code jeśli potrzebujesz.

---

## Kim jest Rob

Technical Pre-Sales Engineer (Associate Solutions Advisor) w Blue Yonder, EMEA (Barcelona). Pracuje z 30-40 klientami rocznie. Ma ADHD. Mówi po polsku naturalnie, kod i dokumentacja zawsze po angielsku. Używa PowerShell, Claude Code (terminal), ten chat (przeglądarka) do architektury i decyzji. Claude Code dostaje prompty wygenerowane tutaj — zawsze jako downloadable .md file, nigdy inline.

---

## Co budujemy

Corporate OS — ekosystem narzędzi do zarządzania wiedzą korporacyjną. Cel: Rob wrzuca plik → system go klasyfikuje, routuje, extrahuje wiedzę → wiedza jest dostępna w Obsidian vault → corp prep generuje briefing na spotkanie z klientem → RFP agent odpowiada na pytania klientów.

---

## Ekosystem (C:\Users\1028120\Documents\Scripts\)

| Repo | Testy | Co robi | Stan |
|------|------:|---------|------|
| corp-by-os | 715 | Orkiestrator. CLI: corp project/run/task/chat/template/index/query/analytics/doctor/ingest/retrieve/prep/rfp/cleanup/freshness. Jedyny repo który pisze do vault. | Working |
| corp-knowledge-extractor (CKE) | 549 | Czysta engine ekstrakcji. v0.5.0: tagi (11 prefixów), auto-routing (Pro/Flash), provenance, file naming `{date}_{name}_{hash4}.md`. Multi-provider: Anthropic/Gemini. | Working |
| corp-os-meta | 105 | Shared Pydantic schema + taxonomy. Product aliases + hierarchy. `expand_product_query("wms")` → wms + children. | Working |
| corp-rfp-agent | 151 | RFP knowledge base. 1155 verified + 174 draft entries, 41 product profiles. Excel feedback loop. ChromaDB. | Working, needs vault integration |
| corp-opportunity-manager | 61 | CLI "com": new/list/show/prep-deck. Boundary violation flagged (vault_path in folder_manager). | Working |
| corp-project-extractor | 45 | Scan + extract-cke + render pipeline. Lenzing pilot: 141/143 files. | Working |
| corp-ops | 74 | PowerShell operational toolbox: backup, sync, cleanup, ecosystem scan. | Working |
| ai-council | 78 | Multi-model CLI debate system (5 models). 12 decisions made. | Working |
| corp-pdf-toolkit | 1 | PDF utilities. | Minimal |
| corp-sca-time-automation | 4 | Weekly SharePoint time tracking (calendar → Gemini → SharePoint API). | Working |

### Architektoniczne reguły (binding):
- corp-by-os jest JEDYNYM orchestratorem i vault writerem
- CKE jest CZYSTĄ extraction engine — zero routing, zero vault writes
- corp-os-meta jest shared source of truth dla schema i taxonomy
- `90_System/routing_map.yaml` jest single routing authority
- Zero manual triage jest hard constraint
- Forward slashes wszędzie w databases
- Git feature branches, nigdy nie usuwaj kodu bez pytania

---

## MyWork (C:\Users\1028120\Documents\MyWork\)

Struktura po Council Decision #9 (3-zone operational):

```
00_Inbox/                    ← MAGISTRALA — pliki wchodzą tu, routing je dystrybuuje
  _Review/                   ← low-confidence files czekają na Roba
  _Unmatched/                ← fallback

20_Workflows/                ← Reusable execution assets
  00_Master_Deck/            ← 1 plik: Blue Yonder Corporate Presentation Deck (94MB)
  Sales/                     ← 4 pliki (pitch deck + 3 moved from Competitive)
  PreSales/
    Technical_Presentations/ ← 8 tech decks (Platform, WMS, Planning, EDO, Integration, S2S)
    Demos/                   ← 8 plików (scripts + payloads + data)
    Discovery/               ← 2 pliki (questionnaire + value proposition matrix)
    RFP/                     ← 12 responses + 1 RFI template
      Databases/             ← 12 plików (canonical JSONs + source Excel — RFP agent source of truth)
      Collected/             ← 3 client folders (Clicks, Lenzing, Michelin) z questionnaires
  Services/                  ← 1 plik (QBR template)

30_Reference/                ← Stable reusable knowledge (ROB RĘCZNIE WYCZYŚCIŁ — sprawdź aktualny stan)
  Product/Platform/          ← ~11 plików (data specs, KYP, service desc, mappings)
  Product/WMS/               ← ~5 plików (architecture, PDC reference)
  Product/Planning/          ← ~3 pliki (cognitive planning, deep meta learning)
  Product/TMS/               ← empty placeholder
  Product/OMS/               ← empty placeholder
  Product/Network/           ← empty placeholder
  Architecture/              ← 2 pliki (platform architecture)
  Brand_Marketing/           ← 2 pliki (brand guidelines PDF + markdown)
  Data_Analytics/            ← 2 pliki (Snowflake, EDO)
  Competitive/Other/         ← 1 plik (Corning differentiation)
  Training/                  ← PUSTY — legacy moved to OneDrive _Legacy_Knowledge

40_Media/                    ← PUSTY — legacy moved to OneDrive _Legacy_Knowledge
  Meetings/
  Demos/
  Training/

70_Admin/                    ← 15 plików (personal admin)
80_Compliance/
  Certificates/Current/      ← 7 latest certs (ISO22301, ISO27001, SOC1 2025, SOC2 2025, etc.)
  Certificates/Archive/      ← 11 old versions
  Policies/                  ← 1 plik (cybersecurity annex)
90_System/                   ← 6 config files at root + .audit/ .logs/ .scripts/
  Project_Codes.xlsm, Platform_Usage_by_Product.xlsx, content_registry.yaml,
  routing_map.yaml, config.json, solution_matrix.json
```

### OneDrive:
```
MyWork_OneDrive/
  10_Projects_OneDrive/       ← 31 SharePoint shortcuts do teamowych kanałów
  80_Archive_OneDrive/
    2024/ (5348), 2025/ (2027), 2026/ (1056)
    _Legacy_Roles/ (610), _Presentations_Legacy/ (261)
    _Legacy_Knowledge/        ← Training + Media legacy (do incremental re-processing)

OD_MyWork/
  OD_10_Projects/             ← 123 Rob's personal project files
```

### SAFETY:
- OneDrive sync client jest OFF
- NIGDY nie pozwalaj cleanup dotykać "OneDrive - Blue Yonder" z delete
- Shadow copies istnieją na C: (5 snapshots)
- Incident 2026-03-14 i 2026-03-22: usunięte pliki odzyskane z shadow copy

---

## Obsidian Vault (C:\Users\1028120\Documents\ObsidianVault\)

```
00_Home/Home.md              ← Dataview dashboard (working, ale vault pusty = brak danych)
01_Knowledge/                ← PUSTY — czeka na extraction
02_Navigate/                 ← 9 empty MOC folders:
  Products/, Clients/, Domains/, Topics/, Competitive/,
  Compliance/, Training/, Recent/, Quality/
99_System/taxonomy.yaml      ← 11 tag dimensions defined
_assets/                     ← empty
_quarantine/                 ← empty
```

### 11 Tag dimensions (from taxonomy.yaml):
product/, client/, domain/, topic/, type/, source/, comp/, compliance/, training/, function/, audience/

### Backup: Obsidian Sync (vault: corp-brain)

---

## 12 Council Decisions (in .ecosystem/decisions/)

| # | Decision | Implemented? |
|---|----------|-------------|
| 1 | Knowledge architecture: hybrid YAML+SQLite, FTS5+metadata, single corp retrieve API | ✅ Yes |
| 2 | Extraction quality: base + 5 overlays, tiered depth, doc_type classifier | ✅ Yes |
| 3 | Model selection | SUPERSEDED by #8 |
| 4 | Vault structure | SUPERSEDED by #7 |
| 5 | Re-extraction strategy: parallel cutover, continuous versioning, identity by source_path | Partial |
| 6 | Quality gate: 4-state ingestion (pass/soft_fail/hard_fail/degraded), heuristic cross-check | ❌ NOT built |
| 7 | Vault navigation: flat 01_Knowledge/ + auto-MOC in 02_Navigate/ + hierarchical tags | ✅ Structure done, MOC generator NOT built |
| 8 | Model tiering + Gemini capabilities: Pro for PPTX/PDF/video, Flash for text. Structured Outputs planned Sprint 2. | ✅ Auto-routing done. Structured Outputs ❌ |
| 9 | Knowledge dimensions: 3-zone MyWork (Workflows/Reference/Compliance) | ✅ Yes |
| 10 | Naming convention: YYYY-MM_TYPE_TOPIC_CLIENT_Title.ext, 11 TYPE prefixes | Defined, ❌ NOT enforced |
| 11 | Distribution algorithm: hybrid rules+LLM, rename on ingest, hash tracking, extract from stable only | Defined, ❌ NOT built |
| 12 | Pattern adoption: gotchas skill, verification scripts, understand-before-plan step | ✅ Yes |

---

## Sprint Plan — co było planowane vs co zrobione

### Sprint 0: FOUNDATION ← MOSTLY DONE
- ✅ Clean vault
- ✅ CKE v0.5.0 (tags, routing, provenance, naming)
- ✅ Corp-by-os ingest routing fix (715 tests)
- ✅ Decisions documented (12)
- 🔄 Batch B extraction (running, ~101 notes, 9 projects)
- ⏸️ Source library extraction (stopped — files moved)
- ❌ corp prep SGDBF test (not done)

### Sprint 1: NAVIGATION ← PARTIALLY DONE
- ✅ Homepage with Dataview queries
- ❌ `corp generate-mocs` command NOT built
- ❌ Obsidian plugins NOT installed (Dataview, Homepage, Omnisearch, Folder Note)

### Sprint 2: EXTRACTION QUALITY ← NOT STARTED
- ❌ Structured Outputs (JSON mode in CKE)
- ❌ JSON in index.db
- ❌ Thinking mode classifier
- ❌ 200 PDF benchmark
- ✅ Provenance metadata (done in v0.5.0)
- ✅ Auto-routing (done in v0.5.0)

### Sprint 3-4: QUALITY, RETRIEVAL, AUTOMATION ← NOT STARTED
- ❌ Quality gate, embeddings, reranker, RFP vault integration, freshness, overnight pipeline

### NOWE (z Decisions #9-12, nie w oryginalnym planie):
- ✅ MyWork 3-zone restructure
- ✅ Deep review + cleanup 30_Reference/ (90% quality ratio)
- ✅ Pattern improvements (gotchas, verification, understand)
- ❌ Naming convention enforcement
- ❌ Magistrala / distribution algorithm (corp ingest-inbox)
- ✅ Legacy Training + Media → OneDrive _Legacy_Knowledge

---

## Lesson Learned (KRYTYCZNE)

1. **Nie rób big-bang.** Próbowaliśmy zrestrukturyzować WSZYSTKO naraz. Straciliśmy pliki (odzyskane z shadow copy). Puściliśmy extraction przed stabilną strukturą. 5 rund cleanup zamiast jednej.

2. **Build incrementally.** Jeden plik → inbox → classify z kontekstem Roba → route → extract → review → feedback → następny plik.

3. **Extract only from stable locations.** Jeśli plik się przeniesie po extraction, source_path w vault note jest złamany.

4. **Rob's context is essential.** Pattern matching nie wystarczy. Rob mówi "to jest hands-on exercise" albo "to jest Cognitive Friday paired z MP4" — ten kontekst musi płynąć przez pipeline.

5. **Archive folders: ZAWSZE verify Rob's files vs SharePoint copies BEFORE delete.**

---

## Co robimy TERAZ

### Priorytet 1: MAGISTRALA (distribution bus)

To jest kluczowy brakujący element. Bez tego nie da się budować wiedzy systematycznie.

```
Rob wrzuca plik do 00_Inbox/
  → CLASSIFY (LLM + rules + Rob's context)
  → RENAME (naming convention)
  → ROUTE (content_registry.yaml)
  → EXTRACT (CKE z stable location)
  → INGEST (corp ingest-extractions → vault)
  → REVIEW (Rob sprawdza jakość)
  → FEEDBACK (improve next cycle)
```

Na TERAZ: Claude Code jest naszym LLM. Rob mówi "wrzucam Cognitive Friday S4E1", Claude Code klasyfikuje, proponuje destination + name, Rob potwierdza, plik się przenosi, CKE extrahuje.

PRZYSZŁOŚĆ: `corp ingest-inbox` command z hybrid rules + Gemini Flash fallback.

### Priorytet 2: End-to-end test

Po zbudowaniu magistrali, przetestuj CAŁY flow:
1. Weź jeden plik z _Legacy_Knowledge (np. Cognitive Friday session)
2. Wrzuć do Inbox
3. Classify → Route → Extract → Ingest → Vault
4. Sprawdź: note w Obsidian, tagi poprawne, corp prep zwraca wynik
5. Iterate

### Priorytet 3: Reference extraction

30_Reference/ ma ~25 czystych plików w stabilnych lokalizacjach. Extract → ingest → vault. To daje baseline content dla corp prep.

### Czego NIE ROBIĆ:
- Nie rób big-bang extraction (Batch A mistake)
- Nie restructuryzuj folderów (już zrobione)
- Nie podejmuj 12 decyzji przed implementacją jednej
- Nie puszczaj równoległych operacji na tych samych folderach
- Nie usuwaj bez verification

---

## Inne czaty (handoff done)

- **CKE chat:** dostał update o v0.5.0, nowych ścieżkach, czeka na prompty z tego chatu
- **RFP Agent chat:** dostał update o przeniesionych databases, czeka na vault integration

Oba chaty czekają na polecenia Z TEGO CHATU. Ten chat decyduje, tamte execute.

---

## Pliki konfiguracyjne (key paths)

| Co | Gdzie |
|---|---|
| API keys | C:\Users\1028120\Documents\.secrets\.env |
| Content registry (routing rules) | MyWork\90_System\content_registry.yaml |
| Vault taxonomy (11 dimensions) | ObsidianVault\99_System\taxonomy.yaml |
| Ecosystem map | Scripts\.ecosystem\ECOSYSTEM.md |
| Council decisions | Scripts\.ecosystem\decisions\DECISION_01..12.md |
| Master handoff | Scripts\.ecosystem\MASTER_HANDOFF.md |
| Global CLAUDE.md | ~/.claude/CLAUDE.md |
| Gotchas skill | ~/.claude/skills/gotchas/gotchas.md |
| Cross-repo validator | ~/.claude/skills/verify/cross-repo-boundaries.ps1 |
| CKE schema validator | CKE/.claude/skills/verify/output-schema.ps1 |

---

*Zacznij od sprawdzenia co jest w 30_Reference/ (Rob ręcznie wyczyścił) i zaproponuj pierwszy krok magistrali.*
