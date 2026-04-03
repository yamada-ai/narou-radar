from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings, load_topics
from app.services.pipeline import IngestionService
from app.storage.duckdb_repo import DuckDBRepository

settings = get_settings()
app = FastAPI(title=settings.app_name)

templates = Jinja2Templates(directory="app/templates")
if Path("app/static").exists():
    app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    repo = DuckDBRepository(settings.db_path)
    repo.migrate()
    themes = repo.list_latest_themes()
    repo.close()
    return templates.TemplateResponse("index.html", {"request": request, "themes": themes})


@app.get("/themes/{theme}", response_class=HTMLResponse)
def theme_detail(theme: str, request: Request) -> HTMLResponse:
    repo = DuckDBRepository(settings.db_path)
    repo.migrate()
    detail = repo.get_theme_detail(theme)
    repo.close()
    return templates.TemplateResponse("theme_detail.html", {"request": request, "theme": theme, "detail": detail})


@app.post("/admin/update")
def run_update(selected_theme: str = Form(default="all")) -> RedirectResponse:
    topics = load_topics()
    if selected_theme != "all":
        topics = [t for t in topics if t.slug == selected_theme]
    ingestion = IngestionService(settings, topics)
    ingestion.run_daily_snapshot()
    return RedirectResponse(url="/", status_code=303)
