"""Test the PMF chart page."""

import pytest


def test_pmf_chart_page(client):
    """Test that the PMF chart page loads."""
    response = client.get("/pmf-chart")
    assert response.status_code == 200
    assert "PMF Chart" in response.text
    assert "chart.js" in response.text