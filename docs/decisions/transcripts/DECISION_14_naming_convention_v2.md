# AI Council Debate: ## Question: What file naming convention should magistrala enforce?

### Current

**Date:** 2026-03-25 17:51:07
**Panel:** claude-opus-4-6, deepseek-reasoner
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 217.5s
**Mode:** custom
**Source:** council_inbox\council_naming_convention_v2.md

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Adopt **Option A with a refinement**: `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` — with CLIENT as a short, registry-controlled alias (max 5 chars), human-friendly abbreviation codes, MISC retained as an explicit fallback, hybrid description cleaning, and the naming convention defined in its own `naming_config.yaml`.

## Rationale

- **CLIENT in the filename is non-negotiable for scannability.** Folder context is fragile — files get emailed, copied to desktops, dropped into Slack, pasted into other directories. The moment a file leaves its folder, Option B loses all client context. For an ADHD-optimized workflow, every file must be self-describing at glance. Option A (`TYPE` before `CLIENT`) is preferable to Option C because the primary sort axis after date is "what kind of document is this?" — you scan for the RFP, not for "all JLR things" (that's what the folder is for).

- **Human-friendly abbreviations over raw CKE `doc_type` values.** `RFI` is universally understood; `rfp_response` is a database slug. The naming layer is a *presentation concern* — it should speak human. Maintain an explicit mapping table in config (abbreviation → CKE doc_type) so the contract is clear and the translation is mechanical. This mapping is the single source of truth; it should be tested.

- **Hybrid description cleaning is the only deterministic option that preserves context.** LLM-generated descriptions violate the determinism constraint and create a debugging nightmare ("why did it call this file something different on re-run?"). Raw original filenames are often garbage (`Copy of Final_v3_REAL (2).pptx`). The right answer: normalize the original stem — strip special characters, collapse whitespace to underscores, title-case words, truncate to ~50 chars at a word boundary. Purely mechanical, fully deterministic, preserves Rob's intent.

- **YYYY-MM is sufficient; YYYY-MM-DD is a trap.** You rarely know the exact day a document was authored vs. received vs. filed. Pretending you do creates false precision that someone will later try to rely on. Monthly granularity is honest and keeps filenames shorter. If exact dates matter, they live in metadata, not the filename.

- **Separate `naming_config.yaml` reduces coupling and cognitive load.** `content_registry.yaml` describes *what content exists and how to process it*. Naming conventions describe *how to present files to humans*. These change for different reasons and at different cadences. Mixing them creates a god-config that no one wants to touch.

## The Concrete Spec

```yaml
# naming_config.yaml
version: 1
pattern: "{date}_{type}_{client}_{description}.{ext}"
date_format: "YYYY-MM"
max_filename_length: 100

type_codes:
  PRES:  { cke_doc_type: presentation,       label: "Presentation" }
  RFP:   { cke_doc_type: rfp_response,       label: "RFP Response" }
  RFI:   { cke_doc_type: rfp_response,       label: "Request for Information" }
  RFQ:   { cke_doc_type: rfp_response,       label: "Request for Quotation" }
  VA:    { cke_doc_type: vendor_assessment,   label: "Vendor Assessment" }
  DISC:  { cke_doc_type: discovery,           label: "Discovery" }
  MEET:  { cke_doc_type: meeting,             label: "Meeting/Workshop" }
  TRAIN: { cke_doc_type: training,            label: "Training" }
  ARCH:  { cke_doc_type: architecture,        label: "Architecture" }
  PROD:  { cke_doc_type: product_doc,         label: "Product Documentation" }
  COMM:  { cke_doc_type: commercial,          label: "Commercial/Pricing" }
  SEC:   { cke_doc_type: security,            label: "Security/Compliance" }
  COMP:  { cke_doc_type: competitive,         label: "Competitive Analysis" }
  DATA:  { cke_doc_type: master_data,         label: "Master Data/Catalog" }
  SOW:   { cke_doc_type: commercial,          label: "Statement of Work" }
  REF:   { cke_doc_type: document,            label: "Reference Document" }
  MISC:  { cke_doc_type: document,            label: "Uncategorized" }

client_aliases:
  JLR:     "Jaguar Land Rover"
  BOSCH:   "Robert Bosch GmbH"
  SHEIN:   "SHEIN Group"
  INT:     "Internal / No Client"
  # max 5 chars, uppercase, no special chars

description_rules:
  strip_chars: '[^a-zA-Z0-9_ ]'
  word_separator: "_"
  case: "Title_Case"
  max_length: 50          # chars, truncate at word boundary
  truncation_suffix: ""   # no ellipsis — just stop cleanly

fallback_policy:
  unknown_type: "MISC"    # explicit, logged, triggers review queue
  unknown_client: "UNK"
```

**Example outputs:**
```
2026-03_RFI_JLR_Transport_Management_Overview.docx
2026-01_PRES_BOSCH_Supply_Chain_Digital_Twin.pptx
2025-11_SOW_SHEIN_Phase_2_Implementation.pdf
2026-04_MISC_UNK_Untitled_Document.docx     ← flags for review
```

## On the MISC Question Specifically

**Keep MISC. Do not kill it. Instrument it.**

Eliminating the fallback means the system either (a) forces a wrong classification to avoid MISC, or (b) halts on unclassifiable input. Both are worse than an honest "I don't know." Instead:

1. Every file classified as MISC gets logged to a review queue.
2. Track MISC rate as a metric. If it's above 15%, the taxonomy is missing a category — add one.
3. Periodic review of the MISC queue surfaces new type codes organically, driven by real data rather than speculation.

This turns MISC from a "garbage drawer" into a **sensor** that tells you when your taxonomy is incomplete.

## Trade-offs

| You gain | You give up |
|----------|-------------|
| Self-describing files that survive being ripped from context | ~8-10 extra characters per filename (client alias) |
| Deterministic, reproducible naming | Some "nicer" descriptions an LLM could generate |
| Human-readable type codes at a glance | A 1:1 mapping to CKE doc_types (you maintain a translation table) |
| Separate, focused config files | One more YAML file to manage |
| Honest MISC fallback as a taxonomy health sensor | The aesthetic satisfaction of "no catch-all" |
| Monthly date granularity that's always honest | The illusion of daily precision when you don't actually have it |

The CLIENT alias registry is the biggest ongoing maintenance item — every new client needs a 3-5 character alias added. Mitigate by making alias registration part of the client onboarding checklist, and by having the system auto-suggest aliases (first N chars of company name) for human approval.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Client alias collisions** (two clients get same abbreviation) | Medium | High — wrong client attribution | Enforce uniqueness in `naming_config.yaml` with a CI validation check. Use a slightly longer alias if needed (5 chars gives 11M+ combinations). |
| **Type code proliferation** — someone adds codes for every sub-variant | Medium | Medium — defeats scannability | Cap at ~20 codes. Any new code requires review. The taxonomy should be *coarse*; fine-grained classification belongs in metadata, not filenames. |
| **Description truncation loses critical info** | Medium | Low — metadata still has full original name | Always preserve the original filename in metadata/registry. The filename is a *label*, not the record of truth. |
| **Windows MAX_PATH (260 chars) hit** | Low | High — file operations fail silently | Enforce a hard budget: ~100 chars for filename leaves ~160 for path. Validate total path length at rename time; alert if within 20 chars of limit. |
| **MISC never gets reviewed** — it becomes the new garbage drawer anyway | Medium | Medium — taxonomy stagnates | Automated weekly report: "You have N files in MISC. Top 3 descriptions suggest these categories: [X, Y, Z]." Make the review friction-free. |
| **Naming config drifts from CKE doc_type enum** | Low | Medium — broken mappings | Single integration test: for every `type_code` in `naming_config.yaml`, assert its `cke_doc_type` exists in the CKE schema. Run on CI. Takes 5 lines of code. |

*Latency: 54.19s | Tokens: 3178*

### Deepseek (deepseek-reasoner)

## Position
Use the format `{YYYY-MM}_{TYPE}_{CLIENT}_{clean-description}.{ext}` (Option A) with human-friendly type codes and MISC as fallback, storing the convention in a separate `naming_config.yaml` for maintainability.

## Rationale
- **Chronological sorting and scannability**: Date-first ensures Explorer sorts chronologically; TYPE and CLIENT in fixed positions allow quick visual identification (supports ADHD scanning needs).
- **Deterministic and searchable**: No LLM randomness in filenames; client and description keywords remain directly searchable in OS/file systems.
- **Balanced specificity**: Retaining CLIENT in filename makes files self-contained when moved or shared; human-friendly codes (like PRES, RFP) are more scannable than CKE doc_type values.

## Trade-offs
- **Redundancy**: CLIENT may duplicate folder context, increasing filename length.
- **Human vs. system mapping**: Maintaining a separate mapping table (type codes to CKE doc_type) adds configuration overhead vs. using CKE values directly.
- **Fallback ambiguity**: Keeping MISC may reduce categorization discipline over time.

## Risks
- **Filename length overflow**: With CLIENT and description, may exceed 100 chars. Mitigation: Enforce description truncation (e.g., 60 chars) and validate during ingestion.
- **Type code proliferation**: Uncontrolled additions to type codes can reduce consistency. Mitigation: Define a change control process for updating `naming_config.yaml`.
- **Mis-categorization**: Overuse of MISC. Mitigation: Require type selection during upload, with MISC only allowed via exception.

### Detailed Answers to Questions:
1. **Format**: Option A (`{date}_{TYPE}_{CLIENT}_{description}`) – keeps client for portability and scannability.
2. **Type codes**: Use human-friendly abbreviations (proposed table) mapped to CKE doc_type – balances readability and system needs.
3. **Uncategorized files**: Keep MISC as fallback but require explicit selection; track MISC usage for future category refinement.
4. **Date format**: YYYY-MM – monthly grouping is sufficient for filing and reduces filename length.
5. **Description**: Hybrid – clean original filename (remove special chars, underscores→spaces, truncate) without LLM to preserve context deterministically.
6. **Configuration storage**: Separate `naming_config.yaml` – enables independent updates without touching content registry logic.

*Latency: 54.11s | Tokens: 2144*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Evaluation of Proposals

## Proposal A: Agree with Position

**Strongest point:** The answer set is complete and pragmatic — every question gets a direct answer with clear reasoning. The hybrid description approach and separate config file are both correct calls.

**Weakest assumption:** "Track MISC usage for future category refinement" is hand-waved. Without a concrete mechanism, this is a wish, not a policy. Who tracks it? When? What threshold triggers action? The proposal also doesn't address what CLIENT looks like — is it free-form text? A controlled alias? The entire scheme's consistency hinges on this, and it's unspecified.

**Overlooked risks:**
- No discussion of client alias governance (free text CLIENT values will immediately diverge: "JLR" vs "Jaguar" vs "JaguarLR")
- No mention of preserving the original filename in metadata, which means the hybrid cleaning is a lossy, irreversible operation with no safety net
- No Windows MAX_PATH validation strategy beyond "enforce truncation"

---

## Proposal B: Strongly Agree with Position

**Strongest point:** The MISC-as-sensor framing is the single best idea across both proposals. "Honest 'I don't know' + instrumentation" is operationally superior to both "force a category" and "let MISC be a garbage drawer." The concrete `naming_config.yaml` spec with client aliases, validation rules, and fallback policy moves this from opinion to implementation. The reasoning about why CLIENT must be in the filename (files leave their folder context) is precisely correct and well-argued.

**Weakest assumption:** The claim that a 5-character alias cap with "11M+ combinations" makes collisions manageable understates the real problem. The collision risk isn't combinatorial — it's *mnemonic*. You need aliases that humans can map to the client without looking them up. "BOSCH" is obvious. What's the alias for "Boston Consulting Group" vs "Boston Scientific"? The constraint is human recall, not namespace size. This will generate more support friction than acknowledged.

**Overlooked risks:**
- The `description_rules` spec assumes incoming filenames have usable stems. In practice, many files arrive as `Document1.docx` or `attachment.pdf`. The spec doesn't define behavior when the cleaned description is empty or meaningless after normalization.
- The weekly MISC review report assumes someone acts on it. Without assigning ownership (a specific role or automated escalation), this will be ignored within 8 weeks. I've seen this pattern repeatedly.
- No versioning strategy for the naming convention itself. What happens when you rename the pattern (say, adding a new field)? Do you retroactively rename existing files? Leave them with the old convention? The `version: 1` field implies you thought about this, but there's no stated migration policy.

---

# Revised Recommendation

I adopt Proposal B's position with three targeted corrections:

## 1. Format: Option A with registry-controlled client aliases — **confirmed**

`{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`

Proposal B's argument is definitive: files leave folder context constantly. A file without its client in the name is a file that will be misattributed. The CLIENT alias registry is the correct mechanism, but I'd tighten the spec:

```yaml
client_aliases:
  # Rules:
  # - 3-6 uppercase alphanumeric characters (not fixed at 5)
  # - Must be recognizable without a lookup table
  # - Uniqueness enforced by CI check on naming_config.yaml
  # - New aliases require PR review
  JLR:      "Jaguar Land Rover"
  BOSCH:    "Robert Bosch GmbH"
  SHEIN:    "SHEIN Group"
  BOSTSC:   "Boston Scientific"    # when mnemonics collide, extend
  BCG:      "Boston Consulting Group"
  INT:      "Internal / No Client"
```

Allowing 3-6 characters instead of a hard 5 lets you use natural abbreviations where they exist (BCG, JLR) while having room to disambiguate when needed. The constraint is *recognizability*, not uniform length.

## 2. MISC policy: keep the sensor, add teeth

Proposal B's framing is correct. I'd make one addition: MISC files that remain unresolved after 30 days get auto-escalated. Not just reported — escalated with a named owner. The config should specify this:

```yaml
fallback_policy:
  unknown_type: "MISC"
  unknown_client: "UNK"
  misc_review:
    report_frequency: "weekly"
    escalation_threshold_days: 30
    escalation_target: "content_owner"  # role, not person
    taxonomy_expansion_trigger: 0.15     # if MISC > 15% of recent files
```

## 3. Empty/garbage description handling — **new addition neither proposal covers**

This is a real gap. Add explicit rules:

```yaml
description_rules:
  strip_chars: '[^a-zA-Z0-9_ ]'
  word_separator: "_"
  case: "Title_Case"
  max_length: 50
  truncation_suffix: ""
  min_meaningful_length: 5          # after cleaning
  empty_fallback: "Untitled"        # when stem is garbage
  garbage_patterns:                  # detect and replace
    - '^Document\d*$'
    - '^Untitled\d*$'
    - '^Copy_Of_.*'
    - '^attachment\d*$'
    - '^\w{1,2}$'                   # single/double char stems
```

When the cleaned description matches a garbage pattern or is below `min_meaningful_length`, use `"Untitled"` and flag the file in the same review queue as MISC. This makes the behavior explicit and testable rather than producing filenames like `2026-03_RFP_JLR_D.docx`.

## 4. Original filename preservation — **mandatory**

Both proposals mention metadata in passing, but this needs to be an explicit, non-negotiable contract:

```yaml
metadata_preservation:
  original_filename: true    # always stored in metadata/registry
  original_path: true        # relative path at time of ingestion
```

The renamed filename is a *presentation label*. The original filename is *evidence*. They serve different purposes. Never discard the original. This protects you from every "the cleaning lost something important" complaint — you can always recover.

## 5. Naming convention versioning

Add a migration policy:

```yaml
version: 1
migration_policy: "coexist"
# Options:
#   "coexist" — old-format files are NOT retroactively renamed
#   "migrate" — batch rename on version bump
# Coexist is default because retroactive renames break external links.
# The version is embedded in metadata, not the filename.
```

Retroactive renames break bookmarks, email links, and shared drive shortcuts. Default to coexistence. If you ever need to find files by convention version, query the metadata.

## 6. Config location: separate `naming_config.yaml` — **confirmed**

Both proposals agree. I want to be explicit about why: `content_registry.yaml` answers "what content do we have and how do we process it?" `naming_config.yaml` answers "how do we label files for humans?" These change at different rates, for different reasons, triggered by different stakeholders. Coupling them creates a config file that everyone fears editing.

## 7. Date format: YYYY-MM — **confirmed**

Proposal B's argument is airtight: false precision is worse than honest imprecision. If you need the exact date, it's in metadata. The filename serves scanning and sorting, not auditing.

## Summary Table

| Decision | Choice | Confidence |
|----------|--------|------------|
| Format | `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` | High |
| Type codes | Human-friendly abbreviations, mapped to CKE in config | High |
| Client in filename | Yes, as registry-controlled 3-6 char alias | High |
| MISC handling | Keep as instrumented fallback with escalation | High |
| Date | YYYY-MM | High |
| Description | Hybrid clean (deterministic) with garbage detection | High |
| Config | Separate `naming_config.yaml` with version field | High |
| Original filename | Always preserved in metadata | Non-negotiable |
| Migration | Coexist by default; no retroactive renames | High |
| Max type codes | Cap at ~20; new codes require review | Medium-High |

The biggest ongoing maintenance costs, in order: (1) client alias registry — mitigate with onboarding checklist and auto-suggestion, (2) MISC review queue — mitigate with automation and escalation, (3) type code governance — mitigate with a cap and PR review requirement. Everything else is configure-once.

*Latency: 53.36s | Tokens: 5902*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concern is that **filenames are untrusted user input that directly interact with the operating system, file storage, and downstream integration pipelines (CKE).** 

Both proposals focus heavily on UX, readability, and metadata mapping, which is important for the business, but they both critically under-address the threat surfaces of file system interactions and untrusted input sanitization. 

Here is my evaluation of the proposals, followed by a hardened architectural recommendation.

---

### Evaluation of Proposal A

**Position:** Partially Agree. 
I agree with the deterministic approach and the `{YYYY-MM}_{TYPE}_{CLIENT}_{clean-description}.{ext}` format, which ensures safe chronological sorting without relying on unpredictable LLM outputs.

**Strongest Point:** Acknowledging that LLM-generated descriptions violate determinism. In an integration pipeline, non-deterministic transformations cause idempotency failures (e.g., processing the same file twice results in two different output filenames).

**Weakest Assumption:** It assumes "clean up original (remove special chars)" is a trivial, self-evident operation. Without a strict regex boundary, "cleaning" usually leaves edge cases that break OS APIs or downstream parsers.

**Overlooked Risks:**
*   **Extension Smuggling / Execution:** It completely ignores the `{ext}` variable. Blindly appending the original extension allows executable masquerading (e.g., `file.docx.exe`, `.scr`, `.pif`).
*   **Directory Traversal:** Fails to explicitly mention stripping pathing characters (`/`, `\`, `..`). If cleaning is flawed, directory traversal during file write is a critical vulnerability.

### Evaluation of Proposal B

**Position:** Mostly Agree. 
This proposal takes a mature systems-engineering approach. Moving from raw CKE `doc_type` to a mapped human-friendly abstraction layer decoupled via `naming_config.yaml` is exactly how we ensure safe interoperability without coupling our presentation layer to our database schema.

**Strongest Point:** The CI validation test between `naming_config.yaml` and the CKE schema, and the treatment of `MISC` as a "sensor" rather than a failure state. This guarantees schema integrity and prevents silent integration failures.

**Weakest Assumption:** Assuming `[^a-zA-Z0-9_ ]` is entirely sufficient for file-system safety. While restrictive, this regex does not account for reserved OS filenames, nor does it address Unicode normalization attacks prior to stripping.

**Overlooked Risks:**
*   **Windows Reserved Names:** A user uploads a file originally named `CON.pdf`. The regex preserves `CON`. Windows will silently fail or crash when attempting to write `2026-03_MISC_UNK_CON.pdf` to disk. (Applies to `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
*   **Unicode/Homoglyph Evasion:** If the input is not normalized before the regex runs, specific Unicode characters might bypass the filter or cause downstream encoding panics in legacy integrations.
*   **Extension Sanitization:** Like Proposal A, it ignores the `{ext}` threat vector entirely.

---

### Revised Recommendation: Hardened Naming Convention Spec

We will adopt **Proposal B's architecture** (Option A format, mapped aliases, config separation, and MISC instrumentation), but we must enforce strict defense-in-depth security measures at the ingestion and renaming boundaries.

#### 1. Threat Mitigation & Integration Safeguards
Before the naming convention is applied, the ingestion service must enforce the following:
*   **Extension Whitelisting:** `{ext}` must NOT be derived blindly from user input. It must be checked against an explicit whitelist of safe document types in `content_registry.yaml` (e.g., `pdf`, `docx`, `pptx`). Force all extensions to lowercase. Reject anything else at the edge.
*   **Unicode Normalization:** The original filename must be passed through NFKC normalization to prevent homoglyph evasion and encoding panics before regex stripping occurs.
*   **Reserved Name Blocking:** After the description is truncated and cleaned, the final string must be checked against Windows reserved keywords.
*   **Path Length Validation:** Enforce length checks at the *byte* level, not just the character level, to prevent buffer overflows or silent truncation in downstream CKE ingestion.

#### 2. Format & Configuration
Use the format: `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`

The `naming_config.yaml` from Proposal B is excellent but requires these security additions to the `description_rules`:

```yaml
# naming_config.yaml (Hardened)
version: 1.1
pattern: "{date}_{type}_{client}_{description}.{ext}"
date_format: "YYYY-MM"
max_filename_bytes: 100 

allowed_extensions: ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "csv"]

description_rules:
  normalization: "NFKC"
  strip_regex: '[^a-zA-Z0-9_ ]'
  word_separator: "_"
  case: "Title_Case"
  max_length: 50
  # SECURITY: Explicitly fail/append if description results in reserved OS keywords
  reserved_keywords_fallback: "Safe_Desc" 
  reserved_keywords: ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

type_codes:
  # ... (Use Proposal B's type mappings, e.g., PRES, RFP, RFI) ...

client_aliases:
  # ... (Use Proposal B's aliases, enforced max 5 alphanumeric chars) ...
```

#### 3. Resolving the Core Questions
1.  **Format:** Use Option A. The fixed-position prefix (`YYYY-MM_TYPE_CLIENT_`) guarantees predictable string slicing for downstream parsers without relying on complex regex, reducing integration fragility.
2.  **Type Codes:** Use human-friendly codes (PRES, RFI) but enforce a rigid mapping to CKE `doc_type` in the YAML config. Mandate the CI test proposed in B to prevent schema drift.
3.  **MISC Fallback:** Keep it. I agree with Proposal B: a fallback provides observability. Forcing categorization leads to users picking "A" just to bypass the screen, poisoning your dataset. Send MISC to a dead-letter/review queue.
4.  **Date:** `YYYY-MM`. Safe, deterministic, and avoids false precision which breaks data trust.
5.  **Description:** Hybrid. LLMs in a critical file-routing pipeline introduce non-determinism, retry inconsistencies, and prompt-injection risks. Mechanical regex (with the security rules added above) is the only architecturally sound choice.
6.  **Config Storage:** Separate `naming_config.yaml`. This establishes a distinct blast radius. Content registry changes shouldn't accidentally break UI presentation rules, and vice versa.

*Latency: 37.62s | Tokens: 6837*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A
**Agreement:** Partially agree (70%).  
**Strongest point:** Emphasizes self-containment for files moved out of folder context—critical for ADHD scanning.  
**Weakest assumption:** That description truncation alone will reliably keep filenames under 100 chars. Client names can be long and variable; without enforced client abbreviation, path limits are threatened.  
**Overlooked risks:** 
- Client name collisions (e.g., "JLR" vs "Jaguar Land Rover" inconsistently used)
- No mechanism to prevent type-code sprawl beyond "change control process"
- Silent failures if truncation cuts critical keywords

### Proposal B
**Agreement:** Mostly agree (85%).  
**Strongest point:** Treats MISC as a taxonomy health sensor with instrumentation and review queues—turns a weakness into a feedback loop.  
**Weakest assumption:** That a 5-character client alias registry will remain maintainable. This creates scaling overhead with each new client (O(n) manual mapping).  
**Overlooked risks:**
- Client alias registry becomes a bottleneck for new client onboarding
- Max 5-char aliases may become cryptic (e.g., "INT" for "Internal" vs "INTL")
- No fallback for unknown clients beyond "UNK"—loses searchability

## Revised Recommendation

**Format:** `{YYYY-MM}_{TYPE}_{CLIENT}_{description}.{ext}` with these specific implementations:

### 1. Client Handling (Hybrid Approach)
- **Primary:** Use folder-inferred client for 95% of cases (reduces filename length)
- **Override:** Allow explicit `{CLIENT}` in filename ONLY when file belongs to multiple clients or context differs from folder
- **Implementation:** 
  ```yaml
  client_in_filename: false  # default
  exceptions:
    - pattern: "*_joint_*"  # multi-client
    - pattern: "*_external_*"
  ```
- **Result:** Most files: `2026-03_RFI_Transport_Management.docx`
  Exception files: `2026-03_RFI_JLR-BMW_Joint_RFP_Response.pptx`

### 2. Type Codes with Validation Gates
- Adopt human-friendly abbreviations BUT enforce via automated checks:
  ```python
  # CI validation rule
  assert len(type_codes) <= 20, "Taxonomy bloat: >20 codes reduces scannability"
  assert all(len(code) == 4 for code in type_codes), "Inconsistent code length"
  ```
- **MISC handling:** Implement Proposal B's instrumentation PLUS:
  - Auto-suggest category based on description keywords (deterministic, no LLM)
  - Require justification field when selecting MISC

### 3. Description Algorithm (Deterministic & Search-Optimized)
```
def clean_description(original: str, max_len: int = 60) -> str:
    # 1. Remove: version numbers (v1, _final), dates in parens, special chars
    # 2. Keep: alphanumeric, spaces, hyphens (convert underscores to spaces)
    # 3. Extract: longest continuous English word sequence (regex [A-Za-z\s-]+)
    # 4. Truncate: at last word boundary before max_len
    # 5. Case: Title Case For Readability
```
**Example:**  
`"Copy of Final_v3_REAL (2025).pptx"` → `"Final Real Copy"`  
Preserves original in metadata with hash for exact recovery.

### 4. Configuration Storage
- **Separate `naming_policy.yaml`** for human-editable rules
- **Generated `naming_schema.json`** for runtime with compiled regex patterns
- **Version both** with compatibility checks

### 5. Performance & Scalability Additions
- **Pre-compute filename hash** for duplicate detection (O(1) lookup)
- **Batch rename operations** sorted by target directory to minimize disk seeks
- **Path length validation** at ingest time with immediate fallback:
  ```python
  if len(full_path) > 240:  # 20 char buffer for Windows 260 limit
      # Auto-shorten via: client_abbrev, type_code, description_truncate
      # Log shortening with original for audit
  ```

### 6. Risk Mitigations Added
- **Client alias automation:** Auto-generate 4-char uppercase from first letters of distinct words, with collision resolution (e.g., "Jaguar Land Rover" → "JLR", conflict → "JLR1")
- **Type code drift prevention:** Unit test that verifies all CKE doc_type values have exactly one mapping (injective)
- **Search degradation guard:** Ensure at least 3 meaningful words survive truncation; else flag for manual naming

### Final Specification Snippet
```yaml
naming_policy:
  version: "2.1"
  base_pattern: "{date}_{type}_{description}.{ext}"
  date_granularity: "month"  # YYYY-MM
  max_component_lengths:
    type: 4
    client: 8    # only when explicitly needed
    description: 60
  deterministic_cleaner:
    remove_patterns: ["_v\d+", "_final", "\(\d{4}\)", "[^\w\s-]"]
    preserve_min_words: 3
  fallbacks:
    unknown_type: "MISC"      # triggers weekly review report
    unknown_client: "MULTI"   # for multi-client docs
  validation:
    max_total_path: 240
    require_type_selection: true
    allow_manual_override: false  # except for admins
```

**Why this outperforms both proposals:**
1. **Reduces 80% of filename redundancy** by omitting client when inferable from folder
2. **Maintains searchability** through deterministic keyword preservation
3. **Enforces scalability** via automated client aliasing and type-code limits
4. **Prevents performance degradation** through path length validation at ingest
5. **Optimizes for ADHD scanning** through consistent 4-character type codes in fixed position

**Trade-off accepted:** Slightly more complex implementation (folder-client inference) for significantly shorter, more scannable filenames in the common case.

*Latency: 123.19s | Tokens: 6600*

## Synthesis (by openai, non-participant)

## Consensus

Areas of broad agreement across the debate:

1. **Date should come first**
   - Everyone agreed the filename should start with the date for Explorer sorting and chronological scanning.
   - Strong preference was for **`YYYY-MM`**, not `YYYY-MM-DD`, because monthly granularity is enough for filing and avoids false precision and longer names.

2. **Type should use human-friendly codes**
   - Most participants favored short, scannable codes like `RFI`, `PRES`, `SOW` rather than raw CKE values like `rfp_response`.
   - There was also strong agreement that these codes should be **mapped explicitly to CKE `doc_type`** in configuration.

3. **Description should be deterministic, not LLM-generated**
   - Clear consensus against LLM-generated filenames because it breaks determinism.
   - Preferred approach: **mechanically clean the original filename stem** to preserve context while normalizing junk.

4. **A fallback category is necessary**
   - Most participants agreed that some files will not fit cleanly and the system needs an honest fallback.
   - The dominant view was to **keep `MISC`**, but instrument it so it becomes a signal that taxonomy needs refinement rather than a dumping ground.

5. **Naming rules should live in a separate config**
   - Strong agreement that naming concerns should be separated from content processing concerns.
   - Preferred location: **`naming_config.yaml`** (or equivalent dedicated naming policy file).

6. **Validation/governance is required**
   - Several participants emphasized that the convention only works if enforced with:
     - controlled type codes
     - controlled client aliases if clients are included
     - filename length checks
     - config/schema validation in CI

---

## Unresolved Disagreements

### 1. Should `CLIENT` be in the filename?
This was the main substantive disagreement.

#### Position 1: **Include CLIENT** (`{date}_{TYPE}_{CLIENT}_{description}`)
Supported by most participants.
- **Merits**
  - Files remain self-describing when copied out of folder context, emailed, dropped in Slack, or saved elsewhere.
  - Better supports “glance and know what it is.”
  - Improves filename-only searchability.
- **Costs**
  - Adds length and some redundancy when folder structure already conveys the client.
  - Requires alias governance to avoid inconsistency.

#### Position 2: **Omit CLIENT by default, infer from folder**
Supported by one revised proposal.
- **Merits**
  - Shorter filenames.
  - Reduces redundancy in the common case.
- **Costs**
  - Breaks once files leave folder context.
  - Adds implementation complexity through folder inference and exception handling.
  - Weakens the “self-contained” requirement.

**Judgment:** The include-client side better matched the stated constraints, especially scannability and portability outside folder context.

---

### 2. How strict should the fallback be?
#### Position 1: **Keep `MISC` as explicit fallback**
- Honest when classification is unclear.
- Prevents forced bad categorization.
- Can be tracked and reviewed.

#### Position 2: **Force type selection / restrict MISC heavily**
- Encourages cleaner data.
- Reduces lazy overuse of catch-all categories.

**Judgment:** The best arguments favored **keeping `MISC` but with controls**: explicit use, logging, review, and thresholds for taxonomy expansion.

---

### 3. How much security hardening belongs in the naming decision?
One participant strongly emphasized:
- extension whitelisting
- Unicode normalization
- reserved filename blocking
- path safety

Others focused more on UX and taxonomy.

**Judgment:** These are valid and important, but they are **implementation safeguards**, not the core naming convention choice. They should be adopted as mandatory guardrails during implementation.

---

## Recommended Decision

Adopt this convention:

**`{YYYY-MM}_{TYPE}_{CLIENT}_{DESCRIPTION}.{ext}`**

Example:
- `2026-03_RFI_JLR_Transport_Management.docx`

### Decision details

1. **Format**
   - Use **Option A**: `{date}_{TYPE}_{CLIENT}_{description}`
   - Order should remain:
     1. date
     2. type
     3. client
     4. description

   This best supports:
   - chronological sorting
   - quick visual scanning by document kind
   - preservation of client context when files move

2. **Type codes**
   - Use **human-friendly abbreviations** as the filename value.
   - Maintain an explicit mapping to CKE `doc_type` in config.
   - Start with the proposed controlled set:
     `PRES, RFP, RFI, RFQ, VA, DISC, MEET, TRAIN, ARCH, PROD, COMM, SEC, COMP, DATA, SOW, REF`
   - Keep the taxonomy coarse; do not let codes proliferate.

3. **Fallback**
   - Keep **`MISC`** as an allowed fallback.
   - But do **not** treat it as normal:
     - require explicit selection or explicit system fallback
     - log every use
     - review periodically
     - use volume thresholds to decide when a missing category should be added

4. **Date**
   - Use **`YYYY-MM`**
   - Exact dates belong in metadata, not filenames.

5. **Description**
   - Use a **deterministic cleaned version of the original filename stem**
   - No LLM generation
   - Cleaning should:
     - normalize Unicode
     - remove unsafe/special characters
     - collapse whitespace
     - convert separators consistently
     - truncate at a word boundary
   - Preserve the **original filename** in metadata.

6. **Configuration**
   - Store naming policy in **`naming_config.yaml`**
   - Keep it separate from `content_registry.yaml`

### Why this was chosen

This recommendation best satisfies the explicit constraints:
- **scannable by eye**: type and client are visible without opening folders
- **sorts well**: date-first
- **searchable**: client + description remain in filename
- **deterministic**: no LLM-generated names
- **bounded length**: manageable with aliases and truncation

### Strongest objections, and why they were not adopted

1. **“CLIENT is redundant if folder already tells you the client.”**
   - True in-place, but weaker overall. The stronger argument was that files frequently leave their original folder context. The naming convention should survive that.

2. **“Force users to pick a type instead of keeping MISC.”**
   - This improves discipline, but the debate persuasively showed that forced categorization often creates bad metadata. An explicit fallback with review is more honest and operationally safer.

3. **“Omit client by default for shorter names.”**
   - This optimizes the common case at the expense of portability and self-description, which were core requirements. The trade-off was not worth it.

---

## Risks

1. **`MISC` becomes the new junk drawer**
   - **Risk:** users overuse it and taxonomy never improves.
   - **Mitigation:**
     - weekly/monthly MISC report
     - named owner for review
     - threshold trigger, e.g. if `MISC > 15%`, review taxonomy

2. **Client aliases become inconsistent or cryptic**
   - **Risk:** `JLR`, `JAGLR`, `JAGUAR` drift or become hard to read.
   - **Mitigation:**
     - controlled alias registry
     - uniqueness checks in CI
     - allow recognizable aliases of roughly 3–6 characters rather than rigid free text

3. **Filename length exceeds practical limits**
   - **Risk:** long descriptions plus client plus path depth hit Windows path constraints.
   - **Mitigation:**
     - enforce max filename length
     - truncate description first
     - validate full path length during rename

4. **Descriptions become meaningless after cleaning**
   - **Risk:** inputs like `Document1.docx` produce poor filenames.
   - **Mitigation:**
     - detect garbage stems
     - fall back to `Untitled` or similar
     - flag for review
     - always store original filename in metadata

5. **Type code sprawl reduces scannability**
   - **Risk:** too many codes make the convention harder to use.
   - **Mitigation:**
     - cap active codes to a small controlled set
     - require review/approval for new codes

6. **Implementation safety issues**
   - **Risk:** unsafe extensions, reserved Windows names, Unicode edge cases.
   - **Mitigation:**
     - extension allowlist
     - lowercase extensions
     - Unicode normalization
     - reserved-name checks
     - path traversal protection

7. **Schema drift between naming codes and CKE**
   - **Risk:** config says one thing, CKE expects another.
   - **Mitigation:**
     - CI validation that every type code maps to a valid CKE `doc_type`

---

## Action Items

1. **Adopt the canonical pattern**
   - Standardize on:
     - `{YYYY-MM}_{TYPE}_{CLIENT}_{DESCRIPTION}.{ext}`

2. **Create `naming_config.yaml`**
   Include:
   - pattern
   - date format
   - max filename length
   - type code → CKE mappings
   - client alias registry
   - description cleaning rules
   - fallback policy

3. **Define and enforce client aliases**
   - Use controlled aliases, ideally **3–6 uppercase alphanumeric characters**
   - Add uniqueness validation
   - Make alias creation part of client onboarding

4. **Implement deterministic description cleaning**
   - Normalize Unicode
   - strip unsafe chars
   - collapse whitespace/separators
   - truncate at word boundary
   - detect garbage stems and fall back safely

5. **Preserve original metadata**
   - Always store:
     - original filename
     - original path
     - applied naming version

6. **Implement `MISC` governance**
   - Allow `MISC`
   - Log every occurrence
   - Review on a schedule
   - Assign an owner
   - Trigger taxonomy review if usage exceeds an agreed threshold

7. **Add validation and safety checks**
   - extension allowlist
   - reserved Windows filename checks
   - full path length validation
   - CI check for type-code/CKE mapping consistency

8. **Set a migration policy**
   - Default to **coexistence**, not retroactive renaming, to avoid breaking links and references.
   - Apply the new convention to newly ingested or newly renamed files going forward.

9. **Document examples and edge cases**
   - Provide examples for:
     - normal files
     - internal/no-client files
     - unknown-type files
     - garbage original names
     - long descriptions

10. **Review after initial rollout**
   - After 4–8 weeks, measure:
     - MISC rate
     - alias confusion
     - average filename length
     - user scan/search success
   - Adjust taxonomy or truncation rules based on actual usage.

If helpful, I can turn this into a concrete `naming_config.yaml` draft next.
