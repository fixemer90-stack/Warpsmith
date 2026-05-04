"""
Tests for F3.5 — Auto-play: AI vs AI Full Scenario.
"""

import pytest

from backend.engine.ai.autoplay import (
    AutoPlayConfig,
    AutoPlayResult,
    InvalidRosterError,
    TimeoutError,
    resolve_ai_for_faction,
    run_auto_game,
)
from backend.engine.ai.deployment import DeploymentType
from backend.model.unit import Unit, Weapon
from backend.state.mission import Mission, MissionConfig, MissionObjective
from backend.state.roster import RosterState


def make_test_unit(name: str, faction: str = "test") -> Unit:
    """Create a simple test unit."""
    return Unit(
        name=name,
        faction=faction,
        category="Infantry",
        movement=5,
        toughness=3,
        save=3,
        wounds=2,
        leadership=7,
        objective_control=1,
        ranged_weapons=[
            Weapon(
                name="Test Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(1, 6, 0),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(1, 3, 0),
            )
        ],
        points=100,
    )


def make_test_roster(
    units: list[Unit] | None = None, faction: str = "test", pts: int = 500
) -> RosterState:
    """Create a test roster."""
    if units is None:
        units = [make_test_unit(f"Unit {i}", faction) for i in range(3)]
    unit_dict = {u.name: u for u in units}
    return RosterState(
        name=f"{faction} roster",
        faction=faction,
        total_pts=pts,
        units=unit_dict,
        warlord_unit_name=units[0].name,
    )


from dataclasses import dataclass


@dataclass
class _TestMission:
    """Minimal mission stub for autoplay tests."""

    name: str = "only_war"
    objectives: list = list


def make_test_mission(name: str = "only_war"):
    """Create a minimal test mission."""
    return _TestMission(name=name)


# ── resolve_ai_for_faction ───────────────────────────────────────


def test_resolve_ai_for_faction_orks():
    """Ork faction returns an AI profile (FactionAIProfile or function)."""
    ai = resolve_ai_for_faction("orks")
    assert ai is not None


def test_resolve_ai_for_faction_tau():
    """T'au faction returns an AI profile."""
    ai = resolve_ai_for_faction("tau")
    assert ai is not None


def test_resolve_ai_for_faction_unknown():
    """Unknown faction falls back to choose_action function."""
    ai = resolve_ai_for_faction("unknown_faction")
    assert callable(ai)


# ── run_auto_game ────────────────────────────────────────────────


def test_run_auto_game_basic():
    """Full simulation completes without errors."""
    roster_a = make_test_roster(faction="orks", pts=1000)
    roster_b = make_test_roster(faction="tau", pts=1000)
    mission = make_test_mission()
    result = run_auto_game(roster_a, roster_b, mission)
    assert result.error is None


def test_auto_game_returns_result():
    """Result is an AutoPlayResult with proper fields."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        make_test_mission(),
    )
    assert isinstance(result, AutoPlayResult)
    assert result.summary["winner"] in [1, 2, None]


def test_invalid_roster_returns_error():
    """Roster exceeding PTS limit returns error."""
    roster_a = make_test_roster(pts=9999)  # exceeds max_pts
    result = run_auto_game(roster_a, make_test_roster(faction="tau"), make_test_mission())
    assert result.error is not None
    assert "validation" in result.error.lower()


def test_single_unit_roster():
    """Roster with 1 unit does not crash."""
    unit = make_test_unit("Solo", "orks")
    roster = make_test_roster(units=[unit], pts=500)
    result = run_auto_game(roster, make_test_roster(faction="tau"), make_test_mission())
    assert result.error is None


def test_timeout_returns_partial():
    """Very short timeout returns partial result."""
    config = AutoPlayConfig(time_limit_seconds=0.001)
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        make_test_mission(),
        config,
    )
    assert result.error is not None
    assert "timeout" in result.error.lower()
    assert len(result.round_logs) < 5  # not all rounds


def test_reproducible_with_seed():
    """Same seed produces same result."""
    config = AutoPlayConfig(seed=42)
    result1 = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        make_test_mission(),
        config,
    )
    result2 = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        make_test_mission(),
        config,
    )
    assert result1.summary["winner"] == result2.summary["winner"]


def test_ork_vs_ork():
    """Same faction vs itself works."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="orks"),
        make_test_mission(),
    )
    assert result.error is None


def test_unknown_faction_uses_default_ai():
    """Unknown faction does not crash (uses choose_action fallback)."""
    roster = make_test_roster(faction="unknown_faction")
    result = run_auto_game(roster, make_test_roster(faction="tau"), make_test_mission())
    assert result.error is None


def test_auto_game_duration_measured():
    """Duration is measured and reported."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        make_test_mission(),
    )
    assert result.total_duration_ms > 0
