from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .. import config
from ..database import get_conn, rows_to_list
from ..scheduler import prune_old_backups, run_backup

router = APIRouter()


@router.get("")
def list_backups():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM backup_log ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    files = []
    if config.BACKUP_PATH.exists():
        for f in sorted(config.BACKUP_PATH.glob("control_panel_*.db"), reverse=True):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
            })
    return {
        "backup_path": str(config.BACKUP_PATH),
        "retention_days": config.BACKUP_RETENTION_DAYS,
        "scheduled_hour": config.BACKUP_HOUR,
        "files": files,
        "log": rows_to_list(rows),
    }


@router.post("/run")
def manual_backup():
    return run_backup()


@router.post("/prune")
def manual_prune():
    return {"removed": prune_old_backups()}


@router.get("/download/{name}")
def download_backup(name: str):
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, "invalid name")
    path = config.BACKUP_PATH / name
    if not path.exists():
        raise HTTPException(404, "backup not found")
    return FileResponse(path, filename=name, media_type="application/octet-stream")
