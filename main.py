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

# ── Конфигурация ─────────────────────────────────────────────────

IS_PRODUCTION = os.getenv("HOSTING", "").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app = FastAPI(
    title="WH40k Battle Simulator",
    version="0.2.0",
    description="Симулятор сценариев боёв Warhammer 40,000 — сбор армии, AI-vs-AI бой, пораундовый реплей.",
)

# ── CORS ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Templates ────────────────────────────────────────────────────

templates = Jinja2Templates(directory=str(Path(__file__).parent / "web" / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Factory ──────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Инициализация: БД, роуты, статика."""
    db.migrate()
    if IS_PRODUCTION:
        pass
    else:
        pass

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

    return app


if __name__ == "__main__":
    import uvicorn

    create_app()
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0" if IS_PRODUCTION else "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=not IS_PRODUCTION,
    )
