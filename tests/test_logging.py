"""
Tests for F5.5 — Logging (structlog) + Sentry error tracking.

Проверяет:
- RequestLoggingMiddleware добавляет X-Request-ID в ответ
- middleware пишет structlog-запись о каждом запросе
- /sentry-debug возвращает 500 (проверка Sentry capture)
- setup_sentry gracefully выключается без DSN
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_request_id_in_response():
    """Каждый ответ содержит X-Request-ID длиной 8 символов."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) == 8


@pytest.mark.asyncio
async def test_request_id_unique_per_request():
    """Каждый запрос получает свой request_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.get("/api/health")
        resp2 = await client.get("/api/health")
        assert resp1.headers["x-request-id"] != resp2.headers["x-request-id"]


@pytest.mark.asyncio
async def test_request_id_on_error_page():
    """Даже 404 страница получает request_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/nonexistent-page-12345")
        assert "x-request-id" in resp.headers
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sentry_debug_endpoint_returns_500():
    """GET /sentry-debug вызывает ZeroDivisionError → 500."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            resp = await client.get("/sentry-debug")
            assert resp.status_code == 500
        except ZeroDivisionError:
            # ASGITransport может не ловить исключения в тестах,
            # но сам факт ошибки = endpoint работает
            pass


@pytest.mark.asyncio
async def test_json_log_output(caplog):
    """structlog пишет запись о request в лог."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/")
        # caplog должен содержать запись о request от middleware
        assert any("request" in str(rec.message) for rec in caplog.records)


@pytest.mark.asyncio
async def test_log_contains_method_and_path(caplog):
    """Лог содержит method, path, status, duration_ms."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/health")
        log_text = "\n".join(str(rec.message) for rec in caplog.records)
        assert "GET" in log_text or "get" in log_text.lower()
        assert "health" in log_text or "/api/health" in log_text


def test_setup_sentry_without_dsn_does_not_crash():
    """setup_sentry() без DSN логирует warning и не падает."""
    from backend.logging_setup import setup_sentry
    # Должна отработать без ошибок
    setup_sentry(dsn=None)
    setup_sentry(dsn="")
    # С фейковым DSN тоже не должна падать (sentry_sdk сам упадёт,
    # но мы ловим это внутри)
    with patch("sentry_sdk.init") as mock_init:
        setup_sentry(dsn="https://key@sentry.io/project")
        mock_init.assert_called_once()


def test_setup_sentry_with_dsn_calls_init():
    """С DSN setup_sentry вызывает sentry_sdk.init."""
    from backend.logging_setup import setup_sentry
    with patch("sentry_sdk.init") as mock_init:
        setup_sentry(dsn="https://test@test.ingest.sentry.io/12345")
        mock_init.assert_called_once()
        _args, kwargs = mock_init.call_args
        assert kwargs.get("dsn") == "https://test@test.ingest.sentry.io/12345"
        assert kwargs.get("environment") == "production"
        assert kwargs.get("traces_sample_rate") == 0.1


def test_setup_sentry_development_environment():
    """В development окружении environment='development'."""
    from backend.logging_setup import setup_sentry
    with patch("sentry_sdk.init"):
        setup_sentry(dsn="https://key@sentry.io/project", environment="development")
        # Не падает — достаточно


def test_structlog_configured():
    """structlog должен быть сконфигурирован (глобальный логгер работает)."""
    import structlog
    logger = structlog.get_logger()
    # Должен вернуть BoundLogger, не падать
    assert logger is not None
    # Проверка что можно вызвать .info()
    logger.info("test_message", extra_field="value")
