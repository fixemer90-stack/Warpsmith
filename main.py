"""
WH40k Battle Simulator — веб-приложение на FastAPI.
Production: python main.py
Dev:       python main.py  (работает на localhost без CORS-проблем)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.db.database import db
from backend.loader.icon_map import CATEGORY_COLORS, get_card_style, get_icon_html
from backend.logging_setup import RequestLoggingMiddleware, setup_logging, setup_sentry

# ── Конфигурация ─────────────────────────────────────────────────

IS_PRODUCTION = os.getenv("HOSTING", "").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
).split(",")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "web" / "templates"))
# Jinja2 globals — для использования в шаблонах карточек юнитов
templates.env.globals["unit_icon"] = get_icon_html
templates.env.globals["card_style"] = get_card_style
templates.env.globals["CATEGORY_COLORS"] = CATEGORY_COLORS


def create_app() -> FastAPI:
    """Создать и настроить FastAPI приложение."""
    # Настройка логирования до создания app
    is_production = os.getenv("HOSTING", "").lower() in ("true", "1", "yes")
    log_level = os.getenv("LOG_LEVEL", "INFO" if is_production else "DEBUG")
    setup_logging(level=log_level)
    setup_sentry(
        dsn=os.getenv("SENTRY_DSN"),
        environment="production" if is_production else "development",
    )

    app = FastAPI(
        title="Warpsmith — WH40k Battle Simulator",
        version="0.3.0",
        description="Warpsmith — симулятор сценариев боёв Warhammer 40,000: сбор армии, AI-vs-AI бой, пораундовый реплей.",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Templates — inject into app state for routes
    app.state.templates = templates

    # Index route
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(request, "index.html", {"request": request})

    # DB init
    db.migrate()

    # Импортируем роуты (lazy, чтобы избежать циклических импортов)
    from backend.auth.providers.routes import router as oauth_router
    from backend.billing.webhooks import router as billing_router
    from web.routes import api, pages
    from web.routes import auth as auth_routes

    app.include_router(pages.router)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth_routes.router)
    app.include_router(billing_router)
    app.include_router(oauth_router)

    # Статика
    static_dir = Path(__file__).parent / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Healthcheck для Sentry
    @app.get("/sentry-debug")
    async def trigger_error():
        division_by_zero = 1 / 0  # noqa

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=not IS_PRODUCTION,
    )
