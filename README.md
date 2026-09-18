$projectDir = Split-Path -Parent $PWD.Path

& "$projectDir\python313\python.exe" `
  ".\tools\provision_auditor.py" `
  --root "$projectDir\auditor" `
  --reader-url "http://127.0.0.1:8766"
