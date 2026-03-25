#!/usr/bin/env pwsh
# Full quality gate — run before merging to main
# Usage: ./scripts/dev-check.ps1

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot | Split-Path -Parent
$failed = @()

Write-Host "`n=== Ruff Format ===" -ForegroundColor Cyan
ruff format "$root/packages/"
if ($LASTEXITCODE -ne 0) { $failed += "ruff-format" }

Write-Host "`n=== Ruff Lint ===" -ForegroundColor Cyan
ruff check "$root/packages/" --fix
if ($LASTEXITCODE -ne 0) { $failed += "ruff-lint" }

Write-Host "`n=== Unit Tests ===" -ForegroundColor Cyan
& "$PSScriptRoot\run-all-tests.ps1"
if ($LASTEXITCODE -ne 0) { $failed += "unit-tests" }

Write-Host "`n=== Integration Tests ===" -ForegroundColor Cyan
py -m pytest "$root/tests/integration/" -v
if ($LASTEXITCODE -ne 0) { $failed += "integration-tests" }

Write-Host "`n=== Results ===" -ForegroundColor Cyan
if ($failed.Count -eq 0) {
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
} else {
    Write-Host "FAILED:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}
