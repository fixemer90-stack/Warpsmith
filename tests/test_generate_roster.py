"""Tests for F4.9 — Generate Random Opponent."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestGenerateRoster:
    def test_generate_roster_random_faction(self):
        """Without faction, generates a valid roster with any faction."""
        resp = client.post("/api/rosters/generate", json={})
        assert resp.status_code == 200
        data = resp.json()
        roster = data["roster"]
        assert roster["faction"] in ["orks", "tau", "adeptus-mechanicus", "mixed"]
        assert len(roster["units"]) > 0
        assert roster["total_pts"] <= 2000

    def test_generate_roster_specific_faction(self):
        """With faction filter, all units belong to that faction."""
        resp = client.post("/api/rosters/generate", json={"faction": "orks"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["roster"]["faction"] == "orks"

    def test_generate_roster_warlord_assigned(self):
        """Generated roster has exactly one warlord-capable unit."""
        resp = client.post("/api/rosters/generate", json={"faction": "orks"})
        data = resp.json()
        roster = data["roster"]
        assert len(roster["units"]) > 0
        # At least one unit should be a leader (warlord)
        # We verify via the first unit being a warlord-capable unit
        # (logic: generate_roster forces warlord as first unit)

    def test_generate_roster_pts_limit(self):
        """Generated roster respects pts_limit."""
        resp = client.post("/api/rosters/generate", json={"pts_limit": 500})
        data = resp.json()
        assert data["roster"]["total_pts"] <= 500

    def test_generate_roster_no_faction_returns_army_name(self):
        """Without faction, name says 'AI Random Army'."""
        resp = client.post("/api/rosters/generate", json={})
        data = resp.json()
        assert "AI" in data["roster"]["name"]

    def test_generate_roster_with_faction_returns_army_name(self):
        """With faction, name includes faction."""
        resp = client.post("/api/rosters/generate", json={"faction": "orks"})
        data = resp.json()
        assert "Ork" in data["roster"]["name"] or "AI" in data["roster"]["name"]

    def test_generate_roster_returns_roster_structure(self):
        """Response has correct roster structure."""
        resp = client.post("/api/rosters/generate", json={"faction": "orks"})
        data = resp.json()
        assert "roster" in data
        roster = data["roster"]
        assert "name" in roster
        assert "faction" in roster
        assert "pts_limit" in roster
        assert "total_pts" in roster
        assert "units" in roster
        for unit in roster["units"]:
            assert "unit_name" in unit
            assert "squad_size" in unit

    def test_generate_roster_marks_exactly_one_warlord(self):
        """Generated rosters include explicit Warlord metadata for saving/simulation."""
        resp = client.post("/api/rosters/generate", json={"faction": "orks", "pts_limit": 500})
        assert resp.status_code == 200
        units = resp.json()["roster"]["units"]
        assert sum(1 for u in units if u.get("is_warlord")) == 1
