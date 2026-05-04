"""Проверка минимального порога покрытия для CI."""

import pytest


def test_coverage_threshold():
    """CI требует > 80% coverage для backend/engine и backend/loader.
    Тест запускается как часть pytest-cov, порог задан в pyproject.toml
    или проверяется воркфлоу через --cov-fail-under=80
    """
