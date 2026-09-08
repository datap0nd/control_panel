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

Copy the `InterfaceIndex` shown for the trusted connection. Replace `12` below with that number. Using the numeric index avoids assuming that the connection is named `Wi-Fi`.

```powershell
$interfaceIndex = 12 # Replace with the trusted connection's InterfaceIndex
$appPort = 8765
$ruleName = "B2B Local Data TCP 8765"

Set-NetConnectionProfile `
    -InterfaceIndex $interfaceIndex `
    -NetworkCategory Private

$existingRule = Get-NetFirewallRule `
    -DisplayName $ruleName `
    -ErrorAction SilentlyContinue

if ($existingRule) {
    Set-NetFirewallRule `
        -DisplayName $ruleName `
        -Enabled True `
        -Direction Inbound `
        -Action Allow `
        -Profile Private
} else {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $appPort `
        -Profile Private
}
```

The rule applies only while Windows classifies the connection as Private.

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

### No listening connection appears

If `Get-NetTCPConnection -LocalPort 8765 -State Listen` returns nothing, confirm that `.env` contains `B2B_LISTEN_HOST=0.0.0.0` and restart the application with `.\start.ps1`.

### The remote connection test fails

If `Test-NetConnection` reports `TcpTestSucceeded: False`, confirm that both PCs are on the same LAN, the B2B PC's network profile is Private, the firewall rule is enabled, and the application is listening. Guest Wi-Fi networks may block communication between devices even when the PC settings are correct.

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
