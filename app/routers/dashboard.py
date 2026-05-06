from fastapi import APIRouter

from .. import config
from ..database import get_conn, rows_to_list

router = APIRouter()


@router.get("")
def overview():
    with get_conn() as conn:
        tasks_by_status = {
            r["status"]: r["n"]
            for r in conn.execute(
                "SELECT status, COUNT(*) AS n FROM tasks GROUP BY status"
            )
        }

        last_backup = conn.execute(
            "SELECT path, status, size_bytes, created_at "
            "FROM backup_log ORDER BY created_at DESC LIMIT 1"
        ).fetchone()

        notes_total = conn.execute("SELECT COUNT(*) AS n FROM notes").fetchone()["n"]

        upcoming_due = conn.execute(
            "SELECT id, title, due_date, priority FROM tasks "
            "WHERE due_date IS NOT NULL AND status != 'done' "
            "ORDER BY due_date ASC LIMIT 5"
        ).fetchall()

        custom_metrics = conn.execute(
            "SELECT key, label, value, unit, updated_at FROM metrics ORDER BY label"
        ).fetchall()

    return {
        "version": config.get_version(),
        "tasks": {
            "backlog": tasks_by_status.get("backlog", 0),
            "doing": tasks_by_status.get("doing", 0),
            "done": tasks_by_status.get("done", 0),
        },
        "last_backup": dict(last_backup) if last_backup else None,
        "notes_total": notes_total,
        "upcoming_due": rows_to_list(upcoming_due),
        "custom_metrics": rows_to_list(custom_metrics),
    }


@router.put("/metrics")
def upsert_metric(payload: dict):
    key = payload.get("key")
    label = payload.get("label")
    value = payload.get("value")
    unit = payload.get("unit")
    if not key or label is None or value is None:
        return {"ok": False, "error": "key, label, value required"}
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO metrics(key, label, value, unit) VALUES(?,?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET label=excluded.label, value=excluded.value, "
            "unit=excluded.unit, updated_at=datetime('now')",
            (key, label, float(value), unit),
        )
    return {"ok": True}


@router.delete("/metrics/{key}")
def delete_metric(key: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM metrics WHERE key = ?", (key,))
    return {"ok": True}
