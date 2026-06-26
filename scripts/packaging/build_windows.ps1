$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$specPath = Join-Path $repoRoot "scripts/packaging/horticalc.spec"
$versionInfoPath = Join-Path $repoRoot "build/horticalc_windows_version_info.txt"

Set-Location $repoRoot
$env:HORTICALC_PROJECT_ROOT = $repoRoot

$releaseVersion = $env:HORTICALC_VERSION
if ([string]::IsNullOrWhiteSpace($releaseVersion) -and $env:GITHUB_REF_TYPE -eq "tag") {
    $releaseVersion = $env:GITHUB_REF_NAME
}
if ([string]::IsNullOrWhiteSpace($releaseVersion)) {
    $releaseVersion = "0.0.0"
}

python scripts/packaging/write_windows_version_info.py --version $releaseVersion --output $versionInfoPath
$env:HORTICALC_VERSION_FILE = $versionInfoPath

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
