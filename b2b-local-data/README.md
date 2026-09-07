# B2B Local Data bootstrap

`setup.ps1` here is the installer from the private `datap0nd/b2b-local-data` repository. It is the only file a work PC needs: it downloads the application source, the SHA-256-verified portable Python, and all libraries from that private repository using a personal access token (PAT), then stages and selects the release. No Git client, administrator rights, pip, Node.js, or system Python is required.

## Install

1. Create an empty install folder, for example `C:\B2B`, and save this `setup.ps1` into it (open the file on GitHub, choose **Raw**, save as `setup.ps1`).
2. In the same folder create a text file named `.env` with one line, using a fine-grained PAT that has **Contents: read** on `datap0nd/b2b-local-data`:

```dotenv
B2B_GITHUB_TOKEN=<the PAT>
```

3. Open PowerShell in that folder and run:

```powershell
.\setup.ps1
```

   The script fetches the exact `main` commit, downloads and verifies everything, runs the self-test, and copies `start.ps1`, `update_app.ps1`, and the current `setup.ps1` next to your `.env`. If this bootstrap copy is older than the downloaded one, it hands over to the fresh script automatically.

4. Complete `.env` with the database and Qwen settings (the full template `.env.example` is now in `releases\<commit>\`), then run:

```powershell
.\start.ps1
```

   and open `http://127.0.0.1:8765`.

## Update

Run `.\setup.ps1` or `.\update_app.ps1` from the install folder again. The PAT in `.env` authenticates every download; unchanged archives are reused, and `.env`, `business_rules.md`, and `data\` are preserved.

## Rules

- The PAT lives only in `.env` (or a process environment variable). Never put it in prompts, scripts, or logs.
- Salesforce exports, result downloads, and test reports stay on the work PC.
- `setup.ps1` sends the PAT to GitHub only; the application never sends it to SQL or Qwen.
