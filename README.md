$codeDir = Split-Path -Parent (Resolve-Path .\setup.ps1)
$auditorRoot = Join-Path (Split-Path -Parent $codeDir) 'auditor'
$account = "$env:USERDOMAIN\$env:USERNAME"

# Confirm the exact folder before changing its permissions
$auditorRoot

takeown.exe /F $auditorRoot /R /D Y
icacls.exe $auditorRoot /reset /T /C
icacls.exe $auditorRoot /grant "${account}:(OI)(CI)F" /T /C

powershell.exe -NoProfile -NoExit -ExecutionPolicy Bypass -File .\setup.ps1
