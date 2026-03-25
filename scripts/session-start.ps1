#!/usr/bin/env pwsh
# Run at the start of each development session
# Usage: ./scripts/session-start.ps1

Write-Host "`n=== Last 5 Journal Entries ===" -ForegroundColor Cyan
$journal = Get-Content "JOURNAL.md" -Raw
$entries = $journal -split "(?=## \d{4}-\d{2}-\d{2})" | Where-Object { $_ -match "^## \d" } | Select-Object -Last 5
$entries | ForEach-Object { Write-Host $_ -ForegroundColor White }

Write-Host "`n=== Git Status ===" -ForegroundColor Cyan
git status --short

Write-Host "`n=== Gotchas Path ===" -ForegroundColor Yellow
Write-Host "~/.claude/skills/gotchas/gotchas.md (36 entries)"

Write-Host "`n=== Ready to work ===" -ForegroundColor Green
