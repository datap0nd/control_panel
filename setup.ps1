# Control Panel - Setup & Update
# Right-click > Run with PowerShell
#
# Idempotent: first run installs everything, later runs update code + deps.
# Auto-elevates to Admin if needed.
# Never deletes your data: control_panel.db, backups/, scripts/ are preserved.
# Uses portable Python 3.13 (no system changes).

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe "-NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
trap {
    Write-Host ""
    Write-Host "SETUP FAILED: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
    pause
    exit 1
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# --- Paths ---
$ServiceName = "ControlPanel"
$CodeDir     = $PSScriptRoot
$ProjectDir  = Split-Path $CodeDir
$DbPath      = "$ProjectDir\control_panel.db"
$BackupPath  = "$ProjectDir\backups"
$LogsPath    = "$ProjectDir\logs"
$ScriptsPath = "$ProjectDir\scripts"
$Port        = 8765
$RepoOwner   = "datap0nd"
$RepoName    = "control_panel"
$ZipUrl      = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/main.zip"
$ZipPath     = "$ProjectDir\_update.zip"
$PyDir       = "$ProjectDir\python313"
$PyExe       = "$PyDir\python.exe"
$PyZipUrl    = "https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip"
$NssmDir     = "$ProjectDir\nssm"
$NssmExe     = "$NssmDir\nssm.exe"
$NssmZipUrl  = "https://nssm.cc/release/nssm-2.24.zip"

if (-not (Test-Path "$CodeDir\app\main.py")) {
    Write-Host "ERROR: Run this from inside the control_panel-main folder." -ForegroundColor Red
    pause; exit 1
}

Write-Host ""
Write-Host "Control Panel Setup" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "  Code:      $CodeDir" -ForegroundColor DarkGray
Write-Host "  Project:   $ProjectDir" -ForegroundColor DarkGray
Write-Host "  Database:  $DbPath" -ForegroundColor DarkGray
if (Test-Path $DbPath) {
    $dbSize = [math]::Round((Get-Item $DbPath).Length / 1024)
    Write-Host "  DB exists: ${dbSize} KB (preserved)" -ForegroundColor Green
} else {
    Write-Host "  DB: new (created on first run)" -ForegroundColor Yellow
}

# --- 1. Portable Python 3.13 ---
if (-not (Test-Path $PyExe)) {
    Write-Host "[1/6] Downloading portable Python 3.13..." -ForegroundColor Yellow
    $PyZipPath = "$ProjectDir\_python.zip"
    Invoke-WebRequest -Uri $PyZipUrl -OutFile $PyZipPath -UseBasicParsing
    New-Item -ItemType Directory -Path $PyDir -Force | Out-Null
    Expand-Archive -Path $PyZipPath -DestinationPath $PyDir -Force
    Remove-Item $PyZipPath -Force

    $pthFile = Get-ChildItem $PyDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName
        $content = $content -replace '^#\s*import site', 'import site'
        Set-Content $pthFile.FullName $content
    }

    Write-Host "  Bootstrapping pip..." -ForegroundColor DarkGray
    $getPipPath = "$PyDir\get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipPath -UseBasicParsing
    & $PyExe $getPipPath --no-warn-script-location -q
    Write-Host "  Portable Python ready." -ForegroundColor Green
} else {
    Write-Host "[1/6] Portable Python 3.13 already installed." -ForegroundColor DarkGray
}

# --- 2. NSSM ---
if (-not (Test-Path $NssmExe)) {
    Write-Host "[2/6] Downloading NSSM..." -ForegroundColor Yellow
    $NssmZipPath = "$ProjectDir\_nssm.zip"
    Invoke-WebRequest -Uri $NssmZipUrl -OutFile $NssmZipPath -UseBasicParsing
    $NssmTemp = "$ProjectDir\_nssm_extract"
    Expand-Archive -Path $NssmZipPath -DestinationPath $NssmTemp -Force
    $NssmInner = Get-ChildItem $NssmTemp -Directory | Select-Object -First 1
    $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
    New-Item -ItemType Directory -Path $NssmDir -Force | Out-Null
    Copy-Item "$($NssmInner.FullName)\$arch\nssm.exe" $NssmExe -Force
    Remove-Item $NssmTemp -Recurse -Force
    Remove-Item $NssmZipPath -Force
    Write-Host "  NSSM installed." -ForegroundColor Green
} else {
    Write-Host "[2/6] NSSM already present." -ForegroundColor DarkGray
}

# --- 3. Stop existing service & free port ---
$ErrorActionPreference = "Continue"
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[3/6] Stopping existing service..." -ForegroundColor Yellow
    & $NssmExe stop $ServiceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    & $NssmExe remove $ServiceName confirm 2>&1 | Out-Null
} else {
    Write-Host "[3/6] No existing service." -ForegroundColor DarkGray
}
$portPid = (netstat -ano | Select-String ":$Port\s" | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique)
foreach ($p in $portPid) {
    if ($p -and $p -ne "0") {
        Write-Host "  Killing PID $p holding port $Port" -ForegroundColor Yellow
        taskkill /PID $p /F 2>&1 | Out-Null
    }
}
$ErrorActionPreference = "Stop"

# --- 4. Download latest code ---
Write-Host "[4/6] Downloading latest code..." -ForegroundColor Yellow
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
Write-Host "  Version stamped: $ver" -ForegroundColor DarkGray

# --- 5. Install Python dependencies ---
Write-Host "[5/6] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $CodeDir
$PipExe = "$PyDir\Scripts\pip.exe"
& $PipExe install -r requirements.txt -q

# --- 6. Create folders & start service ---
Write-Host "[6/6] Creating folders and starting service..." -ForegroundColor Yellow
foreach ($d in @($BackupPath, $LogsPath, $ScriptsPath)) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}

& $NssmExe install $ServiceName $PyExe "-m uvicorn app.main:app --host 0.0.0.0 --port $Port"
& $NssmExe set $ServiceName AppDirectory $CodeDir
& $NssmExe set $ServiceName DisplayName "Control Panel"
& $NssmExe set $ServiceName Description "Personal control panel: scripts, tasks, notes"
& $NssmExe set $ServiceName Start SERVICE_AUTO_START

& $NssmExe set $ServiceName AppEnvironmentExtra `
    "CP_DB_PATH=$DbPath" `
    "CP_BACKUP_PATH=$BackupPath" `
    "CP_LOGS_PATH=$LogsPath" `
    "CP_SCRIPTS_PATH=$ScriptsPath" `
    "CP_PORT=$Port"

if ($env:CP_SVC_PASSWORD) {
    & $NssmExe set $ServiceName ObjectName "$env:USERDOMAIN\$env:USERNAME" $env:CP_SVC_PASSWORD
} else {
    $cred = Get-Credential -UserName "$env:USERDOMAIN\$env:USERNAME" -Message "Enter your Windows password so the service can run as you (needed for script execution)"
    & $NssmExe set $ServiceName ObjectName "$env:USERDOMAIN\$env:USERNAME" $cred.GetNetworkCredential().Password
}

& $NssmExe set $ServiceName AppExit Default Restart
& $NssmExe set $ServiceName AppRestartDelay 5000
& $NssmExe set $ServiceName AppStdout "$LogsPath\control_panel.log"
& $NssmExe set $ServiceName AppStderr "$LogsPath\control_panel_error.log"
& $NssmExe set $ServiceName AppStdoutCreationDisposition 4
& $NssmExe set $ServiceName AppStderrCreationDisposition 4
& $NssmExe set $ServiceName AppRotateFiles 1
& $NssmExe set $ServiceName AppRotateSeconds 86400
& $NssmExe set $ServiceName AppRotateBytes 10485760

& $NssmExe start $ServiceName
Start-Sleep -Seconds 3

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    Write-Host ""
    Write-Host "Done. Control Panel running at http://localhost:$Port" -ForegroundColor Green
    Start-Process "http://localhost:$Port"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "WARNING: Service not running. Check $LogsPath\" -ForegroundColor Red
}
pause
