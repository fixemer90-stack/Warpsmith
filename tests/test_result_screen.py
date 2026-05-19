"""Test the Result Screen (F3.8) feature."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.engine.replay import Replay, ReplayRound


def test_result_page_loads(client):
    """Test that the result page returns 200 and renders correct content."""
    response = client.get("/result/test-id")
    assert response.status_code == 200
    assert "Battle Result" in response.text
    assert "resultScreen()" in response.text
    assert "loadResult" in response.text
    assert "result_chart.js" in response.text
    assert "VP Timeline" in response.text
    assert "Phase Breakdown" in response.text
    assert "View Full Replay" in response.text
    assert "New Simulation" in response.text
    assert "Export JSON" in response.text


def test_result_api_returns_summary(client):
    """Test that the result API endpoint exists and returns proper 404 for unknown ID."""
    response = client.get("/api/results/test-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_vp_chart_renders(client):
    """Test that the result page includes the VP chart canvas and Chart.js bindings."""
    response = client.get("/result/vp-test")
    assert response.status_code == 200
    assert "vp-chart" in response.text
    assert "result_chart.js" in response.text
    # Chart.js is loaded in base.html
    assert "chart.js" in response.text.lower()


def test_export_json_button(client):
    """Test that the result page includes the Export JSON button with exportJSON handler."""
    response = client.get("/result/export-test")
    assert response.status_code == 200
    assert "exportJSON" in response.text or '@click="exportJSON' in response.text
    assert "Export JSON" in response.text
    assert "result_chart.js" in response.text


def test_result_page_contains_stat_cards(client):
    """Test that all 8 stat cards are present on the result page."""
    response = client.get("/result/stats-test")
    assert response.status_code == 200
    # Check for VP cards
    assert "VP" in response.text
    # Check for Kills cards
    assert "Kills" in response.text
    # Check for Damage cards
    assert "Damage" in response.text
    # Check for Charges cards
    assert "Charges" in response.text


def test_result_page_shows_destroyed_units_sections(client):
    """Test that the destroyed units columns are present."""
    response = client.get("/result/destroyed-test")
    assert response.status_code == 200
    assert "Lost" in response.text
    assert "No units lost" in response.text or "destroyedUnits" in response.text


def test_results_api_exposes_authoritative_final_state(monkeypatch, client):
    """/api/results returns final_state + final_victory_points from authoritative source."""
    from web.routes import api_replays

    replay = Replay(
        game_id="authoritative-final",
        created_at="2026-05-19T12:00:00Z",
        rosters={"roster_a": {"name": "A"}, "roster_b": {"name": "B"}},
        mission="only_war",
        deployment="standard",
        seed=42,
        rounds=[
            ReplayRound(
                round=1,
                start_state={"victory_points": {"1": 3, "2": 3}},
                end_state={"victory_points": {"1": 5, "2": 4}},
                events=[],
            )
        ],
        summary={"winner": None, "final_state": {"victory_points": {"1": 15, "2": 14}}},
    )

    monkeypatch.setattr(api_replays, "load_replay", lambda _conn, _gid: replay)

    response = client.get("/api/results/authoritative-final")
    assert response.status_code == 200
    data = response.json()

    assert data["final_state"]["victory_points"] == {"1": 15, "2": 14}
    assert data["summary"]["final_victory_points"] == {"1": 15, "2": 14}
    assert data["summary"]["winner"] == 1
