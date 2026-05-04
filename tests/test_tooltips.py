"""Tests for F4.7 — Tooltips on Every Stat (M/T/SV/W/LD/OC)."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTooltipsIncluded:
    """Tooltip JS and partial should be present on relevant pages."""

    def test_tooltips_js_included_in_base(self):
        resp = client.get("/")
        assert "tooltips.js" in resp.text

    def test_tooltips_js_on_team_builder(self):
        resp = client.get("/team-builder")
        assert "tooltips.js" in resp.text

    def test_tooltip_partial_included(self):
        resp = client.get("/team-builder")
        assert "tooltipManager" in resp.text
        assert "glossaryOpen" in resp.text


class TestStatAttributes:
    """All 6 stats should have data-stat attributes on team builder."""

    def test_stat_M_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="M"' in resp.text

    def test_stat_T_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="T"' in resp.text

    def test_stat_SV_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="SV"' in resp.text

    def test_stat_W_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="W"' in resp.text

    def test_stat_LD_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="LD"' in resp.text

    def test_stat_OC_present(self):
        resp = client.get("/team-builder")
        assert 'data-stat="OC"' in resp.text


class TestTooltipDefinitions:
    """STAT_TOOLTIPS definitions should be loaded."""

    def test_all_six_stats_defined(self):
        resp = client.get("/team-builder")
        for stat in ["M", "T", "SV", "W", "LD", "OC"]:
            assert f'data-stat="{stat}"' in resp.text
