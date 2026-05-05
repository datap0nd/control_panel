import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter

from .. import config

router = APIRouter()

INSTALL_DIR = Path(__file__).resolve().parent.parent.parent


@router.get("")
def info():
    return {
        "version": config.get_version(),
        "repo_url": config.REPO_URL,
        "zip_url": config.ZIP_URL,
        "platform": sys.platform,
        "install_dir": str(INSTALL_DIR),
        "update_script": str(INSTALL_DIR / "update.ps1"),
    }


@router.post("/run")
def trigger_update():
    """Launch update.ps1 in the user's INTERACTIVE session via Task Scheduler.

    Why not subprocess.Popen?
    - The service runs in session 0 (no desktop). PowerShell launched from here
      cannot show a window to the user.
    - update.ps1 self-elevates via Start-Process -Verb RunAs, which requires a
      visible UAC prompt - impossible from session 0.
    - update.ps1 stops the ControlPanel service mid-flight. If launched as a
      child of the service, the whole process tree dies.

    Task Scheduler solves all three: tasks run in the user's session, can request
    elevation, and are independent processes.
    """
    if sys.platform != "win32":
        return {"ok": False, "error": "Windows only"}

    update_script = INSTALL_DIR / "update.ps1"
    if not update_script.exists():
        return {"ok": False, "error": f"update.ps1 not found at {update_script}"}

    task_name = "ControlPanelUpdate"
    attempts: list[str] = []

    # Same pattern as data_governance update flow:
    # - No /RL HIGHEST (the .ps1 self-elevates via its own UAC trigger)
    # - /ST 00:00 (past time - never auto-fires; we /Run on demand)
    # - /IT makes it run in the logged-on user's interactive session (visible window)
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True, timeout=10,
        )

        tr = f'powershell.exe -ExecutionPolicy Bypass -NoExit -File "{update_script}"'
        create_cmd = [
            "schtasks", "/Create", "/TN", task_name,
            "/TR", tr,
            "/SC", "ONCE", "/ST", "00:00",
            "/IT",
            "/F",
        ]
        r = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
        attempts.append(f"create: rc={r.returncode} {(r.stdout + r.stderr).strip()}")

        if r.returncode == 0:
            r2 = subprocess.run(
                ["schtasks", "/Run", "/TN", task_name],
                capture_output=True, text=True, timeout=10,
            )
            attempts.append(f"run: rc={r2.returncode} {(r2.stdout + r2.stderr).strip()}")
            if r2.returncode == 0:
                return {
                    "ok": True,
                    "method": "scheduled_task",
                    "message": "Update task launched. A PowerShell window will appear in your session shortly.",
                    "install_dir": str(INSTALL_DIR),
                    "attempts": attempts,
                }
    except Exception as exc:
        attempts.append(f"scheduled_task exception: {exc}")

    # Fallback: open install folder so user can launch update.ps1 manually
    try:
        subprocess.Popen(["explorer.exe", str(INSTALL_DIR)])
        return {
            "ok": True,
            "method": "explorer_fallback",
            "message": f"Auto-launch did not work. Opened install folder. Right-click update.ps1 > Run with PowerShell.",
            "install_dir": str(INSTALL_DIR),
            "attempts": attempts,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Could not auto-launch. Run update.ps1 manually from: {INSTALL_DIR}",
            "install_dir": str(INSTALL_DIR),
            "attempts": attempts + [f"explorer fallback exception: {exc}"],
        }
