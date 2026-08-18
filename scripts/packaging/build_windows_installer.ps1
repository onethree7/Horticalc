param(
    [string]$Version = $env:HORTICALC_VERSION,
    [string]$ArtifactBaseName,
    [string]$IsccPath = $env:ISCC_PATH
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$sourceDir = Join-Path $repoRoot "dist/Horticalc"
$installerScript = Join-Path $repoRoot "scripts/packaging/horticalc.iss"

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (& python -c "from horticalc import __version__; print(__version__)").Trim()
}
if ([string]::IsNullOrWhiteSpace($ArtifactBaseName)) {
    $ArtifactBaseName = "horticalc-v$Version-windows-setup"
}

$requiredPaths = @(
    (Join-Path $sourceDir "Horticalc.exe"),
    (Join-Path $sourceDir "_internal/pythonnet/runtime/Python.Runtime.dll"),
    (Join-Path $sourceDir "frontend/index.html"),
    (Join-Path $sourceDir "LICENSE"),
    (Join-Path $repoRoot "assets/horticalc.ico"),
    $installerScript
)
foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required installer input not found: $path. Build the Windows package first."
    }
}
foreach ($runtimeDirectory in @("user", "logs")) {
    $runtimePath = Join-Path $sourceDir $runtimeDirectory
    if (Test-Path -LiteralPath $runtimePath) {
        throw "Runtime state found in installer input: $runtimePath. Remove user/ and logs/ from the onedir build first."
    }
}

$isccCandidates = @()
if (-not [string]::IsNullOrWhiteSpace($IsccPath)) {
    $isccCandidates += $IsccPath
}
$isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($null -ne $isccCommand) {
    $isccCandidates += $isccCommand.Source
}
if (${env:ProgramFiles(x86)}) {
    $isccCandidates += Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6/ISCC.exe"
}
if ($env:ProgramFiles) {
    $isccCandidates += Join-Path $env:ProgramFiles "Inno Setup 6/ISCC.exe"
}
$resolvedIscc = $isccCandidates |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
    Select-Object -First 1
if (-not $resolvedIscc) {
    throw "Inno Setup 6 compiler (ISCC.exe) was not found. Install Inno Setup 6 or set ISCC_PATH."
}

& $resolvedIscc "/DAppVersion=$Version" "/DSourceDir=$sourceDir" "/DOutputDir=$repoRoot" "/DOutputBaseFilename=$ArtifactBaseName" $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}

$installerPath = Join-Path $repoRoot "$ArtifactBaseName.exe"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Expected installer output not found: $installerPath"
}

Write-Output $installerPath
