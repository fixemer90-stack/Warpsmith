"""Test the team builder page."""

import pytest


def test_team_builder_page(client):
    """Test that the team builder page loads."""
    response = client.get("/team-builder")
    assert response.status_code == 200
    assert "Team Builder" in response.text
    assert 'x-data="teamBuilder()"' in response.text


def test_team_builder_js_included(client):
    """Test that team_builder.js is included in the page."""
    response = client.get("/team-builder")
    assert "team_builder.js" in response.text


def test_team_builder_zero_warlord_candidates_warns_and_blocks_save(client):
    """Team Builder has explicit zero-eligible Warlord UI state."""
    response = client.get("/static/team_builder.js")
    assert response.status_code == 200
    js = response.text

    assert "if (count === 0) return false" in js
    assert "This roster has no eligible Character" in js
    assert "Add a Character unit to serve as Warlord" in js


def test_team_builder_warlord_eligibility_includes_keywords(client):
    """Frontend candidate logic mirrors backend keyword/tag Character eligibility."""
    response = client.get("/static/team_builder.js")
    assert response.status_code == 200
    js = response.text

    assert "isWarlordEligibleEntry(entry)" in js
    assert "normalizedKeywords.includes('character')" in js
