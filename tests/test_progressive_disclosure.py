"""Tests for F4.6 — Progressive Disclosure: Beginner/Intermediate/Expert Modes."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestProgressiveDisclosureToggle:
    """Toggle button in header should be present on all pages."""

    def test_toggle_on_index(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "progressiveDisclosure" in resp.text
        assert "Beginner" in resp.text or "B</button>" in resp.text
        assert "Intermediate" in resp.text or "I</button>" in resp.text
        assert "Expert" in resp.text or "E</button>" in resp.text

    def test_toggle_on_team_builder(self):
        resp = client.get("/team-builder")
        assert resp.status_code == 200
        assert "progressiveDisclosure" in resp.text

    def test_js_file_included(self):
        resp = client.get("/")
        assert "progressive_disclosure.js" in resp.text

    def test_css_classes_present(self):
        """CSS rules for mode classes should be in base template."""
        resp = client.get("/")
        # Mode CSS classes
        assert "mode-beginner" in resp.text
        assert "mode-intermediate" in resp.text
        assert "mode-expert" in resp.text


class TestModeClassesInTemplates:
    """Templates should have mode-aware CSS classes on elements."""

    def test_stat_value_class_in_team_builder(self):
        resp = client.get("/team-builder")
        assert "stat-value" in resp.text

    def test_beginner_friendly_class_in_team_builder(self):
        resp = client.get("/team-builder")
        assert "beginner-friendly" in resp.text

    def test_expert_only_class_in_team_builder(self):
        resp = client.get("/team-builder")
        assert "expert-only" in resp.text
