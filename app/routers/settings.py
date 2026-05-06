import os
from fastapi import APIRouter

from .. import config
from ..database import get_conn, rows_to_list
from ..models import SettingIn

router = APIRouter()


@router.get("")
def get_settings():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM settings ORDER BY key").fetchall()
    return {
        "env": {
            "CP_DB_PATH": str(config.DB_PATH),
            "CP_SCRIPTS_PATH": str(config.SCRIPTS_PATH),
            "CP_PBI_PATH": str(config.PBI_PATH),
            "CP_BACKUP_PATH": str(config.BACKUP_PATH),
            "CP_LOGS_PATH": str(config.LOGS_PATH),
            "CP_BACKUP_HOUR": str(config.BACKUP_HOUR),
            "CP_BACKUP_RETENTION_DAYS": str(config.BACKUP_RETENTION_DAYS),
            "CP_PORT": str(config.PORT),
            "CP_REPO_URL": config.REPO_URL,
            "CP_GOVERNANCE_URL": config.GOVERNANCE_URL or "(not set)",
            "CP_GOVERNANCE_USER": config.GOVERNANCE_USER or "(not set)",
        },
        "version": config.get_version(),
        "user_settings": rows_to_list(rows),
        "scripts_path_exists": config.SCRIPTS_PATH.exists(),
        "db_size_bytes": config.DB_PATH.stat().st_size if config.DB_PATH.exists() else 0,
    }


@router.put("")
def set_setting(payload: SettingIn):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
            (payload.key, payload.value),
        )
    return {"ok": True}


@router.delete("/{key}")
def delete_setting(key: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    return {"ok": True}
