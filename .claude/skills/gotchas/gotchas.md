# Corp-Monorepo Gotchas

Last updated: 2026-03-30
Source: moved from ~/.claude/skills/gotchas/gotchas.md (global → project scope)

**Format preference:** Use negative constraints ("Do NOT...") over positive descriptions where possible. "Do NOT use print() in library code" is more effective than "use logging module."

## Pipeline (ingest, routing, classification)

- **Gotcha:** File registry dedup must check BEFORE move, not after
  - Trigger: Modifying ingest-inbox pipeline or dedup logic
  - Symptom: Duplicate files routed to destination, registry shows 0
  - Fix: _check_dedup() runs on source file hash before classify/move. register_file() at ROUTE time, not extraction time.
  - verify: Grep("_check_dedup", path="src/corp/ingest/inbox.py") → exists before classify/move calls
  - **Last triggered:** 2026-03-25

- **Gotcha:** --destination flag must override classifier for ALL files including unclassified
  - Trigger: Adding batch processing flags to ingest-inbox
  - Symptom: Unclassified files still require manual [d] even with --destination set
  - Fix: --destination is fallback for any file without a higher-confidence match. Priority: --destination > client_pattern > destination_rules
  - verify: Grep("destination", path="src/corp/ingest/inbox.py") → fallback priority implemented
  - **Last triggered:** 2026-03-25

- **Gotcha:** User context [c] is extraction hint only — never use as filename or classification input
  - Trigger: Modifying context handling in inbox.py
  - Symptom: "This is RFI from client" becomes filename "2026-03_MISC_GEN_This_is_RFI_from_the_client.docx"
  - Fix: Context stored as user_context for CKE prompt. Proposed name always derives from original filename.
  - verify: Grep("user_context", path="src/corp/ingest/") → used only for CKE prompt, not filename
  - **Last triggered:** 2026-03-25

- **Gotcha:** MISC type code >15% triggers taxonomy review warning
  - Trigger: Too many unclassified files in routing feedback
  - Symptom: `corp naming-stats` shows red warning
  - Fix: Add missing type codes to naming_config.yaml
  - verify: Grep("MISC", path="src/corp/ingest/") → threshold check exists in naming-stats
  - **Last triggered:** 2026-03-25

- **Gotcha:** CKE output must be wrapped in `scope/client/` structure before `corp ingest-extractions` [PROMOTED to learned-rules in project CLAUDE.md]
  - Trigger: Running `corp ingest-extractions` on flat `_outputs/` directory (e.g., `jlr_pilot/pkg/extract/`)
  - Symptom: "Found N packages" but 0 notes ingested — packages resolve to `source/docs/` subdirs with no `.md` files
  - Fix: Copy packages into `scope/client/package/` hierarchy first (e.g., `staged/projects/CLIENT_NAME/pkg/extract/`). Run on the `staged/` root.
  - verify: manual (runtime input structure; stage in scope/client/package/ before ingest-extractions)
  - **Last triggered:** 2026-03-26

- **Gotcha:** status.json concurrent read/write race — CKE writes status.json while watcher reads it, causing JSONDecodeError [PROMOTED to learned-rules in project CLAUDE.md]
  - Trigger: Any polling script that reads a JSON file being written by a concurrent batch process (CKE rebuild, ingest pipelines)
  - Symptom: `json.decoder.JSONDecodeError: Expecting property name` crash in polling script; CKE batch continues unaffected
  - Fix: Wrap `json.loads()` in try/except with 2-3 retries and 2s sleep between attempts; return previous count on all failures
  - verify: Grep("JSONDecodeError", path="src/corp/") → retry logic wraps json.loads()
  - **Last triggered:** 2026-03-27

- **Gotcha:** Classifier priority order matters — file-level rules (Junk, Security, RFP_QA, Data) must come BEFORE path-based rules
  - Trigger: Reordering classifier rules or adding new ones
  - Symptom: Q&A files in Original/ classified as RFP_Original instead of RFP_QA; DPA files missed
  - Fix: Keep file-level rules before path-based rules; exception: WIP path check before RFP_Response
  - verify: Grep("Junk|Security|RFP_QA|Data", path="src/corp/project/") → file-level rules exist before path-based rules
  - **Last triggered:** 2026-03-25

- **Gotcha:** "Commercials" as filename substring is ambiguous — client RFP sections also called "Commercials"
  - Trigger: Adding Commercial category detection by filename
  - Symptom: RFP Commercial sections misclassified
  - Fix: Only catch Commercial via path (Implementation Services/) or explicit patterns (PSEstimator, Effort_Estimation, Deal Alignment, T&M)
  - verify: Grep("Commercial", path="src/corp/project/") → caught by path only (Implementation Services/), not filename
  - **Last triggered:** 2026-03-25

## Extraction (extractor, CKE)

- **Gotcha:** gemini-2.5-flash/gemini-2.0-flash strings scattered across repos — all removed as of 2026-03-12. Verified RESOLVED 2026-03-30: 0 matches in src/. Current models in use: gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-3.1-flash, gemini-3.1-pro-preview
  - Trigger: Adding or updating Gemini model references
  - Symptom: Using deprecated model, unexpected API errors or degraded output
  - Fix: Use gemini-3.1-flash-lite (Tier 1) or gemini-3.1-pro-preview (Tier 2); grep for old model strings before releasing
  - verify: Grep("gemini-2.5-flash|gemini-2.0-flash", path="src/") → 0 matches
  - **Last triggered:** 2026-03-25

- **Gotcha:** CKE v0.4.0 output lacks tags/provenance — don't ingest old output into clean vault. Verified still relevant 2026-03-30 (data/_outputs/v2 exists)
  - Trigger: Re-running ingest on pre-v1.0 CKE extraction output
  - Symptom: Notes with missing tags, no routing_reason, no prompt_version
  - Fix: Re-extract with current CKE version before ingesting
  - verify: manual (data quality check; re-extract with current CKE before ingesting old output)
  - **Last triggered:** 2026-03-25

- **Gotcha:** type="presentation" assigned to DOCX and XLSX files
  - Trigger: Any extraction of non-PPTX files
  - Symptom: DOCX gets type="presentation" in frontmatter
  - Fix: enforce_type_from_extension() overrides LLM classification. .docx→document, .xlsx→spreadsheet, .pptx→presentation. Fixed in v0.6.0+
  - verify: Grep("enforce_type_from_extension", path="src/corp/extractor/") → function exists (regression guard)
  - **Last triggered:** 2026-03-25

- **Gotcha:** doc_type="general" for RFI/RFP/Questionnaire files
  - Trigger: Extracting files with RFI/RFP/VA in filename
  - Symptom: All get doc_type="general" instead of rfp_response or vendor_assessment
  - Fix: classify_from_filename() regex runs BEFORE content analysis. Fixed in v0.6.0+
  - verify: Grep("classify_from_filename", path="src/corp/extractor/") → function exists and runs before content analysis
  - **Last triggered:** 2026-03-25

- **Gotcha:** quality_score formula used key_facts instead of max(key_facts, facts)
  - Trigger: Checking quality_score on extractions with structured facts
  - Symptom: 24 verified facts but quality_score=29 (should be 70+)
  - Fix: compute_quality_score() now uses max(key_facts count, facts count). Fixed in v0.6.0+
  - verify: Grep("max.*key_facts|max.*facts", path="src/corp/extractor/") → uses max(key_facts, facts)
  - **Last triggered:** 2026-03-25

- **Gotcha:** OneDrive project files — COPY to Inbox, never modify in place
  - Trigger: Any operation on files under "OneDrive - Blue Yonder"
  - Symptom: Deletion, rename, or move propagates to SharePoint for all team members
  - Fix: Always Copy-Item to local path first. OneDrive paths are READ-ONLY. Hard exclude in all cleanup operations.
  - verify: manual (OneDrive paths are READ-ONLY; always Copy-Item to local first)
  - **Last triggered:** 2026-03-25

- **Gotcha:** _outputs/ is 20GB+ — never git-tracked, always in .gitignore
  - Trigger: git add in CKE package
  - Symptom: Massive commit if _outputs not ignored
  - Fix: Verify .gitignore has _outputs/ pattern
  - verify: Grep("_outputs", path=".gitignore") → pattern exists
  - **Last triggered:** 2026-03-25

- **Gotcha:** Training data fixtures generated from _outputs/ — re-run scripts/extract_training_data.py after major extractions
  - Trigger: New batch extraction done
  - Symptom: Fixtures stale, tests don't reflect new patterns
  - Fix: Run `python scripts/extract_training_data.py`, commit new fixtures
  - verify: Glob("scripts/extract_training_data.py") → script exists
  - **Last triggered:** 2026-03-25

## Vault & Index (vault_io, index_builder)

- **Gotcha:** Vault notes store full client names ("Jaguar Land Rover") but CLI uses aliases ("JLR") — alias resolution needed everywhere client is searched
  - Trigger: Any code that filters/searches by client name (retrieve, prep, rfp, query)
  - Symptom: `corp prep "JLR"` finds 1 note; `corp prep "Jaguar Land Rover"` finds 2 — same client, different hit counts
  - Fix: Call `get_client_variants(client)` from `corp_by_os.ingest.naming_config` to expand to all aliases before building SQL WHERE; use OR LIKE across all variants
  - verify: Grep("get_client_variants", path="src/corp/") → called in all client search paths
  - **Last triggered:** 2026-03-26

- **Gotcha:** vault_writer shutil.move failure — now raises (fixed), was silent
  - Trigger: Disk full, permissions, path too long during vault write
  - Symptom: OSError raised (before: silent file loss)
  - Fix: Already fixed. Handle OSError in caller if needed.
  - verify: Grep("shutil.move", path="src/corp/extraction/") → wrapped with error handling (raises OSError)
  - **Last triggered:** 2026-03-25

- **Gotcha:** _read_trust_level defaults to "verified" on parse failure (safe)
  - Trigger: Malformed frontmatter in vault note
  - Symptom: File treated as verified (protected) even if trust_level unknown
  - Fix: By design — safe default prevents accidental overwrite.
  - verify: Grep("_read_trust_level", path="src/corp/") → defaults to "verified" on parse failure
  - **Last triggered:** 2026-03-25

## Schema & Config (corp.schema, naming)

- **Gotcha:** corp-os-meta schema changes require updates in CKE, corp-by-os, and any repo that validates frontmatter
  - Trigger: Adding/changing fields in corp-os-meta Pydantic models
  - Symptom: Validation failures in downstream repos
  - Fix: Update all consumers in same PR/session
  - verify: manual (cross-repo PR coordination; check during schema changes)
  - **Last triggered:** 2026-03-25

- **Gotcha:** taxonomy.yaml lives inside the package — always co-located with code
  - Trigger: Looking for taxonomy config in config/ directory
  - Symptom: File not found errors
  - Fix: Import via package, don't assume external config path
  - verify: Glob("src/corp/schema/**/taxonomy.yaml") → exists inside package, not external config
  - **Last triggered:** 2026-03-25

- **Gotcha:** Unknown taxonomy terms are preserved, not dropped — allows organic growth
  - Trigger: Expecting strict validation to reject unknown terms
  - Symptom: Unknown terms pass through without error
  - Fix: Check taxonomy_review.yaml for pending unknowns; validation returns issues tuple
  - verify: Grep("taxonomy_review", path="src/corp/") → unknown terms tracked, not dropped
  - **Last triggered:** 2026-03-25

- **Gotcha:** tool_meta dict provides tool-specific namespace without schema changes
  - Trigger: Wanting to add tool-specific fields to frontmatter
  - Symptom: Schema validation rejecting custom fields
  - Fix: Use tool_meta dict for tool-specific data
  - verify: Grep("tool_meta", path="src/corp/schema/") → field exists in schema model
  - **Last triggered:** 2026-03-25

- **Gotcha:** config/paths.toml search order: CWD > monorepo root > ~/.corp/
  - Trigger: Running CLI from unexpected directory
  - Symptom: Wrong paths if stray paths.toml in CWD
  - Fix: Be aware of search order.
  - verify: Grep("paths.toml", path="src/corp/") → search order documented (CWD > monorepo root > ~/.corp/)
  - **Last triggered:** 2026-03-25

- **Gotcha:** Naming convention filename hints OVERRIDE doc_type
  - Trigger: File named "*RFI*" but doc_type="presentation"
  - Symptom: Gets RFI code, not PRES
  - Fix: By design. Filename hint is more specific. Override with [e]dit in interactive mode if wrong.
  - verify: manual (by design; filename hint > doc_type — awareness rule)
  - **Last triggered:** 2026-03-25

- **Gotcha:** Naming convention v2 forward-only — don't retroactively rename old files
  - Trigger: Old files have MISC_GEN pattern, new files have PRES/RFI/VA
  - Symptom: Mixed naming in same folder
  - Fix: Both patterns valid. New convention applies forward-only.
  - verify: manual (both MISC_GEN and PRES/RFI/VA patterns valid; new convention forward-only)
  - **Last triggered:** 2026-03-25

## MyWork & OneDrive (filesystem safety)

- **Gotcha:** Any write/delete action must explicitly guard synced-tree paths — hotfix 2026-04-21 added guards at execute_plan, execute_moves, and _resolve_project_path (writable=True); project/renderer.py already had one. A fourth unguarded site replays INCIDENT 2026-03-14. Centralization deferred to ADR-27.
  - Trigger: Adding a new action/workflow that mutates a filesystem path derived from `_resolve_project_path`, `find_onedrive_overlap`, or raw `moves.yaml` strings
  - Symptom: `shutil.move` / `.unlink()` / `.write_text()` succeeds on a synced-tree path, mutation propagates to SharePoint
  - Fix: Import `OneDriveSafetyError` from `corp.cleanup.errors` and mirror the `_guard_onedrive` pattern used in `cleanup/executor.py`; for resolver callers pass `writable=True` to `_resolve_project_path`. Regression test must use a fake `"OneDrive - Blue Yonder"` segment under `tmp_path` — never a real synced path
  - verify: Grep("OneDrive - Blue Yonder", path="src/corp/") → every write/delete site has a guard call upstream; see docs/ARCHITECTURE.md "OneDrive safety guards" table
  - **Last triggered:** 2026-04-21

- **Gotcha:** moves.yaml must be loaded through `MoveEntry` schema, not raw `yaml.safe_load` — a `"../../etc/passwd"` source escapes `mywork_root` via `Path.__truediv__` (does not normalize). Hotfix 2026-04-21 added schema + runtime `is_relative_to` check.
  - Trigger: Adding a new consumer of moves.yaml, or bypassing `execute_moves()` with a hand-built `MoveEntry`
  - Symptom: Arbitrary-file delete/move outside `mywork_root`; `_guard_onedrive` alone does not stop this
  - Fix: Load via `MoveEntry.from_dict` (rejects `..` and absolute paths at load time); call `_assert_within_root` after every `mywork_root / ...` join
  - verify: Grep("yaml.safe_load", path="src/corp/cleanup/") → wrapped by `MoveEntry.from_dict` in executor.py
  - **Last triggered:** 2026-04-21

- **Gotcha:** OneDrive ReparsePoint attribute does NOT mean SharePoint shortcut — cloud-only placeholders also have it
  - Trigger: Any operation checking for shortcuts on OneDrive paths
  - Symptom: Files incorrectly classified as shortcuts, skipped or deleted
  - Fix: Check for actual shortcut target, not just ReparsePoint flag
  - verify: manual (Windows OS-level attribute; requires runtime check, not code grep)
  - **Last triggered:** 2026-03-25

- **Gotcha:** source_path breaks when files move — extract only from stable locations
  - Trigger: Extracting from files that may be relocated (Inbox, temp folders)
  - Symptom: Broken source_path references in vault notes after file moves
  - Fix: Only extract from settled locations (30_Reference, 20_Workflows, 10_Projects)
  - verify: manual (operational rule; extract only from 30_Reference, 20_Workflows, 10_Projects)
  - **Last triggered:** 2026-03-25

- **Gotcha:** 90_Archive cleanup — verify Rob's files exist outside underscore folders BEFORE delete [MERGED: consolidated from two entries]
  - Trigger: Any bulk delete on OneDrive, MyWork, or 90_Archive folders
  - Symptom: Personal files lost when deleting what looks like SharePoint-only folders
  - Fix: Always scan for non-underscore files before deleting parent folder. List non-underscore files in each folder; if any exist, do NOT delete.
  - verify: manual (OneDrive exclusion zone; list non-underscore files before any delete)
  - **Last triggered:** 2026-03-25

- **Gotcha:** Never delete archive/cleanup folders without verifying Rob's personal files exist SEPARATELY from underscore (SharePoint) folders [MERGED into 90_Archive cleanup entry above]
  - Trigger: Any bulk delete on OneDrive or MyWork folders
  - Symptom: Rob's files deleted alongside SharePoint copies
  - Fix: See consolidated entry above
  - verify: manual (OneDrive exclusion zone; verify before any bulk delete)
  - **Last triggered:** 2026-03-25

- **Gotcha:** Active project files → 10_Projects/, never generic categories
  - Trigger: Classifying files from active client projects
  - Symptom: JLR RFP response routed to 20_Workflows/PreSales/RFP/ instead of project folder
  - Fix: When file belongs to active project, project folder takes priority over content-based classification
  - verify: manual (classification priority logic; project folder > content-based routing)
  - **Last triggered:** 2026-03-25

- **Gotcha:** Active RFPs — don't extract, keep in workflow
  - Trigger: Ingesting files from active (not submitted) RFP responses
  - Symptom: Draft RFP answers treated as verified knowledge, served to other clients
  - Fix: Active RFPs stay in 20_Workflows/ or 10_Projects/. Extract only after submission and project closure.
  - verify: manual (data lifecycle; extract only after submission and project closure)
  - **Last triggered:** 2026-03-25

## CLI & Opportunity

- **Gotcha:** Folder naming: `com new` creates folders as `{client}_{product}` (verbatim case), but vault convention is lowercased
  - Trigger: Creating new opportunities and matching them to vault project_ids
  - Symptom: project_id mismatch between COM folders and vault notes
  - Fix: Use `f"{client}_{product}".lower()` — match upstream naming, then normalize
  - verify: Grep("lower", path="src/corp/opportunity/") → client_product normalized to lowercase
  - **Last triggered:** 2026-03-25

## External Repos (ai-council, corp-ops)

- **Gotcha:** Monorepo pip install overwrites — don't pip install from archived standalone repos
  - Trigger: Running pip install in _archived_* repo
  - Symptom: CLI points to archived repo instead of monorepo
  - Fix: Only pip install from corp-monorepo/ (single `pip install -e ".[dev,llm]"`)
  - verify: manual (process rule; never pip install from _archived_* repos)
  - **Last triggered:** 2026-03-25

- **Gotcha:** git subtree — never rebase branches with subtree history
  - Trigger: git rebase on monorepo branches
  - Symptom: Duplicate commits, lost history
  - Fix: Always merge, never rebase.
  - verify: manual (git workflow; always merge, never rebase on monorepo branches)
  - **Last triggered:** 2026-03-25

- **Gotcha:** google-genai async — use `client.aio.models.generate_content()`, NOT `asyncio.to_thread`
  - Trigger: Adding async Gemini calls
  - Symptom: Blocking event loop, poor concurrency
  - Fix: Use native async API; package is google-genai, not deprecated google-generativeai
  - verify: Grep("asyncio.to_thread", path="src/") → 0 matches (use client.aio instead) [scope: ai-council repo]
  - **Last triggered:** 2026-03-25

- **Gotcha:** Provider isolation — providers must NOT import each other (no shared base class beyond ABC)
  - Trigger: Refactoring to share code between xai.py and openai_provider.py
  - Symptom: Coupling between providers
  - Fix: Intentional duplication is fine; keep providers independent
  - verify: Grep("from.*providers.*import", path="src/ai_council/providers/") → 0 cross-provider imports [scope: ai-council repo]
  - **Last triggered:** 2026-03-25
