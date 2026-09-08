# Share B2B Local Data on a trusted network

The application listens only on this PC by default. Use the steps below to let colleagues on the same trusted LAN open it in a browser.

## 1. Configure the application

In the B2B installation folder, update `.env`:

```env
B2B_LISTEN_HOST=0.0.0.0
APP_PORT=8765
```

Restart the application from that folder:

```powershell
.\start.ps1
```

## 2. Allow the port through Windows Firewall

Open PowerShell **as Administrator**. The window title must begin with `Administrator:`. First inspect the available connections and confirm which one is the trusted LAN:

```powershell
Get-NetConnectionProfile |
    Select-Object InterfaceIndex, Name, InterfaceAlias, `
        NetworkCategory, IPv4Connectivity
```

### Work PC: copy and paste this complete block

The current work PC uses interface `4`. This block detects whether Windows classifies it as `DomainAuthenticated` or `Private`, then applies the firewall rule to the matching profile. It does not try to change a domain-authenticated network to Private, which Windows prohibits.

```powershell
$interfaceIndex = 4
$appPort = 8765
$ruleName = "B2B Local Data TCP 8765"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdministrator = $principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdministrator) {
    throw "Close this window and open PowerShell with Run as administrator."
}

$networkProfile = Get-NetConnectionProfile `
    -InterfaceIndex $interfaceIndex `
    -ErrorAction Stop

$firewallProfile = switch ($networkProfile.NetworkCategory.ToString()) {
    "DomainAuthenticated" { "Domain" }
    "Private" { "Private" }
    "Public" {
        throw "Interface 4 is Public. Stop and confirm the trusted network before changing it."
    }
    default {
        throw "Unsupported network category: $($networkProfile.NetworkCategory)"
    }
}

$existingRule = Get-NetFirewallRule `
    -DisplayName $ruleName `
    -ErrorAction SilentlyContinue

if ($existingRule) {
    Set-NetFirewallRule `
        -DisplayName $ruleName `
        -Enabled True `
        -Direction Inbound `
        -Action Allow `
        -Profile $firewallProfile
} else {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $appPort `
        -Profile $firewallProfile
}

$networkProfile |
    Format-List Name, InterfaceAlias, InterfaceIndex, `
        NetworkCategory, DomainAuthenticationKind

Get-NetFirewallRule -DisplayName $ruleName |
    Format-List DisplayName, Enabled, Direction, Action, Profile

Get-NetFirewallRule -DisplayName $ruleName |
    Get-NetFirewallPortFilter |
    Format-List Protocol, LocalPort
```

The expected result is an enabled inbound Allow rule for TCP port `8765`, using the Domain profile on a domain-authenticated corporate network or the Private profile on a trusted private network.

## 3. Find and test the address

On the B2B PC, find the active IPv4 address and confirm that the application is listening on every interface:

```powershell
Get-NetIPConfiguration |
    Where-Object IPv4DefaultGateway |
    Select-Object InterfaceAlias, `
        @{Name="IPv4"; Expression={$_.IPv4Address.IPAddress}}

Get-NetTCPConnection `
    -LocalPort 8765 `
    -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

If the address is `192.168.0.58`, colleagues on the same LAN open:

```text
http://192.168.0.58:8765
```

From another Windows PC, the connection can be checked with:

```powershell
Test-NetConnection 192.168.0.58 -Port 8765
```

No router port forwarding is needed for access on the same LAN. Do not forward this port to the internet. The app's name prompt separates local conversation history; it is not network authentication.

## Troubleshooting

### `.env` says another port, but startup still prints `8765`

The application gives a Windows process environment variable precedence over `.env`. A stale `APP_PORT=8765` in the PowerShell environment therefore overrides the file. This complete block sets port `8766` for the current launch, saves it for later launches by this Windows user, updates `.env`, creates the matching firewall rule, and starts B2B:

```powershell
$installRoot = "C:\Users\meto.mx\Documents\B2B_Salesforce_AI"
$newPort = "8766"
$interfaceIndex = 4
$envPath = Join-Path $installRoot ".env"
$ruleName = "B2B Local Data TCP $newPort"

if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Missing $envPath. Correct installRoot or run setup.ps1 first."
}

$envText = Get-Content -LiteralPath $envPath -Raw
$pattern = "(?m)^\s*APP_PORT\s*=.*$"
if ([Regex]::IsMatch($envText, $pattern)) {
    $envText = [Regex]::Replace($envText, $pattern, "APP_PORT=$newPort")
} else {
    $envText += [Environment]::NewLine + "APP_PORT=$newPort" + [Environment]::NewLine
}
[IO.File]::WriteAllText($envPath, $envText, [Text.UTF8Encoding]::new($false))

[Environment]::SetEnvironmentVariable("APP_PORT", $newPort, "User")
$env:APP_PORT = $newPort

$networkProfile = Get-NetConnectionProfile -InterfaceIndex $interfaceIndex -ErrorAction Stop
$firewallProfile = switch ($networkProfile.NetworkCategory.ToString()) {
    "DomainAuthenticated" { "Domain" }
    "Private" { "Private" }
    "Public" { throw "Interface 4 is Public. Stop and confirm the trusted network." }
    default { throw "Unsupported network category: $($networkProfile.NetworkCategory)" }
}

$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Set-NetFirewallRule -DisplayName $ruleName -Enabled True -Direction Inbound -Action Allow -Profile $firewallProfile
} else {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort ([int]$newPort) -Profile $firewallProfile
}

Write-Host "File value:"
Select-String -LiteralPath $envPath -Pattern "^APP_PORT="
Write-Host "Value used by this launch: APP_PORT=$env:APP_PORT"

Set-Location -LiteralPath $installRoot
Write-Host "Starting B2B on port $newPort. Keep this window open."
& ".\start.ps1" -InstallDir $installRoot
```

Successful startup must print `http://127.0.0.1:8766`. Use `http://<B2B-PC-IPv4>:8766` from the other PC. To use a different port, change only `$newPort = "8766"` at the top.

### Work PC: port 8765 has no listener

If the command for port `8765` reports that no matching `MSFT_NetTCPConnection` object was found, Windows Firewall is not yet the immediate problem. That result means no application is listening on the port. Run this complete block in PowerShell on the work PC. It updates only the two network settings in `.env`, preserves the remaining configuration, and starts B2B in the same window so any startup error remains visible:

```powershell
$installRoot = "C:\Users\meto.mx\Documents\B2B_Salesforce_AI"
$envPath = Join-Path $installRoot ".env"
$startScript = Join-Path $installRoot "start.ps1"

if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Missing $envPath. Run setup.ps1 first or correct installRoot."
}

if (-not (Test-Path -LiteralPath $startScript)) {
    throw "Missing $startScript. Run setup.ps1 first or correct installRoot."
}

$envText = Get-Content -LiteralPath $envPath -Raw

foreach ($setting in @{
    B2B_LISTEN_HOST = "0.0.0.0"
    APP_PORT = "8765"
}.GetEnumerator()) {
    $escapedName = [Regex]::Escape($setting.Key)
    $pattern = "(?m)^\s*$escapedName\s*=.*$"
    $replacement = "$($setting.Key)=$($setting.Value)"

    if ([Regex]::IsMatch($envText, $pattern)) {
        $envText = [Regex]::Replace($envText, $pattern, $replacement)
    } else {
        if ($envText.Length -gt 0 -and -not $envText.EndsWith("`n")) {
            $envText += "`r`n"
        }
        $envText += "$replacement`r`n"
    }
}

[IO.File]::WriteAllText(
    $envPath,
    $envText,
    [Text.UTF8Encoding]::new($false)
)

Write-Host "B2B network settings:"
Select-String -LiteralPath $envPath `
    -Pattern '^(B2B_LISTEN_HOST|APP_PORT)='

$listener = Get-NetTCPConnection `
    -LocalPort 8765 `
    -State Listen `
    -ErrorAction SilentlyContinue

if ($listener) {
    Write-Host "Port 8765 is already in use by:"
    $listener |
        Select-Object LocalAddress, LocalPort, OwningProcess
    Get-Process -Id ($listener.OwningProcess | Select-Object -Unique) |
        Select-Object Id, ProcessName, Path
    throw "Stop here: another process already owns port 8765."
}

Set-Location -LiteralPath $installRoot
Write-Host "Starting B2B. Keep this window open."
& $startScript -InstallDir $installRoot
```

Successful startup prints a line ending in `listening on 0.0.0.0`. Keep that PowerShell window open. On the B2B PC, test `http://127.0.0.1:8765`. Only after that local address works should another PC test `http://<B2B-PC-IPv4>:8765`.

If startup prints an error and returns to the PowerShell prompt, keep the full error visible for diagnosis. If it reports that port `8765` is already in use, the block identifies the owning process; do not change the B2B port until that process has been identified.

### No network profile found for `Wi-Fi`

```text
Set-NetConnectionProfile: No MSFT_NetConnectionProfile objects found
with InterfaceAlias equal to 'Wi-Fi'
```

The connection on that PC has a different interface name. Run `Get-NetConnectionProfile` and use its actual `InterfaceIndex` as shown above. Do not use `Wi-Fi` unless it appears exactly in the command output.

### `New-NetFirewallRule: Access is denied`

The PowerShell window is not elevated. Close it, search for PowerShell, choose **Run as administrator**, and rerun the complete block—including the three variable assignments at its beginning.

### Network category cannot be changed

If Windows says the category cannot be changed because the network is domain authenticated, do not run `Set-NetConnectionProfile`. Domain membership controls that category. Use the complete interface-`4` block above; it automatically selects the Domain firewall profile.

### No listening connection appears

Use the complete **Work PC: port 8765 has no listener** block above. A firewall rule opens a path to a listening application; it does not start the application or create the listener.

### The remote connection test fails

If `Test-NetConnection` reports `TcpTestSucceeded: False`, confirm that both PCs are on the same LAN, the firewall rule matches the B2B PC's Domain or Private network profile, the rule is enabled, and the application is listening. Guest Wi-Fi networks and corporate policy may block communication between devices even when the local PC settings are correct.

## Undo network access

Change `.env` back to:

```env
B2B_LISTEN_HOST=127.0.0.1
APP_PORT=8765
```

Restart the application, then remove the firewall rule from an Administrator PowerShell window:

```powershell
Remove-NetFirewallRule -DisplayName "B2B Local Data TCP 8765"
```
