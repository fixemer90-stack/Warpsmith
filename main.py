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
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.db.database import db
from backend.loader.icon_map import CATEGORY_COLORS, get_card_style, get_icon_html
from backend.logging_setup import RequestLoggingMiddleware, setup_logging, setup_sentry
from backend.security.headers import CSPMiddleware, SecurityHeadersMiddleware

# ── Rate limiter ──────────────────────────────────────────────────


def _rate_limit_key(request: Request) -> str:
    """Use user from request.state if available, else remote IP."""
    if hasattr(request.state, "user") and request.state.user:
        return str(request.state.user)
    return get_remote_address(request)


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[os.getenv("RATE_LIMIT_ANON", "30/minute")],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
    headers_enabled=True,
)


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

    # CORS — production-aware
    if IS_PRODUCTION:
        production_origin = os.getenv(
            "PRODUCTION_ORIGIN", "https://warpsmith-production.up.railway.app"
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[production_origin],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            allow_headers=["Content-Type", "Authorization"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    # app.add_middleware(CSPMiddleware)  # отключено для локальной разработки

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Templates — inject into app state for routes
    app.state.templates = templates

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Index route
    @app.get("/", response_class=HTMLResponse)
    @limiter.limit(os.getenv("RATE_LIMIT_ANON", "30/minute"))
    async def index(request: Request):
        return templates.TemplateResponse(request, "index.html", {"request": request})

    # DB init
    db.migrate()

    # Импортируем роуты (lazy, чтобы избежать циклических импортов)
    from backend.auth.providers.routes import router as oauth_router
    from backend.billing.webhooks import router as billing_router
    from web.routes import api, api_detachments, api_replays, api_rosters, pages
    from web.routes import auth as auth_routes

    app.include_router(pages.router)
    app.include_router(api.router, prefix="/api")
    app.include_router(api_detachments.router, prefix="/api")
    app.include_router(api_replays.router, prefix="/api")
    app.include_router(api_rosters.router, prefix="/api")
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

    # Healthcheck — exempt from rate limiting
    @app.get("/health")
    @limiter.exempt
    async def health_check():
        return {"status": "ok"}

    # Favicon
    @app.get("/favicon.ico")
    async def favicon():
        return RedirectResponse("/static/favicon.svg")

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
