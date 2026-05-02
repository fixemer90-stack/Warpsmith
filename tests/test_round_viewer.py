"""Test the Round Viewer page."""

import pytest


def test_round_viewer_page(client):
    """Test that the round viewer page loads."""
    response = client.get("/round-viewer/1")
    assert response.status_code == 200
    assert "Round Viewer" in response.text
    assert "Simulation Summary" in response.text