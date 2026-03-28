# ecosystem-snapshot.ps1
# Run from Scripts root. Outputs a markdown file with ecosystem or single-repo context.
#
# Usage:
#   .\.ecosystem\ecosystem-snapshot.ps1                    # Full ecosystem snapshot
#   .\.ecosystem\ecosystem-snapshot.ps1 -Repo corp-by-os   # Single-repo handoff document
#
# Output: .ecosystem/snapshots/YYYY-MM-DD.md (ecosystem) or <repo>-handoff-YYYY-MM-DD.md (single)

param(
    [string]$Repo
)

$ErrorActionPreference = "Stop"
$date = Get-Date -Format "yyyy-MM-dd"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# === CONFIGURE THESE PATHS ===
$scriptsRoot = if ($env:SCRIPTS_ROOT) { $env:SCRIPTS_ROOT } else { "$env:USERPROFILE\Documents\Dev" }
$vaultRoot = "$env:USERPROFILE\Documents\ObsidianVault"
$myWorkRoot = "$env:USERPROFILE\Documents\MyWork"

# Known repos in the ecosystem (corp-* packages are inside corp-monorepo/packages/)
$allRepos = @(
    "corp-monorepo",
    "corp-ops",
    "corp-sca-time-automation",
    "ai-council"
)

# === HELPER: Generate per-repo section ===
function Get-RepoSection {
    param(
        [string]$RepoName,
        [string]$RepoPath,
        [bool]$Deep = $false
    )

    $section = @()

    if (-not (Test-Path $RepoPath)) {
        $section += "## $RepoName"
        $section += "*NOT FOUND at $RepoPath*"
        $section += ""
        return $section
    }

    $section += "## $RepoName"
    $section += ""

    # --- CLAUDE.md (full for handoff, truncated for ecosystem) ---
    $claudePath = Join-Path $RepoPath "CLAUDE.md"
    if (Test-Path $claudePath) {
        $claudeContent = Get-Content $claudePath -Raw -ErrorAction SilentlyContinue
        if (-not $Deep -and $claudeContent.Length -gt 2000) {
            $claudeContent = $claudeContent.Substring(0, 2000) + "`n`n... [TRUNCATED at 2000 chars]"
        }
        $section += "### CLAUDE.md"
        $section += '```'
        $section += $claudeContent
        $section += '```'
        $section += ""
    }

    # --- README (full for handoff, truncated for ecosystem) ---
    $readmePath = Join-Path $RepoPath "README.md"
    if (Test-Path $readmePath) {
        $readmeContent = Get-Content $readmePath -Raw -ErrorAction SilentlyContinue
        if (-not $Deep -and $readmeContent.Length -gt 3000) {
            $readmeContent = $readmeContent.Substring(0, 3000) + "`n`n... [TRUNCATED at 3000 chars]"
        }
        $section += "### README.md"
        $section += '```'
        $section += $readmeContent
        $section += '```'
        $section += ""
    } else {
        $section += "### README.md"
        $section += "*No README.md found*"
        $section += ""
    }

    # --- pyproject.toml ---
    $pyprojectPath = Join-Path $RepoPath "pyproject.toml"
    if (Test-Path $pyprojectPath) {
        $pyprojectContent = Get-Content $pyprojectPath -Raw -ErrorAction SilentlyContinue
        $section += "### pyproject.toml"
        $section += '```toml'
        $section += $pyprojectContent
        $section += '```'
        $section += ""
    }

    # --- requirements.txt (fallback) ---
    $reqPath = Join-Path $RepoPath "requirements.txt"
    if ((-not (Test-Path $pyprojectPath)) -and (Test-Path $reqPath)) {
        $reqContent = Get-Content $reqPath -Raw -ErrorAction SilentlyContinue
        $section += "### requirements.txt"
        $section += '```'
        $section += $reqContent
        $section += '```'
        $section += ""
    }

    # --- Directory tree ---
    $depth = if ($Deep) { 3 } else { 2 }
    $section += "### Directory Structure (depth $depth)"
    $section += '```'
    try {
        $tree = Get-ChildItem $RepoPath -Recurse -Depth $depth -Name -ErrorAction SilentlyContinue |
            Where-Object {
                $_ -notmatch '(\.venv|venv\\|__pycache__|\.git\\|node_modules|\.mypy_cache|\.ruff_cache|\.pytest_cache|\.egg-info|dist\\)'
            } |
            ForEach-Object { $_ }
        $section += ($tree -join "`n")
    } catch {
        $section += "Error reading directory tree: $_"
    }
    $section += '```'
    $section += ""

    # --- Git status ---
    $section += "### Git Status"
    $section += '```'
    try {
        Push-Location $RepoPath
        $branch = git rev-parse --abbrev-ref HEAD 2>&1
        $lastCommit = git log -1 --format="%h %s (%cr)" 2>&1
        $status = git status --short 2>&1
        $testCount = (Get-ChildItem -Path $RepoPath -Recurse -Filter "test_*.py" -ErrorAction SilentlyContinue).Count
        $testCount += (Get-ChildItem -Path $RepoPath -Recurse -Filter "*_test.py" -ErrorAction SilentlyContinue).Count

        $section += "Branch: $branch"
        $section += "Last commit: $lastCommit"
        $section += "Test files: $testCount"
        if ($status) {
            $section += "Dirty files:"
            $section += $status
        } else {
            $section += "Working tree: clean"
        }
        Pop-Location
    } catch {
        $section += "Error reading git status: $_"
        Pop-Location -ErrorAction SilentlyContinue
    }
    $section += '```'
    $section += ""

    # --- Key config files ---
    $keyConfigs = @(
        "config.yaml",
        "config\config.yaml",
        "config\settings.yaml",
        "config\default.yaml",
        ".env.example"
    )
    foreach ($config in $keyConfigs) {
        $configPath = Join-Path $RepoPath $config
        if (Test-Path $configPath) {
            $configContent = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
            if ($configContent.Length -gt 2000) {
                $configContent = $configContent.Substring(0, 2000) + "`n`n... [TRUNCATED]"
            }
            $section += "### Config: $config"
            $section += '```yaml'
            $section += $configContent
            $section += '```'
            $section += ""
        }
    }

    # --- CLI entry points ---
    $cliFiles = Get-ChildItem $RepoPath -Recurse -Filter "cli.py" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\.venv|venv\\' }
    if ($cliFiles) {
        $section += "### CLI Entry Points"
        foreach ($cliFile in $cliFiles) {
            $relativePath = $cliFile.FullName.Replace($RepoPath + "\", "")
            $clickCommands = Get-Content $cliFile.FullName -ErrorAction SilentlyContinue |
                Select-String -Pattern '@\w+\.(command|group)\(' |
                ForEach-Object { $_.Line.Trim() }
            $section += "**$relativePath**"
            if ($clickCommands) {
                $section += '```python'
                $section += ($clickCommands -join "`n")
                $section += '```'
            }
        }
        $section += ""
    }

    # --- Deep mode extras: tasks, lessons, recent git log ---
    if ($Deep) {
        # tasks/todo.md
        $todoPath = Join-Path $RepoPath "tasks\todo.md"
        if (Test-Path $todoPath) {
            $todoContent = Get-Content $todoPath -Raw -ErrorAction SilentlyContinue
            if ($todoContent.Length -gt 50) {
                $section += "### tasks/todo.md"
                $section += '```'
                $section += $todoContent
                $section += '```'
                $section += ""
            }
        }

        # tasks/lessons.md
        $lessonsPath = Join-Path $RepoPath "tasks\lessons.md"
        if (Test-Path $lessonsPath) {
            $lessonsContent = Get-Content $lessonsPath -Raw -ErrorAction SilentlyContinue
            if ($lessonsContent.Length -gt 50) {
                $section += "### tasks/lessons.md"
                $section += '```'
                $section += $lessonsContent
                $section += '```'
                $section += ""
            }
        }

        # .claude/rules/
        $rulesDir = Join-Path $RepoPath ".claude\rules"
        if (Test-Path $rulesDir) {
            $ruleFiles = Get-ChildItem $rulesDir -Filter "*.md" -ErrorAction SilentlyContinue
            foreach ($rule in $ruleFiles) {
                $ruleContent = Get-Content $rule.FullName -Raw -ErrorAction SilentlyContinue
                $section += "### .claude/rules/$($rule.Name)"
                $section += '```'
                $section += $ruleContent
                $section += '```'
                $section += ""
            }
        }

        # Recent git log (last 20 commits)
        $section += "### Recent Git History (last 20 commits)"
        $section += '```'
        try {
            Push-Location $RepoPath
            $gitLog = git log -20 --format="%h %s (%cr) <%an>" 2>&1
            $section += $gitLog
            Pop-Location
        } catch {
            $section += "Error reading git log: $_"
            Pop-Location -ErrorAction SilentlyContinue
        }
        $section += '```'
        $section += ""
    }

    $section += "---"
    $section += ""

    return $section
}

# =============================================================================
# SINGLE-REPO HANDOFF MODE
# =============================================================================
if ($Repo) {
    # Validate repo name
    if ($Repo -notin $allRepos) {
        Write-Host "Unknown repo: $Repo" -ForegroundColor Red
        Write-Host "Known repos: $($allRepos -join ', ')" -ForegroundColor Yellow
        exit 1
    }

    $repoPath = Join-Path $scriptsRoot $Repo
    $outputFile = "$Repo-handoff-$date.md"

    $output = @()
    $output += "# Handoff Document: $Repo"
    $output += "**Generated:** $timestamp"
    $output += "**Purpose:** Complete context for a new Claude Code session working on this repo."
    $output += ""
    $output += "---"
    $output += ""

    # --- Ecosystem context (abbreviated) ---
    $ecosystemPath = Join-Path $scriptsRoot "ECOSYSTEM.md"
    if (Test-Path $ecosystemPath) {
        $ecoContent = Get-Content $ecosystemPath -Raw -ErrorAction SilentlyContinue
        # Extract just the repo table, dependency graph, and architectural invariants
        $output += "## Ecosystem Context (from ECOSYSTEM.md)"
        $output += ""
        # Get content up to "## Architecture Rules" (the essential parts)
        $cutoff = $ecoContent.IndexOf("## Architecture Rules")
        if ($cutoff -gt 0) {
            $output += $ecoContent.Substring(0, $cutoff)
        } else {
            if ($ecoContent.Length -gt 5000) {
                $output += $ecoContent.Substring(0, 5000) + "`n`n... [TRUNCATED]"
            } else {
                $output += $ecoContent
            }
        }
        $output += ""
        $output += "---"
        $output += ""
    }

    # --- Full repo section (deep mode) ---
    $output += Get-RepoSection -RepoName $Repo -RepoPath $repoPath -Deep $true

    # --- Footer ---
    $output += "*End of handoff document. Paste into Claude Code for full repo context.*"

    $output -join "`n" | Set-Content -Path $outputFile -Encoding UTF8
    $fileSize = (Get-Item $outputFile).Length / 1KB
    Write-Host "Handoff document saved to: $outputFile ($([math]::Round($fileSize, 1)) KB)" -ForegroundColor Green
    Write-Host "Repo: $Repo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. cd $repoPath"
    Write-Host "  2. claude"
    Write-Host "  3. Paste or reference $outputFile for full context"
    exit 0
}

# =============================================================================
# FULL ECOSYSTEM SNAPSHOT MODE
# =============================================================================
$snapshotsDir = Join-Path $scriptsRoot ".ecosystem\snapshots"
if (-not (Test-Path $snapshotsDir)) {
    New-Item -ItemType Directory -Path $snapshotsDir -Force | Out-Null
}
$outputFile = Join-Path $snapshotsDir "$date.md"

$output = @()

# --- Header ---
$output += "# Corporate OS Ecosystem Snapshot"
$output += "**Generated:** $timestamp"
$output += "**Scripts root:** ``$scriptsRoot``"
$output += "**Vault root:** ``$vaultRoot``"
$output += ""
$output += "---"
$output += ""

# --- Per-repo section ---
foreach ($repo in $allRepos) {
    $repoPath = Join-Path $scriptsRoot $repo
    $output += Get-RepoSection -RepoName $repo -RepoPath $repoPath -Deep $false
}

# --- Vault structure ---
$output += "## Obsidian Vault Structure"
$output += '```'
if (Test-Path $vaultRoot) {
    $vaultDirs = Get-ChildItem $vaultRoot -Directory -Depth 1 -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch '^\.' } |
        ForEach-Object { $_.FullName.Replace($vaultRoot + "\", "") }
    $output += ($vaultDirs -join "`n")
} else {
    $output += "Vault not found at $vaultRoot"
}
$output += '```'
$output += ""

# --- Summary table ---
$output += "## Ecosystem Summary"
$output += ""
$output += "| Repo | Branch | Last Commit | Test Files | Clean? |"
$output += "|------|--------|-------------|------------|--------|"

foreach ($repo in $allRepos) {
    $repoPath = Join-Path $scriptsRoot $repo
    if (-not (Test-Path $repoPath)) {
        $output += "| $repo | - | NOT FOUND | - | - |"
        continue
    }
    try {
        Push-Location $repoPath
        $branch = git rev-parse --abbrev-ref HEAD 2>&1
        $lastCommit = git log -1 --format="%h %s (%cr)" 2>&1
        $testCount = (Get-ChildItem -Recurse -Filter "test_*.py" -ErrorAction SilentlyContinue).Count
        $testCount += (Get-ChildItem -Recurse -Filter "*_test.py" -ErrorAction SilentlyContinue).Count
        $isDirty = git status --porcelain 2>&1
        $clean = if ($isDirty) { "dirty" } else { "clean" }
        $output += "| $repo | $branch | $lastCommit | $testCount | $clean |"
        Pop-Location
    } catch {
        $output += "| $repo | error | error | - | - |"
        Pop-Location -ErrorAction SilentlyContinue
    }
}

$output += ""
$output += "---"
$output += "*End of snapshot. Upload this file to any Claude chat or Claude Code session for full ecosystem context.*"

# Write output
$output -join "`n" | Set-Content -Path $outputFile -Encoding UTF8
$fileSize = (Get-Item $outputFile).Length / 1KB
Write-Host "Snapshot saved to: $outputFile ($([math]::Round($fileSize, 1)) KB)" -ForegroundColor Green
Write-Host "Repos scanned: $($allRepos.Count)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Upload this file to Claude chat or Claude Code session"
Write-Host "  2. Ask: 'Review this ecosystem snapshot and identify issues'"
Write-Host "  3. Or use it as context for building the corp-ecosystem skill"
