import json
import subprocess
import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .. import config
from ..database import get_conn
from ..models import ScriptRunRequest

router = APIRouter()

ALLOWED_EXTS = {".ps1", ".py", ".bat", ".cmd", ".sh"}


def _effective_scripts_path() -> Path:
    """DB override (settings.scripts_path) wins, else CP_SCRIPTS_PATH env default."""
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='scripts_path'").fetchone()
    if row and row["value"]:
        return Path(row["value"])
    return config.SCRIPTS_PATH


def _safe_path(rel_path: str) -> Path:
    base = _effective_scripts_path().resolve()
    candidate = (base / rel_path).resolve()
    if not str(candidate).startswith(str(base)):
        raise HTTPException(400, "path escapes scripts root")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(404, "script not found")
    if candidate.suffix.lower() not in ALLOWED_EXTS:
        raise HTTPException(400, f"unsupported extension: {candidate.suffix}")
    return candidate


def _meta_for(path: Path) -> dict:
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if not meta_path.exists():
        meta_path = path.with_name(path.stem + ".meta.json")
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


@router.get("/path")
def get_path():
    eff = _effective_scripts_path()
    is_override = eff.resolve() != config.SCRIPTS_PATH.resolve()
    return {
        "path": str(eff),
        "exists": eff.exists(),
        "default_path": str(config.SCRIPTS_PATH),
        "is_override": is_override,
    }


@router.put("/path")
def set_path(payload: dict):
    raw = (payload.get("path") or "").strip().strip('"')
    if not raw:
        raise HTTPException(400, "path required")
    p = Path(raw)
    if not p.exists() or not p.is_dir():
        raise HTTPException(400, f"folder does not exist or not a directory: {raw}")
    resolved = str(p.resolve())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES('scripts_path', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
            (resolved,),
        )
    return {"ok": True, "path": resolved}


@router.delete("/path")
def reset_path():
    with get_conn() as conn:
        conn.execute("DELETE FROM settings WHERE key='scripts_path'")
    return {"ok": True, "path": str(config.SCRIPTS_PATH)}


@router.get("")
def list_scripts(include_archived: bool = False):
    base = _effective_scripts_path()
    if not base.exists():
        return {"scripts_path": str(base), "scripts": [], "exists": False}

    with get_conn() as conn:
        db_meta = {r["script_path"]: dict(r) for r in
                   conn.execute("SELECT * FROM script_metadata").fetchall()}

    items = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in ALLOWED_EXTS:
            continue
        rel = str(f.relative_to(base)).replace("\\", "/")
        sidecar = _meta_for(f)
        db = db_meta.get(rel, {})
        archived = bool(db.get("archived", 0))
        if archived and not include_archived:
            continue
        items.append({
            "path": rel,
            "name": db.get("name") or sidecar.get("name") or f.stem,
            "description": db.get("description") or sidecar.get("description"),
            "archived": archived,
            "has_db_override": rel in db_meta,
            "language": f.suffix.lstrip(".").lower(),
            "size_bytes": f.stat().st_size,
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime)),
        })
    archived_count = sum(1 for r in db_meta.values() if r.get("archived"))
    return {"scripts_path": str(base), "scripts": items, "exists": True, "archived_count": archived_count}


@router.patch("/metadata")
def update_metadata(payload: dict):
    """Set/clear DB-backed metadata for a script. Body: {path, name?, description?, archived?}"""
    rel = (payload.get("path") or "").strip()
    if not rel:
        raise HTTPException(400, "path required")
    name = payload.get("name")
    description = payload.get("description")
    archived = payload.get("archived")
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM script_metadata WHERE script_path = ?", (rel,)
        ).fetchone()
        if existing:
            fields = []
            vals = []
            for k, v in [("name", name), ("description", description),
                         ("archived", 1 if archived else 0 if archived is False else None)]:
                if v is not None:
                    fields.append(f"{k} = ?")
                    vals.append(v)
            if fields:
                fields.append("updated_at = datetime('now')")
                vals.append(rel)
                conn.execute(f"UPDATE script_metadata SET {', '.join(fields)} WHERE script_path = ?", vals)
        else:
            conn.execute(
                "INSERT INTO script_metadata(script_path, name, description, archived) "
                "VALUES(?, ?, ?, ?)",
                (rel, name, description, 1 if archived else 0),
            )
    return {"ok": True}


@router.delete("/metadata/{path:path}")
def clear_metadata(path: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM script_metadata WHERE script_path = ?", (path,))
    return {"ok": True}


def _runner_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".ps1":
        return f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{path}"'
    if ext == ".py":
        return f'python "{path}"'
    if ext in {".bat", ".cmd"}:
        return f'"{path}"'
    if ext == ".sh":
        return f'bash "{path}"'
    raise HTTPException(400, f"no runner for {ext}")


@router.post("/run")
def run_script(payload: ScriptRunRequest):
    """Open a cmd window in the user's interactive session and run the script.

    Service lives in session 0 (no desktop), so subprocess.Popen cannot show a
    window. Same Task Scheduler trick as the Update flow: schtasks /IT runs
    in the logged-on user's session. cmd.exe /K keeps the window open after
    the script exits so the user can read output.
    """
    if sys.platform != "win32":
        raise HTTPException(400, "Windows only")

    path = _safe_path(payload.script_path)
    runner = _runner_for(path)
    task_name = "ControlPanelScript"
    tr = f'cmd.exe /K {runner}'

    subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"],
                   capture_output=True, timeout=10)
    create = subprocess.run(
        ["schtasks", "/Create", "/TN", task_name,
         "/TR", tr, "/SC", "ONCE", "/ST", "00:00", "/IT", "/F"],
        capture_output=True, text=True, timeout=30,
    )
    if create.returncode != 0:
        raise HTTPException(500, f"create task failed: {(create.stdout + create.stderr).strip()}")
    run = subprocess.run(
        ["schtasks", "/Run", "/TN", task_name],
        capture_output=True, text=True, timeout=10,
    )
    if run.returncode != 0:
        raise HTTPException(500, f"run task failed: {(run.stdout + run.stderr).strip()}")
    return {"ok": True}
