# Control Panel - Update
# Called from the Update tab in the app, or run manually.
# Downloads latest code from GitHub and restarts the service.
# Re-uses the existing portable Python and NSSM. For first-time install, run setup.ps1 instead.

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe "-NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
trap {
    Write-Host "UPDATE FAILED: $_" -ForegroundColor Red
    pause; exit 1
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ServiceName = "ControlPanel"
$CodeDir     = $PSScriptRoot
$ProjectDir  = Split-Path $CodeDir
$ZipUrl      = "https://github.com/datap0nd/control_panel/archive/refs/heads/main.zip"
$ZipPath     = "$ProjectDir\_update.zip"
$NssmExe     = "$ProjectDir\nssm\nssm.exe"
$PipExe      = "$ProjectDir\python313\Scripts\pip.exe"

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

if (Test-Path $PipExe) {
    Write-Host "Refreshing dependencies..." -ForegroundColor Yellow
    & $PipExe install -r "$CodeDir\requirements.txt" -q
}

if (Test-Path $NssmExe) {
    & $NssmExe start $ServiceName
    Write-Host "Service restarted." -ForegroundColor Green
}

Write-Host "Done."
