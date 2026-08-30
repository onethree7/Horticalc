param(
    [Parameter(Mandatory = $true)]
    [string]$SetupPath,
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot
)

$ErrorActionPreference = "Stop"

$setup = (Resolve-Path -LiteralPath $SetupPath).Path
$installParent = Split-Path -Parent $InstallRoot
if (-not (Test-Path -LiteralPath $installParent)) {
    New-Item -ItemType Directory -Path $installParent | Out-Null
}
$installRootPath = [System.IO.Path]::GetFullPath($InstallRoot)
if (Test-Path -LiteralPath $installRootPath) {
    throw "Refusing to reuse an existing installer smoke-test directory."
}
$uninstallRegistryKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{50DF7813-DAE5-4976-8B13-6D677CF44660}_is1"
if (Test-Path -LiteralPath $uninstallRegistryKey) {
    throw "Refusing to run the installer smoke test while Horticalc is already registered for this user."
}
$startMenuShortcut = Join-Path ([Environment]::GetFolderPath("Programs")) "Horticalc/Horticalc.lnk"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Horticalc.lnk"

function Invoke-ExecutableAndWait {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FilePath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    foreach ($argument in $ArgumentList) {
        $startInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "$Description did not start."
    }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "$Description failed with exit code $($process.ExitCode)."
    }
}

function Invoke-Setup {
    param(
        [string]$RequestedInstallRoot = $installRootPath,
        [string]$MergeTasks = ""
    )
    $arguments = @(
        "/VERYSILENT"
        "/SUPPRESSMSGBOXES"
        "/NORESTART"
        "/DIR=$RequestedInstallRoot"
    )
    if (-not [string]::IsNullOrWhiteSpace($MergeTasks)) {
        $arguments += "/MERGETASKS=$MergeTasks"
    }
    Invoke-ExecutableAndWait -FilePath $setup -Description "Installer" -ArgumentList $arguments
}

function Test-InstalledApplication {
    $binary = Join-Path $installRootPath "Horticalc.exe"
    if (-not (Test-Path -LiteralPath $binary)) {
        throw "Installed executable not found: $binary"
    }

    $previousNoGui = $env:HORTICALC_NO_GUI
    $env:HORTICALC_NO_GUI = "1"
    $process = Start-Process -FilePath $binary -WorkingDirectory $installRootPath -PassThru -WindowStyle Hidden
    try {
        $lockfile = Join-Path $installRootPath "user/horticalc.lock.json"
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        while (-not (Test-Path -LiteralPath $lockfile) -and [DateTime]::UtcNow -lt $deadline) {
            Start-Sleep -Milliseconds 500
        }
        if (-not (Test-Path -LiteralPath $lockfile)) {
            throw "Installed application did not create its lockfile."
        }

        $lock = Get-Content -LiteralPath $lockfile -Raw | ConvertFrom-Json
        if ($lock.port -lt 8000 -or $lock.port -gt 8100) {
            throw "Installed application lockfile has an invalid port."
        }

        $healthUrl = "http://127.0.0.1:$($lock.port)/health"
        $healthy = $false
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        while (-not $healthy -and [DateTime]::UtcNow -lt $deadline) {
            try {
                $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -UseBasicParsing
                $healthy = $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
            }
            catch {
                Start-Sleep -Milliseconds 500
            }
        }
        if (-not $healthy) {
            throw "Installed application health check failed: $healthUrl"
        }
    }
    finally {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit()
        }
        if ($null -eq $previousNoGui) {
            Remove-Item Env:HORTICALC_NO_GUI -ErrorAction SilentlyContinue
        }
        else {
            $env:HORTICALC_NO_GUI = $previousNoGui
        }
    }
}

Set-Content -LiteralPath $setup -Stream Zone.Identifier -Value "[ZoneTransfer]`r`nZoneId=3"
Invoke-Setup
if (-not (Test-Path -LiteralPath $startMenuShortcut)) {
    throw "Installer did not create the default Start Menu shortcut."
}
if (Test-Path -LiteralPath $desktopShortcut) {
    throw "Installer created the optional desktop shortcut by default."
}

$runtimeDll = Join-Path $installRootPath "_internal/pythonnet/runtime/Python.Runtime.dll"
if (-not (Test-Path -LiteralPath $runtimeDll)) {
    throw "Installed pythonnet runtime not found: $runtimeDll"
}
$runtimeMotw = Get-Item -LiteralPath $runtimeDll -Stream Zone.Identifier -ErrorAction SilentlyContinue
if ($null -ne $runtimeMotw) {
    throw "Installed pythonnet runtime inherited Mark of the Web."
}

Test-InstalledApplication

$sentinel = Join-Path $installRootPath "user/installer-smoke-sentinel.txt"
Set-Content -LiteralPath $sentinel -Value "preserve"

$webviewDefault = Join-Path $installRootPath "user/webview/EBWebView/Default"
$webviewCacheSentinels = @(
    (Join-Path $webviewDefault "Cache/stale-http-cache.bin"),
    (Join-Path $webviewDefault "Code Cache/stale-code-cache.bin")
)
foreach ($cacheSentinel in $webviewCacheSentinels) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $cacheSentinel) -Force | Out-Null
    Set-Content -LiteralPath $cacheSentinel -Value "remove"
}
$webviewStateSentinel = Join-Path $webviewDefault "Local Storage/installer-smoke-state.txt"
New-Item -ItemType Directory -Path (Split-Path -Parent $webviewStateSentinel) -Force | Out-Null
Set-Content -LiteralPath $webviewStateSentinel -Value "preserve"
$repairTarget = Join-Path $installRootPath "frontend/index.html"
Remove-Item -LiteralPath $repairTarget

$conflictingInstallRoot = Join-Path $installParent "Horticalc-conflicting-path"
if (Test-Path -LiteralPath $conflictingInstallRoot) {
    throw "Refusing to reuse an existing conflicting-path smoke-test directory."
}
Invoke-Setup -RequestedInstallRoot $conflictingInstallRoot -MergeTasks "!startmenuicon,desktopicon"
if (Test-Path -LiteralPath (Join-Path $conflictingInstallRoot "Horticalc.exe")) {
    throw "Installer created a second installation when /DIR conflicted with the registered path."
}
$registeredPath = (Get-ItemProperty -LiteralPath $uninstallRegistryKey -Name InstallLocation).InstallLocation
$normalizedRegisteredPath = [System.IO.Path]::GetFullPath($registeredPath).TrimEnd([char[]]"\/")
$normalizedInstallRoot = $installRootPath.TrimEnd([char[]]"\/")
if ($normalizedRegisteredPath -ne $normalizedInstallRoot) {
    throw "Installer changed the registered install path during update."
}
if (-not (Test-Path -LiteralPath $repairTarget)) {
    throw "Installer repair did not restore a missing application file."
}
if (Test-Path -LiteralPath $startMenuShortcut) {
    throw "Installer did not remove the deselected Start Menu shortcut."
}
if (-not (Test-Path -LiteralPath $desktopShortcut)) {
    throw "Installer did not create the selected desktop shortcut."
}
if (-not (Test-Path -LiteralPath $sentinel)) {
    throw "Installer update removed user data."
}
foreach ($cacheSentinel in $webviewCacheSentinels) {
    if (Test-Path -LiteralPath $cacheSentinel) {
        throw "Installer update left stale WebView cache: $cacheSentinel"
    }
}
if (-not (Test-Path -LiteralPath $webviewStateSentinel)) {
    throw "Installer update removed preserved WebView state."
}

Invoke-Setup -RequestedInstallRoot $conflictingInstallRoot
if (Test-Path -LiteralPath $startMenuShortcut) {
    throw "Installer did not preserve the deselected Start Menu task."
}
if (-not (Test-Path -LiteralPath $desktopShortcut)) {
    throw "Installer did not preserve the selected desktop task."
}

$uninstaller = Get-ChildItem -LiteralPath $installRootPath -Filter "unins*.exe" -File |
    Select-Object -First 1
if ($null -eq $uninstaller) {
    throw "Inno Setup uninstaller was not created."
}
Invoke-ExecutableAndWait -FilePath $uninstaller.FullName -Description "Uninstaller" -ArgumentList @(
    "/VERYSILENT"
    "/SUPPRESSMSGBOXES"
    "/NORESTART"
)

if (Test-Path -LiteralPath (Join-Path $installRootPath "Horticalc.exe")) {
    throw "Uninstaller left the application executable behind."
}
if (Test-Path -LiteralPath (Join-Path $installRootPath "_internal")) {
    throw "Uninstaller left packaged runtime files behind."
}
if (Test-Path -LiteralPath (Join-Path $installRootPath "logs")) {
    throw "Uninstaller did not remove logs."
}
if (-not (Test-Path -LiteralPath $sentinel)) {
    throw "Uninstaller removed user data."
}
if (-not (Test-Path -LiteralPath $webviewStateSentinel)) {
    throw "Uninstaller removed preserved WebView state."
}
if (Test-Path -LiteralPath $startMenuShortcut) {
    throw "Uninstaller left the Start Menu shortcut behind."
}
if (Test-Path -LiteralPath $desktopShortcut) {
    throw "Uninstaller left the desktop shortcut behind."
}

Unblock-File -LiteralPath $setup
Write-Output "Windows installer smoke test passed."
