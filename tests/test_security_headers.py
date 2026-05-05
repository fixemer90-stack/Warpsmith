"""Tests for F5.4 — CORS hardening + security headers."""

import os

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_security_headers_present():
    """X-Content-Type-Options, X-Frame-Options, Referrer-Policy присутствуют."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert resp.headers.get("permissions-policy") is not None


@pytest.mark.asyncio
async def test_security_headers_hsts():
    """HSTS присутствует для HTTPS-запросов."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        resp = await client.get("/health")
        assert resp.headers.get("strict-transport-security") is not None


@pytest.mark.asyncio
async def test_cors_production_restricted():
    """В production CORS не пропускает неразрешённые origins."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("HOSTING", "true")
        mp.setenv("PRODUCTION_ORIGIN", "https://example.com")

        import web.routes.api  # noqa
        import web.routes.pages
        from backend.security import headers

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
            acao = resp.headers.get("access-control-allow-origin", "")
            assert "evil.com" not in acao
