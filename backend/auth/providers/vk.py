"""VK OAuth 2.0 провайдер.

Для включения:
  1. Создать приложение в https://vk.com/apps?act=manage
  2. Добавить в .env:
       VK_CLIENT_ID=...
       VK_CLIENT_SECRET=...
"""

import os
from urllib.parse import urlencode

import httpx

from .base import OAuthError, OAuthProvider, OAuthUserInfo, register_provider

AUTH_URL = "https://id.vk.com/authorize"
TOKEN_URL = "https://api.vk.com/method/auth.exchangeSilentAuthToken"
USER_GET_URL = "https://api.vk.com/method/users.get"
API_VERSION = "5.199"


@register_provider
class VKProvider(OAuthProvider):
    """OAuth через VK ID."""

    @property
    def name(self) -> str:
        return "vk"

    @property
    def _client_id(self) -> str:
        return os.getenv("VK_CLIENT_ID", "")

    @property
    def _client_secret(self) -> str:
        return os.getenv("VK_CLIENT_SECRET", "")

    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email",
            "state": state,
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Обменять code на access_token через VK API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                TOKEN_URL,
                params={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "v": API_VERSION,
                },
            )
        if resp.status_code != 200:
            raise OAuthError(f"Token exchange failed: {resp.text}", self.name)
        data: dict = resp.json()
        if "error" in data:
            raise OAuthError(f"VK API error: {data['error']}", self.name)
        result: dict = data["response"]
        return result

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Получить профиль VK пользователя."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                USER_GET_URL,
                params={
                    "access_token": access_token,
                    "v": API_VERSION,
                    "fields": "photo_200",
                },
            )
        if resp.status_code != 200:
            raise OAuthError(f"User get failed: {resp.text}", self.name)
        data = resp.json()
        user = data["response"][0]
        return OAuthUserInfo(
            sub=str(user["id"]),
            email="",  # VK не отдаёт email через users.get
            display_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            avatar_url=user.get("photo_200", ""),
        )
