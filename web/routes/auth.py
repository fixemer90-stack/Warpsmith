"""Auth routes: /register, /login, /logout, /me.

Для production:
  - Формы → POST /auth/register и POST /auth/login
  - Выход → GET /auth/logout (редирект на /)
  - Текущий пользователь → GET /auth/me (JSON)
  - Алиас → GET /api/me (тот же handler)
  - Cookie: httponly + Secure + SameSite=Lax
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.auth import (
    User,
    create_jwt,
    get_current_user,
    get_optional_user,
    make_auth_cookie,
    make_logout_cookie,
    validate_email,
    validate_password_strength,
)
from backend.loader.icon_map import CATEGORY_COLORS, get_card_style, get_icon_html

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
# Jinja2 globals для карточек юнитов
templates.env.globals["unit_icon"] = get_icon_html
templates.env.globals["card_style"] = get_card_style
templates.env.globals["CATEGORY_COLORS"] = CATEGORY_COLORS

# Определяем, HTTPS ли мы (production) или localhost
_IS_SECURE = os.getenv("HOSTING", "").lower() in ("true", "1", "yes")


# ── Страницы ─────────────────────────────────────────────────────


@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Форма входа."""
    return templates.TemplateResponse(request, "auth/login.html", {"request": request})


@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Форма регистрации."""
    return templates.TemplateResponse(request, "auth/register.html", {"request": request})


# ── Регистрация ──────────────────────────────────────────────────


@router.post("/auth/register")
async def register(request: Request):
    """Регистрация нового пользователя. → редирект на /team-builder."""
    data = await request.form()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    display_name = str(data.get("display_name", "")).strip()

    # Валидация
    if not email:
        raise HTTPException(400, "Email is required")
    if not validate_email(email):
        raise HTTPException(400, "Invalid email format")
    pw_err = validate_password_strength(password)
    if pw_err:
        raise HTTPException(400, pw_err)

    # Проверка существования
    if User.by_email(email):
        raise HTTPException(409, "This email is already registered — please log in instead")

    user = User.register(email, password, display_name)
    if user is None:
        raise HTTPException(500, "Registration failed — please try again")

    # Успех: JWT + редирект
    token = create_jwt(user.id)
    resp = RedirectResponse(url="/team-builder", status_code=302)
    resp.set_cookie(**make_auth_cookie(token, secure=_IS_SECURE))
    return resp


# ── Вход ─────────────────────────────────────────────────────────


@router.post("/auth/login")
async def login(request: Request):
    """Вход. → редирект на /team-builder."""
    data = await request.form()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        raise HTTPException(400, "Email and password are required")

    user = User.login(email, password)
    if user is None:
        raise HTTPException(401, "Invalid email or password")

    token = create_jwt(user.id)
    resp = RedirectResponse(url="/team-builder", status_code=302)
    resp.set_cookie(**make_auth_cookie(token, secure=_IS_SECURE))
    return resp


# ── Выход ────────────────────────────────────────────────────────


@router.get("/auth/logout")
async def logout():
    """Удалить cookie и редирект на главную."""
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie(**make_logout_cookie())
    return resp


# ── Текущий пользователь ─────────────────────────────────────────


@router.get("/auth/me")
async def me(request: Request, user=Depends(get_optional_user)):
    """JSON с данными текущего пользователя (или null)."""
    if user is None:
        return JSONResponse(None, status_code=200)
    return JSONResponse(user.to_dict())


@router.get("/api/me")
async def api_me(request: Request, user=Depends(get_optional_user)):
    """Алиас /api/me для Alpine.js в base.html."""
    if user is None:
        return JSONResponse(None, status_code=200)
    return JSONResponse(user.to_dict())


# ── Health check ─────────────────────────────────────────────────


@router.get("/api/health")
async def health():
    return JSONResponse({"status": "ok"})
