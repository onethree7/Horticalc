$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$specPath = Join-Path $repoRoot "scripts/packaging/horticalc.spec"

python -m PyInstaller --noconfirm --clean $specPath

$distRoot = Join-Path $repoRoot "dist"
$appRoot = Join-Path $distRoot "Horticalc"

if (-not (Test-Path $appRoot)) {
    throw "Expected PyInstaller output folder not found: $appRoot"
}

$assetDirs = @("frontend", "data", "recipes")
foreach ($dir in $assetDirs) {
    $source = Join-Path $repoRoot $dir
    $destination = Join-Path $appRoot $dir
    if (Test-Path $destination) {
        Remove-Item -Recurse -Force $destination
    }
    Copy-Item -Recurse -Force $source $destination
}
