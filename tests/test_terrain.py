"""Regression tests for Task 5.3 — terrain/LoS/cover blockers."""

import pytest

from backend.state.game_state import TerrainType
from backend.state.map import BattlefieldMap


class TestSetTerrainInvalidatesLosCache:
    """set_terrain() clears the LoS cache."""

    def test_set_terrain_clears_cache(self) -> None:
        bf = BattlefieldMap.create_empty(6, 4)
        # Prime the cache
        assert bf.has_los(0, 0, 5, 3)
        assert len(bf._los_cache) > 0, "Cache should have entries after has_los()"

        # Change terrain — cache must be cleared
        bf.set_terrain(2, 2, TerrainType.RUINS)
        assert len(bf._los_cache) == 0, "LoS cache should be empty after set_terrain()"

    def test_set_terrain_cache_invalidation_rechecks_los(self) -> None:
        bf = BattlefieldMap.create_empty(6, 4)
        # Clear path initially
        assert bf.has_los(0, 0, 5, 3), "Should have LoS on empty map"

        # Block the path
        bf.set_terrain(3, 2, TerrainType.IMPASSABLE)
        # After cache invalidation, LoS should be rechecked and found blocked
        assert not bf.has_los(0, 0, 5, 3), (
            "LoS should be blocked after terrain changed to IMPASSABLE"
        )


class TestCoverArgumentOrder:
    """Cover helper gets target position first, shooter position second."""

    def test_has_cover_target_first(self) -> None:
        """Verify _has_cover grants cover when ruin blocks line between shooter and target."""
        import numpy as np

        from backend.engine.combat import _has_cover

        terrain = np.full((4, 6), TerrainType.OPEN_GROUND, dtype=object)
        # Place ruin at (2, 1) — Bresenham from (0,2) to (4,0) passes through (2,1)
        terrain[1, 2] = TerrainType.RUINS

        # Target at (0, 2), shooter at (4, 0) — ruins at (2,1) is on the line
        assert _has_cover((0, 2), (4, 0), terrain, "infantry"), (
            "Infantry target should get cover when ruin blocks line"
        )

    def test_scenario_cover_target_is_defender(self) -> None:
        """In scenario shooting, cover is checked with defender as target."""
        import numpy as np

        from backend.engine.combat import _has_cover

        terrain = np.full((4, 6), TerrainType.OPEN_GROUND, dtype=object)
        terrain[1, 2] = TerrainType.RUINS  # ruins at (2, 1)

        # Attacker at (0, 1), defender at (4, 1) — ruins at (2,1) between them
        # has_cover(defender_pos, attacker_pos, ...)
        assert _has_cover((4, 1), (0, 1), terrain, "infantry"), (
            "Defender (target) should get cover when ruin is between"
        )


class TestAP0CoverCap:
    """Cover against AP0 cannot improve save beyond 3+."""

    def test_ap0_cover_sv3_stays_3(self) -> None:
        """SV3+ with cover vs AP0 stays at SV3+ (cap)."""
        from backend.engine.combat import compute_save

        # SV3+ with cover vs AP0
        prob = compute_save(effective_sv=3, has_cover=True, ignores_cover=False, weapon_ap=0)
        # SV3+ save probability is (7-3)/6 = 4/6
        expected = (7 - 3) / 6
        assert prob == pytest.approx(expected), (
            f"SV3+ with AP0 cover cap: expected {expected}, got {prob}"
        )

    def test_ap0_cover_sv2_stays_2(self) -> None:
        """SV2+ with cover vs AP0 stays at SV2+ (already better than cap)."""
        from backend.engine.combat import compute_save

        prob = compute_save(effective_sv=2, has_cover=True, ignores_cover=False, weapon_ap=0)
        expected = (7 - 2) / 6  # 5/6
        assert prob == pytest.approx(expected), f"SV2+ with AP0: expected {expected}, got {prob}"

    def test_ap1_cover_sv3_becomes_2(self) -> None:
        """SV3+ with cover vs AP-1: AP-1 makes it SV4+, cover restores to SV3+."""
        from backend.engine.combat import compute_save

        # AP-1: effective_sv already adjusted (best_save(-1) for SV3+ = 4)
        # Cover: 4-1 = 3
        prob = compute_save(effective_sv=4, has_cover=True, ignores_cover=False, weapon_ap=-1)
        expected = (7 - 3) / 6  # 4/6
        assert prob == pytest.approx(expected), (
            f"SV3+ vs AP-1 with cover: expected {expected}, got {prob}"
        )

    def test_ap0_cover_sv4_becomes_3(self) -> None:
        """SV4+ with cover vs AP0 becomes SV3+ (allowed, cap is at 3+)."""
        from backend.engine.combat import compute_save

        prob = compute_save(effective_sv=4, has_cover=True, ignores_cover=False, weapon_ap=0)
        expected = (7 - 3) / 6  # 4/6
        assert prob == pytest.approx(expected), (
            f"SV4+ with AP0 cover: expected SV3+ ({expected}), got {prob}"
        )

    def test_ignores_cover_bypasses_cap(self) -> None:
        """Ignores Cover cancels cover benefit entirely."""
        from backend.engine.combat import compute_save

        prob = compute_save(effective_sv=3, has_cover=True, ignores_cover=True, weapon_ap=0)
        expected = (7 - 3) / 6  # no cover benefit
        assert prob == pytest.approx(expected), f"Ignores Cover: expected {expected}, got {prob}"


if __name__ == "__main__":
    pytest.main([__file__])
