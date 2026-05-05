import json
import subprocess
import time
from pathlib import Path
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .. import config
from ..database import get_conn, rows_to_list
from ..models import ScriptRunRequest

router = APIRouter()

ALLOWED_EXTS = {".ps1", ".py", ".bat", ".cmd", ".sh"}


def _safe_path(rel_path: str) -> Path:
    base = config.SCRIPTS_PATH.resolve()
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


@router.get("")
def list_scripts():
    base = config.SCRIPTS_PATH
    if not base.exists():
        return {"scripts_path": str(base), "scripts": [], "exists": False}
    items = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in ALLOWED_EXTS:
            continue
        rel = str(f.relative_to(base)).replace("\\", "/")
        meta = _meta_for(f)
        items.append({
            "path": rel,
            "name": meta.get("name") or f.stem,
            "description": meta.get("description"),
            "args_help": meta.get("args"),
            "language": f.suffix.lstrip(".").lower(),
            "size_bytes": f.stat().st_size,
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime)),
        })
    return {"scripts_path": str(base), "scripts": items, "exists": True}


@router.get("/runs")
def list_runs(limit: int = 50, script: str | None = None):
    sql = "SELECT * FROM script_runs"
    params: tuple = ()
    if script:
        sql += " WHERE script_path = ?"
        params = (script,)
    sql += " ORDER BY started_at DESC LIMIT ?"
    params = params + (limit,)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_list(rows)


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM script_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise HTTPException(404, "run not found")
    return dict(row)


def _build_command(path: Path, args: str | None) -> list[str]:
    ext = path.suffix.lower()
    arg_list = args.split() if args else []
    if ext == ".ps1":
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path), *arg_list]
    if ext == ".py":
        import sys
        return [sys.executable, str(path), *arg_list]
    if ext in {".bat", ".cmd"}:
        return ["cmd", "/c", str(path), *arg_list]
    if ext == ".sh":
        return ["bash", str(path), *arg_list]
    raise HTTPException(400, f"no runner for {ext}")


@router.post("/run")
def run_script(payload: ScriptRunRequest):
    path = _safe_path(payload.script_path)
    cmd = _build_command(path, payload.args)
    started = time.time()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO script_runs(script_path, args) VALUES(?,?)",
            (payload.script_path, payload.args),
        )
        run_id = cur.lastrowid
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=payload.timeout_seconds,
            cwd=path.parent,
        )
        duration = time.time() - started
        with get_conn() as conn:
            conn.execute(
                "UPDATE script_runs SET finished_at = datetime('now'), exit_code = ?, "
                "stdout = ?, stderr = ?, duration_seconds = ? WHERE id = ?",
                (proc.returncode, proc.stdout, proc.stderr, duration, run_id),
            )
        return {
            "ok": True,
            "run_id": run_id,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_seconds": duration,
        }
    except subprocess.TimeoutExpired:
        with get_conn() as conn:
            conn.execute(
                "UPDATE script_runs SET finished_at = datetime('now'), exit_code = -1, "
                "stderr = ?, duration_seconds = ? WHERE id = ?",
                ("Timeout", payload.timeout_seconds, run_id),
            )
        raise HTTPException(408, "script timed out")
    except Exception as exc:
        with get_conn() as conn:
            conn.execute(
                "UPDATE script_runs SET finished_at = datetime('now'), exit_code = -1, "
                "stderr = ? WHERE id = ?",
                (str(exc), run_id),
            )
        raise HTTPException(500, str(exc))


@router.post("/run/stream")
def run_script_stream(payload: ScriptRunRequest):
    path = _safe_path(payload.script_path)
    cmd = _build_command(path, payload.args)

    def generate() -> Iterator[bytes]:
        started = time.time()
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO script_runs(script_path, args) VALUES(?,?)",
                (payload.script_path, payload.args),
            )
            run_id = cur.lastrowid
        yield f"event: start\ndata: {json.dumps({'run_id': run_id})}\n\n".encode()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=path.parent,
        )
        captured: list[str] = []
        try:
            for line in proc.stdout:  # type: ignore[union-attr]
                captured.append(line)
                yield f"data: {json.dumps({'line': line.rstrip()})}\n\n".encode()
        finally:
            code = proc.wait()
            duration = time.time() - started
            with get_conn() as conn:
                conn.execute(
                    "UPDATE script_runs SET finished_at = datetime('now'), exit_code = ?, "
                    "stdout = ?, duration_seconds = ? WHERE id = ?",
                    (code, "".join(captured), duration, run_id),
                )
            yield f"event: end\ndata: {json.dumps({'exit_code': code, 'duration': duration})}\n\n".encode()

    return StreamingResponse(generate(), media_type="text/event-stream")
