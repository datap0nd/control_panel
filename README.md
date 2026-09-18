$ExistingAuditorService = Get-Service -Name $AuditorServiceName -ErrorAction SilentlyContinue
if ($ExistingAuditorService -and $ExistingAuditorService.Status -ne 'Stopped') {
    & $NssmExe stop $AuditorServiceName 2>&1 | Out-Null
}


& $PyExe "$CodeDir\tools\provision_auditor.py" --root $AuditorRoot --reader-url "http://127.0.0.1:$AuditorPort" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not provision the managed auditor configuration.' }
