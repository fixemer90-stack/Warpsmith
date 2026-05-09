"""Tests for F4.5 — Canvas Map: Terrain Tiles + Deploy Zones Interactivity."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestMapTilesAPI:
    def test_map_tiles_endpoint(self):
        resp = client.get("/api/map/tiles")
        assert resp.status_code == 200
        data = resp.json()
        assert "width" in data
        assert "height" in data
        assert "tiles" in data
        assert "deploy_zones" in data
        assert "units" in data

        assert data["width"] == 16
        assert data["height"] == 16
        assert len(data["tiles"]) == 16
        assert len(data["tiles"][0]) == 16

    def test_map_tiles_structure(self):
        resp = client.get("/api/map/tiles")
        data = resp.json()

        # Check tiles are integers 0-5 (TileType enum)
        for row in data["tiles"]:
            for tile in row:
                assert isinstance(tile, int)
                assert 0 <= tile <= 5

        # Check deploy zones
        assert "p1" in data["deploy_zones"]
        assert "p2" in data["deploy_zones"]
        assert isinstance(data["deploy_zones"]["p1"], list)
        assert isinstance(data["deploy_zones"]["p2"], list)

    def test_map_tiles_deploy_zones_valid(self):
        resp = client.get("/api/map/tiles")
        data = resp.json()

        # All deploy zone coordinates should be valid (x,y within grid bounds)
        for coord in data["deploy_zones"]["p1"] + data["deploy_zones"]["p2"]:
            assert len(coord) == 2
            x, y = coord
            assert 0 <= x < 16
            assert 0 <= y < 16

    def test_map_tiles_no_units_by_default(self):
        resp = client.get("/api/map/tiles")
        data = resp.json()
        assert data["units"] == []


class TestStrategicBattlefieldMapIntegration:
    """Strategic SVG battlefield map replaces the old Canvas/Leaflet previews."""

    def test_scenario_setup_includes_strategic_svg_map(self):
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "battlefield-map" in resp.text
        assert "battlefield-map-svg" in resp.text
        assert "battlefield_map.js" in resp.text
        assert "map_view.js" not in resp.text
        assert "leaflet.js" not in resp.text

    def test_strategic_map_always_visible(self):
        """Map is always visible and includes scale/objective/unit legend."""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert 'id="battlefield-map"' in resp.text
        assert "Scale: 1 grid = 6″" in resp.text
        assert "Objective" in resp.text
        assert "P1 Unit" in resp.text
        assert "P2 Unit" in resp.text

    def test_map_tiles_dynamic_size(self):
        """Map tiles API accepts dynamic width/height for different formats."""
        for w, h in [(44, 30), (44, 44), (44, 60), (44, 90)]:
            resp = client.get(f"/api/map/tiles?width={w}&height={h}")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["tiles"]) == h
            assert len(data["tiles"][0]) == w

    def test_map_tiles_dynamic_deploy_zones(self):
        """Deploy zones scale proportionally with map size."""
        resp = client.get("/api/map/tiles?width=44&height=60")
        data = resp.json()
        zone_p1 = data["deploy_zones"]["p1"]
        zone_p2 = data["deploy_zones"]["p2"]
        # Each zone should cover ~20% of map width
        xs_p1 = {c[0] for c in zone_p1}
        xs_p2 = {c[0] for c in zone_p2}
        assert max(xs_p1) < min(xs_p2)  # zones don't overlap
        assert len(xs_p1) <= 9  # ~20% of 44

    def test_battlefield_map_supports_mission_objectives_units_and_scale(self):
        """New map must render mission objectives, roster units, and real table scale."""
        from pathlib import Path

        js_file = Path(__file__).parent.parent / "web" / "static" / "battlefield_map.js"
        assert js_file.exists()
        content = js_file.read_text(encoding="utf-8")
        assert "initMap" in content
        assert "showUnits" in content
        assert "getMissionObjectives" in content
        assert "drawScaleRuler" in content
        assert "bottomPadding: 64" in content
        assert "fieldH + this.padding + this.bottomPadding" in content
        assert "only-war" in content
        assert "take-and-hold" in content
        assert "purge-the-foe" in content

    def test_base_template_has_no_leaflet_dependency(self):
        from pathlib import Path

        base = Path(__file__).parent.parent / "web" / "templates" / "base.html"
        content = base.read_text(encoding="utf-8")
        assert "leaflet" not in content.lower()
        assert "L.map" not in content

    def test_compatible_rosters_filter(self):
        """scenario_setup.js should have compatibleRosters."""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "compatibleRosters" in resp.text


class TestTileTypes:
    """Test tile type constants in map tiles API."""

    def test_tile_type_constants(self):
        resp = client.get("/api/map/tiles?width=10&height=10")
        data = resp.json()
        for row in data["tiles"]:
            for tile in row:
                assert isinstance(tile, int)
                assert 0 <= tile <= 5  # TileType enum values

    def test_deploy_zone_overlay(self):
        resp = client.get("/api/map/tiles?width=10&height=10")
        data = resp.json()
        p1_coords = data["deploy_zones"]["p1"]
        p2_coords = data["deploy_zones"]["p2"]
        # Verify zones exist and don't overlap
        p1_set = set(tuple(c) for c in p1_coords)
        p2_set = set(tuple(c) for c in p2_coords)
        assert p1_set & p2_set == set()  # no overlap
