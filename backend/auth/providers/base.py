"""OAuthProvider — абстрактный интерфейс для провайдеров.

Любой новый OAuth-провайдер реализует этот класс.
Достаточно добавить файл в backend/auth/providers/ и зарегистрировать в PROVIDER_REGISTRY.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class OAuthUserInfo:
    """Нормализованный профиль пользователя от OAuth-провайдера."""

    sub: str  # Уникальный ID провайдера (Google sub, VK id)
    email: str
    display_name: str
    avatar_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class OAuthProvider(ABC):
    """Абстрактный OAuth-провайдер.

    Все провайдеры следуют этому интерфейсу. Регистрируются в PROVIDER_REGISTRY.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя: 'google', 'vk'."""

    @abstractmethod
    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        """Вернуть URL для редиректа пользователя на OAuth-сервер.

        Args:
            redirect_uri: Куда OAuth-сервер отправит code после подтверждения
            state: Случайная строка (CSRF-защита)

        Returns:
            Полный URL для редиректа браузера
        """

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Обменять authorization code на access_token.

        Args:
            code: Authorization code от OAuth-сервера
            redirect_uri: Должен совпадать с переданным в get_authorize_url

        Returns:
            Сырой ответ от токен-эндпоинта (access_token, refresh_token, expires_in)
        """

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Получить профиль пользователя по access_token."""


class OAuthError(Exception):
    """Ошибка OAuth-потока."""

    def __init__(self, message: str, provider: str = ""):
        self.provider = provider
        super().__init__(f"[{provider}] {message}" if provider else message)


# ── Registry ────────────────────────────────────────────────────

PROVIDER_REGISTRY: dict[str, type[OAuthProvider]] = {}
"""Реестр провайдеров. Провайдер регистрируется сам при импорте."""


def register_provider(provider_cls: type[OAuthProvider]):
    """Декоратор для авторегистрации провайдера."""
    instance = provider_cls()
    PROVIDER_REGISTRY[instance.name] = provider_cls
    return provider_cls


def get_provider(name: str) -> OAuthProvider:
    """Получить экземпляр провайдера по имени."""
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        msg = f"Unknown OAuth provider: {name}"
        raise OAuthError(msg, name)
    return cls()


def list_providers() -> list[str]:
    """Список зарегистрированных провайдеров."""
    return list(PROVIDER_REGISTRY.keys())
