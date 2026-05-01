"""Google OAuth 2.0 / OpenID Connect провайдер.

Для включения:
  1. Получить client_id и client_secret в Google Cloud Console (OAuth 2.0)
  2. Добавить в .env:
       GOOGLE_CLIENT_ID=...
       GOOGLE_CLIENT_SECRET=...
"""

import os
from urllib.parse import urlencode

import httpx

from .base import OAuthError, OAuthProvider, OAuthUserInfo, register_provider

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPE = "openid email profile"


@register_provider
class GoogleProvider(OAuthProvider):
    """OAuth через Google (OpenID Connect)."""

    @property
    def name(self) -> str:
        return "google"

    @property
    def _client_id(self) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "")

    @property
    def _client_secret(self) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "")

    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        if resp.status_code != 200:
            raise OAuthError(f"Token exchange failed: {resp.text}", self.name)
        return dict(resp.json())

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
        if resp.status_code != 200:
            raise OAuthError(f"Userinfo failed: {resp.text}", self.name)
        data = resp.json()
        return OAuthUserInfo(
            sub=data["sub"],
            email=data.get("email", ""),
            display_name=data.get("name", data.get("email", "User")),
            avatar_url=data.get("picture", ""),
        )
