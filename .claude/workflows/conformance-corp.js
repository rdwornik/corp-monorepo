export const meta = {
  name: 'conformance-corp',
  description: 'Read-only documentation-conformance review of the corp-monorepo repo: 3 verifiers (JOURNAL vs git, living-doc structural claims, deterministic numeric-inventory drift) fan out, an adversarial skeptic kills false positives, a digest synthesizes. Findings are returned as structured data with a required evidence_command; agents never write. Self-contained per ADR-72 (no hub reference on the executing path). Counts are code-owned (marker contract D); the digest .md is written deterministically by scripts/render_conformance_digest.py (the code-owned write path), and the Action parser reads ONLY the marker (contract C).',
  phases: [
    { title: 'Stage 1 - verifiers', detail: '3 read-only verifiers fan out (Sonnet)', model: 'claude-sonnet-4-6' },
    { title: 'Stage 2 - skeptic', detail: 'adversarial review of all findings (Opus)', model: 'claude-opus-4-8' },
    { title: 'Stage 3 - digest', detail: 'synthesis sorted by severity (Opus)', model: 'claude-opus-4-8' },
  ],
}

// SELF-CONTAINMENT (ADR-72 / PLAYBOOK "Cloud-session hub-independence"): the
// cloud Routine clones ONLY this repo to a single-repo Linux clone at
// /home/user/corp-monorepo/. REPO is the repo root = cwd; portable across the
// local Windows session and the Linux cloud clone. This script references NO
// hub path (../.dev-knowledge/...) anywhere -- doing so would be a defect that
// only a reviewer can catch, since the degradation is silent in cloud.
const REPO = '.'

const READONLY = [
  'You are STRICTLY READ-ONLY. You may Read files, run read-only git (git log, git show, git diff, "git log -p -S"), and grep/shell read commands (wc -l, ls, grep -c, sqlite3 SELECT).',
  'You MUST NOT write or edit any file (Write/Edit are denied this session anyway). Do NOT use Bash to write either (no Set-Content, no >, no New-Item, no sqlite3 write).',
  'Operate ONLY within ' + REPO + ' (this repo). Do NOT read or touch any sibling repo or any hub path.',
  'Return your findings as the structured object only. NEVER write findings to disk.',
  'Every finding MUST include a concrete evidence_command: the exact git/grep/shell command (or file:line read) that PROVES or DISPROVES the claim. If you cannot produce such a command, DROP the finding entirely.',
  'If the evidence requires a file/artifact that is NOT present in this clone (e.g. a gitignored database, an _outputs/ tree, a ~/.claude user path), the claim is OUT-OF-SCOPE for the nightly -- do NOT flag it as contradicted/unsupported; record it in checked_clean as "unverifiable-in-clone: <claim>".',
].join(' ')

const findingSchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    domain: { type: 'string', description: 'journal | living-docs | counts' },
    claim: { type: 'string', description: 'the exact claim being checked' },
    location: { type: 'string', description: 'where the claim lives, e.g. JOURNAL.md:24 or ARCHITECTURE.md:244 or commit hash' },
    evidence_command: { type: 'string', description: 'exact command that proves/disproves the claim (REQUIRED)' },
    verdict: { type: 'string', enum: ['contradicted', 'unsupported', 'omitted'], description: 'contradicted=repo disproves it; unsupported=no corroborating evidence found; omitted=real work missing from the doc' },
    severity: { type: 'string', enum: ['high', 'med', 'low'] },
    note: { type: 'string', description: 'what the evidence actually shows' },
  },
  required: ['domain', 'claim', 'location', 'evidence_command', 'verdict', 'severity', 'note'],
}

const verifierSchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    verifier_id: { type: 'string' },
    checked_clean: { type: 'array', items: { type: 'string' }, description: 'claims/areas checked that produced NO finding (so absence is informative)' },
    findings: { type: 'array', items: findingSchema },
    summary: { type: 'string' },
  },
  required: ['verifier_id', 'checked_clean', 'findings', 'summary'],
}

const skepticSchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    surviving_findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          domain: { type: 'string' },
          claim: { type: 'string' },
          location: { type: 'string' },
          evidence_command: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'med', 'low'] },
          proposed_fix: { type: 'string', description: 'one-line proposal only; no action' },
          skeptic_note: { type: 'string', description: 'why it survived' },
        },
        required: ['domain', 'claim', 'location', 'evidence_command', 'severity', 'proposed_fix'],
      },
    },
    killed_findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          claim: { type: 'string' },
          kill_reason: { type: 'string', enum: ['opinion', 'style', 'true-but-irrelevant', 'documented-decision', 'evidence-not-definitive'] },
          kill_detail: { type: 'string', description: 'explanation; cite ADR id if documented-decision' },
        },
        required: ['claim', 'kill_reason', 'kill_detail'],
      },
    },
    survive_count: { type: 'number' },
    kill_count: { type: 'number' },
  },
  required: ['surviving_findings', 'killed_findings', 'survive_count', 'kill_count'],
}

const digestSchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    summary: { type: 'string' },
    findings_by_severity: {
      type: 'object',
      additionalProperties: false,
      properties: {
        high: { type: 'array', items: { type: 'string' } },
        med: { type: 'array', items: { type: 'string' } },
        low: { type: 'array', items: { type: 'string' } },
      },
      required: ['high', 'med', 'low'],
    },
    counts: {
      type: 'object',
      additionalProperties: false,
      properties: {
        raw_findings: { type: 'number' },
        survived_skeptic: { type: 'number' },
        killed_false_positive: { type: 'number' },
      },
      required: ['raw_findings', 'survived_skeptic', 'killed_false_positive'],
    },
    // Machine-readable counts contract (D). The agent must echo the EXACT
    // code-computed marker string provided in the Stage-3 prompt, verbatim.
    // Code (below) validates this against the authoritative counts and throws
    // on mismatch, so the agent's free prose is NEVER the parse target.
    // Format: <!-- counts: raw=N survived=N killed=N -->
    counts_marker: { type: 'string', description: 'EXACT machine-readable marker, copied verbatim from the prompt; format "<!-- counts: raw=N survived=N killed=N -->". Never recompute it.' },
    checked_clean: { type: 'array', items: { type: 'string' } },
    next_actions: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'findings_by_severity', 'counts', 'counts_marker', 'checked_clean', 'next_actions'],
}

// --- Verifier domains (corp-monorepo adaptation) ----------------------------
// Nightly scope is the DRIFT-PRONE claim classes only (commands, hooks, paths,
// counts) + the rolling JOURNAL/git coherence -- deliberately smaller than the
// #75 deep-audit, recurring-safe. The baseline (docs/audits/2026-06-04-
// conformance-baseline-digest.md insight (f)) found 5/5 real findings were
// ARCHITECTURE.md count drift; so V3 is a DETERMINISTIC count-verifier (the
// hub's backlog-coherence domain is dropped for the nightly -- count drift is
// corp's empirically dominant class).

const V1 = READONLY + '\n\nDOMAIN V1 - JOURNAL vs git reality.\n'
  + 'Read the LAST 10 entries (newest-first) of ' + REPO + '/JOURNAL.md. Each entry has "### YYYY-MM-DD - <topic>" then Did / Result / Changes / (Abandoned) / Next lines (ADR-49 shape; older entries use Did/Failed/Next).\n'
  + 'For each concrete claim of work done (Did/Result/Changes), corroborate it against git: use "git log --oneline -40", "git show <hash>", "git log -p -S \"<string>\" -- <file>", and direct file existence checks.\n'
  + 'SHALLOW-HISTORY GUARD: before flagging a JOURNAL entry commit SHA as absent, verify that SHA date falls within the available git history (the cloud clone may be SHALLOW -- it starts at the first push). SHAs older than the history boundary are OUT-OF-SCOPE, not findings (record in checked_clean).\n'
  + 'FLAG: (a) entries asserting work that git history does NOT show (verdict contradicted/unsupported); (b) significant merged work in git (recent commits/merges) that the last-10 JOURNAL entries do NOT mention (verdict omitted).\n'
  + 'Populate checked_clean with the claims you verified as TRUE (so their absence from findings is informative). Set verifier_id="V1".'

const V2 = READONLY + '\n\nDOMAIN V2 - Living-doc STRUCTURAL claims vs repo state (paths, commands, hooks, CLI/module names).\n'
  + 'Scan CLAUDE.md and ARCHITECTURE.md (and VISION.md / CONTRIBUTING.md if they assert structure) for VERIFIABLE STRUCTURAL claims in these DRIFT classes ONLY -- do NOT check numeric counts here (V3 owns counts):\n'
  + '  - PATHS: a cited file/dir exists, e.g. config/paths.toml, src/corp/ namespace, tests/safety/test_vault_writer_invariant.py, config/naming_config.yaml, .pre-commit-config.yaml.\n'
  + '  - COMMANDS: the 5 CLIs (corp, corp-meta, cke, cpe, com) are declared in pyproject.toml [project.scripts]; scripts named in docs exist (scripts/run-all-tests.ps1, scripts/dev-check.ps1); repo-level slash commands in .claude/commands/ match CLAUDE.md s7 ("none currently").\n'
  + '  - HOOKS / CI: pre-commit hooks named in CLAUDE.md s9 / s4 (ruff, tach) exist in .pre-commit-config.yaml; CI workflows in .github/workflows/ match what docs claim.\n'
  + '  - NAMES: ADR ids referenced in CLAUDE.md s11 exist under docs/decisions/ (corp ADR-14, ADR-23, ADR-27); module/CLI names in ARCHITECTURE.md resolve under src/corp/.\n'
  + 'For each claim run the disproving command (test it exists / grep the registry). FLAG mismatches with exact file:line and the command (verdict contradicted). USER-LEVEL items (~/.claude/commands, ~/.claude/skills) are NOT in this clone -> OUT-OF-SCOPE (checked_clean "unverifiable-in-clone").\n'
  + 'Only flag falsifiable structural claims; ignore prose/opinion and ignore numbers. Populate checked_clean with the structural claims you verified as correct. Set verifier_id="V2".'

const V3 = READONLY + '\n\nDOMAIN V3 - DETERMINISTIC numeric-inventory drift (count-verifier).\n'
  + 'This domain is MACHINE-DETERMINISTIC: for every numeric inventory ARCHITECTURE.md (and CLAUDE.md) asserts, COMPUTE the live number with a non-LLM command and diff it against the doc. Do NOT estimate or eyeball -- run the command. Known count claims (re-locate exact line numbers yourself; they drift):\n'
  + '  - LOC counts: "wc -l src/corp/extractor/extract.py", "src/corp/project/router.py", "src/corp/ingest/inbox.py", "src/corp/ops/database.py".\n'
  + '  - Module/file counts: "ls src/corp/actions/*.py | wc -l" (actions modules); "ls src/corp/cli/*.py | wc -l" (cli files).\n'
  + '  - Config list sizes: type codes and client aliases via "grep -cE \"^  [a-z]\" config/naming_config.yaml" sections, or count the relevant YAML keys; agents via config/agents.yaml.\n'
  + '  - CLI/package facts: 5 CLIs in pyproject.toml [project.scripts]; "5 repos" the OpsDB facade delegates to.\n'
  + 'UNREACHABLE-DATA GUARD: counts that need a gitignored artifact NOT in the clone (e.g. the notes count needs index.db, which is not committed) are OUT-OF-SCOPE -- record "unverifiable-in-clone: notes count (index.db not in clone)" in checked_clean; do NOT flag as drift.\n'
  + 'IGNORE struck/historical numbers (ARCHITECTURE.md lines marked RESOLVED / strikethrough record the OLD value on purpose -- e.g. "705 LOC" inside a ~~God class~~ row -- and are not live claims).\n'
  + 'FLAG only a LIVE count whose computed value differs from the doc (verdict contradicted; severity by magnitude). Populate checked_clean with the counts you verified as MATCHING (number + command). Set verifier_id="V3".'

log('conformance-corp: read-only self-contained documentation-conformance review (ADR-72). Target ~80k tokens (single pass).')
log('budget.total=' + String(budget.total) + ' spent=' + budget.spent())

phase('Stage 1 - verifiers')
const [v1, v2, v3] = await parallel([
  () => agent(V1, { label: 'V1-journal-vs-git', phase: 'Stage 1 - verifiers', schema: verifierSchema, model: 'claude-sonnet-4-6' }),
  () => agent(V2, { label: 'V2-structural-claims', phase: 'Stage 1 - verifiers', schema: verifierSchema, model: 'claude-sonnet-4-6' }),
  () => agent(V3, { label: 'V3-deterministic-counts', phase: 'Stage 1 - verifiers', schema: verifierSchema, model: 'claude-sonnet-4-6' }),
])

const verifiers = [v1, v2, v3].filter(Boolean)
const raw = []
for (const v of verifiers) for (const f of (v.findings || [])) raw.push(f)
const cleanAll = []
for (const v of verifiers) for (const c of (v.checked_clean || [])) cleanAll.push((v.verifier_id || '?') + ': ' + c)
log('Stage 1 raw findings: ' + raw.length + ' (V1=' + (v1 ? v1.findings.length : 'null') + ' V2=' + (v2 ? v2.findings.length : 'null') + ' V3=' + (v3 ? v3.findings.length : 'null') + '). spent=' + budget.spent())

phase('Stage 2 - skeptic')
const skepticPrompt = READONLY + '\n\nYou are an ADVERSARIAL SKEPTIC. Below are ' + raw.length + ' findings from 3 read-only verifiers. Default to KILLING a finding unless its evidence_command definitively proves a real conformance problem.\n'
  + 'KILL if the finding is: opinion; style preference; technically-true-but-irrelevant; explainable by a documented decision (CONSULT ' + REPO + '/docs/decisions before deciding - cite the ADR id); references an artifact not in this clone (unverifiable-in-clone); or its evidence_command is not actually definitive.\n'
  + 'You MAY re-run any evidence_command yourself (read-only) to confirm before keeping. For each SURVIVOR set: severity (high/med/low), keep the evidence_command, and a one-line proposed_fix (PROPOSAL ONLY - take no action). For each KILL: claim + kill_reason + kill_detail.\n\n'
  + 'FINDINGS JSON:\n```json\n' + JSON.stringify(raw, null, 2) + '\n```'
const skeptic = await agent(skepticPrompt, { label: 'skeptic-adversarial', phase: 'Stage 2 - skeptic', schema: skepticSchema, model: 'claude-opus-4-8' })

// Enforce the /goal-equivalent: no survivor without a state-based evidence_command reaches the digest.
const survivors = (skeptic.surviving_findings || []).filter(f => f.evidence_command && String(f.evidence_command).trim().length > 0)
const droppedNoEvidence = (skeptic.surviving_findings || []).length - survivors.length
log('Stage 2: survived=' + survivors.length + ' killed=' + (skeptic.kill_count || (skeptic.killed_findings || []).length) + ' dropped_no_evidence=' + droppedNoEvidence + '. spent=' + budget.spent())

// --- Counts contract (D): code-owned, code-computed, machine-readable -------
// These three integers are the AUTHORITATIVE counts, computed here in code from
// the run's own data structures (NOT from the agent's prose). The marker is the
// only thing the Action parser reads; the agent's free rendering is never parsed.
// NOTE the executing-path caveat (PLAYBOOK / LESSONS 2026-06-05): in cloud the
// native launcher is absent, so this .js is read as a SPEC, not run -- the
// throw-below is INERT there. The load-bearing guarantees live where bytes
// actually flow: (1) scripts/render_conformance_digest.py recomputes the marker
// from counts and writes it deterministically (code-owned write path that DOES
// run in cloud, via the Routine's Bash); (2) the Action parser reads ONLY the
// marker and fails closed on absence (contract C). The D mechanism here is the
// native-path guard the prompt requires.
const rawCount = raw.length
const survivedCount = survivors.length
const killedCount = (skeptic.killed_findings || []).length
const countsMarker = '<!-- counts: raw=' + rawCount + ' survived=' + survivedCount + ' killed=' + killedCount + ' -->'
log('counts contract (code-owned): ' + countsMarker)

phase('Stage 3 - digest')
const digestPrompt = 'Synthesize a documentation-conformance digest from the data below. Do not re-investigate; just synthesize faithfully.\n'
  + 'Produce: findings_by_severity (one-line each, sorted high->med->low, survivors only); counts {raw_findings=' + rawCount + ', survived_skeptic=' + survivedCount + ', killed_false_positive=' + killedCount + '}; an explicit checked_clean list (so absence of findings is informative); a one-paragraph summary of overall doc health and the skeptic kill-rate; and next_actions ONLY if survivors exist (proposals for the operator, no action).\n\n'
  + 'COUNTS CONTRACT (machine-readable, REQUIRED): set the field `counts_marker` to EXACTLY this string, copied verbatim character-for-character (do NOT recompute the numbers): ' + countsMarker + '\n'
  + 'This marker is the SOLE count contract the nightly Action parses; your prose counts are for humans and are never parsed. The digest .md is rendered deterministically from this structured output by scripts/render_conformance_digest.py, which writes the marker on its own line. Do NOT emit a "### Counts" table.\n\n'
  + 'SURVIVORS:\n```json\n' + JSON.stringify(survivors, null, 2) + '\n```\n\n'
  + 'KILLED:\n```json\n' + JSON.stringify(skeptic.killed_findings || [], null, 2) + '\n```\n\n'
  + 'CHECKED-CLEAN (from verifiers):\n```json\n' + JSON.stringify(cleanAll, null, 2) + '\n```'
const digest = await agent(digestPrompt, { label: 'digest-synthesis', phase: 'Stage 3 - digest', schema: digestSchema, model: 'claude-opus-4-8' })

// --- Validation code step (D, native path): the contract holder --------------
// Fail the Routine run LOUDLY if the agent did not echo the code-computed marker
// verbatim. On the native launcher path this throws before any digest with a
// wrong/absent count contract is returned. (Inert on the spec-orchestration
// path -- see the executing-path note above; the renderer + Action are the
// backstops there.)
if (!digest || digest.counts_marker !== countsMarker) {
  throw new Error(
    'Counts-marker contract violation (fail-closed): digest.counts_marker='
    + JSON.stringify(digest && digest.counts_marker) + ' but code-computed marker='
    + JSON.stringify(countsMarker) + '. The Stage-3 agent must echo the marker verbatim. '
    + 'Refusing to emit a digest whose machine-readable counts do not match the authoritative code counts.'
  )
}
log('counts contract validated: agent echoed marker verbatim.')

log('conformance-corp complete. spent=' + budget.spent())

// Return shape is the INPUT CONTRACT for scripts/render_conformance_digest.py.
// The Routine writes this object to a JSON file and runs the renderer to produce
// docs/audits/<date>-conformance-nightly-digest.md (the code-owned write path).
return {
  schema_version: 1,
  raw_count: rawCount,
  raw_findings: raw,
  verifier_checked_clean: cleanAll,
  skeptic: { survive_count: survivedCount, kill_count: killedCount, killed_findings: skeptic.killed_findings || [], dropped_no_evidence: droppedNoEvidence },
  survivors,
  // counts_marker is the canonical line the renderer MUST write verbatim into
  // docs/audits/<date>-conformance-nightly-digest.md (on its own line). The
  // renderer also recomputes it from `counts` and fails closed on disagreement.
  counts_marker: countsMarker,
  counts: { raw_findings: rawCount, survived_skeptic: survivedCount, killed_false_positive: killedCount },
  digest,
}
