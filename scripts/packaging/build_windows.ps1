$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$specPath = Join-Path $repoRoot "scripts/packaging/horticalc.spec"

Set-Location $repoRoot
$env:HORTICALC_PROJECT_ROOT = $repoRoot

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

$binaryPath = Join-Path $appRoot "Horticalc.exe"
if (-not (Test-Path $binaryPath)) {
    throw "Expected packaged binary not found: $binaryPath"
}

foreach ($dir in $assetDirs) {
    $path = Join-Path $appRoot $dir
    if (-not (Test-Path $path)) {
        throw "Expected packaged asset directory not found: $path"
    }
}
