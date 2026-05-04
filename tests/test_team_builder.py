"""Test the team builder page."""

import pytest


def test_team_builder_page(client):
    """Test that the team builder page loads."""
    response = client.get("/team-builder")
    assert response.status_code == 200
    assert "Team Builder" in response.text
    assert 'x-data="teamBuilder()"' in response.text


def test_team_builder_js_included(client):
    """Test that team_builder.js is included in the page."""
    response = client.get("/team-builder")
    assert "team_builder.js" in response.text
