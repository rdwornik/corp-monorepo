# SessionStart surfacing for the corp-monorepo nightly conformance loop.
#
# Ported from the hub's scripts/surface_triage.ps1 (proven pattern), adapted to
# corp-monorepo. READ-ONLY, fail-soft, ALWAYS exit 0, silent on the happy path
# (gh absent / offline, or nothing to report). Surfaces four things, each only
# when there is something to say:
#   [gh]      — gh is present but NOT authenticated (skips all gh checks below)
#   [triage]  — open `nightly-triage` Issues await review
#   [nightly] — the last "Nightly Conformance Triage" Action run did NOT succeed
#   [nightly] — the expected dated digest is missing from the default branch
#               (the no-retry silent-skip class — side-effect check)
# This is a surfacing nudge only — it never blocks or noises the session.
#
# Self-contained per ADR-72: queries only this repo (gh fills {owner}/{repo}
# from the cwd's git remote); references no hub path. This is a LOCAL surfacing
# hook (runs on the dev machine), not part of the cloud executing path.
#
# verify: under Windows PowerShell 5.1 (`powershell -File scripts/surface-conformance.ps1`,
#   the hook's actual runtime) with zero open `nightly-triage` Issues it prints NO
#   "[triage]" line (NOT "[triage] 1 ... await: #"); with N open it prints
#   "[triage] N nightly finding(s) await: #a, #b ...". It emits a "[nightly]" line
#   ONLY when the last Action run failed or the expected dated digest is missing
#   from the default branch; on the all-green happy path it prints nothing, exit 0.
#   When gh is present but unauthenticated (`gh auth status` exits non-zero) it
#   prints exactly one "[gh] auth invalid -- run: gh auth refresh -h github.com"
#   line and skips every gh-dependent check (still exit 0) -- this stops an auth
#   failure from masquerading as a missing-digest "[nightly]" false alarm.

$ErrorActionPreference = 'SilentlyContinue'
try {
    # Resolve gh: PATH first, then the default Windows install location as a fallback
    # (the SessionStart shell does not always inherit an updated PATH).
    $gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
    if (-not $gh) {
        $fallback = Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe'
        if (Test-Path -LiteralPath $fallback) { $gh = $fallback }
    }
    if (-not $gh) { exit 0 }

    # Resolve the repo from the project dir (gh reads the cwd's git remote).
    $dir = $env:CLAUDE_PROJECT_DIR
    if ($dir -and (Test-Path -LiteralPath $dir)) { Set-Location -LiteralPath $dir }

    # --- Leading gate: gh auth (mirrors hub e1e1abc) -------------------------
    # gh is on PATH but may not be AUTHENTICATED. Without this gate an invalid /
    # expired token makes every gh call below fail silently (2>$null) -- and the
    # digest side-effect check (b) would then FALSE-ALARM "digest NOT on default
    # branch" on what is really an auth problem (gh api 404s the same on auth
    # failure as on a genuinely-missing file). Probe auth ONCE up front: on
    # failure print a single actionable ASCII banner and skip ALL gh-dependent
    # checks (still fail-soft, still exit 0). `gh auth status` exits non-zero
    # when no usable token is stored.
    & $gh auth status 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Output "[gh] auth invalid -- run: gh auth refresh -h github.com"
        exit 0
    }

    # --- Surfacing 1: open nightly-triage Issues -----------------------------
    # NOTE: do NOT early-exit when there are zero open issues -- the nightly
    # run-health checks below must run on every session, and zero open triage
    # issues is the common case.
    $json = & $gh issue list --label nightly-triage --state open --json number,title 2>$null
    if ($json) {
        # Two Windows PowerShell 5.1 traps (the SessionStart hook runs under 5.1,
        # NOT pwsh 7 -- both are real and were masking each other):
        #  (1) Empty result: `'[]' | ConvertFrom-Json` piped on yields a 1-element
        #      $null array, so an EMPTY gh result printed the bogus banner
        #      "[triage] 1 nightly finding await: #" (Count=1, .number empty).
        #  (2) Non-empty result: ConvertFrom-Json does NOT unroll a root JSON array
        #      into the pipeline, so `... | ConvertFrom-Json | Where-Object` sees
        #      the whole array as ONE item and miscounts N issues as 1.
        # Fix for both: ASSIGN the parse to a variable first (it becomes Object[]),
        # THEN filter that array element-wise, keeping only real entries (.number
        # set). Now 0 open -> no banner; N open -> correct N + issue numbers.
        # (pwsh 7 is unaffected by either trap; this is correct on both.)
        $parsed = $json | ConvertFrom-Json
        $issues = @($parsed | Where-Object { $_ -and $null -ne $_.number })
        if ($issues.Count -gt 0) {
            $nums = ($issues | ForEach-Object { "#$($_.number)" }) -join ', '
            $word = if ($issues.Count -eq 1) { 'finding' } else { 'findings' }
            Write-Output "[triage] $($issues.Count) nightly $word await: $nums -- see the Issues tab."
        }
    }

    # --- Surfacing 2: nightly run health (outcome loop) ----------------------
    # The platform emails on a failed Routine run but has NO retry and NO
    # in-session surfacing -- so a failed run, or a silently-skipped one (machine
    # asleep at 01:15Z), goes unseen until someone notices a missing digest.
    # Side-effect checks are the documented best practice for the no-retry class.

    # (a) Last "Nightly Conformance Triage" Action run -- not success -> loud.
    $runJson = & $gh run list --workflow "Nightly Conformance Triage" --limit 1 --json conclusion,status,url 2>$null
    if ($runJson) {
        $runParsed = $runJson | ConvertFrom-Json
        $runs = @($runParsed | Where-Object { $_ -and $_.url })
        if ($runs.Count -gt 0 -and $runs[0].status -eq 'completed' -and $runs[0].conclusion -ne 'success') {
            Write-Output "[nightly] last Nightly Conformance Triage run did NOT succeed (conclusion=$($runs[0].conclusion)): $($runs[0].url)"
        }
    }

    # (b) Side-effect check: the expected digest for the most recent run date
    #     should exist on the default branch. Missing -> last night's nightly
    #     likely silently skipped (no-retry class). Query GitHub directly (gh
    #     fills {owner}/{repo} from cwd) so a stale local `main` cannot
    #     false-alarm. Get-Date is the real local clock (correct at runtime).
    $now = Get-Date
    $expected = if ($now.Hour -ge 4) { $now } else { $now.AddDays(-1) }
    $stamp = $expected.ToString('yyyy-MM-dd')
    $digestPath = "docs/audits/$stamp-conformance-nightly-digest.md"
    # IMPORTANT: `gh api --jq '.name'` on a 404 prints the error BODY
    # ({"message":"Not Found",...,"status":"404"}) to STDOUT, so a naive
    # stdout-truthiness check ($found non-empty) wrongly reads a MISSING digest
    # as "present" and never fires the silent-skip nudge. Gate on the exit code
    # ($LASTEXITCODE -eq 0 only on HTTP 200) AND a .md-shape check on the name.
    $found = & $gh api "repos/{owner}/{repo}/contents/$digestPath" --jq '.name' 2>$null
    $present = ($LASTEXITCODE -eq 0) -and ($found -match '\.md\s*$')
    if (-not $present) {
        Write-Output "[nightly] expected digest '$digestPath' is NOT on the default branch -- last night's nightly may have silently skipped (no retry)."
    }
} catch {
    # never block or noise the session on a surfacing failure
}
exit 0
