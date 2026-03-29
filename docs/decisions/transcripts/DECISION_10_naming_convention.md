# AI Council Debate: # Council Question: MyWork File & Folder Naming Convention + Structure Vision

#

**Date:** 2026-03-23 00:28:08
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 256.3s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_naming_convention.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
Adopt a strict, context-rich filename contract (`YYYY-MM_{CATEGORY}_{Scope}_{Description}.ext`) as the immutable source of truth for all metadata, treating folder structures as secondary operational boundaries. CKE must act as a read-only consumer of this file system to safely map filename schemas into Obsidian YAML tags without mutating source assets.

## Rationale
*   **Zero-Trust File Context:** By embedding `{CATEGORY}` and `{Scope}` (e.g., a Client name or "Internal") directly in the filename, you mitigate the threat surface of accidental data spillage (e.g., sharing a Michelin deck with Lenzing) regardless of which folder the file gets moved or copied to.
*   **Safe Interoperability (CKE to Obsidian):** Relying on filenames rather than folder paths provides a durable API contract for CKE. If a file is moved across folders, CKE still accurately generates `tags: [type/deck, scope/internal]` in the Obsidian vault based on the parsed string.
*   **Compliance & Chain of Trust:** For RFP responses and SOC/ISO certificates, explicitly segregating active assets from deprecated ones while enforcing `{YYYY-MM}` in the filename prevents the critical business risk of distributing superseded compliance documentation.
*   **Asset Segregation by Risk/Weight:** Grouping heavy, unstructured binaries (`RECORDING`) in a dedicated `40_Media/` folder prevents sync saturation in OneDrive and clearly separates highly-scrubbed shareable deliverables from raw, unreviewed meeting captures.

## Trade-offs
*   **Metadata Redundancy:** You will experience duplication between folder names and file names (e.g., `30_Templates/Decks/Platform/2026-03_DECK_Platform_...`), which violates DRY (Don't Repeat Yourself) principles but maximizes file portability.
*   **Cognitive Friction:** Enforcing this naming convention requires discipline at the exact moment of file creation, which adds slight friction to ADHD workflows. 
*   **Legacy Technical Debt:** Adopting a practical "day-forward" policy (enforcing rules only on new files) means the existing 200+ files will remain a disorganized threat surface until manually remediated or phased out.

## Risks
*   **Integration Risk: Source File Mutation by CKE**
    *   *What could go wrong:* If CKE is configured to auto-rename source files to enforce the new convention, it creates race conditions with OneDrive sync, breaks existing hyperlink references in other documents, and risks file corruption.
    *   *Mitigation:* Architect CKE to be strictly **read-only** against `MyWork/`. It should map vault tags based on compliant filenames and simply skip/flag non-compliant files during extraction without executing write operations on the source filesystem.
*   **Threat Surface: Cross-Contamination of Sensitive Data**
    *   *What could go wrong:* Storing raw data payloads (`DATA`), competitive intel (`COMPETITIVE`), and client deliverables (`DECK`) in mixed folders increases the risk of inadvertently sharing proprietary system configurations or competitive battlecards with prospects.
    *   *Mitigation:* Treat folders as security boundaries. Keep `COMPETITIVE` and `DATA` strictly in isolated internal folders. Use clear delimiters (e.g., underscores `_` for schema sections, hyphens `-` for spaces) so automated DLP (Data Loss Prevention) scanners and PowerShell scripts can easily audit file locations.
*   **Operational Risk: Compliance Document Drift**
    *   *What could go wrong:* Mixing multiple versions of ISO 27001 or SOC 2 certificates in the root `50_RFP/Certificates/` folder guarantees that an expired certificate will eventually be attached to a multi-million dollar RFP.
    *   *Mitigation:* Create a strict `/Current` and `/Archive` subfolder structure. Move all older certs to `/Archive` immediately. The filename must explicitly state the valid year/version (e.g., `2025-10_CERT_SOC2_Cloud.pdf`) so the context is obvious even when attached to an email.
*   **System Risk: Context Loss on Master Assets**
    *   *What could go wrong:* If "The" Master Corporate Deck is mixed in with localized or client-specific decks, colleagues or scripts may pull the wrong base template, degrading brand trust.
    *   *Mitigation:* Protect the hierarchy. `00_Master_Deck` must be a dedicated, visually distinct folder. The file itself should be named `YYYY-MM_DECK_Internal_Corporate_Master_DO_NOT_EDIT.pptx` to explicitly state its authoritative status.

*Latency: 29.66s | Tokens: 6571*

### Deepseek (deepseek-reasoner)

## Position
Adopt a hierarchical folder-first organization with simplified semantic naming (client-topic-type-date), complemented by CKE-driven auto-tagging in Obsidian—not manual filename tags. Implement phased migration starting with critical directories.

## Rationale
- **Folder hierarchy provides primary categorization** while reducing filename verbosity—humans navigate folders, scripts search by metadata. A `40_Media/Meetings/2025-10-Michelin/` structure naturally groups related files without cramming all context into filenames.
- **Simple, memorable naming convention (`Client_Topic_Type_Date`)** reduces cognitive load for ADHD workflows while preserving searchability. Example: `Lenzing_WMS_Deck_2025-10.pptx` is scannable and OneDrive-safe.
- **CKE should infer Obsidian tags from folder location + file content**, not require duplicate tags in filenames. This separates concerns: source files remain human-readable, vault notes become machine-optimized via extraction rules.
- **Media files belong with their logical context**, not a separate media silo. A meeting recording should live in `60_Source_Library/02_Training/2025-10-Planning/` alongside its deck—this matches mental models and preserves relationships.

## Trade-offs
- **Loss of full context in filenames**—searching across folders requires tooling (PowerShell/Claude) rather than pure filename grep. However, folder-based searches are more structured.
- **Initial reorganization effort** requires scripting to move/rename files based on current metadata. This is a one-time cost.
- **Less explicit tagging in filenames** means sharing files externally may require manual explanation of folder context. Mitigate by including key descriptors in filenames.

## Risks
1. **Folder sprawl** if subcategories multiply unchecked. Mitigation: Enforce a fixed-depth limit (max 3 subfolders) and periodic audits.
2. **CKE mis-tagging** if folder→tag mapping rules are incomplete. Mitigation: Maintain a explicit `content_registry.yaml` mapping (e.g., `30_Templates/01_Decks/Platform/` → `tags: [type/deck, product/platform]`).
3. **Legacy file migration paralysis**. Mitigation: Phase migration—start with `30_Templates` and `50_RFP`, use PowerShell to batch rename using AI-extracted metadata from current files.
4. **Inconsistent adoption**. Mitigation: Create a saved Claude prompt that generates correct filenames on demand, and implement a lightweight pre-commit hook for OneDrive that warns on non-conforming names.

## Implementation Priorities
1. **Immediate**: Clean `30_Templates` using audit data—create `00_Master_Deck/`, `01_Decks/` by product, `02_Demo_Scripts/`. Rename files to `Client_Topic_Type_Date.ext`.
2. **Quick win**: Flatten `50_RFP`—keep only latest certs in `Certificates/` with `YYYY-MM_CertName.pdf`, archive old versions to `_archive/`.
3. **Tooling**: Enhance CKE to rename source files during extraction (configurable) and generate Obsidian tags from folder mapping rules.
4. **Governance**: Add a `_template` subfolder in each category showing correct naming examples.

This approach balances immediate usability with scalable automation, leveraging existing tooling while establishing clear conventions for future files.

*Latency: 45.08s | Tokens: 5134*

### Openai (gpt-5.4)

## Position
Adopt a **lightweight, mandatory filename schema for new files** plus a **type-first folder structure**, and do a **targeted cleanup of high-value existing assets only**.  
Do **not** try to encode full Obsidian-style tags in filenames; use filenames as structured metadata signals and let CKE derive vault tags from filename + folder path.

## Rationale
- **This is usable under ADHD/time pressure.** A naming standard only works if Rob can apply it in 5–10 seconds while saving a file. A shorter schema with fixed fields beats a “perfect” but verbose taxonomy that gets ignored.
- **Folder path should answer “where does this live,” filename should answer “what is this.”** If both try to carry the full taxonomy, you get redundancy, ugly names, and eventual drift.
- **Type-first organization matches the real workflows described.** Rob’s pain is usually “find the master deck / latest cert / recording / exec summary,” which starts with file type and purpose more than abstract knowledge taxonomy.
- **CKE can close the source-to-vault gap without forcing human tagging.** Humans should not manually maintain filename tags and YAML tags separately. CKE should infer structured tags from convention and location.
- **A partial migration is the only pragmatic path.** Renaming 200+ files for purity is expensive and brittle. Clean the assets people actually search for weekly; leave low-value archive material alone until touched.

## Trade-offs
- You give up **perfect semantic precision** in filenames. Some nuance will live in folder structure or extracted metadata rather than the file name itself.
- You accept **some redundancy** between folder and filename for searchability, especially for critical fields like type and topic.
- Historical files will remain **partially inconsistent** for a while if you only normalize high-value assets and all new files.
- A type-first structure makes some topic-based browsing less elegant; topic-based discovery will rely more on search and CKE/Obsidian indexing.
- Auto-renaming by CKE introduces operational complexity and a chance of breaking links if done carelessly.

## Risks
- **Risk: convention is too complex, so people stop using it.**  
  Mitigation: limit required fields to 4–5 tokens max; publish examples; provide save-as cheat sheet and PowerShell rename helper.
- **Risk: over-reliance on folder location causes ambiguity when files get moved or shared standalone.**  
  Mitigation: keep `TYPE` in filename always, and usually `TOPIC`; don’t rely on folder alone for identity.
- **Risk: CKE renames originals and breaks references/shared links.**  
  Mitigation: only auto-rename in controlled folders like `00_Inbox`; elsewhere suggest rename and require approval or create a renamed copy.
- **Risk: “media folder” becomes a dumping ground.**  
  Mitigation: split `40_Media` by origin/purpose and enforce recording-specific naming fields.
- **Risk: taxonomy drift (`Platform` vs `platform`, `CyberSecurity` vs `Security`).**  
  Mitigation: define a short controlled vocabulary for `TYPE`, `TOPIC`, `CLIENT`, and make CKE normalize aliases.

---

## Concrete recommendations

### 1. Naming convention: simplify it
Your proposed pattern is close, but I would tighten it to:

```text
YYYY-MM_TYPE_TOPIC_CLIENT_TITLE[_STATUS].ext
```

Where:
- `YYYY-MM` = required
- `TYPE` = required
- `TOPIC` = required except for pure admin/certs
- `CLIENT` = required if client-specific, else `GEN`
- `TITLE` = short human-readable description
- `STATUS` = optional, only for special cases like `MASTER`, `FINAL`, `V2`, `ARCHIVE`

### Why this version
- Keeps the high-signal fields first
- Still readable in Explorer/Finder/search
- Avoids overly long filenames
- Professional when emailed/shared
- Easy for scripts to parse

### Recommended examples
```text
2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
2026-03_DECK_WMS_LENZING_Architecture_Overview.pptx
2025-10_RFP_SECURITY_WURTH_Cloud_Approval.xlsx
2025-09_CERT_GEN_ISO27001_2023.pdf
2025-10_RECORDING_PLANNING_MICHELIN_Design_Thinking.mp4
2026-01_DEMO_PLATFORM_GEN_Analytics_Script.md
2025-11_DATA_PLATFORM_LENZING_Payload.csv
2026-02_EXEC_WMS_PRH_Summary.docx
```

### Practical rule
If Rob cannot name it in one pass, use:

```text
YYYY-MM_TYPE_TOPIC_CLIENT_Working.ext
```

and let CKE suggest a better title later.

---

## 2. Minimum required fields
For practicality, make these required:

- `date`
- `type`
- `topic`
- `client-or-GEN`
- short title

That’s enough.

Do **not** require:
- full tag list
- subtype
- version on every file
- “internal/external” in every filename
- exact usage date vs created date distinction

Use folder, file properties, or vault metadata for those.

---

## 3. Should filenames have tags?
**No, not the full Obsidian tag system.**  
**Yes, they should contain structured metadata tokens** that can be mapped to tags.

### Recommendation
Use filename tokens as **controlled labels**, not freeform tags:
- `DECK` → `type/deck`
- `PLATFORM` → `product/platform`
- `LENZING` → `client/lenzing`

Then let CKE derive:
- tags
- aliases
- note title
- source-type metadata

### Why
Embedding actual tag syntax in filenames is ugly and brittle.  
Example of what **not** to do:
```text
2026-03_type-deck_product-platform_topic-saas-architecture_client-lenzing.pptx
```

That is unmaintainable.

---

## 4. Folder structure: keep it type-first, but tighten it
I recommend this structure:

```text
MyWork/
  00_Inbox/
  10_Active_Work/
    CLIENT/
      Lenzing/
      Michelin/
  30_Templates/
    00_Master_Deck/
    01_Deck_Modules/
      Platform/
      WMS/
      Planning/
      TMS/
      Security/
    02_Demo/
    03_Discovery/
    04_Brand_Assets/
  40_Media/
    01_Client_Meetings/
    02_Demos/
    03_Training/
  50_RFP/
    01_Certificates/
      Current/
      Archive/
    02_Executive_Summaries/
      Generic/
      Client/
    03_Responses/
      Client/
    04_Databases/
    05_RFI_Templates/
  60_Source_Library/
    01_Product_Docs/
    02_Training_Enablement/
    03_Competitive/
  70_Admin/
  90_System/
```

## Why adjust your proposal
- `10_Active_Work` is worth reintroducing. Real client work-in-progress needs a home, especially for decks and recordings tied to a live engagement.
- `30_Templates/01_Decks` should become **Deck_Modules**, because many files are not true “templates”; they are reusable supporting assets.
- `04_Brand_Assets` prevents brand guidelines from being buried in reference folders.
- `50_RFP/Certificates/Current + Archive` solves the latest-vs-old problem cleanly.
- `Executive_Summaries` should separate generic from client-specific.

---

## 5. Master deck concept
Represent the hierarchy explicitly:

```text
30_Templates/
  00_Master_Deck/
    2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
    2026-03_GUIDE_PLATFORM_GEN_Master_Usage_Guide.docx
  01_Deck_Modules/
    Platform/
    WMS/
    Planning/
    Security/
```

### Rule
- `00_Master_Deck` contains **exactly one live master deck** plus immediate support files like usage guide or brand rules.
- Everything else is either:
  - a reusable module
  - a client variant in `10_Active_Work`
  - an archived superseded master in an archive folder

Suggested archive:
```text
30_Templates/00_Master_Deck/Archive/
```

This makes “Where is THE master?” trivial.

---

## 6. Where do MP4 recordings go?
**Put all recordings in `40_Media`, not scattered by topic.**

### Recommendation
Use `40_Media` as the canonical home for actual media binaries:
- MP4
- WAV
- M4A
- screen capture video

Then connect them to topic/client through filename and metadata.

Examples:
```text
2026-03_RECORDING_PLATFORM_MICHELIN_Discovery_Call.mp4
2026-03_RECORDING_TRAINING_GEN_Lighthouse_Session_04.mp4
2026-03_RECORDING_DEMO_GEN_WMS_Flow.mp4
```

### Why this is better
- Media files are large, operationally different, and often handled differently for sync/backup.
- It eliminates the “where does the MP4 go?” decision fatigue.
- Search still works because topic/client are in filename.

### Exception
If a recording is truly part of a purchased/vendor source pack and should remain intact as reference material, keep it in `60_Source_Library`, but that should be the exception, not the norm.

---

## 7. Should CKE rename source files?
**Yes, but only in a controlled way.**

### Recommendation
- In `00_Inbox`: **CKE may auto-suggest and optionally auto-rename**
- In structured folders: **CKE should recommend, not force**
- For files already linked/shared: **do not auto-rename silently**

### Safe operating model
1. File lands in `00_Inbox`
2. CKE extracts metadata and proposes:
   - target folder
   - normalized filename
   - vault tags
3. Rob approves or bulk-approves
4. CKE moves/renames file

### Why
This gives the value of automation without creating sync chaos.

### Hard no
Do not let CKE mass-rename the whole historical archive unattended.

---

## 8. Obsidian tag mapping
**Use filename + folder path + extracted content together.**

### Best model
Filename provides:
- `type/*`
- `product/*` or `topic/*`
- `client/*`
- `status/*` if present

Folder path provides:
- broader context like `library/competitive`, `rfp/certificates`, `template/master`

Content extraction provides:
- deeper semantic tags like `topic/saas-architecture`, `vendor/manhattan`, `capability/analytics`

### Example
File:
```text
2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
```

Folder:
```text
30_Templates/00_Master_Deck/
```

Derived vault frontmatter:
```yaml
source_file: 2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
source_path: MyWork/30_Templates/00_Master_Deck/
type: deck
topic: platform
client: generic
status: master
tags:
  - type/deck
  - product/platform
  - client/generic
  - asset/template
  - asset/master
```

This is the right division of labor.

---

## 9. Certificates management
For certs, optimize for **latest retrieval** first.

### Structure
```text
50_RFP/
  01_Certificates/
    Current/
    Archive/
```

### Naming
```text
2025-09_CERT_GEN_ISO27001_Current.pdf
2025-09_CERT_GEN_ISO22301_Current.pdf
2025-09_CERT_GEN_SOC2_Current.pdf
2024-08_CERT_GEN_SOC2_Archive.pdf
```

### Better rule
Only one `Current` file per cert family in `Current/`.  
Older ones move to `Archive/` with full date and optional version.

If official filenames must be preserved for legal/compliance reasons:
- keep original in `Archive/Originals`
- maintain a normalized copy or shortcut in `Current/`

### Also do now
Flatten all email subfolders. Email-origin is not a durable filing logic.

---

## 10. Consistency vs practicality: migration strategy
**Do not rename everything now.** Use a 3-tier migration.

### Tier 1: rename now
High-frequency, high-value assets:
- master deck
- reusable deck modules
- all current certs
- executive summaries
- demo scripts
- discovery tools
- active competitive intel
- recurring training assets

### Tier 2: clean structure, rename on touch
- old client deliverables
- historical source docs
- older training files
- scattered recordings

### Tier 3: leave alone unless needed
- deep archive
- deprecated material
- low-value one-off files

This gives 80% of the value for 20–30% of the effort.

---

## Direct answers to the 8 council questions

### 1. Is the naming convention practical?
**Mostly yes, but slightly too verbose in its current framing.**  
Use:

```text
YYYY-MM_TYPE_TOPIC_CLIENT_TITLE[_STATUS]
```

That is the practical minimum.

### 2. Should filenames have tags or rely on folder location?
**Filenames should include key structured fields; do not rely on folder alone.**  
Always include at least `TYPE` and usually `TOPIC`. Folder is supportive, not sufficient.

### 3. Where do MP4 recordings go?
**Canonical home = `40_Media/`**  
Split by `Client_Meetings`, `Demos`, `Training`. Don’t scatter large media across topic folders.

### 4. Should CKE rename source files?
**Yes in Inbox; cautious elsewhere.**  
Auto-suggest globally, auto-rename only in controlled intake flow.

### 5. How does this map to Obsidian tags?
**CKE should derive tags from filename tokens + folder path + content.**  
Filename is a signal, not the full metadata system.

### 6. Master deck concept?
**Single live master in `30_Templates/00_Master_Deck/`; all supporting reusable content in `01_Deck_Modules/`.**  
Client-customized versions belong in `10_Active_Work/Client/...`.

### 7. RFP certificates management?
**`Current/` + `Archive/` with one live file per cert family.**  
Flatten email subfolders and normalize names now.

### 8. Rename everything now or only new files?
**Enforce for new files immediately; retroactively fix only high-value assets now.**  
Rename-on-touch for the rest.

---

## Final implementation policy I’d recommend

### Mandatory filename vocabulary
Controlled `TYPE` list:
- `DECK`
- `DEMO`
- `RECORDING`
- `RFP`
- `CERT`
- `EXEC`
- `DATA`
- `GUIDE`
- `TRAINING`
- `COMPETITIVE`
- `ADMIN`

Controlled `TOPIC` list:
- `PLATFORM`
- `WMS`
- `PLANNING`
- `TMS`
- `SECURITY`
- `GEN`

Controlled `CLIENT` rule:
- uppercase short canonical client token
- else `GEN`

### File naming cheat sheet
- Generic reusable deck:
  `2026-03_DECK_PLATFORM_GEN_Overview.pptx`
- Client deck:
  `2026-03_DECK_WMS_LENZING_Solution_Overview.pptx`
- Recording:
  `2026-03_RECORDING_PLANNING_MICHELIN_Workshop.mp4`
- Cert:
  `2025-09_CERT_GEN_ISO27001_Current.pdf`

### Operational rules
- New files start in `00_Inbox`
- CKE proposes route + rename
- Rob approves in batch
- Only approved folders are considered “organized”

This is the smallest system that is robust enough to stick.

*Latency: 51.03s | Tokens: 6509*

### Grok (grok-4.20-beta)

**Position**
Adopt a *minimal* naming convention of `{YYYY-MM}_{CLIENT}_{TOPIC}_{ShortDesc}.ext` (date at *end*, no redundant CATEGORY prefix) and keep the proposed folder hierarchy but strip almost all leading numbers and over-nested subfolders. The source filename is *not* the source of truth—folder + filename together are. CKE should parse the *path* first, then filename, for Obsidian tags. Only enforce the new convention on new files.

**Rationale**
- The proposed `{date}_{CATEGORY}_{topic}_{client}_{description}` pattern is classic over-engineering that violates the ADHD constraint. Rob will not consistently type `2026-03_DECK_Platform_Corporate_Master` when he’s in a hurry. Shorter names with date at the end keep the *semantically important* tokens left-aligned so “Corporate Master” and “Platform Overview” actually sort together.
- Category in the filename is pure redundancy when the folder is already `30_Templates/01_Decks/Platform/`. We are optimizing for *human* scanning, not for a hypothetical perfect parser. The current mess proves that when naming is painful, people stop doing it.
- Numbered prefixes (00_, 30_, 90_) are a smell. They are an admission that the folder names themselves aren’t strong enough signals. Let’s make the folder names strong enough that the numbers become unnecessary (Inbox, Templates, Media, RFP, Library, Admin).
- Master deck problem is solved by *location*, not naming: `Templates/00_Masters/Corporate.pptx` (singular, no date). Everything else is a derivative. This is the unpopular truth everyone avoids: most of the 30_Templates folder should not exist as “live” files.
- Obsidian already wins on tagging. Treating the filename as the primary signal for `tags: [type/deck, product/platform]` is fragile. Path-based tagging is more robust and requires less filename gymnastics.

**Trade-offs**
- You lose the ability to understand a file’s type when it appears in global search results or is detached from its folder (e.g. emailed or dropped in Teams). We accept this because Rob almost always finds files *from within* the structure or via Obsidian.
- Chronological sorting in flat views becomes slightly harder (though still possible via OneDrive’s date columns).
- Slightly more work to train CKE to read the folder path as the primary category signal.
- You give up the fantasy of a perfectly self-describing filename that answers every question without context.

**Risks**
- **Inconsistent adoption / regression to chaos.** Mitigation: One-page “Save As” cheat sheet permanently pinned in Obsidian + a simple PowerShell `Test-MyWorkName` function that Rob runs before major cleanups. Quarterly 30-minute cleanup ritual, not heroic 5-round marathons.
- **CKE gets worse tagging initially.** Mitigation: Make the path parser the default and treat filename as fallback. Add a manual tag override layer in the vault for the few files that need it.
- **Colleagues see “ugly” names when files are shared.** Mitigation: Rob almost always renames deliverables before sending anyway. The internal name can stay structured; the exported version can be `Lenzing_Planning_Architecture_Overview_Mar2026.pptx`.
- **Recordings become unfindable in 40_Media.** Mitigation: Enforce strict `{YYYY-MM}_{Client}_{Topic}_Recording.ext` inside `Media/Meetings/` and add a simple year/month subfolder structure (2025/03/, 2025/04/). Never mix MP4s with PPTs again.

This approach deliberately chooses *sustainable discipline* over *perfect taxonomy*. The consensus view is “we just need a better, more complete naming standard.” The contrarian view is that the standard was already too heavy—that’s why five cleanup rounds failed. Make it so simple that the sixth round is the last one.

*Latency: 47.20s | Tokens: 6799*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, I view this file system not just as a personal organizer, but as a heterogeneous data pipeline spanning local storage, OneDrive sync, CKE (Claude Knowledge Extractor) processing, and eventual Google Drive backup. 

My primary concerns are **data spillage** (sending competitive/internal data to clients), **sync race conditions** (automated tools fighting OneDrive/G-Drive), and **context loss** (metadata stripped when files cross system boundaries).

Here is my evaluation of the council’s proposals, followed by a hardened architectural recommendation.

---

### Evaluation of Proposal A
**Position:** Partially Agree.
I agree with the targeted cleanup and the use of an Inbox for automated routing, but it relies too heavily on soft conventions rather than hard system boundaries for sensitive assets.
*   **Strongest point:** The `00_Inbox` operational flow. Quarantining new files in an Inbox where CKE can safely auto-suggest renames *before* they enter the synced file system prevents breaking established links.
*   **Weakest assumption:** Assumes adding a "GEN" (Generic) token to a filename is sufficient to prevent data spillage. Filename tokens do not enforce Data Loss Prevention (DLP) rules; folder paths do.
*   **Overlooked risks:** Allowing an automated script (CKE) to move/rename files from `00_Inbox` into synced OneDrive folders introduces classic race conditions. If OneDrive attempts to sync the file while CKE is writing the rename or moving it, the file locks, generating `[Filename]-Copy.sync-conflict.ext` artifacts.

### Evaluation of Proposal B
**Position:** Agree.
This proposal correctly identifies the severe integration and security risks of mutating source files and mixing data classifications.
*   **Strongest point:** Mandating that CKE operates as strictly **read-only** against the structured file system. This is the only way to guarantee safe interoperability between Obsidian, Claude, and OneDrive without risking file corruption or broken sharing links.
*   **Weakest assumption:** Assumes an ADHD user will strictly adhere to a verbose, "context-rich" manual naming convention under time pressure without automated intake assistance. If the system requires zero-friction, strict manual enforcement will fail.
*   **Overlooked risks:** Ignores the future Google Drive backup constraint. Treating folders merely as "secondary operational boundaries" ignores that enterprise backup and selective-sync rules operate at the folder level. You cannot easily exclude a 5GB video from syncing if it sits in the same directory as a 50KB spreadsheet.

### Evaluation of Proposal C
**Position:** Disagree.
This proposal optimizes entirely for immediate visual aesthetics at the expense of data portability and security.
*   **Strongest point:** Recognizing the human constraint. If the naming schema is too long, it simply won't be used, rendering the entire architectural debate moot.
*   **Weakest assumption:** Assumes folder paths are durable and static. Relying on the folder path as the primary semantic signal guarantees catastrophic context loss the second a file is dragged to a desktop, emailed to a client, or uploaded to a vendor portal.
*   **Overlooked risks:** Massive threat surface for data leakage. If `{CATEGORY}` is removed from the filename, a file named `2026-03_Michelin_Architecture.pptx` could be a sanitized client deliverable, or it could be a highly confidential internal vulnerability assessment. Detached from its folder, the file is a loaded gun.

### Evaluation of Proposal D
**Position:** Disagree.
This architecture actively promotes system instability and mixes highly disparate data types in a way that breaks defense-in-depth principles.
*   **Strongest point:** Utilizing a `content_registry.yaml` to explicitly map folder locations to Obsidian tags. This establishes a deterministic, version-controlled integration contract between the file system and the vault.
*   **Weakest assumption:** Mixing massive 500MB MP4 recordings with 5MB text files/decks in granular subfolders just because they share a "topic." This is catastrophic for OneDrive sync performance and bandwidth management.
*   **Overlooked risks:** Recommending CKE auto-rename existing files in-place. If Rob has shared a OneDrive link to `Lenzing_Draft.pptx` with a client, and CKE silently renames it to `Lenzing_WMS_Deck_2025-10.pptx`, the client's link instantly breaks. Automated mutation of shared production assets is an unacceptable integration risk.

---

### Revised Recommendation: The Architect's Blueprint

To satisfy defense-in-depth, safe interoperability, and the ADHD constraints, we must separate **Identity** (what the file is, carried in the filename) from **Access & Processing** (how the system handles it, governed by folders).

#### 1. The Immutable Naming Schema (Context-as-a-String)
Filenames must carry enough context to prevent accidental data leakage when detached from their folder, but be short enough to type in 5 seconds.
**Schema:** `YYYY-MM_[TYPE]_[CLIENT|GEN]_[Short_Title].ext`
*   *Why no TOPIC?* Because `TYPE` and `CLIENT` dictate the *risk and classification* of the file. Topic dictates the *content*, which Obsidian/CKE can index perfectly via content extraction and path mapping.
*   *Examples:*
    *   `2026-03_DECK_LENZING_Architecture.pptx` (Safe to share with Lenzing)
    *   `2026-03_DATA_MICHELIN_Payloads.csv` (High risk, never share)
    *   `2025-10_CERT_GEN_ISO27001.pdf` (Public trust asset)

#### 2. Folder Architecture as Security & Sync Boundaries
Folders must segregate assets by their sync weight and security classification, not just their topic.
*   `00_Inbox/` — **The Intake Zone.** (Only place CKE has Write permissions).
*   `10_Client_Active/` — **External risk boundary.**
*   `30_Master_Templates/` — **Brand trust boundary.** (Read-only for day-to-day work).
*   `40_Media_Recordings/` — **Heavy asset boundary.** (Isolate all MP4s here to prevent OneDrive/G-Drive sync saturation and allow selective exclusion from backups).
*   `50_Compliance_RFP/` — **Legal trust boundary.**
    *   `/Current/` (Strictly maintained, only latest versions).
    *   `/Archive/`
*   `60_Internal_Intel/` — **Internal risk boundary.** (Competitor data, scripts. Never to be shared).

#### 3. CKE Integration Contract (Safe Interoperability)
CKE must follow a strict **Read-Only + Quarantine Write** model to prevent race conditions and broken links:
1.  **In `00_Inbox/`:** CKE reads the file, extracts content, and outputs a recommended PowerShell rename/move command for Rob to execute, OR executes it locally before OneDrive has time to lock the file.
2.  **In all other folders (10 through 60):** CKE is strictly **READ-ONLY**. It parses the filename to grab `TYPE` and `CLIENT`, parses the path via `content_registry.yaml` to grab `TOPIC` and `CLASSIFICATION`, and generates the Obsidian YAML.
3.  **Source File Mutation is banned.** CKE must never rename files in active folders. If a file is misnamed, CKE flags it in an Obsidian "Audit Dashboard" note for human remediation.

#### 4. Migration Strategy
Do not attempt a massive automated rename of legacy files.
1.  **Tier 1 (Immediate, Manual):** Manually secure the "Trust Assets" (Master Deck and `50_RFP/Current` certificates). Flatten the cert folders. Archive the rest.
2.  **Tier 2 (Day-Forward):** Enforce the new schema via the `00_Inbox/` workflow. Let CKE assist in tagging.
3.  **Tier 3 (Legacy):** Move `03_Competitive` and `02_Demo_Scripts` into the `60_Internal_Intel` boundary immediately to stop the threat surface of mixed client/internal folders, even if the filenames inside remain ugly for now.

*Latency: 36.12s | Tokens: 13759*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A
**Position:** Lightweight mandatory schema + type-first folders + targeted cleanup  
**Verdict:** Partially agree - Strong foundation but misses key optimization opportunities

**Strongest point:** Pragmatic phased migration strategy (Tier 1-2-3). This acknowledges real-world constraints and avoids the "big bang" failure mode.

**Weakest assumption:** That type-first organization matches real workflows. Analysis shows Rob's searches are actually topic/product-first ("platform demo deck"), not type-first ("deck for platform"). This creates cognitive friction.

**Overlooked risks:**
1. **Search performance degradation:** Files scattered across multiple type-based folders require recursive searches for topic-based queries
2. **Duplicate maintenance:** Same topic appears in DECK, DEMO, RECORDING folders → triplicate updates
3. **Cache locality penalty:** Related files accessed together (deck + recording + data) are physically separated, increasing I/O overhead

### Proposal B
**Position:** Strict filename-as-contract + CKE read-only  
**Verdict:** Disagree - Architecturally rigid and operationally impractical

**Strongest point:** Zero-trust context embedding prevents data spillage - important for compliance materials.

**Weakest assumption:** That filename redundancy is acceptable for portability. This violates DRY at scale and creates maintenance synchronization problems.

**Overlooked risks:**
1. **O(n²) maintenance complexity:** Every folder reorganization requires filename updates
2. **Metadata drift:** Filename fields become stale when underlying metadata changes (client name, product rebranding)
3. **Search false negatives:** Partial filename matches miss moved files due to path dependency in real-world search tools

### Proposal C
**Position:** Minimal naming + stripped folders + path-based tagging  
**Verdict:** Disagree - Over-corrects toward simplicity, sacrificing discoverability

**Strongest point:** ADHD-friendly naming - correctly identifies that cognitive load matters more than completeness.

**Weakest assumption:** That "Rob almost always finds files from within the structure." Audit data shows frequent cross-folder searches (projects vs templates vs library).

**Overlooked risks:**
1. **Loss of programmatic access:** Without structured tokens, PowerShell/Claude searches require regex gymnastics
2. **Compression impossibility:** Can't implement efficient prefix-based compression for OneDrive/Google Drive sync
3. **Versioning chaos:** Date-at-end prevents chronological sorting in flat views

### Proposal D
**Position:** Folder-first + semantic naming + CKE auto-tagging  
**Verdict:** Partially agree - Correct diagnosis but wrong prescription

**Strongest point:** Recognition that folder hierarchy provides primary categorization - aligns with how humans actually navigate.

**Weakest assumption:** That "Client_Topic_Type_Date" naming reduces cognitive load. Actually increases decision complexity by forcing client-first thinking for generic files.

**Overlooked risks:**
1. **Access pattern mismatch:** Forces client context even for product-focused workflows
2. **Hash collision potential:** Similar names for different clients create confusion in global searches
3. **Cache invalidation:** Changing client relationships requires mass renaming

---

## Revised Recommendation: Optimized Hybrid with Performance Guarantees

### Core Principles
1. **Access-pattern-optimized structure:** Organize by primary access pattern (topic/product), secondarily by type
2. **Fixed-width tokens for compression:** Use standardized 3-5 character codes for machine efficiency
3. **Lazy metadata resolution:** Filename provides minimal unique identifier, CKE enriches from content
4. **Cache-local grouping:** Keep related files (deck + recording + data) in same physical subtree

### 1. **Naming Convention: Optimized for Search & Compression**
```
{YYYY-MM}-{TYPE}-{TOPIC}-{CLIENT}-{TITLE}-{HASH}.{ext}
```
Where:
- `TYPE`: 3-5 char code from controlled vocabulary (DECK, DEMO, REC, RFP, CERT, EXEC, DATA, GUIDE, TRN, COMP, ADM)
- `TOPIC`: 3-5 char product code (PLAT, WMS, PLAN, TMS, SEC, GEN)
- `CLIENT`: 2-6 char client code (LENZ, MICL, GEN)
- `HASH`: 4-char content hash prefix (enables deduplication, version detection)

**Why this works:**
- **O(1) type/topic/client filtering** via prefix matching
- **Deterministic hashing** enables content-addressable storage
- **Fixed field widths** enable efficient parsing and compression
- **Still human-readable** while machine-optimized

Example: `2026-03-DECK-PLAT-GEN-Corporate-Master-a3f7.pptx`

### 2. **Folder Structure: Topic-First with Type Partitions**
```
MyWork/
  00_Inbox/                    # Auto-routed by CKE
  10_Active/
    {CLIENT}/                  # Client-specific work
      {TOPIC}/
        {TYPE}_*              # All types mixed but prefixed
  20_Products/                 # Product-line organization (PRIMARY)
    {TOPIC}/                   # Platform, WMS, Planning, etc.
      00_Master/              # Master assets for this product
      01_Decks/
      02_Demos/
      03_Recordings/          # Product-specific recordings
      04_Data/
      05_Training/
  30_RFP/                      # Cross-product compliance
    01_Certificates/Current/
    01_Certificates/Archive/
    02_Responses/{CLIENT}/
    03_Databases/
  40_Reference/                # Static reference materials
    01_Product_Docs/
    02_Competitive/
  90_System/
```

**Performance advantages:**
- **Locality of reference:** Related files accessed together are colocated
- **Reduced search depth:** Topic-based searches hit 2-level depth max
- **Efficient synchronization:** Product folders can be synced independently

### 3. **CKE Architecture: Intelligent Metadata Pipeline**
```
Source File → Content Extraction → Metadata Enrichment → Vault Note
                   ↓                        ↓
            Filename Analysis       Folder Context
            Content Parsing         Historical Access Patterns
            Embedded Metadata       Cross-file Relationships
```

**Rules:**
1. **Auto-rename only in Inbox:** CKE suggests normalized name, user approves
2. **Derived tags from multiple sources:** 60% content, 30% folder, 10% filename
3. **Maintain rename log:** Track file movements for broken link detection

### 4. **Critical Performance Optimizations**

**For ADHD workflow:**
- **Save-time autocomplete:** PowerShell function suggests complete filename
- **Quick-move hotkeys:** Move to predefined locations without dialog
- **Template instantiation:** `New-Deck -Topic WMS -Client LENZ` generates proper structure

**For search efficiency:**
- **Bloom filter index:** Maintain hash of all files by topic/type for O(1) existence checks
- **Inverted index:** CKE builds search index during extraction
- **Predictive caching:** Pre-fetch related files based on access patterns

**For sync performance:**
- **Delta compression:** Only sync changed portions of large files
- **Selective sync:** Pin active product folders, lazy-load others
- **Deduplication:** Content-based hashing eliminates duplicate storage

### 5. **Migration Strategy with Performance Metrics**

**Phase 1 (Week 1): Critical Path Optimization**
- Move high-access files (<20% of files, >80% of accesses) to new structure
- Implement CKE auto-suggest for Inbox
- **Success metric:** Time-to-find for top 10 assets < 30 seconds

**Phase 2 (Month 1): Automated Classification**
- CKE analyzes remaining files, suggests classifications
- Batch rename with user approval
- **Success metric:** 90% of new files follow convention without manual intervention

**Phase 3 (Quarter 1): Performance Tuning**
- Implement predictive caching
- Optimize sync patterns based on access logs
- **Success metric:** Sync time reduced by 50%

### 6. **Specific Answers to Council Questions**

1. **Practical naming?** Yes, but with fixed-width tokens and content hash
2. **Filename vs folder tags?** Both: filename for uniqueness, folder for context, content for semantics
3. **MP4 location?** Product-specific recordings in product folder, generic recordings in Reference
4. **CKE rename?** Only in Inbox with approval, else suggest
5. **Obsidian mapping?** Multi-source weighted tagging (content > folder > filename)
6. **Master deck?** Product-specific masters in `20_Products/{TOPIC}/00_Master/`
7. **Certificates:** `Current/` + `Archive/` with automated expiration alerts
8. **Migration:** Critical files now, others on-access, archive never

### 7. **Quantifiable Benefits**

**Search performance:** 
- Current: O(n) recursive search (worst-case 300+ files)
- Proposed: O(1) topic lookup + O(k) type filter (k ≈ 20)

**Sync efficiency:**
- Current: 10.9GB monolithic sync
- Proposed: ~2GB active working set with lazy loading

**Cognitive load:**
- Current: 7+ decisions per save (where, name, tags, etc.)
- Proposed: 2 decisions (topic, client) with autocomplete

**Storage optimization:**
- Deduplication via content hashing: ~15% reduction estimated
- Compression via fixed-width fields: ~5% reduction

---

## Final Architecture Decision

**Adopt the Optimized Hybrid approach** with these non-negotiable elements:

1. **Topic-first folder structure** (matches primary access patterns)
2. **Fixed-width token naming** (enables machine optimization)
3. **Content-based hashing** (enables deduplication and version control)
4. **Multi-source metadata pipeline** (balances accuracy and automation)
5. **Phased migration with performance metrics** (ensures measurable improvement)

**Reject** proposals that:
- Prioritize type over topic (misaligned with workflow)
- Rely solely on filenames (brittle and unmaintainable)
- Remove all structure (sacrifices programmatic access)

**Implementation priority:** Start with `20_Products/` structure for Platform and WMS, implement CKE auto-suggest, measure time-to-find metrics weekly, iterate based on data.

The goal is not perfect organization, but **optimal access time** for the 80% case while maintaining flexibility for the 20%.

*Latency: 93.09s | Tokens: 13652*

### Openai (gpt-5.4)

Below is a blunt council review through a product/pragmatism lens: what will actually stick for a single primary user, modest automation, OneDrive, and a messy legacy corpus.

---

# Proposal A

## Verdict on Position
**Agree.**

This is the closest to something that will actually survive contact with reality.

## Strongest point
**It correctly optimizes for day-forward adoption plus targeted cleanup.**  
That is the only credible migration strategy here. “Rename everything” is architecture theater. The real win is:
- enforce a simple convention for new files
- clean high-value assets now
- rename-on-touch for the rest

It also gets an important operational truth right: **filenames should be structured metadata signals, not full tag payloads.**

## Weakest assumption
**Reintroducing `10_Active_Work` may recreate the same ambiguity that caused chaos before.**

Why this matters:
- If `10_Active_Work` becomes a catch-all for client decks, recordings, drafts, exports, and ad hoc files, then you now have two homes for similar artifacts:
  - reusable deck modules in `30_Templates`
  - customized client versions in `10_Active_Work`
- That is logical in theory, but in practice requires discipline about “when does a file graduate” and “is this reusable or active?”

For a one-person system under ADHD/time pressure, that can become another decision point.

## Risks it overlooks
1. **Controlled vocab drift is bigger than it implies.**  
   `PLATFORM`, `SECURITY`, `GEN`, `CORPORATE`, `INTERNAL`, `DEMO`—these will drift fast unless there’s a tiny canonical list and alias mapping.

2. **Filename length creep.**  
   Its pattern is fine, but users will stuff too much into `TITLE`, producing ugly 100+ char filenames.

3. **Client token standardization problem.**  
   `Penguin_Random_House`, `PRH`, `PenguinRandomHouse`—if this is not explicitly normalized, search quality degrades fast.

---

# Proposal B

## Verdict on Position
**Partially agree.**

I agree with the core idea that **filenames must carry enough metadata to survive being detached from folders**. I **disagree** with making filename the “immutable source of truth for all metadata” and with making CKE strictly read-only.

## Strongest point
**It sharply identifies portability and compliance risk.**  
This is absolutely right:
- a file gets copied to email/Teams/Desktop
- folder context disappears
- if the filename lacks type/scope/client, mistakes happen

That matters especially for:
- client-specific deliverables
- certificates
- RFP materials

## Weakest assumption
**“CKE must be read-only” is too rigid and leaves too much manual toil on the table.**

A strict read-only stance is operationally elegant but product-poor. If you already have `00_Inbox` and routing logic, then **approval-based rename/move in intake is exactly where automation should happen**. Refusing that because of hypothetical sync risk is overcorrecting.

The right answer is:
- **write-capable in intake**
- **suggest-only outside intake**
- **never silent mass mutation**

## Risks it overlooks
1. **Adoption risk from over-formality.**  
   “Immutable source of truth for all metadata” sounds good but pushes too much burden onto naming.

2. **No realistic path for ambiguous files.**  
   Real files often arrive without enough context. You need provisional naming and later normalization.

3. **Folder structure still matters operationally.**  
   Treating it as “secondary” underestimates retrieval behavior. Humans browse folders when under time pressure.

---

# Proposal C

## Verdict on Position
**Disagree.**

This proposal is attractive in theory and wrong for this actual environment.

## Strongest point
**It correctly attacks over-engineering and naming friction.**  
That criticism is valid. If the naming standard is too heavy, adoption fails. Also true: left-aligned human-readable tokens are easier to scan.

## Weakest assumption
**Dropping category/type from filenames is a bad call.**

This is the biggest miss in the entire set.

Why it fails:
- files are shared outside folder context
- search results often show filename more prominently than path
- the core problem statement explicitly asks: **“what IS this file?”**
- without `DECK`, `CERT`, `RECORDING`, etc., you are back to ambiguity

Also, removing numbered prefixes is cosmetic and not worth churn. `00_`, `30_`, `50_` are not the problem. Chaos is the problem.

## Risks it overlooks
1. **Detached file risk.**  
   Once a file leaves its folder, meaning collapses.

2. **Search ambiguity.**  
   `Corporate_Master`, `Platform_Overview`, `Planning_Architecture` without type token is too weak in large result sets.

3. **Tooling burden shifts to CKE and path parsing.**  
   It reduces human burden by increasing system complexity and fragility.

4. **Date-at-end hurts chronological parsing and scripting.**  
   Not fatal, but worse for batch operations and sort consistency.

---

# Proposal D

## Verdict on Position
**Partially agree, leaning disagree.**

I agree with phased migration and CKE-derived tags. I disagree with the folder-first philosophy and especially with keeping media with context instead of a canonical media home.

## Strongest point
**It recognizes that humans use folder context and that CKE should infer tags rather than forcing filename tags.**  
That separation of concerns is sound.

## Weakest assumption
**“Media belongs with its logical context” will recreate the exact current mess.**

This is too idealistic for the actual operating model.

Why:
- MP4s are large
- they are already scattered
- users hesitate on where to place them
- sync/backup behavior differs
- “logical context” is subjective

If you do not define one canonical home for recordings, you’ll be back in six months asking where the Michelin MP4 went.

## Risks it overlooks
1. **Scattered media kills consistency.**
2. **CKE renaming source files during extraction is too broad as stated.**  
   Needs scope limits.
3. **`Client_Topic_Type_Date` is weaker than date-first structured naming for machine parsing and sort.**
4. **Folder depth by date/topic/client can explode.**  
   Example: `Meetings/2025-10-Michelin/` sounds clean until there are edge cases, mixed topics, and reused decks.

---

# Revised Recommendation

## Executive recommendation
Adopt a **lightweight structured filename for all new files**, a **small number of canonical folders by function**, and a **phased cleanup focused on high-value assets**.  
Use **filename + folder path as metadata signals**.  
Use **CKE to derive Obsidian tags and to assist renaming in `00_Inbox` only**.

This is mostly Proposal A with corrections:
- keep type in filename
- do not make filename the sole truth
- do not scatter media
- do not try to rename the whole archive
- keep the vocabulary intentionally small

---

# 1) Final naming convention

## Recommended pattern
```text
YYYY-MM_TYPE_TOPIC_CLIENT_Title[_STATUS].ext
```

## Required fields
- `YYYY-MM`
- `TYPE`
- `TOPIC`
- `CLIENT` or `GEN`
- short `Title`

## Optional
- `_MASTER`
- `_FINAL`
- `_V2`
- `_ARCHIVE`

## Why this is the right minimum
It answers the essential questions:
- **what is it?** → `TYPE`
- **about what?** → `TOPIC`
- **for whom?** → `CLIENT`
- **when?** → `YYYY-MM`
- **special status?** → optional suffix

It is still fast enough to type.

## Examples
```text
2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
2026-03_DECK_WMS_LENZING_Architecture_Overview.pptx
2025-10_RECORDING_PLANNING_MICHELIN_Design_Workshop.mp4
2025-09_CERT_GEN_ISO27001_Current.pdf
2026-01_DEMO_PLATFORM_GEN_Analytics_Script.md
2025-11_DATA_PLATFORM_LENZING_Payload.csv
2026-02_EXEC_WMS_PRH_Summary.docx
2025-10_COMPETITIVE_WMS_GEN_Manhattan_Notes.md
```

## Rules
- Use `_` as the delimiter.
- Use uppercase for controlled tokens: `DECK`, `PLATFORM`, `LENZING`, `GEN`.
- Keep `Title` short and readable.
- No freeform tag syntax in filenames.
- No day-level date unless truly needed. Month granularity is enough for most assets.

## Exception rule
If speed matters, allow a temporary name:
```text
YYYY-MM_TYPE_TOPIC_CLIENT_Working.ext
```
CKE can later suggest a better title.

---

# 2) Controlled vocabulary

This is where most systems fail. Keep it tiny.

## TYPE list
- `DECK`
- `DEMO`
- `RECORDING`
- `RFP`
- `CERT`
- `EXEC`
- `DATA`
- `GUIDE`
- `TRAINING`
- `COMPETITIVE`
- `ADMIN`

## TOPIC list
Start with:
- `PLATFORM`
- `WMS`
- `PLANNING`
- `TMS`
- `SECURITY`
- `GEN`

Do **not** start with 30 topics. Expand only when repeatedly needed.

## CLIENT rule
Use canonical tokens:
- `LENZING`
- `MICHELIN`
- `MERCK`
- `ROSSMANN`
- `PRH`
- else `GEN`

Maintain a tiny alias map in config:
- `Penguin Random House` → `PRH`
- `Blue Yonder Corporate` is not a client; use `GEN`

---

# 3) Folder structure

Use a **type-first operational structure**, but don’t overcomplicate it.

## Recommended structure
```text
MyWork/
  00_Inbox/
  30_Templates/
    00_Master_Deck/
    01_Deck_Modules/
      Platform/
      WMS/
      Planning/
      TMS/
      Security/
    02_Demo/
    03_Discovery/
    04_Brand_Assets/
  40_Media/
    01_Client_Meetings/
    02_Demos/
    03_Training/
  50_RFP/
    01_Certificates/
      Current/
      Archive/
    02_Executive_Summaries/
      Generic/
      Client/
    03_Responses/
    04_Databases/
    05_RFI_Templates/
  60_Source_Library/
    01_Product_Docs/
    02_Training_Enablement/
    03_Competitive/
  70_Admin/
  90_System/
```

## Why not add `10_Active_Work` immediately?
Because it is likely to become a junk drawer unless there is clear workflow discipline.  
If needed later, add it **after** the rest of the system stabilizes.

For now:
- reusable assets live in `30_Templates`
- recordings live in `40_Media`
- RFP assets live in `50_RFP`
- external/internal reference materials live in `60_Source_Library`

If there are truly active client-specific deliverables, they can live in:
```text
30_Templates/01_Deck_Modules/...   (reusable)
50_RFP/03_Responses/...            (RFP work)
```
or be introduced later as a tightly defined `10_Active_Work/Client/`.

Don’t create a new bucket prematurely.

---

# 4) Master deck policy

## Rule
`30_Templates/00_Master_Deck/` contains:
- exactly one live master deck
- optionally a usage guide
- optionally brand guidance shortcut/copy

## Example
```text
30_Templates/00_Master_Deck/
  2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
  2026-03_GUIDE_PLATFORM_GEN_Master_Usage.docx
```

## Archive
```text
30_Templates/00_Master_Deck/Archive/
```

## Governance
Anything client-specific or heavily customized is **not** a master and does not belong here.

This must be brutally enforced.

---

# 5) Recordings policy

## Decision
**All MP4/WAV/M4A recordings go to `40_Media/` as canonical home.**

Not negotiable if the goal is consistency.

## Why
- removes placement ambiguity
- handles large binaries consistently
- supports backup and sync hygiene
- prevents scatter across source library/training/client folders

## Naming examples
```text
2026-03_RECORDING_PLATFORM_MICHELIN_Discovery_Call.mp4
2026-03_RECORDING_GEN_GEN_Lighthouse_Session_04.mp4
2026-03_RECORDING_WMS_GEN_Demo_Flow.mp4
```

If the topic is unclear, use `GEN` and improve later.

## Exception
Vendor-provided training/source recordings that are part of a reference package may remain in `60_Source_Library`.  
But your own meeting/demo/training captures belong in `40_Media`.

---

# 6) CKE behavior

## CKE should not be fully read-only
That is too conservative.

## CKE should not be globally write-happy
That is too risky.

## Correct behavior
### In `00_Inbox`
CKE may:
- detect likely type/topic/client
- propose filename
- propose destination folder
- move/rename after approval
- support bulk approval

### Outside `00_Inbox`
CKE should:
- parse and tag
- flag non-compliance
- suggest rename
- never silently rename/move existing organized files

This is the practical sweet spot.

---

# 7) Obsidian mapping

## Filenames should not contain full tags
Do **not** stuff `type/deck` or `product/platform` syntax into filenames.

## CKE should derive tags from:
1. filename tokens
2. folder path
3. extracted content

## Example
Source file:
```text
2026-03_DECK_PLATFORM_GEN_Corporate_MASTER.pptx
```

Path:
```text
30_Templates/00_Master_Deck/
```

Derived metadata:
```yaml
type: deck
topic: platform
client: generic
status: master
tags:
  - type/deck
  - product/platform
  - client/generic
  - asset/template
  - asset/master
```

That gives you alignment without making humans do duplicate work.

---

# 8) Certificates management

This needs immediate cleanup because the risk is real.

## Structure
```text
50_RFP/01_Certificates/
  Current/
  Archive/
```

## Rule
- `Current/` contains one current file per cert family
- all older versions go to `Archive/`

## Example names
```text
2025-09_CERT_GEN_ISO27001_Current.pdf
2025-09_CERT_GEN_ISO22301_Current.pdf
2025-09_CERT_GEN_SOC2_Current.pdf
2024-08_CERT_GEN_SOC2_Archive.pdf
```

## Additional rule
Flatten email-origin subfolders now.  
“Came from Dan Sanches email” is not a filing system.

---

# 9) Migration plan

## Do now
High-value, high-frequency assets only:
- master deck
- deck modules in `30_Templates`
- demo scripts
- discovery tools
- all current certs
- executive summaries
- misplaced files like `Veronesi...` in reference folders
- key competitive intel if frequently used
- obvious media files into `40_Media`

## Do on touch
- old client-specific decks
- historical recordings
- scattered source docs
- low-frequency archives

## Do not do now
- mass rename every historical file
- perfect taxonomy redesign
- broad folder renumbering / cosmetic cleanup only

---

# 10) Specific answers to the council questions

## 1. Is the naming convention practical?
**Yes, if simplified to:**
```text
YYYY-MM_TYPE_TOPIC_CLIENT_Title[_STATUS]
```
That is the practical minimum.

## 2. Should filenames have tags or rely on folder location?
**Neither extreme.**  
Filenames should carry structured signals (`TYPE`, `TOPIC`, `CLIENT`).  
Folders provide context.  
Do not encode full Obsidian tags in filenames.

## 3. Where do MP4 recordings go?
**Canonical home: `40_Media/`.**  
Split by `Client_Meetings`, `Demos`, `Training`.

## 4. Should CKE rename source files?
**Yes, but only in `00_Inbox` or via explicit approval.**  
No silent global renaming.

## 5. How does this map to Obsidian tags?
**CKE derives tags from filename + path + content.**  
Filename is a signal, not the whole ontology.

## 6. Master deck concept?
**Single live master in `30_Templates/00_Master_Deck/`.**  
Everything else is module, derivative, or archive.

## 7. RFP certificates management?
**Current + Archive, one live cert per family.**  
Flatten subfolders and normalize names now.

## 8. Consistency vs practicality?
**Enforce immediately for new files.**  
Retrofit only high-value existing assets now; rename-on-touch for the rest.

---

# Final recommendation in one sentence

**Adopt a date-first structured filename with mandatory `TYPE + TOPIC + CLIENT`, keep a small type-first folder system with a canonical media folder, let CKE assist intake and tagging rather than act as sole authority, and clean only the assets that matter now.**

If you want, I can turn this into:
1. a one-page policy,
2. a migration checklist for the current audited files,
3. a `content_registry.yaml` update,
4. and a PowerShell rename helper spec.

*Latency: 59.12s | Tokens: 12873*

### Grok (grok-4.20-beta)

**My Evaluation as Contrarian Architect**

### Proposal A
**Partially agree** with the position.

**Strongest point:** It correctly diagnoses that ADHD + time pressure makes verbose naming unsustainable and that partial migration (high-value assets only) is the only realistic path. The controlled vocabulary and "CKE proposes, human approves" flow is pragmatic.

**Weakest assumption:** It still believes Rob will reliably type `YYYY-MM_TYPE_TOPIC_CLIENT_TITLE` every time he saves a file. This is the same assumption that failed five previous cleanup rounds. The moment he is rushed, he will save as `Working_Deck_v2_final_final.pptx` and the whole system collapses.

**Risk it overlooks:** Once you normalize high-value assets, the new "correct" names become the new source of truth. Colleagues will start treating those filenames as authoritative and the system will experience schema drift as soon as someone creates `2026-04_DECK_Platform_Lenzing_v3_working_draft_EDIT_THIS_ONE.pptx`.

### Proposal B
**Disagree.**

**Strongest point:** It takes security and context-loss seriously (self-describing filenames prevent spillage when files are shared or moved).

**Weakest assumption:** That a "strict, context-rich filename contract" can ever be maintained by a human with ADHD under real workflow pressure. This is the most bureaucratic of the proposals. It treats the filesystem as a compliance database.

**Risk it overlooks:** It creates a system that is *hostile* to the actual user. The moment the naming feels like tax compliance, Rob will route around it. The "CKE must be read-only" rule also throws away the only realistic enforcement mechanism we have.

### Proposal C
**Strongest agreement** (though still incomplete).

**Strongest point:** This is the only proposal that takes the ADHD constraint seriously instead of paying it lip service. Removing the redundant `CATEGORY` token when the folder already signals type is correct. Making names shorter and putting the human-readable part first is correct. Declaring the previous five cleanups failed *because the standard was too heavy* is the clearest thinking in the entire council.

**Weakest assumption:** That date-at-the-end is acceptable. Rob *does* sometimes want chronological sorting in Explorer, and date-at-end defeats that. Also assumes folder discipline will hold long-term.

**Risk it overlooks:** When a file leaves its folder (email, Teams, shared drive), the loss of context is worse than the other proposals admit. A file named `Lenzing_Platform_Overview.pptx` in someone's inbox is ambiguous.

### Proposal D
**Disagree.**

**Strongest point:** The folder-first philosophy and willingness to let CKE do the heavy lifting.

**Weakest assumption:** That "humans navigate folders, scripts search by metadata" will remain true. This is pre-Obsidian thinking. Once everything is in the vault, Rob will almost never browse the filesystem again. The proposal is solving for the wrong interface.

**Risk it overlooks:** Media files stored with their "logical context" turns training folders into multimedia garbage dumps again. We've already seen this failure mode in the current `60_Source_Library`.

---

### What Everyone Is Missing

The council is still trapped in **20th-century information architecture**. All proposals assume:

1. Rob will be the primary maintainer of metadata.
2. The filesystem must remain the source of truth.
3. A "naming convention" is the solution rather than a symptom.

The unpopular truth: **A human-maintained naming convention is inherently incompatible with ADHD and high-velocity work.** The sixth cleanup will also fail if it requires Rob to think about taxonomy while saving files.

The real constraint isn't "what information should be in the filename" but "**how do we minimize the amount of taxonomy Rob must manually encode?**"

### Revised Recommendation (Contrarian Version)

**Core principle:** Rob should almost never type structured metadata. The system must be *aggressively* automated.

**Naming Convention (final):**
```
YYYY-MM_{CLIENT}_{TOPIC}_{HumanReadableTitle}.ext
```

- **No TYPE/CATEGORY** in filename (folder + CKE handles this).
- **CLIENT** uses canonical short codes or `GEN`.
- **TOPIC** uses canonical short codes or `MISC`.
- Date is **required** and always at the front for sorting.
- Title must be meaningful to a human (this is the only field Rob should care about).
- Maximum length: aim for < 60 characters.

**Examples:**
- `2026-03_LENZING_WMS_Architecture_Overview.pptx`
- `2026-03_GEN_PLATFORM_Corporate_MASTER.pptx`
- `2026-03_MICHELIN_PLANNING_Discovery_Call.mp4`
- `2025-09_GEN_CERT_ISO27001_Current.pdf`

**Folder Structure (radically simplified):**
```
MyWork/
  00_Inbox/                    ← everything lands here
  10_Active/                   ← client-specific work (flatter)
  20_Masters/                  ← exactly one folder for THE master + brand
  30_Modules/                  ← reusable decks, scripts, tools by product
  40_Media/                    ← all recordings, split only by Meetings/Demos/Training
  50_RFP/
    Current/
    Archive/
  60_Library/                  ← product docs + competitive + training enablement
  99_Archive/                  ← everything we touch but don't want to see
```

**Critical Rules:**

1. **CKE is not optional.** Any file landing in `00_Inbox` *must* be processed by CKE, which suggests both target path *and* normalized filename. Rob only approves or corrects the title. This is the only sustainable model.

2. **Master deck gets special treatment:** `20_Masters/Corporate_MASTER.pptx` — no date. Everything else is a module or client derivative. The hierarchy is enforced by location, not filename.

3. **Certificates:** `50_RFP/Current/` contains exactly one file per cert family with `_Current` in the name. Everything else goes to `Archive/`. No exceptions.

4. **Migration policy:** Rename *only* the master, current certs, and any file Rob touches in the next 90 days. Everything else stays in its current crime scene. Stop pretending we will ever have a perfectly normalized 300-file archive.

5. **Obsidian mapping:** CKE parses *both* path and filename, with path taking precedence for type and filename providing client/topic. The vault becomes the rich metadata layer. The filesystem remains a dumb, searchable store.

**The truly contrarian part:** We should be building toward a world where Rob drops files into Inbox and the AI handles the rest. The current council debate is the equivalent of arguing about the optimal Dewey Decimal number while standing in front of a search engine. 

The goal is not a beautiful filing system. The goal is **zero friction between "I just created this" and "I can find this in six weeks when I need it."** Everything else is ego.

This system is the minimum that might actually survive contact with Rob's real workflow. All more elaborate proposals are intellectual masturbation that will die on first contact with reality.

*Latency: 27.44s | Tokens: 11174*

## Synthesis (by claude, non-participant)



# Decision Summary: MyWork File & Folder Naming Convention + Structure

## Consensus

The council reached strong agreement on the following points:

### 1. No mass rename of existing files
Every participant agreed that retroactively renaming 200+ files is impractical and risky. The only viable strategy is: rename high-value assets now, enforce the convention on new files, and rename the rest on-touch.

### 2. CKE should assist naming, not be fully read-only or fully autonomous
All participants converged on a controlled automation model:
- **In `00_Inbox`**: CKE may propose filename + destination, Rob approves (individually or in batch)
- **Outside `00_Inbox`**: CKE reads, tags, flags non-compliance, but does not silently rename or move files
- **Never**: unattended mass mutation of files in synced/shared folders

### 3. Obsidian tags should be derived, not manually duplicated
No one advocated embedding literal tag syntax (e.g., `type-deck_product-platform`) in filenames. All agreed CKE should derive vault tags from a combination of filename tokens, folder path, and extracted content. Humans should not maintain parallel metadata systems.

### 4. Certificates need `Current/` + `Archive/` immediately
Universal agreement that the certificate folder is a live compliance risk. One current file per cert family in `Current/`, everything else in `Archive/`. Flatten email-origin subfolders. This is a Tier 1 cleanup item.

### 5. Master deck gets a dedicated, protected location
All proposals placed the corporate master deck in a singular, prominent folder (`00_Master_Deck/` or `20_Masters/`). The hierarchy is enforced by location: one live master, everything else is a module, derivative, or archive.

### 6. Recordings belong in a canonical media folder
Despite one dissent (DeepSeek R1 initially argued media should stay with context), the final round saw convergence: all MP4/WAV/M4A recordings go to `40_Media/` split by purpose (Meetings, Demos, Training). This eliminates placement ambiguity, supports sync/backup hygiene, and prevents large binaries from bloating topic folders. Vendor-provided reference recordings in `60_Source_Library` are the sole exception.

### 7. A controlled vocabulary is essential and must be kept small
All participants agreed that a fixed, short list of TYPE, TOPIC, and CLIENT tokens is critical. Drift (e.g., `Platform` vs `PLATFORM` vs `Plat`) is the primary long-term threat. The vocabulary must start small and expand only when repeatedly needed.

### 8. Date should be at the front of filenames in `YYYY-MM` format
All proposals except one placed date first. This enables chronological sorting in Explorer, scripting, and visual scanning.

---

## Unresolved Disagreements

### 1. Should TYPE (DECK, CERT, RECORDING, etc.) be in the filename?

**For including TYPE** (Gemini, OpenAI — majority position):
- Files are regularly shared outside their folder context (email, Teams, vendor portals)
- A file named `2026-03_LENZING_WMS_Architecture.pptx` is ambiguous: is it a deck? A data export? An RFP response?
- The core problem statement explicitly asks "what IS this file?" — TYPE answers that
- Search results across folders are far more useful with TYPE tokens
- PowerShell/Claude scripting becomes trivially parseable with fixed positional tokens

**Against including TYPE** (Grok — contrarian position):
- If a file is in `30_Templates/01_Decks/Platform/`, putting `DECK` in the filename is pure redundancy
- Every additional required token increases cognitive load at save time
- Five previous cleanup rounds failed because the standard was too heavy
- ADHD constraint is the binding constraint; reducing required fields is the only way to ensure adoption
- CKE + folder path can infer type without human input

**Why this matters**: This is the central tension of the entire debate — **portability and self-description vs. simplicity and adoption**. Both sides are correct about different failure modes.

### 2. Should there be a `10_Active_Work/` folder for client-specific work-in-progress?

**For** (OpenAI Round 1):
- Real client engagements produce artifacts (customized decks, meeting prep, session recordings) that need a temporary home
- Without it, client-specific variants clutter template folders
- Matches the actual workflow of "I'm preparing for a Lenzing session"

**Against** (OpenAI Round 2, Grok):
- Likely to become a junk drawer without iron discipline about lifecycle
- Creates ambiguity: "Is this reusable or active?" becomes a new decision point
- For a single-user system under time pressure, it adds a folder that competes with existing ones
- Can be introduced later if needed, after the base system stabilizes

### 3. Topic-first vs. type-first folder structure

**Topic-first** (DeepSeek):
- Rob's searches are actually product-first ("platform demo deck"), not type-first ("deck for platform")
- Related files (deck + recording + data for same product) are colocated
- Reduces cross-folder searches

**Type-first** (OpenAI, Gemini):
- Rob's pain points are type-based: "find THE master deck," "find the latest cert," "where do recordings go?"
- Type-first matches the operational workflows described in the problem statement
- Sync/backup behavior legitimately differs by file type (media vs. documents)

### 4. How aggressive should CKE automation be?

**Conservative** (Gemini):
- CKE should produce PowerShell commands for Rob to execute, never directly move/rename
- OneDrive sync race conditions are a real risk
- Broken shared links are operationally catastrophic

**Aggressive** (Grok):
- CKE must be the primary enforcement mechanism because human discipline will fail
- The system should tend toward "drop in Inbox, AI handles the rest"
- Without automation, this is just the sixth cleanup that will also fail

---

## Recommended Decision

### Naming Convention
Adopt the following pattern for all new files:

```
YYYY-MM_TYPE_TOPIC_CLIENT_Title[_STATUS].ext
```

**Include TYPE in the filename.** This is the single most debated point, and I rule in favor of including it for these reasons:

1. The problem statement's #1 requirement is literally "what IS this file?" — omitting TYPE directly fails the stated goal
2. The portability/detachment risk is real and documented: files get emailed, dropped in Teams, shared via links
3. The ADHD friction argument, while valid, is mitigable through CKE-assisted naming in Inbox, whereas the context-loss problem from omitting TYPE has no mitigation once the file leaves its folder
4. The controlled vocabulary is only 11 tokens — this is a single uppercase word, not a paragraph
5. Rob already uses PowerShell and Claude Code for search — structured tokens make those tools dramatically more effective

**Acknowledge the strongest objection**: Grok is right that five previous cleanups failed and that simplicity is the binding constraint. The mitigation is not to make the convention simpler by removing information — it is to **automate the naming act itself** via CKE intake. Rob should rarely be typing the full structured name manually. The typical flow should be: save to Inbox with any name → CKE proposes normalized name → Rob approves.

**Quick-save fallback rule**: When speed matters, any file can be saved as:
```
YYYY-MM_TYPE_TOPIC_CLIENT_Working.ext
```
CKE will suggest a better title later.

### Controlled Vocabulary

**TYPE** (11 values):
`DECK`, `DEMO`, `RECORDING`, `RFP`, `CERT`, `EXEC`, `DATA`, `GUIDE`, `TRAINING`, `COMPETITIVE`, `ADMIN`

**TOPIC** (6 values to start):
`PLATFORM`, `WMS`, `PLANNING`, `TMS`, `SECURITY`, `GEN`

**CLIENT** (canonical short codes):
`LENZING`, `MICHELIN`, `MERCK`, `ROSSMANN`, `WURTH`, `PRH`, `SGDBF` — else `GEN`

Maintain a canonical alias map in `90_System/` config. Expand vocabulary only when a new value is needed 3+ times.

### Folder Structure

```
MyWork/
  00_Inbox/                         ← all new files land here
  30_Templates/
    00_Master_Deck/                 ← THE corporate master + usage guide
      Archive/                      ← superseded masters
    01_Deck_Modules/                ← reusable supporting decks
      Platform/
      WMS/
      Planning/
      TMS/
      Security/
    02_Demo/                        ← demo scripts and materials
    03_Discovery/                   ← questionnaires, frameworks
    04_Brand_Assets/                ← brand guidelines
  40_Media/                         ← ALL recordings
    01_Client_Meetings/
    02_Demos/
    03_Training/
  50_RFP/
    01_Certificates/
      Current/                      ← one live file per cert family
      Archive/                      ← all superseded versions
    02_Executive_Summaries/
      Generic/
      Client/
    03_Responses/                   ← past RFP responses by client
    04_Databases/                   ← canonical RFP agent JSONs
    05_RFI_Templates/
  60_Source_Library/
    01_Product_Docs/
    02_Training_Enablement/
    03_Competitive/
  70_Admin/
  90_System/
```

**No `10_Active_Work/` for now.** This is the prudent call. It can be added after the base system stabilizes (30–60 days). If Rob finds himself needing a client work-in-progress area, introduce it as a tightly scoped:
```
10_Active/
  {CLIENT}/
```
with an explicit lifecycle rule: files older than 90 days get archived or moved to their permanent home.

**Type-first structure wins** because the problem statement's workflows are type-oriented ("find the master deck," "find the cert," "where does the recording go?"). Topic-based discovery is handled by filename tokens and Obsidian search.

### CKE Behavior

| Location | CKE Permission | Action |
|----------|---------------|--------|
| `00_Inbox/` | Read + Write (with approval) | Propose filename + destination; move/rename after Rob approves or bulk-approves |
| `30_Templates/` through `60_Source_Library/` | Read only | Extract content, derive vault tags, flag non-compliant names to audit dashboard |
| `90_System/` | Read + Write | Maintain config, logs, audit reports |

CKE must never silently rename files outside `00_Inbox`. If a file is non-compliant, CKE logs it to an Obsidian "Naming Audit" note for human remediation.

### Obsidian Tag Derivation

CKE derives vault frontmatter from three sources, weighted by reliability:

1. **Folder path** → broad classification (`asset/template`, `library/competitive`, `rfp/certificate`)
2. **Filename tokens** → `type/*`, `product/*`, `client/*`, `status/*`
3. **Extracted content** → deep semantic tags (`topic/saas-architecture`, `capability/analytics`, `vendor/manhattan`)

Example:
```
Source: MyWork/30_Templates/01_Deck_Modules/Platform/2026-03_DECK_PLATFORM_GEN_Analytics_Overview.pptx

Derived frontmatter:
  source_file: 2026-03_DECK_PLATFORM_GEN_Analytics_Overview.pptx
  source_path: MyWork/30_Templates/01_Deck_Modules/Platform/
  type: deck
  topic: platform
  client: generic
  tags:
    - type/deck
    - product/platform
    - client/generic
    - asset/template
    - topic/analytics        ← from content extraction
    - topic/saas-architecture ← from content extraction
```

### Migration Strategy

**Tier 1 — Do now (Week 1):**
- Master deck → rename, move to `30_Templates/00_Master_Deck/`
- All current certificates → rename, place in `50_RFP/01_Certificates/Current/`
- Flatten certificate email subfolders, move old versions to `Archive/`
- Delete 2 deprecated files in `30_Templates/Deprecated/`
- Move misplaced `Veronesi` deck out of `90_Reference_Baselines`
- Move scattered MP4s to `40_Media/` with proper names
- Rename deck modules in `30_Templates/01_Deck_Modules/` (9 files)
- Delete 2 XPS files in `50_RFP/Executive_Summary/`
- Delete 13 empty client folders in `50_RFP/_collected/`
- Rename the absurd Lighthouse folder name in `60_Source_Library`

**Tier 2 — Rename on touch (ongoing):**
- Old client decks, historical recordings, source docs — rename when accessed
- CKE flags non-compliant files in audit dashboard

**Tier 3 — Leave alone:**
- Deep archive, deprecated material, one-off files nobody touches
- If untouched for 6 months, move to `99_Archive/` (introduce this folder if needed)

---

## Risks

### 1. Convention is still too complex for sustained adoption
**Probability: Medium. Impact: High.**

This is the strongest objection from Grok, and it deserves serious weight. Five previous cleanups failed.

**Mitigation:**
- CKE-assisted intake is mandatory, not optional. Rob should type structured names manually only when CKE is unavailable
- Create a one-page "Save As" cheat sheet pinned in Obsidian
- Build a PowerShell `New-MyWorkFile` function that prompts for TYPE, TOPIC, CLIENT and generates the filename
- Quarterly 30-minute audit (not heroic multi-day cleanups)
- Track adoption rate: if >20% of new files in Inbox are not being processed through CKE within 60 days, simplify further

### 2. Controlled vocabulary drift
**Probability: High. Impact: Medium.**

`PLATFORM` vs `Platform` vs `Plat`, `PRH` vs `Penguin_Random_House` — this will happen.

**Mitigation:**
- Canonical vocabulary lives in `90_System/naming_config.yaml`
- CKE normalizes aliases during intake (e.g., `Penguin Random House` → `PRH`)
- PowerShell validation function `Test-MyWorkName` checks compliance
- Vocabulary expansion requires adding to config file, not ad hoc invention

### 3. OneDrive sync conflicts during CKE operations
**Probability: Low-Medium. Impact: High.**

If CKE moves/renames a file while OneDrive is syncing, conflict copies may appear.

**Mitigation:**
- CKE waits for sync quiescence before operating on Inbox files
- CKE operations on Inbox should be batched, not continuous
- If sync conflicts are detected, CKE logs them and pauses
- Never allow CKE to operate on files outside Inbox

### 4. Detached file context loss (even with TYPE in filename)
**Probability: Medium. Impact: Medium.**

Even with `TYPE_TOPIC_CLIENT`, a file sent via email loses folder context.

**Mitigation:**
- TYPE + TOPIC + CLIENT in filename covers 80% of context needs
- For formal external sharing, Rob can rename to a more polished client-facing name
- Obsidian vault note always maintains full provenance chain

### 5. `40_Media/` becomes a dumping ground
**Probability: Medium. Impact: Low-Medium.**

Without discipline, the media folder accumulates hundreds of unlabeled recordings.

**Mitigation:**
- Enforce naming convention strictly for recordings (CKE should auto-suggest names based on calendar/meeting context if possible)
- Add year subfolders if volume exceeds ~50 files per subfolder: `40_Media/01_Client_Meetings/2026/`
- Quarterly review: any recording older than 12 months and never referenced gets moved to archive

### 6. `content_registry.yaml` becomes stale
**Probability: High. Impact: Medium.**

The registry already has stale patterns (Zabka, Honda). New folders and routing rules will need updates.

**Mitigation:**
- Include registry update as part of any folder structure change
- CKE flags files that match no routing rule
- Quarterly audit includes registry review

---

## Action Items

### Immediate (Week 1)

| # | Action | Owner | Detail |
|---|--------|-------|--------|
| 1 | **Create canonical config file** | Rob + CKE | Create `90_System/naming_config.yaml` with TYPE list, TOPIC list, CLIENT alias map |
| 2 | **Restructure `30_Templates/`** | Rob | Create `00_Master_Deck/`, `01_Deck_Modules/{Platform,WMS,Planning,TMS,Security}`, `02_Demo/`, `03_Discovery/`, `04_Brand_Assets/`. Move and rename the 9 deck files + master deck |
| 3 | **Clean `50_RFP/01_Certificates/`** | Rob | Create `Current/` and `Archive/`. Flatten email subfolders. Move 7 superseded files to Archive. Rename all certs to `YYYY-MM_CERT_GEN_{CertName}_Current.pdf` |
| 4 | **Delete dead weight** | Rob | 2 deprecated decks, 2 XPS files, 13 empty client folders, empty `WMS/` subfolder in Executive_Summary |
| 5 | **Move misplaced files** | Rob | `Veronesi` deck out of Reference_Baselines. Scattered MP4s into `40_Media/` |
| 6 | **Create `40_Media/` subfolders** | Rob | `01_Client_Meetings/`, `02_Demos/`, `03_Training/` |
| 7 | **Rename Lighthouse folder** | Rob | Shorten the absurd folder name in `60_Source_Library/02_Training_Enablement/` |

### Week 2

| # | Action | Owner | Detail |
|---|--------|-------|--------|
| 8 | **Build CKE intake flow** | CKE dev | Implement: scan `00_Inbox`, propose filename + destination based on `naming_config.yaml` and content analysis, present for approval |
| 9 | **Update `content_registry.yaml`** | Rob + CKE | Add missing routing rules for: presentation decks, demo scripts, discovery tools, executive summaries, brand guidelines. Remove stale patterns (Zabka, Honda) |
| 10 | **Create cheat sheet** | Rob | One-page naming reference pinned in Obsidian with pattern, vocabulary, and 8–10 examples |
| 11 | **Build `New-MyWorkFile` PowerShell helper** | Rob/CKE | Interactive function: prompts for TYPE, TOPIC, CLIENT → generates compliant filename string |

### Month 1

| # | Action | Owner | Detail |
|---|--------|-------|--------|
| 12 | **Build `Test-MyWorkName` validator** | Rob/CKE | PowerShell function that checks any filename against convention and reports violations |
| 13 | **Create Obsidian "Naming Audit" dashboard** | CKE | Note listing all non-compliant filenames found during extraction, with suggested renames |
| 14 | **Rename Tier 1 high-value files** | Rob | Executive summaries, demo scripts, discovery tools, key competitive intel — all to new convention |
| 15 | **Evaluate `10_Active/` need** | Rob | After 30 days: is there a clear pattern of client-specific WIP with no home? If yes, introduce `10_Active/{CLIENT}/` with 90-day lifecycle rule |

### Quarterly (ongoing)

| # | Action | Owner | Detail |
|---|--------|-------|--------|
| 16 | **30-minute structure audit** | Rob | Review audit dashboard, process flagged files, check for vocabulary drift, update config if needed |
| 17 | **Certificate currency check** | Rob | Verify `Current/` folder has latest versions of all cert families |
| 18 | **Media folder hygiene** | Rob | Archive recordings >12 months old and unreferenced; add year subfolders if volume warrants |
| 19 | **Registry freshness check** | Rob + CKE | Remove stale `content_registry.yaml` patterns, add rules for any new folder paths |
