  ## [CRITICAL] src/corp/retrieve/engine.py:30 — upward layer import from ingest

  What: retrieve.engine imports corp.ingest.naming_config, so the retrieval layer
  depends on the ingest pipeline.
  Why: AGENTS.md marks upward layer dependencies as merge-blocking; this couples a
  low-level retrieval module to a higher-layer ingest concern.
  Fix direction: Move client-alias expansion into a lower shared layer such as
  schema/ or a neutral config/helper module and have both retrieve and ingest depend
  on that.

  ## [CRITICAL] src/corp/extractor/synthesize.py:257 — extractor writes markdown/
  package artifacts

  What: write_transcript_note() and build_package() create directories, copy source
  files, and write .md/_meta.yaml/index.md artifacts directly from extractor.
  Why: AGENTS.md requires extractor/ to stay pure and says vault/package writing
  belongs only in ingest/ and extraction/vault_writer.py; this module is doing that
  write side itself.
  Fix direction: Keep extractor limited to returning structured extraction results
  and move package/note/materialization into the approved vault-writing layer.

  ## [CRITICAL] src/corp/schema/cli.py:113 — schema module can rewrite vault notes in
  place

  What: corp-meta normalize --in-place writes normalized frontmatter back to the
  target markdown file from inside schema/cli.py.
  Why: That breaks the “sole vault writer” invariant and also places mutating vault
  behavior under a Layer 0 package.
  Fix direction: Route note rewrites through the dedicated vault-writing path, or
  make this command report-only and delegate persistence elsewhere.

  ## [CRITICAL] src/corp/project/renderer.py:53 — project renderer mutates caller-
  supplied project folders without OneDrive guard

  What: render_project() writes project-info.yaml, facts.yaml, and index.md directly
  under project_path / _knowledge with no safety check on the source root.
  Why: Project folders in this repo’s model can live under OneDrive, and AGENTS.md
  explicitly says OneDrive paths are read-only and must never be modified.
  Fix direction: Add an explicit OneDrive block/safety gate before any project-folder
  write, or redirect output to a non-OneDrive managed workspace.

  ## [HIGH] src/corp/retrieve/engine.py:142 — product expansion drops the rfp_only
  filter

  What: When filters.products is set, retrieve() rebuilds RetrievalFilter but forgets
  to carry over rfp_only.
  Why: RFP-only searches silently widen into general-note searches as soon as product
  expansion runs, which changes retrieval behavior in a hard-to-detect way.
  Fix direction: Preserve every existing filter field when constructing the
  replacement RetrievalFilter, including rfp_only.

  ## [HIGH] src/corp/retrieve/engine.py:276 — vault_root is ignored and read failures
  are silently flattened to empty content

  What: Retrieved note paths are opened via Path(row["note_path"]) without anchoring
  relative paths to vault_root, and _load_note_content() / _load_note_metadata() then
  swallow any read/parse failure by returning empty values.
  Why: If notes.note_path is stored relative, or if the file/frontmatter is
  malformed, retrieval degrades silently into blank note bodies and missing metadata
  instead of surfacing a broken index/path condition.
  Fix direction: Resolve relative note paths against vault_root before I/O and log or
  propagate read/parse failures rather than converting them to empty content.

  ## [HIGH] src/corp/rfp/rfp_feedback.py:51 — feedback ID allocation is not atomic

  What: _next_feedback_id() reads the counter, increments it in memory, and writes it
  back with no lock or transactional primitive.
  Why: Concurrent feedback submissions can race and emit duplicate FB_###
  identifiers, corrupting append-only audit history.
  Fix direction: Allocate IDs through an atomic store such as SQLite or use a
  filesystem locking strategy around counter read/write.

  ## [HIGH] src/corp/schema/cli.py:53 — public CLI entrypoints are missing return
  type annotations

  What: Exported functions like main, validate, normalize, and report are public but
  unannotated.
  Why: AGENTS.md lists missing return annotations on public functions as a high-
  severity type-safety issue, and these are user-facing entrypoints.
  Fix direction: Add explicit return annotations such as -> None to the CLI command
  functions.

  ## [MEDIUM] src/corp/project/manifest_generator.py:147 — stored manifest references
  use Windows-native paths

  What: The generated CKE manifest stores path and output_dir using
  str(...resolve()), which yields backslashes on Windows.
  Why: AGENTS.md requires forward slashes in stored references; Windows-native
  separators make downstream consumers and cross-platform tooling inconsistent.
  Fix direction: Normalize manifest paths to POSIX-style strings before persisting
  them.
