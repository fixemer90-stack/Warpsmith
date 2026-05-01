"""OAuth routes: /auth/{provider}/login, /auth/{provider}/callback.

Поток:
  1. GET /auth/google/login → редирект на Google OAuth
  2. Google → code → GET /auth/google/callback → JWT cookie → /
"""

import os
import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.auth import User, create_jwt, make_auth_cookie
from backend.auth.providers.base import get_provider, list_providers
from backend.db.database import db

router = APIRouter(prefix="/auth", tags=["oauth"])
templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent.parent / "web" / "templates")
)

_SECURE = os.getenv("HOSTING", "").lower() in ("true", "1", "yes")


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Шаг 1: редирект на OAuth-сервер провайдера."""
    try:
        prov = get_provider(provider)
    except Exception as e:
        raise HTTPException(400, str(e)) from e

    state = secrets.token_urlsafe(32)
    # Сохраняем state в сессии (для проверки при callback)
    request.session["oauth_state"] = state

    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    auth_url = prov.get_authorize_url(redirect_uri, state)
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, code: str = "", state: str = ""):
    """Шаг 2: OAuth-сервер редиректит сюда с code.

    1. Проверяем state (CSRF)
    2. Обмениваем code на access_token
    3. Получаем профиль пользователя
    4. Ищем/создаём user в БД + oauth_accounts
    5. Выдаём JWT → Set-Cookie → редирект
    """
    # CSRF check
    saved_state = request.session.get("oauth_state", "")
    if saved_state and state != saved_state:
        raise HTTPException(400, "State mismatch — possible CSRF")

    if not code:
        raise HTTPException(400, "No authorization code received")

    try:
        prov = get_provider(provider)
    except Exception as e:
        raise HTTPException(400, str(e)) from e

    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    # Обмен code → token
    token_data = await prov.exchange_code(code, redirect_uri)
    access_token = token_data.get("access_token", "")

    if not access_token:
        raise HTTPException(400, "No access token received from provider")

    # Получить профиль
    user_info = await prov.get_user_info(access_token)

    # Ищем существующую связку
    row = db.fetchone(
        "SELECT user_id FROM oauth_accounts WHERE provider = ? AND provider_user_id = ?",
        (provider, user_info.sub),
    )

    if row:
        # Уже привязан — логиним этого пользователя
        user = User.by_id(row["user_id"])
    else:
        # Новый OAuth-вход
        # Пытаемся привязать к существующему email
        if user_info.email:
            existing = User.by_email(user_info.email)
            if existing:
                user = existing
            else:
                user = User.register(
                    user_info.email, secrets.token_urlsafe(16), user_info.display_name
                )
        else:
            # VK не отдаёт email — создаём пользователя без пароля
            user = User.register(
                f"{provider}_{user_info.sub}@social.local",
                secrets.token_urlsafe(16),
                user_info.display_name,
            )

        if user is None:
            raise HTTPException(500, "Failed to create/link user account")

        # Сохраняем привязку
        db.execute(
            "INSERT OR IGNORE INTO oauth_accounts (user_id, provider, provider_user_id, access_token) VALUES (?, ?, ?, ?)",
            (user.id, provider, user_info.sub, access_token),
        )
        db.commit()

    # Выдать JWT
    assert user is not None  # checked above
    token = create_jwt(user.id)
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(**make_auth_cookie(token, secure=_SECURE))
    return resp


@router.get("/providers")
async def auth_providers():
    """Список доступных OAuth-провайдеров (для UI)."""
    return JSONResponse(list_providers())
