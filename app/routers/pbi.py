import subprocess
import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .. import config
from ..database import get_conn

router = APIRouter()

ALLOWED_EXTS = {".pbix", ".pbip", ".pbit"}


def _effective_pbi_path() -> Path:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='pbi_path'").fetchone()
    if row and row["value"]:
        return Path(row["value"])
    return config.PBI_PATH


def _safe_path(rel: str) -> Path:
    base = _effective_pbi_path().resolve()
    candidate = (base / rel).resolve()
    if not str(candidate).startswith(str(base)):
        raise HTTPException(400, "path escapes pbi root")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(404, "file not found")
    if candidate.suffix.lower() not in ALLOWED_EXTS:
        raise HTTPException(400, f"unsupported extension: {candidate.suffix}")
    return candidate


@router.get("/path")
def get_path():
    eff = _effective_pbi_path()
    return {
        "path": str(eff),
        "exists": eff.exists(),
        "default_path": str(config.PBI_PATH),
        "is_override": eff.resolve() != config.PBI_PATH.resolve(),
    }


@router.put("/path")
def set_path(payload: dict):
    raw = (payload.get("path") or "").strip().strip('"')
    if not raw:
        raise HTTPException(400, "path required")
    p = Path(raw)
    if not p.exists() or not p.is_dir():
        raise HTTPException(400, f"folder does not exist: {raw}")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES('pbi_path', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
            (str(p.resolve()),),
        )
    return {"ok": True, "path": str(p.resolve())}


@router.delete("/path")
def reset_path():
    with get_conn() as conn:
        conn.execute("DELETE FROM settings WHERE key='pbi_path'")
    return {"ok": True}


@router.get("")
def list_pbi(include_archived: bool = False):
    base = _effective_pbi_path()
    if not base.exists():
        return {"pbi_path": str(base), "files": [], "exists": False}

    with get_conn() as conn:
        db_meta = {r["file_path"]: dict(r) for r in
                   conn.execute("SELECT * FROM pbi_metadata").fetchall()}

    items = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in ALLOWED_EXTS:
            continue
        rel = str(f.relative_to(base)).replace("\\", "/")
        db = db_meta.get(rel, {})
        archived = bool(db.get("archived", 0))
        if archived and not include_archived:
            continue
        stat = f.stat()
        items.append({
            "path": rel,
            "name": db.get("name") or f.stem,
            "description": db.get("description"),
            "archived": archived,
            "has_db_override": rel in db_meta,
            "kind": f.suffix.lstrip(".").lower(),
            "size_bytes": stat.st_size,
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        })
    archived_count = sum(1 for r in db_meta.values() if r.get("archived"))
    return {"pbi_path": str(base), "files": items, "exists": True, "archived_count": archived_count}


@router.patch("/metadata")
def update_metadata(payload: dict):
    rel = (payload.get("path") or "").strip()
    if not rel:
        raise HTTPException(400, "path required")
    name = payload.get("name")
    description = payload.get("description")
    archived = payload.get("archived")
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM pbi_metadata WHERE file_path = ?", (rel,)).fetchone()
        if existing:
            fields, vals = [], []
            for k, v in [("name", name), ("description", description),
                         ("archived", 1 if archived else 0 if archived is False else None)]:
                if v is not None:
                    fields.append(f"{k} = ?")
                    vals.append(v)
            if fields:
                fields.append("updated_at = datetime('now')")
                vals.append(rel)
                conn.execute(f"UPDATE pbi_metadata SET {', '.join(fields)} WHERE file_path = ?", vals)
        else:
            conn.execute(
                "INSERT INTO pbi_metadata(file_path, name, description, archived) VALUES(?, ?, ?, ?)",
                (rel, name, description, 1 if archived else 0),
            )
    return {"ok": True}


@router.post("/open")
def open_file(payload: dict):
    """Open a .pbix/.pbip in the user's interactive session via schtasks (same trick as the Update flow)."""
    if sys.platform != "win32":
        return {"ok": False, "error": "Windows only"}

    rel = (payload.get("path") or "").strip()
    if not rel:
        raise HTTPException(400, "path required")
    full = _safe_path(rel)

    task_name = "ControlPanelOpenPBI"
    # cmd /c start "" "<file>" launches with the OS-default app (PBI Desktop)
    tr = f'cmd.exe /c start "" "{full}"'

    subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"], capture_output=True, timeout=10)
    create = subprocess.run(
        ["schtasks", "/Create", "/TN", task_name, "/TR", tr,
         "/SC", "ONCE", "/ST", "00:00", "/IT", "/F"],
        capture_output=True, text=True, timeout=30,
    )
    if create.returncode != 0:
        return {"ok": False, "error": (create.stderr + create.stdout).strip()}
    run = subprocess.run(["schtasks", "/Run", "/TN", task_name],
                         capture_output=True, text=True, timeout=10)
    if run.returncode != 0:
        return {"ok": False, "error": (run.stderr + run.stdout).strip()}
    return {"ok": True, "message": f"Opening {rel} in Power BI Desktop"}
