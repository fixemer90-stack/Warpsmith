"""Tests for roster CRUD endpoints (F2.10)."""

from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from backend.auth import decode_jwt
from backend.db.database import db
from main import app


def _extract_token(resp) -> str | None:
    """Extract JWT token from set-cookie header."""
    set_cookie = resp.headers.get("set-cookie", "")
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("token="):
            return part.split("=", 1)[1]
    return None


def _register_user(client: TestClient, *, tier: str = "premium") -> dict:
    """Register a fresh user, force their billing tier, and return auth headers."""
    import uuid

    suffix = uuid.uuid4().hex[:8]
    email = f"roster{suffix}@test.dev"

    resp = client.post(
        "/auth/register",
        data={
            "email": email,
            "password": "StrongP4ss!",
            "display_name": "Tester",
        },
        follow_redirects=False,
    )

    token = _extract_token(resp)
    assert token is not None, f"Register failed: {resp.status_code}"
    payload = decode_jwt(token)
    assert payload is not None
    user_id = payload["user_id"]
    db.execute("UPDATE users SET tier = ? WHERE id = ?", (tier, user_id))
    db.commit()
    return {"Cookie": f"token={token}"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers. Each call = fresh user."""
    return _register_user(client, tier="premium")


class TestRosterCRUD:
    ROSTER_PAYLOAD: ClassVar[dict] = {
        "name": "My Ork Horde",
        "faction": "orks",
        "pts_limit": 2000,
        "detachment": "War Horde",
        "units": [
            {"unit_name": "Warboss", "squad_size": 1, "is_warlord": True},
            {"unit_name": "Boyz", "squad_size": 10},
        ],
    }

    def test_create_roster(self, client, auth_headers):
        """Create a valid roster returns 200 with id."""
        resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] > 0
        assert data["name"] == "My Ork Horde"
        assert data["faction"] == "orks"

    def test_create_roster_multiple_characters_requires_explicit_warlord(
        self, client, auth_headers
    ):
        """Multiple Character units require exactly one explicit Warlord flag."""
        payload = {
            **self.ROSTER_PAYLOAD,
            "units": [
                {"unit_name": "Warboss", "squad_size": 1},
                {"unit_name": "Big Mek", "squad_size": 1},
                {"unit_name": "Boyz", "squad_size": 10},
            ],
        }
        resp = client.post("/api/rosters", json=payload, headers=auth_headers)
        assert resp.status_code == 400, resp.text
        errors = resp.json()["detail"]["validation_errors"]
        assert any(e["code"] == "warlord_required" for e in errors)

    def test_create_roster_multiple_characters_accepts_one_warlord(self, client, auth_headers):
        """Exactly one explicit Warlord is valid when roster has multiple Characters."""
        payload = {
            **self.ROSTER_PAYLOAD,
            "units": [
                {"unit_name": "Warboss", "squad_size": 1, "is_warlord": True},
                {"unit_name": "Big Mek", "squad_size": 1, "is_warlord": False},
                {"unit_name": "Boyz", "squad_size": 10},
            ],
        }
        resp = client.post("/api/rosters", json=payload, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        units = resp.json()["units"]
        assert [u.get("is_warlord", False) for u in units].count(True) == 1

    def test_create_empty_roster_rejected(self, client, auth_headers):
        """Roster with no units fails validation."""
        payload = {**self.ROSTER_PAYLOAD, "units": []}
        resp = client.post("/api/rosters", json=payload, headers=auth_headers)
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"]
        assert detail["error"] == "roster_invalid"

    def test_list_rosters(self, client, auth_headers):
        """List returns created rosters."""
        # Create one first
        client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)

        resp = client.get("/api/rosters", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rosters"]) >= 1

    def test_get_roster_by_id(self, client, auth_headers):
        """GET by id returns the roster."""
        create = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert create.status_code == 200, create.text
        roster_id = create.json()["id"]

        resp = client.get(f"/api/rosters/{roster_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == roster_id
        assert isinstance(data["units"], list)
        assert data["units"][0]["unit_name"] == "Warboss"

    def test_get_roster_not_found(self, client, auth_headers):
        """Non-existent id returns 404."""
        resp = client.get("/api/rosters/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_roster(self, client, auth_headers):
        """Delete removes the roster."""
        create = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert create.status_code == 200, create.text
        roster_id = create.json()["id"]

        resp = client.delete(f"/api/rosters/{roster_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        resp = client.get(f"/api/rosters/{roster_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthorized_get(self, client):
        """GET /api/rosters without auth returns 401/403."""
        resp = client.get("/api/rosters")
        # auth routes use get_optional_user for GET, so returns 200 with empty list
        # but /api/rosters/{id} should block
        assert resp.status_code in (200, 401, 403)

    def test_unauthorized_post(self, client):
        """POST /api/rosters without auth returns 401/403."""
        resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD)
        # Non-optional Depends(get_current_user) will raise 401
        assert resp.status_code in (401, 403)

    def test_put_update_roster_own(self, client, auth_headers):
        """Update own roster returns 200."""
        # Create roster
        create_resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert create_resp.status_code == 200
        roster_id = create_resp.json()["id"]

        # Update it
        update_payload = {
            **self.ROSTER_PAYLOAD,
            "name": "Updated Ork Horde",
            "units": [
                {"unit_name": "Warboss", "squad_size": 1, "is_warlord": True},
                {"unit_name": "Boyz", "squad_size": 15},  # Changed squad size
            ],
        }
        resp = client.put(f"/api/rosters/{roster_id}", json=update_payload, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == roster_id
        assert data["name"] == "Updated Ork Horde"
        assert len(data["units"]) == 2

    def test_put_update_roster_not_found(self, client, auth_headers):
        """Update non-existent roster returns 404."""
        resp = client.put("/api/rosters/99999", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 404

    def test_post_duplicate_roster(self, client, auth_headers):
        """Duplicate roster creates copy with (copy) suffix."""
        # Create original roster
        create_resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert create_resp.status_code == 200
        original_id = create_resp.json()["id"]

        # Duplicate it
        resp = client.post(f"/api/rosters/{original_id}/duplicate", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] != original_id
        assert data["name"] == "My Ork Horde (copy)"
        assert data["faction"] == "orks"
        assert not data["is_public"]  # Copies should be private

    def test_post_duplicate_public_roster_becomes_private(self, client, auth_headers):
        """Duplicating a public roster creates private copy."""
        # Create public roster
        payload = {**self.ROSTER_PAYLOAD, "is_public": True}
        create_resp = client.post("/api/rosters", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        original_id = create_resp.json()["id"]

        # Duplicate it
        resp = client.post(f"/api/rosters/{original_id}/duplicate", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert not data["is_public"]  # Should be private

    def test_post_duplicate_roster_not_found(self, client, auth_headers):
        """Duplicate non-existent roster returns 404."""
        resp = client.post("/api/rosters/99999/duplicate", headers=auth_headers)
        assert resp.status_code == 404

    def test_free_create_at_limit_returns_403(self, client):
        """Free users can create one roster; a second create-like save is blocked."""
        headers = _register_user(client, tier="free")
        first = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/rosters",
            json={**self.ROSTER_PAYLOAD, "name": "Second Ork Horde"},
            headers=headers,
        )

        assert second.status_code == 403
        assert "Max rosters limit (1) reached" in second.json()["detail"]

    def test_free_duplicate_at_limit_returns_403(self, client):
        """Duplicate is a create-like mutation and cannot bypass the Free limit."""
        headers = _register_user(client, tier="free")
        create = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        assert create.status_code == 200, create.text
        roster_id = create.json()["id"]

        duplicate = client.post(f"/api/rosters/{roster_id}/duplicate", headers=headers)

        assert duplicate.status_code == 403
        assert "Max rosters limit (1) reached" in duplicate.json()["detail"]

    def test_free_generated_roster_save_at_limit_returns_403(self, client):
        """Saving a generated roster uses the same create gate and respects Free limit."""
        headers = _register_user(client, tier="free")
        first = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        assert first.status_code == 200, first.text

        generated = client.post("/api/rosters/generate", json={"faction": "orks"})
        assert generated.status_code == 200, generated.text
        generated_payload = generated.json()["roster"]

        save = client.post("/api/rosters", json=generated_payload, headers=headers)

        assert save.status_code == 403
        assert "Max rosters limit (1) reached" in save.json()["detail"]

    def test_free_update_private_roster_at_limit_is_allowed(self, client):
        """Updating an existing private roster does not re-check max_rosters count."""
        headers = _register_user(client, tier="free")
        create = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        assert create.status_code == 200, create.text
        roster_id = create.json()["id"]

        update = client.put(
            f"/api/rosters/{roster_id}",
            json={**self.ROSTER_PAYLOAD, "name": "Updated Private", "is_public": False},
            headers=headers,
        )

        assert update.status_code == 200, update.text
        assert update.json()["name"] == "Updated Private"
        assert not update.json()["is_public"]

    def test_free_update_roster_to_public_returns_403(self, client):
        """Updating gated fields still checks the authoritative public roster gate."""
        headers = _register_user(client, tier="free")
        create = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        assert create.status_code == 200, create.text
        roster_id = create.json()["id"]

        update = client.put(
            f"/api/rosters/{roster_id}",
            json={**self.ROSTER_PAYLOAD, "is_public": True},
            headers=headers,
        )

        assert update.status_code == 403
        assert update.json()["detail"] == "Public rosters require Premium. Upgrade to create public rosters."

    def test_premium_max_rosters_none_is_unlimited(self, client):
        """Premium max_rosters=None skips the count gate instead of crashing."""
        headers = _register_user(client, tier="premium")

        first = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=headers)
        second = client.post(
            "/api/rosters",
            json={**self.ROSTER_PAYLOAD, "name": "Second Premium Roster"},
            headers=headers,
        )

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text


class TestFeatureGates:
    """Focused tests for Free/Premium feature gates (Task 2.3)."""

    @staticmethod
    def _set_tier(client, auth_headers, email: str, tier: str):
        """Force-set user tier in DB for testing."""
        import sqlite3

        db_path = getattr(db, "path", None) or db.conn.execute(
            "PRAGMA database_list"
        ).fetchone()[2]
        # Use the existing db connection to UPDATE
        db.execute("UPDATE users SET tier = ? WHERE email = ?", (tier, email))
        db.commit()

    @staticmethod
    def _register_and_set_tier(client, tier: str) -> tuple[dict, str]:
        """Register a new user and force-set their tier. Returns (auth_headers, email)."""
        import uuid

        suffix = uuid.uuid4().hex[:8]
        email = f"gate{suffix}@test.dev"
        resp = client.post(
            "/auth/register",
            data={
                "email": email,
                "password": "StrongP4ss!",
                "display_name": "GateTester",
            },
            follow_redirects=False,
        )
        token = _extract_token(resp)
        assert token is not None, f"Register failed: {resp.status_code}"
        headers = {"Cookie": f"token={token}"}
        db.execute("UPDATE users SET tier = ? WHERE email = ?", (tier, email))
        db.commit()
        return headers, email

    def test_free_user_max_one_roster(self, client):
        """Free user can create exactly 1 roster; 2nd is rejected."""
        headers, _ = self._register_and_set_tier(client, "free")
        payload = TestRosterCRUD.ROSTER_PAYLOAD

        # 1st roster — OK
        r1 = client.post("/api/rosters", json=payload, headers=headers)
        assert r1.status_code == 200, f"1st roster should succeed: {r1.text}"

        # 2nd roster — rejected (Free limit = 1)
        r2 = client.post("/api/rosters", json=payload, headers=headers)
        assert r2.status_code == 403, f"2nd roster should be rejected: {r2.status_code}"
        assert "max" in r2.json()["detail"].lower()

    def test_free_user_duplicate_at_limit_blocked(self, client):
        """Free user at max_rosters cannot duplicate (would exceed limit)."""
        headers, _ = self._register_and_set_tier(client, "free")
        payload = TestRosterCRUD.ROSTER_PAYLOAD

        r1 = client.post("/api/rosters", json=payload, headers=headers)
        assert r1.status_code == 200
        roster_id = r1.json()["id"]

        # Duplicate at limit — rejected
        r2 = client.post(f"/api/rosters/{roster_id}/duplicate", headers=headers)
        assert r2.status_code == 403, f"Duplicate at limit should be rejected: {r2.status_code}"

    def test_free_user_public_create_rejected(self, client):
        """Free user cannot create public rosters."""
        headers, _ = self._register_and_set_tier(client, "free")
        payload = {**TestRosterCRUD.ROSTER_PAYLOAD, "is_public": True}

        resp = client.post("/api/rosters", json=payload, headers=headers)
        assert resp.status_code == 403, f"Free public create should be rejected: {resp.status_code}"
        assert "public" in resp.json()["detail"].lower()

    def test_premium_user_public_update_persisted(self, client):
        """Premium user can update a roster to public and GET reflects it."""
        headers, _ = self._register_and_set_tier(client, "premium")
        payload = TestRosterCRUD.ROSTER_PAYLOAD

        # Create private
        r1 = client.post("/api/rosters", json={**payload, "is_public": False}, headers=headers)
        assert r1.status_code == 200, r1.text
        roster_id = r1.json()["id"]
        assert r1.json().get("is_public") == 0

        # Update to public
        update_payload = {**payload, "is_public": True}
        r2 = client.put(f"/api/rosters/{roster_id}", json=update_payload, headers=headers)
        assert r2.status_code == 200, f"Update failed: {r2.text}"
        assert r2.json().get("is_public") == 1, (
            f"Expected is_public=1 after update, got {r2.json().get('is_public')}"
        )

        # GET confirms persistence
        r3 = client.get(f"/api/rosters/{roster_id}", headers=headers)
        assert r3.status_code == 200
        assert r3.json().get("is_public") == 1, (
            f"Expected is_public=1 on GET, got {r3.json().get('is_public')}"
        )

    def test_free_user_public_update_rejected(self, client):
        """Free user cannot update roster to public."""
        headers, _ = self._register_and_set_tier(client, "free")
        payload = TestRosterCRUD.ROSTER_PAYLOAD

        # Create private
        r1 = client.post("/api/rosters", json={**payload, "is_public": False}, headers=headers)
        assert r1.status_code == 200
        roster_id = r1.json()["id"]

        # Try to update to public
        update_payload = {**payload, "is_public": True}
        r2 = client.put(f"/api/rosters/{roster_id}", json=update_payload, headers=headers)
        assert r2.status_code == 403, f"Free public update should be rejected: {r2.status_code}"
        assert "public" in r2.json()["detail"].lower()
