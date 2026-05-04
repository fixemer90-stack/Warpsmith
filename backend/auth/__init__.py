"""Auth: JWT-регистрация, вход, middleware. Production-ready.

Архитектура:
  - Пароли: bcrypt (passlib), не SHA-256
  - Токен: JWT (python-jose), хранится в httponly Secure SameSite=Lax cookie
  - Middleware: читает из cookie (веб-интерфейс) или Bearer header (API-клиенты)
  - Гость (без токена) → user_id=None для публичных страниц
  - Для создания/изменения данных обязателен JWT
"""

import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, Request

from backend.db.database import db

load_dotenv()

# ── Конфигурация ────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
GUEST_USER_ID = 1  # для просмотра публичных ростереров без регистрации

# ── Хеширование ──────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """bcrypt — production-ready, автоматически генерирует соль."""
    import bcrypt as _bcrypt

    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt as _bcrypt

    try:
        return _bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


# ── Валидация ────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def validate_password_strength(password: str) -> str | None:
    if len(password) < 6:
        return "Password must be at least 6 characters"
    if len(password) > 128:
        return "Password is too long"
    return None


# ── JWT ──────────────────────────────────────────────────────────


def create_jwt(user_id: int) -> str:
    """Создать JWT-токен с user_id в payload."""
    import jwt as pyjwt

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Декодировать JWT. Возвращает None при любой ошибке."""
    import jwt as pyjwt

    try:
        return dict(pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]))
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


# ── User model ───────────────────────────────────────────────────


class User:
    """Пользователь системы: id, email, display_name, tier."""

    def __init__(self, id: int, email: str, display_name: str, tier: str = "free"):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.tier = tier

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "display_name": self.display_name, "tier": self.tier}

    @classmethod
    def by_email(cls, email: str) -> Optional["User"]:
        row = db.fetchone(
            "SELECT id, email, display_name, tier FROM users WHERE email = ?",
            (email.strip().lower(),),
        )
        return cls(**row) if row else None

    @classmethod
    def by_id(cls, user_id: int) -> Optional["User"]:
        row = db.fetchone(
            "SELECT id, email, display_name, tier FROM users WHERE id = ?",
            (user_id,),
        )
        return cls(**row) if row else None

    @classmethod
    def register(cls, email: str, password: str, display_name: str = "") -> Optional["User"]:
        """Зарегистрировать нового пользователя. Возвращает None, если email занят."""
        email = email.strip().lower()
        if not display_name:
            display_name = email.split("@")[0]
        pw_hash = hash_password(password)
        # На localhost — сразу Premium для удобства тестирования
        is_local = os.getenv("HOSTING", "").lower() not in ("true", "1", "yes")
        tier = "premium" if is_local else "free"
        cur = db.execute(
            "INSERT INTO users (email, password_hash, display_name, tier) VALUES (?, ?, ?, ?)",
            (email, pw_hash, display_name, tier),
        )
        db.commit()
        return cls.by_id(cur.lastrowid)

    @classmethod
    def login(cls, email: str, password: str) -> Optional["User"]:
        """Проверить учётные данные. Возвращает User или None."""
        email = email.strip().lower()
        row = db.fetchone(
            "SELECT id, email, display_name, tier, password_hash FROM users WHERE email = ?",
            (email,),
        )
        if not row:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        # Обновить last_login
        db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
        db.commit()
        return cls.by_id(row["id"])


# ── Middleware ────────────────────────────────────────────────────


def _extract_token(request: Request) -> str | None:
    """Извлечь JWT из cookie (веб) или Authorization header (API)."""
    # 1. Cookie (веб-интерфейс)
    token = request.cookies.get("token")
    if token:
        return token
    # 2. Authorization: Bearer ... (API-клиенты)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def get_current_user(request: Request) -> User:
    """Depends — обязательная авторизация. HTTPException 401, если нет токена."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required — please log in")
    payload = decode_jwt(token)
    if payload is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token — please log in again"
        )
    user = User.by_id(payload["user_id"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_user_optional(request: Request) -> User | None:
    """Get current user or None if not authenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def get_optional_user(request: Request) -> User | None:
    """Depends — опциональный пользователь (публичные страницы)."""
    token = _extract_token(request)
    if not token:
        return None
    payload = decode_jwt(token)
    if payload is None:
        return None
    return User.by_id(payload["user_id"])


# ── Cookie helpers ───────────────────────────────────────────────


def make_auth_cookie(token: str, secure: bool = True) -> dict:
    """Параметры cookie для Set-Cookie header.

    Args:
        token: JWT-строка
        secure: True в production (HTTPS), False для localhost
    """
    return {
        "key": "token",
        "value": token,
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "max_age": TOKEN_EXPIRE_DAYS * 86400,
        "path": "/",
    }


def make_logout_cookie() -> dict:
    """Параметры cookie для удаления токена."""
    return {
        "key": "token",
        "value": "",
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "max_age": 0,
        "path": "/",
    }
