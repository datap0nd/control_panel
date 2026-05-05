import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DB_PATH = Path(os.environ.get("CP_DB_PATH", ROOT / "control_panel.db"))
SCRIPTS_PATH = Path(os.environ.get("CP_SCRIPTS_PATH", ROOT / "scripts"))
BACKUP_PATH = Path(os.environ.get("CP_BACKUP_PATH", ROOT / "backups"))
LOGS_PATH = Path(os.environ.get("CP_LOGS_PATH", ROOT / "logs"))

BACKUP_HOUR = int(os.environ.get("CP_BACKUP_HOUR", "2"))
BACKUP_RETENTION_DAYS = int(os.environ.get("CP_BACKUP_RETENTION_DAYS", "30"))
PORT = int(os.environ.get("CP_PORT", "8765"))

REPO_URL = os.environ.get("CP_REPO_URL", "https://github.com/datap0nd/control_panel")
ZIP_URL = f"{REPO_URL}/archive/refs/heads/main.zip"

VERSION_FILE = ROOT / "VERSION"


def get_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        return "dev"


def ensure_dirs() -> None:
    for p in (BACKUP_PATH, LOGS_PATH, SCRIPTS_PATH):
        p.mkdir(parents=True, exist_ok=True)
