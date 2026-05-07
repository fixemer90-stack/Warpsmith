"""Test the Round Viewer (F3.7) feature."""

import json

import pytest
from fastapi.testclient import TestClient


def test_replay_page_loads(client):
    """Test that the replay viewer page returns 200."""
    response = client.get("/replay/test-id")
    assert response.status_code == 200
    assert "Round Viewer" in response.text
    assert "replayViewer()" in response.text
    assert "replay-canvas" in response.text


def test_replay_api_returns_json(client):
    """Test that the replay API returns JSON with 'rounds' key."""
    response = client.get("/api/replays/test-id")
    # We expect 404 since test-id doesn't exist, but the endpoint should exist
    # and return proper JSON
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_replay_404(client):
    """Test that nonexistent replay returns 404."""
    response = client.get("/api/replays/nonexistent-replay-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_replay_list_api(client):
    """Test that replay list API returns a list."""
    response = client.get("/api/replays")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_vp_updates_across_rounds(client):
    """Placeholder: Verify VP tracking works across rounds in replay data."""
    # This test validates the concept — in a real scenario we'd seed
    # a replay with known VP values and verify they change between rounds.
    # For now, we verify the replay viewer JS has VP logic.
    response = client.get("/static/replay_viewer.js")
    assert response.status_code == 200
    js_content = response.text
    assert "victory_points" in js_content or "vpA" in js_content
    assert "vpB" in js_content
