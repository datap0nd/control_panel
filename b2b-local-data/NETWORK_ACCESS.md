# Put B2B on the network

B2B now uses the same Windows-service method as Data Governance/Metronome. The installer uses the reviewed NSSM executable, runs the application automatically in the background, restarts it after failures and Windows restarts, and binds it explicitly to `0.0.0.0:8766`.

## Run this one command

On the B2B work PC, open the installation folder and run only:

```powershell
Set-Location "C:\Users\meto.mx\Documents\B2B_Salesforce_AI"
.\update_app.ps1
```

Accept the Administrator prompt. Keep the elevated update window open until it reports:

```text
B2B service is running and listening on 0.0.0.0:8766.
```

The update preserves `.env`, `business_rules.md`, history, data, SQL settings, and AI settings. It downloads and validates the latest GitHub `main`, installs or refreshes the `B2BLocalData` service, creates the `B2B Local Data TCP 8766` firewall rule, starts the service, and checks the local HTTP endpoint. Do not edit `APP_PORT`, run `start.ps1`, or run separate firewall commands for the installed service.

## Addresses

On the work PC:

```text
http://127.0.0.1:8766
```

Using the IPv4 address currently seen on the work PC, another reachable computer uses:

```text
http://111.101.7.211:8766
```

If the work PC address changes, the successful update prints the current `Network:` address.

## Copy-and-paste verification

Run this in Administrator PowerShell on the work PC:

```powershell
$serviceName = "B2BLocalData"
$port = 8766
$ruleName = "B2B Local Data TCP 8766"

Get-Service -Name $serviceName |
    Format-List Name, DisplayName, Status, StartType

Get-CimInstance Win32_Service -Filter "Name='B2BLocalData'" |
    Select-Object Name, State, StartMode, PathName

Get-NetTCPConnection -LocalPort $port -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess

Get-NetFirewallRule -DisplayName $ruleName |
    Format-List DisplayName, Enabled, Direction, Action, Profile

Get-NetFirewallRule -DisplayName $ruleName |
    Get-NetFirewallPortFilter |
    Format-List Protocol, LocalPort

Invoke-WebRequest "http://127.0.0.1:$port/api/status" -UseBasicParsing |
    Select-Object StatusCode
```

Expected results:

- Service status: `Running`
- Service start type: `Automatic`
- Listener address: `0.0.0.0` on port `8766`
- Firewall rule: enabled inbound allow for TCP `8766`
- HTTP status: `200`

From the other Windows PC:

```powershell
Test-NetConnection 111.101.7.211 -Port 8766
```

The expected result is `TcpTestSucceeded: True`.

## If the update reports an error

The service logs are:

```text
C:\Users\meto.mx\Documents\B2B_Salesforce_AI\logs\b2b.log
C:\Users\meto.mx\Documents\B2B_Salesforce_AI\logs\b2b_error.log
```

Copy the last lines without exposing passwords:

```powershell
Get-Content "C:\Users\meto.mx\Documents\B2B_Salesforce_AI\logs\b2b_error.log" -Tail 50
```

No router port forwarding is required. This exposes B2B only through the work PC and the network policies already governing it.
