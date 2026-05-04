"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Test client for testing FastAPI app."""
    with TestClient(app) as client:
        yield client
