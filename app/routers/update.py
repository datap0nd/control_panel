import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter

from .. import config

router = APIRouter()


@router.get("")
def info():
    return {
        "version": config.get_version(),
        "repo_url": config.REPO_URL,
        "zip_url": config.ZIP_URL,
        "platform": sys.platform,
    }


@router.post("/run")
def trigger_update():
    """Launch the bundled update.ps1 script in a detached process. Windows only.

    The user may also click the 'Open repo' link and run setup.ps1 manually.
    """
    if sys.platform != "win32":
        return {"ok": False, "error": "update.ps1 only runs on Windows"}

    update_script = Path(__file__).resolve().parent.parent.parent / "update.ps1"
    if not update_script.exists():
        return {"ok": False, "error": f"update.ps1 not found at {update_script}"}

    try:
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(update_script),
            ],
            creationflags=0x00000008,  # DETACHED_PROCESS
        )
        return {"ok": True, "message": "Update started in background. Service will restart."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
