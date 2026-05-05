from fastapi import APIRouter, HTTPException

from ..database import get_conn, row_to_dict, rows_to_list
from ..models import TaskIn, TaskMove, TaskUpdate

router = APIRouter()


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
