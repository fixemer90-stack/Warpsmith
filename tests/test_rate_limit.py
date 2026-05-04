"""Tests for F5.3 — Rate limiting with slowapi.

Проверяет:
- Анонимные запросы к / лимитируются (default: 30/min)
- /health exempted — не лимитируется
- 429 ответ содержит Retry-After / X-RateLimit заголовки
"""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_rate_limit_anon():
    """После превышения лимита (31 запрос с хвостом) получаем 429.

    Создаём отдельное приложение с очень низким лимитом, чтобы не зависеть
    от лимита, израсходованного другими тестами.
    """
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("RATE_LIMIT_ANON", "5/minute")
        from main import create_app as _create_app

        fresh_app = _create_app()

    transport = ASGITransport(app=fresh_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            resp = await client.get("/")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        # 6-й запрос должен превысить лимит
        resp = await client.get("/")
        assert resp.status_code == 429, f"Expected 429 rate limited, got {resp.status_code}"


@pytest.mark.asyncio
async def test_rate_limit_health_exempt():
    """Health endpoint exempt от rate limiting — 40 запросов все OK.

    Используем отдельное приложение с низким лимитом.
    """
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("RATE_LIMIT_ANON", "3/minute")
        from main import create_app as _create_app

        fresh_app = _create_app()

    transport = ASGITransport(app=fresh_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Используем лимит на /
        for _ in range(3):
            r = await client.get("/")
            assert r.status_code in (200, 429)

        # /health должен быть доступен всегда
        for _ in range(40):
            resp = await client.get("/health")
            assert resp.status_code == 200, (
                f"Expected 200 on exempt endpoint, got {resp.status_code}"
            )


@pytest.mark.asyncio
async def test_rate_limit_headers():
    """429 ответ содержит Retry-After или X-RateLimit заголовки.

    Используем отдельное приложение с низким лимитом.
    """
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("RATE_LIMIT_ANON", "3/minute")
        from main import create_app as _create_app

        fresh_app = _create_app()

    transport = ASGITransport(app=fresh_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Исчерпать лимит
        for _ in range(3):
            await client.get("/")

        # 4-й запрос — проверяем заголовки
        resp = await client.get("/")
        assert resp.status_code == 429

        has_retry_after = "retry-after" in resp.headers
        has_ratelimit = any(k.lower().startswith("x-ratelimit") for k in resp.headers)
        assert has_retry_after or has_ratelimit, (
            "429 response should have Retry-After or X-RateLimit headers. "
            f"Headers: {dict(resp.headers)}"
        )
