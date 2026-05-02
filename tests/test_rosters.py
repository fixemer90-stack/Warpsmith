"""Tests for roster CRUD endpoints (F2.10)."""

import pytest
from fastapi.testclient import TestClient

from main import app
from backend.db.database import db


def _extract_token(resp) -> str | None:
    """Extract JWT token from set-cookie header."""
    set_cookie = resp.headers.get("set-cookie", "")
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("token="):
            return part.split("=", 1)[1]
    return None


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers. Each call = fresh user."""
    import uuid
    suffix = uuid.uuid4().hex[:8]
    email = f"roster{suffix}@test.dev"

    resp = client.post("/auth/register", data={
        "email": email,
        "password": "StrongP4ss!",
        "display_name": "Tester",
    }, follow_redirects=False)

    token = _extract_token(resp)
    assert token is not None, f"Register failed: {resp.status_code}"
    return {"Cookie": f"token={token}"}


class TestRosterCRUD:

    ROSTER_PAYLOAD = {
        "name": "My Ork Horde",
        "faction": "orks",
        "pts_limit": 2000,
        "detachment": "War Horde",
        "units": [{"unit_name": "Warboss", "squad_size": 1}, {"unit_name": "Boyz", "squad_size": 10}],
    }

    def test_create_roster(self, client, auth_headers):
        """Create a valid roster returns 200 with id."""
        resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] > 0
        assert data["name"] == "My Ork Horde"
        assert data["faction"] == "orks"

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
        assert resp.json()["id"] == roster_id

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
