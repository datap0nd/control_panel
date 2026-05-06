import json
import urllib.error
import urllib.request

from fastapi import APIRouter, HTTPException

from .. import config
from ..database import get_conn, row_to_dict, rows_to_list
from ..models import TaskIn, TaskMove, TaskUpdate

router = APIRouter()


@router.get("/governance")
def governance_tasks():
    """Live-fetch tasks from a Data Governance instance, filtered by assignee.

    Configured via:
      CP_GOVERNANCE_URL  e.g. http://192.168.1.50:8000
      CP_GOVERNANCE_USER e.g. Rafael (case-insensitive contains match against task.assignee)
    """
    if not config.GOVERNANCE_URL:
        return {"configured": False, "tasks": [], "error": "CP_GOVERNANCE_URL not set"}
    url = f"{config.GOVERNANCE_URL}/api/tasks"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ControlPanel"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return {"configured": True, "url": url, "tasks": [], "error": f"connection: {exc}"}
    except Exception as exc:
        return {"configured": True, "url": url, "tasks": [], "error": str(exc)}

    # Governance returns either {tasks: [...]} or [...] depending on version
    items = payload.get("tasks") if isinstance(payload, dict) else payload
    items = items or []

    user = (config.GOVERNANCE_USER or "").lower()
    if user:
        # Match against multiple possible field names. Governance currently uses 'assigned_to'.
        # Case-insensitive contains so "Rafael" matches "Rafael Cunha" etc.
        def _matches(t):
            for field in ("assigned_to", "assignee", "owner"):
                v = str(t.get(field) or "").lower()
                if user in v:
                    return True
            return False
        items = [t for t in items if _matches(t)]

    return {
        "configured": True,
        "url": url,
        "filter_user": config.GOVERNANCE_USER or None,
        "count": len(items),
        "tasks": items,
    }


@router.get("")
def list_tasks():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY status, position, id"
        ).fetchall()
    return rows_to_list(rows)


@router.post("")
def create_task(payload: TaskIn):
    with get_conn() as conn:
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS p FROM tasks WHERE status = ?",
            (payload.status,),
        ).fetchone()["p"]
        cur = conn.execute(
            "INSERT INTO tasks(title, description, status, priority, due_date, position) "
            "VALUES(?,?,?,?,?,?)",
            (
                payload.title,
                payload.description,
                payload.status,
                payload.priority,
                payload.due_date,
                max_pos,
            ),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not fields:
        return {"ok": False, "error": "no fields to update"}
    sets = ", ".join(f"{k} = ?" for k in fields)
    sets += ", updated_at = datetime('now')"
    with get_conn() as conn:
        conn.execute(
            f"UPDATE tasks SET {sets} WHERE id = ?",
            (*fields.values(), task_id),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(404, "task not found")
    return row_to_dict(row)


@router.patch("/{task_id}/move")
def move_task(task_id: int, payload: TaskMove):
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, position = ?, updated_at = datetime('now') WHERE id = ?",
            (payload.status, payload.position, task_id),
        )
    return {"ok": True}


@router.delete("/{task_id}")
def delete_task(task_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return {"ok": True}
