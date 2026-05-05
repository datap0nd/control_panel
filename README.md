# Control Panel

Personal web-based control panel: dashboard with custom metrics, kanban tasks, markdown notes, runnable scripts, and one-click self-update. Daily SQLite backups.

FastAPI + vanilla JS SPA. No build step. Runs as a Windows service.

## Quick install (Windows)

1. Pick a project folder, e.g. `C:\Users\YOU\Documents\Control Panel\`
2. Download the repo ZIP from GitHub: [main.zip](https://github.com/datap0nd/control_panel/archive/refs/heads/main.zip)
3. Extract so the structure is:
   ```
   C:\Users\YOU\Documents\Control Panel\control_panel-main\
     app\
     setup.ps1
     update.ps1
     ...
   ```
4. Right-click `setup.ps1` > Run with PowerShell. It will:
   - Auto-elevate to Admin
   - Download a portable Python 3.13 (no system install)
   - Download NSSM (service wrapper)
   - Install Python deps
   - Register `ControlPanel` Windows service
   - Start it on http://localhost:8765
5. The browser opens automatically when ready.

Re-run `setup.ps1` any time to update + reinstall deps. Or use the **Update** tab in the app for a code-only refresh.

## Folder layout after install

```
Control Panel\
  control_panel-main\        <- this repo's code
  control_panel.db           <- your data (SQLite, preserved across updates)
  backups\                   <- daily SQLite backups
  logs\                      <- service stdout/stderr
  scripts\                   <- drop your .ps1 / .py / .bat / .sh files here
  python313\                 <- portable Python (auto-installed)
  nssm\                      <- service manager (auto-installed)
```

## Tabs

- **Dashboard** - tasks counts, scripts run today, last backup, custom metrics
- **Scripts** - lists files in your `scripts/` folder, one-click run, output capture, run history
- **Tasks** - kanban (backlog / doing / done), drag-and-drop
- **Notes** - markdown notes with tags, pin important ones
- **Update** - one-click "download latest from GitHub + restart" + repo links
- **Settings** - env vars, backup management, custom user settings

## Scripts

Drop any `.ps1`, `.py`, `.bat`, `.cmd`, or `.sh` file into the `scripts/` folder. It appears in the Scripts tab automatically.

Optional metadata: place a sidecar JSON file next to the script with the same stem, e.g. `cleanup.ps1` and `cleanup.meta.json`:

```json
{
  "name": "Clean temp files",
  "description": "Removes everything older than 7 days from %TEMP%",
  "args": "[-DryRun]"
}
```

## Environment variables

All configurable via NSSM (`nssm edit ControlPanel`) or by re-running `setup.ps1`:

| Variable | Default | Notes |
|---|---|---|
| `CP_DB_PATH` | `..\control_panel.db` | SQLite file location |
| `CP_SCRIPTS_PATH` | `..\scripts` | Where to look for runnable scripts |
| `CP_BACKUP_PATH` | `..\backups` | Where daily backups land |
| `CP_LOGS_PATH` | `..\logs` | Service log dir |
| `CP_BACKUP_HOUR` | `2` | 24h hour for daily backup |
| `CP_BACKUP_RETENTION_DAYS` | `30` | How long backups are kept |
| `CP_PORT` | `8765` | Web UI port |
| `CP_REPO_URL` | this repo | Used by Update tab |

## Daily backup

A scheduled job runs at `CP_BACKUP_HOUR` each day, copying `control_panel.db` to `backups\control_panel_YYYYMMDD_HHMMSS.db` using SQLite's online backup API. Old backups beyond `CP_BACKUP_RETENTION_DAYS` are pruned.

Manual backup button in Settings.

## Run without the service (dev)

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

## API

All endpoints under `/api/`:

| Router | Path | Operations |
|---|---|---|
| Dashboard | `/api/dashboard` | GET overview, PUT/DELETE custom metrics |
| Scripts | `/api/scripts` | GET list, POST `/run`, POST `/run/stream`, GET `/runs` |
| Tasks | `/api/tasks` | CRUD + PATCH `/move` |
| Notes | `/api/notes` | CRUD |
| Update | `/api/update` | GET info, POST `/run` |
| Backup | `/api/backup` | GET list, POST `/run`, POST `/prune`, GET `/download/{name}` |
| Settings | `/api/settings` | GET, PUT, DELETE |

## License

MIT.
