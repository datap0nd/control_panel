from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .database import init_db
from .scheduler import shutdown_scheduler, start_scheduler
from .routers import (
    backup,
    dashboard,
    notes,
    scripts,
    settings,
    tasks,
    update,
)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.ensure_dirs()
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Control Panel", version=config.get_version(), lifespan=lifespan)

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(update.router, prefix="/api/update", tags=["update"])
app.include_router(backup.router, prefix="/api/backup", tags=["backup"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/api/health")
def health():
    return {"ok": True, "version": config.get_version()}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{path:path}")
def spa_fallback(path: str):
    target = STATIC_DIR / path
    if target.is_file():
        return FileResponse(target)
    return FileResponse(STATIC_DIR / "index.html")
