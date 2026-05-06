from typing import Literal, Optional
from pydantic import BaseModel, Field


TaskStatus = Literal["backlog", "doing", "done"]
TaskPriority = Literal["low", "normal", "high"]


class TaskIn(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = "backlog"
    priority: TaskPriority = "normal"
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[str] = None
    position: Optional[int] = None


class TaskMove(BaseModel):
    status: TaskStatus
    position: int


class NoteIn(BaseModel):
    title: str
    content: str = ""
    tags: Optional[str] = None
    pinned: bool = False


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    pinned: Optional[bool] = None


class ScriptRunRequest(BaseModel):
    script_path: str


class SettingIn(BaseModel):
    key: str
    value: str


class MetricIn(BaseModel):
    key: str
    label: str
    value: float
    unit: Optional[str] = None
