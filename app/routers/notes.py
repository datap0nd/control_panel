from fastapi import APIRouter, HTTPException

from ..database import get_conn, row_to_dict, rows_to_list
from ..models import NoteIn, NoteUpdate

router = APIRouter()


@router.get("")
def list_notes():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY pinned DESC, updated_at DESC"
        ).fetchall()
    return rows_to_list(rows)


@router.get("/{note_id}")
def get_note(note_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        raise HTTPException(404, "note not found")
    return row_to_dict(row)


@router.post("")
def create_note(payload: NoteIn):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO notes(title, content, tags, pinned) VALUES(?,?,?,?)",
            (payload.title, payload.content, payload.tags, 1 if payload.pinned else 0),
        )
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.patch("/{note_id}")
def update_note(note_id: int, payload: NoteUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if "pinned" in fields:
        fields["pinned"] = 1 if fields["pinned"] else 0
    if not fields:
        return {"ok": False}
    sets = ", ".join(f"{k} = ?" for k in fields)
    sets += ", updated_at = datetime('now')"
    with get_conn() as conn:
        conn.execute(
            f"UPDATE notes SET {sets} WHERE id = ?",
            (*fields.values(), note_id),
        )
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        raise HTTPException(404, "note not found")
    return row_to_dict(row)


@router.delete("/{note_id}")
def delete_note(note_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return {"ok": True}
