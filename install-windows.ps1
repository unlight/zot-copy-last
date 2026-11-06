# Repoints an installed copy at the bundled copy.cmd launcher.
# zot spawns extension.json "exec" via CreateProcess, which ignores shebangs.
param([string]$Path = $PSScriptRoot)

$Path = (Resolve-Path -LiteralPath $Path).Path
$manifestPath = Join-Path $Path 'extension.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "extension.json not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifest.exec = (Join-Path $Path 'copy.cmd')
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Host "exec -> $($manifest.exec)"
