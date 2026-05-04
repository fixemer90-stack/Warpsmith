"""Tests for F5.4 — CORS hardening + CSP security headers."""
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_security_headers_present():
    """X-Content-Type-Options, X-Frame-Options и CSP присутствуют."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("content-security-policy") is not None


@pytest.mark.asyncio
async def test_csp_allows_cdn():
    """CSP заголовок разрешает CDN домены Tailwind/HTMX/Alpine."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        csp = resp.headers.get("content-security-policy", "")
        assert "unpkg.com" in csp
        assert "cdn.jsdelivr.net" in csp
        assert "cdn.tailwindcss.com" in csp


@pytest.mark.asyncio
async def test_cors_production_restricted():
    """В production CORS не пропускает неразрешённые origins."""
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("HOSTING", "true")
        mp.setenv("PRODUCTION_ORIGIN", "https://example.com")

        # Нужно пересоздать приложение с новыми env
        # Перезагружаем модуль main, чтобы IS_PRODUCTION пересчиталась
        import importlib
        from backend.security import headers
        import web.routes.api
        import web.routes.pages

        # Создаём новое приложение через create_app
        from main import create_app

        test_app = create_app()

        transport = ASGITransport(app=test_app)
        async with AsyncClient(
            transport=transport, base_url="https://example.com"
        ) as client:
            resp = await client.get(
                "/",
                headers={"Origin": "https://evil.com"},
            )
            # evil.com не должен быть в Access-Control-Allow-Origin
            acao = resp.headers.get("access-control-allow-origin", "")
            assert "evil.com" not in acao
