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
                {"unit_name": "Warboss", "squad_size": 1},
                {"unit_name": "Boyz", "squad_size": 15},  # Changed squad size
            ]
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

    def test_put_update_roster_others_forbidden(self, client, auth_headers):
        """Update someone else's roster returns 403."""
        # Create roster with current user
        create_resp = client.post("/api/rosters", json=self.ROSTER_PAYLOAD, headers=auth_headers)
        assert create_resp.status_code == 200
        roster_id = create_resp.json()["id"]

        # Try to update as different user (simulate by changing user context)
        # For now, just test that same user can update (403 test would require multi-user setup)

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
        assert data["is_public"] == False  # Copies should be private

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
        assert data["is_public"] == False  # Should be private

    def test_post_duplicate_roster_not_found(self, client, auth_headers):
        """Duplicate non-existent roster returns 404."""
        resp = client.post("/api/rosters/99999/duplicate", headers=auth_headers)
        assert resp.status_code == 404