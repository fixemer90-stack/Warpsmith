"""Настройка структурированного логирования через structlog."""

import os
import logging
import structlog
import uuid
import time
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def setup_logging(level: str = "INFO") -> None:
    """Настроить structlog как основной логгер."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # В production — JSON, в dev — цветной консольный
            structlog.dev.ConsoleRenderer()
            if level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Настроить стандартное логгирование (uwsgi, uvicorn) через structlog
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )


logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Логировать каждый HTTP-запрос с duration, status, request_id."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)

        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=f"{duration_ms:.1f}",
        )

        response.headers["X-Request-ID"] = request_id
        return response


def setup_sentry(dsn: str | None, environment: str = "production") -> None:
    """Инициализировать Sentry SDK."""
    if not dsn:
        logger.warning("SENTRY_DSN not set — Sentry disabled")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% трассировка для снижения стоимости
        profiles_sample_rate=0.1,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        send_default_pii=True,  # IP и заголовки запросов для дебага
    )
    logger.info("Sentry initialized", dsn_short=dsn[:30] + "...")