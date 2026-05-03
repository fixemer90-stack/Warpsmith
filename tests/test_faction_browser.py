"""Tests for F4.1 — Faction Browser with Category/PTS Filter."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestBrowseUnitsAPI:
    def test_browse_units_no_filters(self):
        resp = client.get("/api/units/browse")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert "factions" in data
        assert "categories" in data

    def test_browse_units_faction_filter(self):
        resp = client.get("/api/units/browse?faction=orks")
        data = resp.json()
        for item in data["items"]:
            assert item["faction"] == "orks"

    def test_browse_units_category_filter(self):
        resp = client.get("/api/units/browse?category=character")
        data = resp.json()
        for item in data["items"]:
            assert item["category"].lower() == "character"

    def test_browse_units_pts_range(self):
        resp = client.get("/api/units/browse?pts_min=50&pts_max=100")
        data = resp.json()
        for item in data["items"]:
            assert 50 <= item["points"] <= 100

    def test_browse_units_pts_min_only(self):
        resp = client.get("/api/units/browse?pts_min=200")
        data = resp.json()
        for item in data["items"]:
            assert item["points"] >= 200

    def test_browse_units_pts_max_only(self):
        resp = client.get("/api/units/browse?pts_max=50")
        data = resp.json()
        for item in data["items"]:
            assert item["points"] <= 50

    def test_browse_units_search(self):
        resp = client.get("/api/units/browse?search=warboss")
        data = resp.json()
        if data["total"] > 0:
            for item in data["items"]:
                assert "warboss" in item["name"].lower()

    def test_browse_units_role_leader(self):
        resp = client.get("/api/units/browse?role=leader")
        data = resp.json()
        for item in data["items"]:
            assert "leader" in item["role_flags"]

    def test_browse_units_role_transport(self):
        resp = client.get("/api/units/browse?role=transport")
        data = resp.json()
        for item in data["items"]:
            assert "transport" in item["role_flags"]

    def test_browse_units_role_battleline(self):
        resp = client.get("/api/units/browse?role=battleline")
        data = resp.json()
        for item in data["items"]:
            assert "battleline" in item["role_flags"]

    def test_browse_units_empty_state(self):
        resp = client.get("/api/units/browse?pts_min=99999")
        data = resp.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_browse_units_pagination(self):
        resp = client.get("/api/units/browse?per_page=5&page=1")
        data = resp.json()
        assert data["page"] == 1
        assert len(data["items"]) <= 5
        if data["total"] > 5:
            assert data["pages"] > 1

    def test_browse_units_sort_by_points(self):
        resp = client.get("/api/units/browse?sort_by=points&sort_dir=asc&per_page=10")
        data = resp.json()
        pts = [item["points"] for item in data["items"]]
        assert pts == sorted(pts)

    def test_browse_units_sort_by_points_desc(self):
        resp = client.get("/api/units/browse?sort_by=points&sort_dir=desc&per_page=10")
        data = resp.json()
        pts = [item["points"] for item in data["items"]]
        assert pts == sorted(pts, reverse=True)

    def test_browse_units_sort_by_name(self):
        resp = client.get("/api/units/browse?sort_by=name&per_page=10")
        data = resp.json()
        names = [item["name"].lower() for item in data["items"]]
        assert names == sorted(names)

    def test_browse_units_item_fields(self):
        resp = client.get("/api/units/browse?per_page=1")
        data = resp.json()
        if data["items"]:
            item = data["items"][0]
            for key in ["name", "faction", "category", "points", "movement",
                        "toughness", "save", "wounds", "leadership", "oc",
                        "icon_url", "color", "role_flags"]:
                assert key in item, f"Missing field: {key}"


class TestFactionBrowserPage:
    def test_faction_browser_page(self):
        resp = client.get("/faction-browser")
        assert resp.status_code == 200
        assert "faction-browser" in resp.text.lower() or "factionbrowser" in resp.text.lower().replace(" ", "")

    def test_faction_browser_js_included(self):
        resp = client.get("/faction-browser")
        assert "faction_browser.js" in resp.text

    def test_nav_link_exists(self):
        resp = client.get("/")
        assert "/faction-browser" in resp.text
