# Set up B2B Local Data on the work PC with a PAT

Install and update the B2B Salesforce Query Agent (`https://github.com/datap0nd/b2b-local-data`, version 0.5.0) on a Windows work PC using only downloads and the repository's `setup.ps1`. No Git client, administrator rights, pip, Node.js, or system Python is needed. Later updates authenticate with a personal access token (PAT) issued through data governance.

## Safety requirements

- Never paste, print, or store the PAT in prompts, command arguments, scripts, or logs. It belongs only in the install folder's `.env` or in a process environment variable.
- The PAT needs **Contents: read** on `datap0nd/b2b-local-data` only. Prefer a fine-grained token scoped to that single repository.
- Keep Salesforce exports, copies, result downloads, and test reports on the work PC. `*.csv`, `*.xlsx`, `.env`, and `data\` are Git-ignored in the app repository and must never be committed anywhere.
- The app's own database credentials (`RO_SQL_USER`, `RO_SQL_PW`) and the Qwen key (`LLM_API_KEY`) also live only in `.env`. `B2B_GITHUB_TOKEN` is never sent to SQL or Qwen.

## 1. Get the PAT

1. Request a fine-grained PAT from data governance, or create one under GitHub **Settings → Developer settings → Fine-grained tokens**.
2. Scope: repository `datap0nd/b2b-local-data`, permission **Contents: Read-only**. Nothing else.
3. Note the expiry date. Setup fails with a GitHub download error when the token expires; replacing the value in `.env` fixes it.

## 2. First install

1. Download the source ZIP of the `main` branch from `https://github.com/datap0nd/b2b-local-data` (**Code → Download ZIP**).
2. Create the install folder, for example `C:\B2B`, and extract the ZIP so that `setup.ps1` sits directly in that folder (move the contents up if the ZIP created a subfolder).
3. Copy `.env.example` to `.env` in that folder and set the values below. Leave the rest at their defaults.

```dotenv
B2B_GITHUB_TOKEN=<paste the PAT here, nowhere else>
DB_KIND=postgres
PGURL=your-host:5432/postgres
RO_SQL_USER=your-read-only-user
RO_SQL_PW=your-password
DB_SSL=true
B2B_RAW_TABLE=bi_reporting.b2b_project

AI_PROVIDER=openai_compatible
LLM_API_URL=http://your-qwen-host:4002/v1/chat/completions
LLM_API_KEY=your-local-key
LLM_MODEL_NAME=qwen3.8-27b-fast
```

   For a CSV-only trial before the database connection exists, use instead:

```dotenv
DB_KIND=csv
B2B_CSV_PATH=exports\salesforce.csv
B2B_CSV_ENCODING=utf-8-sig
```

   The path is relative to the folder containing `.env`; an absolute path also works. The export must contain all 30 Salesforce columns.

4. Open PowerShell in the install folder and run:

```powershell
.\setup.ps1
```

   Setup resolves `main` to an exact commit, downloads that source archive and the SHA-256-verified portable Python and packages from the repository's release assets (using the PAT), runs the self-test, and switches the active release under `releases\`. Local `.env`, `business_rules.md`, and `data\` are preserved.

5. Start the app:

```powershell
.\start.ps1
```

   Open `http://127.0.0.1:8765`. The status line names the configured source. In CSV mode the **Summary table**, **Detailed table**, and **Amounts by stage** buttons work without Qwen; natural-language questions always use the configured model.

## 3. Updates

Run the same command again from the install folder whenever a new version is on `main`:

```powershell
.\setup.ps1
```

or `.\update_app.ps1`. Both use the PAT from `.env` (or the `B2B_GITHUB_TOKEN` process variable) for the commit lookup, the source archive, and any changed dependency assets. Unchanged archives are reused from `.downloads\` and `dependencies\`. Stop the running app with Ctrl+C and run `start.ps1` again to use the new release.

To roll back, stop the app and run the portable interpreter with `updater.py --home <install-folder> --rollback`, then `start.ps1`.

If the repository is made private again later, nothing changes: the PAT already authenticates every download.

## 4. Verify the sample export (optional)

With the supplied export stored locally, run the self-test with the opt-in check. It expects 307 raw rows to produce 112 opportunities and 305 opportunity/SKU rows:

```powershell
$env:B2B_SAMPLE_CSV_PATH = 'C:\B2B\exports\salesforce.csv'
& (Get-Content .\current.json | ConvertFrom-Json).python (Join-Path (Get-Content .\current.json | ConvertFrom-Json).release 'run.py') --self-test
```

## 5. Run the acceptance test

1. In the app, click **Test** in the header, then **Run all checks**. The suite runs 54 prompt turns and 12 browser checks against one frozen snapshot of the configured source with the configured model.
2. Leave the panel open until it reports **Finished**. **Cancel** produces a partial report; a browser reload offers **Resume**.
3. Click **Download report** and paste the `b2b-test-<timestamp>-<run-id>.md` file into the review.
4. Repeat until the header shows **Ready for review**, which requires three consecutive full passes with the same source fingerprint, app revision, suite, rules, model configuration, and effective date.

## Troubleshooting

- `GitHub download failed. Check access and B2B_GITHUB_TOKEN`: the PAT is missing, expired, or lacks Contents: read on the repository.
- `The CSV source file is missing required Salesforce columns`: the export lacks one of the 30 columns; the message lists them.
- `PostgreSQL read failed`: check `PGURL`, the read-only credentials, TLS (`DB_CA_FILE` for an internal CA), and the timeout. The app never falls back to CSV or demo data on a SQL failure.
- `This release requires portable Python 3.13 for Windows x64`: always start through `start.ps1`, not a system Python.
