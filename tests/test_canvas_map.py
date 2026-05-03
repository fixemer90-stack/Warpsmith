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
        assert "player1" in data["deploy_zones"]
        assert "player2" in data["deploy_zones"]
        assert isinstance(data["deploy_zones"]["player1"], list)
        assert isinstance(data["deploy_zones"]["player2"], list)

    def test_map_tiles_deploy_zones_valid(self):
        resp = client.get("/api/map/tiles")
        data = resp.json()

        # All deploy zone coordinates should be valid (x,y within 0-15)
        for coord in data["deploy_zones"]["player1"] + data["deploy_zones"]["player2"]:
            assert len(coord) == 2
            x, y = coord
            assert 0 <= x < 16
            assert 0 <= y < 16

    def test_map_tiles_no_units_by_default(self):
        resp = client.get("/api/map/tiles")
        data = resp.json()
        assert data["units"] == []


class TestCanvasMapIntegration:
    def test_scenario_setup_includes_canvas_map(self):
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "battle-map" in resp.text
        assert "canvas_map.js" in resp.text

    def test_canvas_map_html_included(self):
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "Battlefield Map" in resp.text
        assert "canvas" in resp.text.lower()

    def test_canvas_map_legend_present(self):
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "Light Cover" in resp.text
        assert "Heavy Cover" in resp.text
        assert "Obstacle" in resp.text


class TestCanvasMapRendering:
    """Test canvas map JavaScript functionality (placeholder for integration tests)"""

    def test_canvas_map_js_loaded(self):
        """Canvas map JavaScript should be included"""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "canvasMap()" in resp.text

    def test_canvas_map_init_function(self):
        """Canvas map should have initMap function"""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "initMap()" in resp.text


class TestTileTypes:
    """Test that tile types are correctly defined and used"""

    def test_tile_type_constants(self):
        """Tile type constants should be defined in canvas_map.js"""
        # Check that canvas_map.js is included in scenario-setup
        resp = client.get("/scenario-setup")
        assert "canvas_map.js" in resp.text

        # Check the actual JS file content
        import os
        from pathlib import Path
        js_file = Path(__file__).parent.parent / "web" / "static" / "canvas_map.js"
        if js_file.exists():
            content = js_file.read_text()
            assert "TILE_COLORS" in content
            assert "TILE_LABELS" in content
            assert "TILE_SYMBOLS" in content

    def test_deploy_zone_overlay(self):
        """Deploy zone overlay should be present in HTML"""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "Deploy Zone P1" in resp.text
        assert "Deploy Zone P2" in resp.text


class TestUnitPlacement:
    """Test unit placement and drag functionality (placeholder)"""

    def test_unit_drag_interface(self):
        """Unit drag interface should be present"""
        resp = client.get("/scenario-setup")
        assert resp.status_code == 200
        assert "cursor-move" in resp.text
        assert "startUnitDrag" in resp.text

    def test_canvas_event_handlers(self):
        """Canvas should have mouse event handlers"""
        resp = client.get("/scenario-setup")
        content = resp.text
        assert "@mousedown" in content
        assert "@mousemove" in content
        assert "@mouseup" in content
        assert "@click" in content
        assert "@wheel" in content