"""Pytest configuration and fixtures."""

import os

# Отключаем rate limiter для тестов — должен быть ДО импорта main
os.environ.setdefault("RATE_LIMIT_ANON", "9999/minute")

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Test client for testing FastAPI app."""
    with TestClient(app) as client:
        yield client
