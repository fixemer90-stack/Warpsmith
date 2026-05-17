"""Tests for roster validation (F2.9)."""

import pytest

from backend.model.unit import Unit, Weapon
from backend.state.roster import validate_roster, validate_squad_size


def _make_unit(
    name: str = "TestUnit",
    points: int = 100,
    model_count: tuple[int, int] = (1, 5),
    keywords: list[str] | None = None,
    can_be_warlord: bool = False,
    is_epic_hero: bool = False,
) -> Unit:
    """Helper to build a Unit with minimal boilerplate."""
    min_sq, max_sq = model_count
    return Unit(
        name=name,
        faction="orks",
        category="Infantry",
        movement=6,
        toughness=5,
        save=5,
        wounds=1,
        leadership=7,
        objective_control=1,
        points=points,
        model_count=model_count,
        squad_size={"min": min_sq, "max": max_sq, "step": 1},
        keywords=keywords or ["Infantry", "Orks"],
        can_be_warlord=can_be_warlord,
        is_epic_hero=is_epic_hero,
    )


# ── Fixtures ─────────────────────────────────────────────


@pytest.fixture
def boyz():
    return _make_unit(
        "Boyz", points=85, model_count=(10, 20), keywords=["Infantry", "Battleline", "Orks"]
    )


@pytest.fixture
def warboss():
    return _make_unit(
        "Warboss",
        points=80,
        model_count=(1, 1),
        keywords=["Infantry", "Character", "Orks"],
        can_be_warlord=True,
    )


@pytest.fixture
def weirdboy():
    return _make_unit(
        "Weirdboy",
        points=65,
        model_count=(1, 1),
        keywords=["Infantry", "Character", "Orks"],
        can_be_warlord=True,
    )


@pytest.fixture
def ghaz():
    return _make_unit(
        "Ghazghkull Thraka",
        points=235,
        model_count=(1, 1),
        keywords=["Infantry", "Character", "Epic Hero", "Orks"],
        can_be_warlord=True,
        is_epic_hero=True,
    )


@pytest.fixture
def registry(boyz, warboss, weirdboy, ghaz):
    return {
        "Boyz": boyz,
        "Warboss": warboss,
        "Weirdboy": weirdboy,
        "Ghazghkull Thraka": ghaz,
    }


# ── Tests ────────────────────────────────────────────────


class TestValidateRoster:
    """Tests for validate_roster()."""

    def test_valid_roster(self, registry):
        """A standard legal roster passes."""
        units = [("Warboss", 1), ("Boyz", 10), ("Weirdboy", 1)]
        result = validate_roster(units, registry)
        assert result.is_valid
        assert result.total_pts > 0
        assert len(result.errors) == 0

    def test_valid_roster_minimal(self, registry):
        """Single Warlord + one unit = minimal valid roster."""
        units = [("Warboss", 1)]
        result = validate_roster(units, registry)
        assert result.is_valid
        assert result.total_pts == 80

    def test_pts_exceeded(self, registry):
        """Over the pts limit returns pts_exceeded error."""
        too_expensive = [("Warboss", 1)] * 100
        result = validate_roster(too_expensive, registry)
        assert not result.is_valid
        assert any(e.code == "pts_exceeded" for e in result.errors)

    def test_no_warlord(self, registry):
        """Roster without a Warlord-capable unit fails."""
        units = [("Boyz", 10)]
        result = validate_roster(units, registry)
        assert not result.is_valid
        assert any(e.code == "no_warlord" for e in result.errors)

    def test_too_many_copies_non_battleline(self, registry):
        """Non-Battleline units capped at 3 copies."""
        units = [("Warboss", 1)] * 4
        result = validate_roster(units, registry)
        assert not result.is_valid
        assert any(e.code == "too_many_copies" for e in result.errors)

    def test_battleline_allows_6_copies(self, registry, boyz):
        """Battleline units can have up to 6 copies."""
        units = [("Boyz", 10)] * 6
        result = validate_roster(units, registry)
        # Should pass the 6-copy check but may fail pts
        copies_errors = [e for e in result.errors if e.code == "too_many_copies"]
        assert len(copies_errors) == 0

    def test_battleline_rejects_7_copies(self, registry, boyz):
        """Battleline units rejected at 7 copies."""
        units = [("Boyz", 10)] * 7
        result = validate_roster(units, registry)
        assert any(e.code == "too_many_copies" for e in result.errors)

    def test_duplicate_epic_hero(self, registry, ghaz):
        """Epic Hero can only appear once."""
        units = [("Ghazghkull Thraka", 1), ("Ghazghkull Thraka", 1), ("Warboss", 1)]
        result = validate_roster(units, registry)
        assert any(e.code == "duplicate_epic_hero" for e in result.errors)

    def test_single_epic_hero_allowed(self, registry, ghaz):
        """One Epic Hero is fine."""
        units = [("Ghazghkull Thraka", 1), ("Warboss", 1)]
        result = validate_roster(units, registry)
        epic_errors = [e for e in result.errors if e.code == "duplicate_epic_hero"]
        assert len(epic_errors) == 0

    def test_empty_roster(self, registry):
        """Empty roster is rejected."""
        result = validate_roster([], registry)
        assert not result.is_valid
        assert any(e.code == "empty_roster" for e in result.errors)

    def test_unknown_unit(self, registry):
        """Unknown unit name generates an error."""
        units = [("Warboss", 1), ("NotAUnit", 5)]
        result = validate_roster(units, registry)
        assert not result.is_valid
        assert any(e.code == "unknown_unit" for e in result.errors)

    def test_pts_limit_override(self, registry):
        """Custom pts_limit is respected."""
        units = [("Warboss", 1), ("Weirdboy", 1)]  # 80 + 65 = 145
        result = validate_roster(units, registry, pts_limit=100)
        assert not result.is_valid
        assert any(e.code == "pts_exceeded" for e in result.errors)

    def test_total_models_tracked(self, registry):
        """total_models reflects squad count * max model per squad."""
        units = [("Boyz", 2), ("Warboss", 1)]
        result = validate_roster(units, registry)
        # Boyz max = 20 per squad, 2 squads = 40. Warboss max = 1.
        assert result.total_models == 41

    def test_game_size_incursion(self, registry):
        """Incursion (1000pts) enforces a tighter limit."""
        from backend.state.roster import GameSize

        units = [("Warboss", 1)] * 10  # 800pts, over 500
        result = validate_roster(units, registry, game_size=GameSize.INCURSION)
        assert result.total_pts <= 1000
        # 10 Warbosses = 800pts, should pass Incursion
        excess = [e for e in result.errors if e.code == "pts_exceeded"]
        assert len(excess) == 0, f"800pts should be OK for Incursion: {result.errors}"

    def test_game_size_combat_patrol_limits(self, registry):
        """Combat Patrol (500pts) rejects >500pts."""
        from backend.state.roster import GameSize

        units = [("Warboss", 10)]  # 800pts
        result = validate_roster(units, registry, game_size=GameSize.COMBAT_PATROL)
        assert any(e.code == "pts_exceeded" for e in result.errors)

    def test_game_size_onslaught(self, registry):
        """Onslaught (3000pts) is more permissive."""
        from backend.state.roster import GameSize

        units = [("Warboss", 25)]  # 2000pts
        result = validate_roster(units, registry, game_size=GameSize.ONSLAUGHT)
        excess = [e for e in result.errors if e.code == "pts_exceeded"]
        assert len(excess) == 0

    def test_game_size_properties(self):
        """GameSize enum exposes pts_limit and label."""
        from backend.state.roster import GameSize

        assert GameSize.STRIKE_FORCE.pts_limit == 2000
        assert GameSize.STRIKE_FORCE.label == "Strike Force (2000pts)"
        assert GameSize.INCURSION.pts_limit == 1000
        assert GameSize.ONSLAUGHT.pts_limit == 3000


class TestValidateSquadSize:
    """Tests for validate_squad_size()."""

    def test_valid_squad_size(self, boyz):
        """Squad within range returns None."""
        err = validate_squad_size("Boyz", 10, boyz)
        assert err is None

    def test_squad_too_small(self, warboss):
        """Below min size returns error."""
        err = validate_squad_size("Warboss", 0, warboss)
        assert err is not None
        assert err.code == "squad_too_small"

    def test_squad_too_large(self, boyz):
        """Above max size returns error."""
        err = validate_squad_size("Boyz", 30, boyz)
        assert err is not None
        assert err.code == "squad_too_large"

    def test_exact_min_size(self, boyz):
        """Exactly min size is valid."""
        err = validate_squad_size("Boyz", 10, boyz)
        assert err is None

    def test_exact_max_size(self, boyz):
        """Exactly max size is valid."""
        err = validate_squad_size("Boyz", 20, boyz)
        assert err is None


# ── Task 2.1 — Canonical PTS formula tests ──────────────────────────────


class TestCalculateSquadPts:
    """Tests for calculate_squad_pts()."""

    def test_boyz_minimum_squad(self):
        """Boyz minimum squad: 85 / 10 * 10 = 85."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=85, min_squad=10, squad_size=10)
        assert pts == 85, f"Expected 85, got {pts}"

    def test_boyz_expanded_squad(self):
        """Boyz expanded squad: 85 / 10 * 20 = 170."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=85, min_squad=10, squad_size=20)
        assert pts == 170, f"Expected 170, got {pts}"

    def test_boyz_with_per_model_loadout(self):
        """Boyz with per-model loadout upgrade: (85/10 + 5) * 10 = 135."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=85, min_squad=10, squad_size=10, loadout_pts=5)
        assert pts == 135, f"Expected 135, got {pts}"

    def test_boyz_with_nob_flat_upgrade(self):
        """Boyz with Nob flat upgrade: (85/10) * 10 + 25 = 110."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=85, min_squad=10, squad_size=10, nob_pts=25)
        assert pts == 110, f"Expected 110, got {pts}"

    def test_boyz_with_loadout_and_nob(self):
        """Boyz with loadout + Nob together: (85/10 + 5) * 10 + 25 = 160."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=85, min_squad=10, squad_size=10, loadout_pts=5, nob_pts=25)
        assert pts == 160, f"Expected 160, got {pts}"

    def test_nobz_min_squad_different(self):
        """Nobz with different minSquad: (50/2) * 2 = 50."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=50, min_squad=2, squad_size=2)
        assert pts == 50, f"Expected 50, got {pts}"

    def test_nobz_expanded(self):
        """Nobz expanded: (50/2) * 5 = 125."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=50, min_squad=2, squad_size=5)
        assert pts == 125, f"Expected 125, got {pts}"

    def test_single_model_vehicle(self):
        """Single-model vehicle with minSquad=1, squadSize=1: (120/1) * 1 = 120."""
        from backend.state.roster import calculate_squad_pts

        pts = calculate_squad_pts(points=120, min_squad=1, squad_size=1)
        assert pts == 120, f"Expected 120, got {pts}"

    def test_roster_total_pts_sum(self):
        """Roster totalPts equals sum of all squad_pts."""
        from backend.model.unit import Unit
        from backend.state.roster import RosterState, calculate_squad_pts, validate_roster

        # Create a minimal roster with 2 units
        boyz = Unit(
            name="Boyz",
            faction="orks",
            category="Infantry",
            movement=5,
            toughness=4,
            save=4,
            wounds=2,
            leadership=7,
            objective_control=1,
            points=85,
            model_count=(10, 20),
            squad_size={"min": 10, "max": 20, "step": 5},
            keywords=["Infantry", "Battleline", "Orks"],
        )
        warboss = Unit(
            name="Warboss",
            faction="orks",
            category="Character",
            movement=6,
            toughness=6,
            save=3,
            wounds=7,
            leadership=6,
            objective_control=2,
            points=80,
            model_count=(1, 1),
            squad_size={"min": 1, "max": 1, "step": 1},
            keywords=["Infantry", "Character", "Orks"],
            can_be_warlord=True,
        )

        registry = {"Boyz": boyz, "Warboss": warboss}
        units = [("Boyz", 10), ("Warboss", 1)]
        result = validate_roster(units, registry)

        # total_pts should equal sum of squad_pts
        expected_total = 85 + 80  # Boyz min squad 85 + Warboss 80
        assert result.total_pts == expected_total, (
            f"Expected {expected_total}, got {result.total_pts}"
        )

        squad_sum = sum(s["squad_pts"] for s in result.squad_pts)
        assert squad_sum == result.total_pts, (
            f"squad_pts sum {squad_sum} != total_pts {result.total_pts}"
        )

    def test_validate_roster_squad_pts_breakdown(self):
        """validate_roster returns squad_pts breakdown per unit."""
        from backend.model.unit import Unit
        from backend.state.roster import validate_roster

        warboss = Unit(
            name="Warboss",
            faction="orks",
            category="Character",
            movement=6,
            toughness=6,
            save=3,
            wounds=7,
            leadership=6,
            objective_control=2,
            points=80,
            model_count=(1, 1),
            squad_size={"min": 1, "max": 1, "step": 1},
            keywords=["Infantry", "Character", "Orks"],
            can_be_warlord=True,
        )

        result = validate_roster([("Warboss", 1)], {"Warboss": warboss})
        assert len(result.squad_pts) == 1
        entry = result.squad_pts[0]
        assert entry["unit_name"] == "Warboss"
        assert entry["squad_size"] == 1
        assert entry["base_pts"] == 80
        assert entry["min_squad"] == 1
        assert entry["squad_pts"] == 80

    def test_pts_exceeded_with_canonical_formula(self):
        """PTS exceeded error still works with canonical formula."""
        from backend.model.unit import Unit
        from backend.state.roster import validate_roster

        warboss = Unit(
            name="Warboss",
            faction="orks",
            category="Character",
            movement=6,
            toughness=6,
            save=3,
            wounds=7,
            leadership=6,
            objective_control=2,
            points=80,
            model_count=(1, 1),
            squad_size={"min": 1, "max": 1, "step": 1},
            keywords=["Infantry", "Character", "Orks"],
            can_be_warlord=True,
        )

        units = [("Warboss", 1)] * 100  # 8000pts
        result = validate_roster(units, {"Warboss": warboss}, pts_limit=2000)
        assert not result.is_valid
        assert any(e.code == "pts_exceeded" for e in result.errors)


class TestValidateRosterUpgraded:
    """Production-path tests: validate_roster() with loadout/nob PTS."""

    def _make_boyz(self) -> Unit:
        return Unit(
            name="Boyz",
            faction="orks",
            category="Infantry",
            movement=5,
            toughness=4,
            save=4,
            wounds=2,
            leadership=7,
            objective_control=1,
            points=85,
            model_count=(10, 20),
            squad_size={"min": 10, "max": 20, "step": 5},
            keywords=["Infantry", "Battleline", "Orks"],
        )

    def test_validate_roster_with_loadout_pts(self):
        """validate_roster with loadout_pts uses canonical formula."""
        boyz = self._make_boyz()
        result = validate_roster(
            [("Boyz", 10)],
            {"Boyz": boyz},
            loadout_pts=[5],
            nob_pts=[0],
        )
        # (85/10 + 5) * 10 = 135
        assert result.total_pts == 135, f"Expected 135, got {result.total_pts}"

    def test_validate_roster_with_nob_pts(self):
        """validate_roster with nob_pts uses canonical formula."""
        boyz = self._make_boyz()
        result = validate_roster(
            [("Boyz", 10)],
            {"Boyz": boyz},
            loadout_pts=[0],
            nob_pts=[25],
        )
        # (85/10) * 10 + 25 = 110
        assert result.total_pts == 110, f"Expected 110, got {result.total_pts}"

    def test_validate_roster_with_both_upgrades(self):
        """validate_roster with loadout + Nob uses canonical formula."""
        boyz = self._make_boyz()
        result = validate_roster(
            [("Boyz", 10)],
            {"Boyz": boyz},
            loadout_pts=[5],
            nob_pts=[25],
        )
        # (85/10 + 5) * 10 + 25 = 160
        assert result.total_pts == 160, f"Expected 160, got {result.total_pts}"

    def test_validate_roster_mixed_units_with_upgrades(self):
        """Mixed roster with upgrades: total_pts sums correctly."""
        boyz = self._make_boyz()
        warboss = Unit(
            name="Warboss",
            faction="orks",
            category="Character",
            movement=6,
            toughness=6,
            save=3,
            wounds=7,
            leadership=6,
            objective_control=2,
            points=80,
            model_count=(1, 1),
            squad_size={"min": 1, "max": 1, "step": 1},
            keywords=["Infantry", "Character", "Orks"],
            can_be_warlord=True,
        )
        result = validate_roster(
            [("Boyz", 10), ("Warboss", 1)],
            {"Boyz": boyz, "Warboss": warboss},
            loadout_pts=[5, 0],
            nob_pts=[25, 0],
        )
        # Boyz: (85/10 + 5) * 10 + 25 = 160, Warboss: (80/1 + 0) * 1 + 0 = 80
        expected = 160 + 80
        assert result.total_pts == expected, f"Expected {expected}, got {result.total_pts}"

        # Verify squad_pts breakdown
        assert len(result.squad_pts) == 2
        assert result.squad_pts[0]["squad_pts"] == 160
        assert result.squad_pts[1]["squad_pts"] == 80

    def test_validate_roster_upgraded_squad_pts_in_result(self):
        """squad_pts breakdown includes loadout/nob in per-squad total."""
        boyz = self._make_boyz()
        result = validate_roster(
            [("Boyz", 20)],
            {"Boyz": boyz},
            loadout_pts=[5],
            nob_pts=[25],
        )
        # (85/10 + 5) * 20 + 25 = 295
        assert len(result.squad_pts) == 1
        entry = result.squad_pts[0]
        assert entry["unit_name"] == "Boyz"
        assert entry["squad_size"] == 20
        assert entry["base_pts"] == 85
        assert entry["min_squad"] == 10
        assert entry["squad_pts"] == 295
