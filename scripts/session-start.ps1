#!/usr/bin/env pwsh
# Run at the start of each development session
# Usage: ./scripts/session-start.ps1

$root = $PSScriptRoot | Split-Path -Parent

Write-Host "`n=== Last 5 Journal Entries ===" -ForegroundColor Cyan
$journal = Get-Content "$root/JOURNAL.md" -Raw
$entries = $journal -split "(?=## \d{4}-\d{2}-\d{2})" | Where-Object { $_ -match "^## \d" } | Select-Object -Last 5
$entries | ForEach-Object { Write-Host $_ -ForegroundColor White }

Write-Host "`n=== Git Status ===" -ForegroundColor Cyan
git -C $root status --short

$gotchasPath = "$HOME/.claude/skills/gotchas/gotchas.md"
$gotchaCount = (Select-String -Path $gotchasPath -Pattern "^\- \*\*Gotcha").Count
Write-Host "`n=== Gotchas ===" -ForegroundColor Yellow
Write-Host "$gotchasPath ($gotchaCount entries)"

Write-Host "`n=== Ready to work ===" -ForegroundColor Green
