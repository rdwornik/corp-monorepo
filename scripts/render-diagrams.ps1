# Render Mermaid diagrams to SVG
# Requires: npm install -g @mermaid-js/mermaid-cli
# Usage: powershell scripts/render-diagrams.ps1

$diagramDir = Join-Path (Join-Path $PSScriptRoot "..") "docs\diagrams"

# Check mmdc is available
if (-not (Get-Command mmdc -ErrorAction SilentlyContinue)) {
    Write-Error "mmdc not found. Install: npm install -g @mermaid-js/mermaid-cli"
    exit 1
}

$count = 0
Get-ChildItem -Path $diagramDir -Filter "*.mermaid" | ForEach-Object {
    $svgPath = $_.FullName -replace '\.mermaid$', '.svg'
    Write-Host "  Rendering $($_.Name) -> $([System.IO.Path]::GetFileName($svgPath))"
    & mmdc -i $_.FullName -o $svgPath -t neutral --backgroundColor transparent
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to render $($_.Name)"
    } else {
        $count++
    }
}
Write-Host "Done. $count SVGs rendered."
