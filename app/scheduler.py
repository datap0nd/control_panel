import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .database import get_conn

_scheduler: BackgroundScheduler | None = None


def run_backup() -> dict:
    config.BACKUP_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"control_panel_{timestamp}.db"
    out_path = config.BACKUP_PATH / out_name

    if not config.DB_PATH.exists():
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO backup_log(path, status, error) VALUES (?, ?, ?)",
                (str(out_path), "error", "DB does not exist"),
            )
        return {"ok": False, "error": "DB does not exist"}

    try:
        src = sqlite3.connect(config.DB_PATH)
        dst = sqlite3.connect(out_path)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()

        size = out_path.stat().st_size
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO backup_log(path, size_bytes, status) VALUES (?, ?, ?)",
                (str(out_path), size, "ok"),
            )

        prune_old_backups()
        return {"ok": True, "path": str(out_path), "size": size}
    except Exception as exc:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO backup_log(path, status, error) VALUES (?, ?, ?)",
                (str(out_path), "error", str(exc)),
            )
        return {"ok": False, "error": str(exc)}


def prune_old_backups() -> int:
    cutoff = datetime.now() - timedelta(days=config.BACKUP_RETENTION_DAYS)
    removed = 0
    for f in config.BACKUP_PATH.glob("control_panel_*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        run_backup,
        CronTrigger(hour=config.BACKUP_HOUR, minute=0),
        id="daily_backup",
        replace_existing=True,
    )
    _scheduler.start()


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
