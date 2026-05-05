# Control Panel - Update
# Called from the Update tab in the app, or run manually.
# Downloads latest code from GitHub, re-extracts bundled libraries (no pip), restarts the service.
# For first-time install, run setup.ps1 instead.

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe "-NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
trap { Write-Host "UPDATE FAILED: $_" -ForegroundColor Red; pause; exit 1 }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ServiceName  = "ControlPanel"
$CodeDir      = $PSScriptRoot
$ProjectDir   = Split-Path $CodeDir
$ZipUrl       = "https://github.com/datap0nd/control_panel/archive/refs/heads/main.zip"
$ZipPath      = "$ProjectDir\_update.zip"
$NssmExe      = "$ProjectDir\nssm\nssm.exe"
$PyDir        = "$ProjectDir\python313"
$SitePackages = "$PyDir\Lib\site-packages"

Write-Host "Updating Control Panel..." -ForegroundColor Cyan

if (Test-Path $NssmExe) {
    & $NssmExe stop $ServiceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
$TempExtract = "$ProjectDir\_extract_temp"
if (Test-Path $TempExtract) { Remove-Item $TempExtract -Recurse -Force }
Expand-Archive -Path $ZipPath -DestinationPath $TempExtract -Force
$Inner = Get-ChildItem $TempExtract -Directory | Select-Object -First 1
if ($Inner) {
    Copy-Item "$($Inner.FullName)\*" $CodeDir -Recurse -Force
    Remove-Item $TempExtract -Recurse -Force
}
Remove-Item $ZipPath -Force

$ver = Get-Date -Format "yyyyMMdd-HHmmss"
Set-Content "$CodeDir\VERSION" $ver
Write-Host "Updated to: $ver" -ForegroundColor Green

# Re-extract bundled wheels (in case any changed)
$VendorDir = "$CodeDir\vendor"
if (Test-Path $VendorDir) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    foreach ($whl in Get-ChildItem -Path $VendorDir -Filter "*.whl") {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($whl.FullName)
        try {
            foreach ($entry in $archive.Entries) {
                if ($entry.FullName.EndsWith('/')) { continue }
                $target = Join-Path $SitePackages $entry.FullName
                $targetDir = Split-Path $target -Parent
                if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
                [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
            }
        } finally { $archive.Dispose() }
    }
    Write-Host "Libraries refreshed from vendor\" -ForegroundColor DarkGray
}

if (Test-Path $NssmExe) {
    & $NssmExe start $ServiceName
    Write-Host "Service restarted." -ForegroundColor Green
}
Write-Host "Done."
