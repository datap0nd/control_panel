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

If `Get-NetTCPConnection -LocalPort 8765 -State Listen` returns nothing, confirm that `.env` contains `B2B_LISTEN_HOST=0.0.0.0` and restart the application with `.\start.ps1`.

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
