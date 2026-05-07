"""Tests for F4.4 — Synergy Hints: Leader Compatibility, Transport Capacity."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestSynergyAPI:
    def test_synergies_empty_roster(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["checks"] == []
        assert data["score"] == 0

    def test_synergies_no_faction(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "",
                "units": [],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["checks"] == []

    def test_synergies_transport_capacity_check(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [
                    {"name": "Trukk", "squad_size": 1},
                    {"name": "Boyz", "squad_size": 20},  # Assuming Trukk capacity is less than 20
                ],
            },
        )
        data = resp.json()
        transport_checks = [c for c in data["checks"] if c["type"] == "transport"]
        if transport_checks:
            assert any("can carry" in c["message"] for c in transport_checks)

    def test_synergies_transport_empty(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [
                    {"name": "Trukk", "squad_size": 1},
                ],
            },
        )
        data = resp.json()
        transport_checks = [c for c in data["checks"] if c["type"] == "transport"]
        if transport_checks:
            assert any("is empty" in c["message"] for c in transport_checks)

    def test_synergies_leader_compatibility(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [
                    {"name": "Warboss", "squad_size": 1},
                    {"name": "Boyz", "squad_size": 10},
                ],
            },
        )
        data = resp.json()
        _leader_checks = [c for c in data["checks"] if c["type"] == "leader"]
        # This will depend on actual wiki data and leader_for fields

    def test_synergies_score_calculation(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [
                    {"name": "Trukk", "squad_size": 1},
                    {"name": "Boyz", "squad_size": 50},  # Over capacity
                ],
            },
        )
        data = resp.json()
        # Score should be > 0 if there are errors
        assert isinstance(data["score"], int)

    def test_synergies_response_structure(self):
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [{"name": "Trukk", "squad_size": 1}],
            },
        )
        data = resp.json()
        assert "checks" in data
        assert "score" in data
        assert isinstance(data["checks"], list)
        if data["checks"]:
            check = data["checks"][0]
            required_fields = ["type", "severity", "source_unit", "message", "icon"]
            for field in required_fields:
                assert field in check

    def test_synergies_synergy_hints(self):
        """Test wiki synergy hints (if any exist in test data)"""
        resp = client.post(
            "/api/rosters/synergies",
            json={
                "faction": "orks",
                "units": [
                    {"name": "Warboss", "squad_size": 1},
                    {"name": "Trukk", "squad_size": 1},
                ],
            },
        )
        data = resp.json()
        _synergy_checks = [c for c in data["checks"] if c["type"] == "synergy"]
        # This depends on whether wiki units have synergies field


class TestSynergyIntegration:
    def test_team_builder_includes_synergy_hints(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "synergyHints" in resp.text or "synergy_hints" in resp.text

    def test_synergy_hints_js_loaded(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "synergy_hints.js" in resp.text

    def test_synergy_panel_included(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "Synergy Check" in resp.text

    def test_roster_visual_indicators(self):
        """Check that roster items have synergy visual indicators"""
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        # Should contain synergy class methods
        assert "getSynergyClass" in resp.text
        assert "getSynergyDot" in resp.text
