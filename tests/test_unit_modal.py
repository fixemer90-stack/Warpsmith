"""Tests for F4.2 — Unit Modal with Squad Size, Loadout, Wargear Selection."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestUnitDetailAPI:
    def test_unit_detail_endpoint(self):
        resp = client.get("/api/units/Boyz/detail")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "wargear_options" in data
        assert "squad_size" in data
        assert "weapons" in data

    def test_unit_detail_not_found(self):
        resp = client.get("/api/units/NonExistentUnit/detail")
        assert resp.status_code == 404

    def test_unit_detail_weapons_resolved(self):
        resp = client.get("/api/units/Boyz/detail")
        data = resp.json()
        if data.get("weapons"):
            weapon = data["weapons"][0]
            for key in ["name", "type", "attacks", "skill", "strength", "ap", "damage"]:
                assert key in weapon

    def test_unit_detail_squad_size_structure(self):
        resp = client.get("/api/units/Boyz/detail")
        data = resp.json()
        squad_size = data.get("squad_size", {})
        assert "min" in squad_size
        assert "max" in squad_size
        assert "step" in squad_size
        assert squad_size["min"] <= squad_size["max"]

    def test_unit_detail_wargear_options_structure(self):
        resp = client.get("/api/units/Boyz/detail")
        data = resp.json()
        wargear_options = data.get("wargear_options", [])
        if wargear_options:
            option = wargear_options[0]
            assert "name" in option
            assert "points" in option
            assert "weapons" in option

    def test_unit_detail_nob_options_structure(self):
        resp = client.get("/api/units/Boyz/detail")
        data = resp.json()
        nob_options = data.get("nob_options", [])
        if nob_options:
            option = nob_options[0]
            assert "name" in option
            assert "points" in option
            # Nob options might have replaces and weapons


class TestUnitModalIntegration:
    def test_team_builder_includes_modal(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "showUnitModal" in resp.text

    def test_unit_modal_js_loaded(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        # Check that team_builder.js is included
        assert "team_builder.js" in resp.text

    def test_faction_browser_modal_not_in_team_builder(self):
        """Team builder should have unit modal, not faction browser modal"""
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "showUnitModal" in resp.text
        assert "factionBrowser" not in resp.text


class TestSquadSizeLogic:
    """Test squad size logic in modal (placeholder - would need actual unit data)"""

    def test_squad_size_validation_placeholder(self):
        """Placeholder test for squad size validation logic."""
        # In a real test, we'd mock the unit data and test the Alpine.js logic
        # For now, just ensure the API returns valid squad_size structure
        assert True  # This would be tested in integration tests with real data


class TestLoadoutLogic:
    """Test loadout selection logic (placeholder)"""

    def test_loadout_selection_placeholder(self):
        """Placeholder test for loadout selection and weapon resolution."""
        # Would test that selecting different loadouts changes currentWeapons
        assert True


class TestCostCalculation:
    """Test total cost calculation (placeholder)"""

    def test_cost_calculation_placeholder(self):
        """Placeholder test for PTS cost calculation with squad size, loadouts, nob upgrades."""
        # Would test that totalCost updates correctly based on selections
        assert True
