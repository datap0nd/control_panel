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

Open PowerShell **as Administrator**. First inspect the active connection and confirm that it is a trusted network:

```powershell
Get-NetConnectionProfile |
    Select-Object Name, InterfaceAlias, NetworkCategory, IPv4Connectivity
```

Replace `Wi-Fi` below if the active interface has another name. Mark the trusted connection as Private, then create or enable the inbound rule:

```powershell
$interfaceAlias = "Wi-Fi"
$appPort = 8765
$ruleName = "B2B Local Data TCP 8765"

Set-NetConnectionProfile `
    -InterfaceAlias $interfaceAlias `
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
