#!/usr/bin/env pwsh
# Run all package tests sequentially
# Usage: ./scripts/run-all-tests.ps1

$ErrorActionPreference = "Stop"
$failed = @()
$total = 0
$passed = 0

$packages = @(
    "packages/corp-os-meta",
    "packages/corp-knowledge-extractor",
    "packages/corp-by-os",
    "packages/corp-project-extractor"
)

foreach ($pkg in $packages) {
    if (Test-Path "$pkg/pyproject.toml") {
        Write-Host "`n=== Testing $pkg ===" -ForegroundColor Cyan
        Push-Location $pkg
        $result = pytest --tb=short -q 2>&1
        $exitCode = $LASTEXITCODE
        Pop-Location

        if ($exitCode -ne 0) {
            $failed += $pkg
            Write-Host "FAILED: $pkg" -ForegroundColor Red
        } else {
            Write-Host "PASSED: $pkg" -ForegroundColor Green
        }
    } else {
        Write-Host "SKIP: $pkg (no pyproject.toml)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Results ===" -ForegroundColor Cyan
if ($failed.Count -eq 0) {
    Write-Host "ALL PACKAGES PASSED" -ForegroundColor Green
} else {
    Write-Host "FAILED PACKAGES:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}
