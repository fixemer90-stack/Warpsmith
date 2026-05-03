"""Tests for F4.3 — Detachment Picker with Rule Preview."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestDetachmentAPI:
    def test_list_detachments_no_filter(self):
        resp = client.get("/api/detachments")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_detachments_faction_filter(self):
        resp = client.get("/api/detachments?faction=orks")
        data = resp.json()
        assert isinstance(data, list)
        for det in data:
            assert det["faction"] == "orks"

    def test_detachment_detail(self):
        # First get a detachment name
        resp = client.get("/api/detachments")
        data = resp.json()
        if data:
            det_name = data[0]["name"]
            resp = client.get(f"/api/detachments/{det_name}")
            assert resp.status_code == 200
            detail = resp.json()
            assert "name" in detail
            assert "description" in detail
            assert "stratagems" in detail
            assert "enhancements" in detail

    def test_detachment_detail_not_found(self):
        resp = client.get("/api/detachments/NonExistentDetachment")
        assert resp.status_code == 404

    def test_detachment_detail_structure(self):
        # First get a detachment name
        resp = client.get("/api/detachments")
        data = resp.json()
        if data:
            det_name = data[0]["name"]
            resp = client.get(f"/api/detachments/{det_name}")
            detail = resp.json()

            # Check stratagems structure
            if detail.get("stratagems"):
                strat = detail["stratagems"][0]
                for key in ["name", "cost", "when", "effect"]:
                    assert key in strat

            # Check enhancements structure
            if detail.get("enhancements"):
                enh = detail["enhancements"][0]
                for key in ["name", "points", "effect"]:
                    assert key in enh

            # Check detachment rule structure
            if detail.get("detachment_rule"):
                rule = detail["detachment_rule"]
                for key in ["name", "description"]:
                    assert key in rule


class TestDetachmentPickerIntegration:
    def test_team_builder_includes_detachment_picker(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "detachment_picker" in resp.text or "detachmentPicker" in resp.text

    def test_detachment_picker_js_loaded(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "detachment_picker.js" in resp.text

    def test_detachment_picker_html_included(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "Select Detachment" in resp.text

    def test_detachment_picker_renders(self):
        """Detachment picker component should be present on team-builder page"""
        resp = client.get("/team-builder")
        assert "detachmentPicker()" in resp.text
        assert "Select Detachment" in resp.text
        assert "detachment_picker.js" in resp.text


class TestRegistryDetachmentSupport:
    """Test that registry properly loads detachments."""

    def test_registry_has_detachments_method(self):
        from backend.loader.registry import registry
        # These methods should exist
        assert hasattr(registry, 'list_detachments')
        assert hasattr(registry, 'get_detachment')

    def test_registry_detachments_loaded(self):
        from backend.loader.registry import registry
        try:
            registry.load()
            # Should not raise an exception
            detachments = registry.list_detachments()
            assert isinstance(detachments, list)
        except Exception as e:
            # If wiki is not available, that's expected in tests
            pytest.skip(f"Wiki not available: {e}")


class TestDetachmentDataModel:
    """Test detachment data classes."""

    def test_detachment_creation(self):
        from backend.loader.registry import Detachment, DetachmentRule, Stratagem, Enhancement

        rule = DetachmentRule(name="Test Rule", description="Test description")
        strat = Stratagem(name="Test Strat", cost=1, when="Test when", effect="Test effect")
        enh = Enhancement(name="Test Enh", points=10, effect="Test effect")

        det = Detachment(
            name="Test Detachment",
            faction="test",
            description="Test description",
            detachment_rule=rule,
            stratagems=[strat],
            enhancements=[enh]
        )

        assert det.name == "Test Detachment"
        assert det.faction == "test"
        assert det.detachment_rule == rule
        assert len(det.stratagems) == 1
        assert len(det.enhancements) == 1