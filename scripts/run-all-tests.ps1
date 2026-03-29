#!/usr/bin/env pwsh
# Run all tests
# Usage: ./scripts/run-all-tests.ps1

pytest tests/ -x --tb=short
