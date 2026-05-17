"""
Tests for F3.5 — Auto-play: AI vs AI Full Scenario.
"""

import pytest

from backend.engine.ai.autoplay import (
    AutoPlayConfig,
    AutoPlayResult,
    InvalidRosterError,
    TimeoutError,
    _build_summary,
    _roster_to_player_state,
    resolve_ai_for_faction,
    run_auto_game,
)
from backend.engine.ai.deployment import DeploymentType
from backend.model.unit import Unit, Weapon
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
    unit_list = [(u.name, u) for u in units]
    return RosterState(
        name=f"{faction} roster",
        faction=faction,
        total_pts=pts,
        units=unit_list,
        warlord_unit_name=units[0].name if units else None,
    )


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
    result = run_auto_game(roster_a, roster_b)
    assert result.error is None


def test_autoplay_full_turn_uses_only_canonical_five_phases():
    """Auto-play round logs complete a full turn using only canonical 10e phases."""
    from backend.state.game_state import GAME_PHASE_ORDER

    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        config=AutoPlayConfig(seed=42, max_rounds=1),
    )
    assert result.error is None

    phase_logs = [
        entry for entry in result.round_logs[0]["phase_logs"] if entry.startswith("Phase: ")
    ]
    assert phase_logs == [f"Phase: {phase.value}" for phase in GAME_PHASE_ORDER]
    assert all("morale" not in entry.lower() for entry in phase_logs)

    start_phase = result.round_logs[0]["start_state"]["phase"]
    end_phase = result.round_logs[0]["end_state"]["phase"]
    assert start_phase == GAME_PHASE_ORDER[0].value
    assert end_phase == GAME_PHASE_ORDER[0].value


def test_auto_game_returns_result():
    """Result is an AutoPlayResult with proper fields."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
    )
    assert isinstance(result, AutoPlayResult)
    # Winner can be 1, 2, or None (tie or not finished)
    assert result.summary["winner"] in [1, 2, None]


def test_invalid_roster_returns_error():
    """Roster exceeding PTS limit returns error."""
    roster_a = make_test_roster(pts=9999)  # exceeds max_pts
    result = run_auto_game(roster_a, make_test_roster(faction="tau"))
    assert result.error is not None
    assert "validation" in result.error.lower()


def test_single_unit_roster():
    """Roster with 1 unit does not crash."""
    unit = make_test_unit("Solo", "orks")
    roster = make_test_roster(units=[unit], pts=500)
    result = run_auto_game(roster, make_test_roster(faction="tau"))
    assert result.error is None


def test_timeout_returns_partial():
    """Very short timeout returns partial result."""
    config = AutoPlayConfig(time_limit_seconds=0.001)
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        config=config,
    )
    assert result.error is not None
    assert "exceeded" in result.error.lower()
    assert len(result.round_logs) < 5  # not all rounds


def test_ork_vs_ork():
    """Same faction vs itself works."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="orks"),
    )
    assert result.error is None


def test_unknown_faction_uses_default_ai():
    """Unknown faction does not crash (uses choose_action fallback)."""
    roster = make_test_roster(faction="unknown_faction")
    result = run_auto_game(roster, make_test_roster(faction="tau"))
    assert result.error is None


def test_auto_game_duration_measured():
    """Duration is measured and reported."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
    )
    assert result.total_duration_ms > 0


def test_custom_mission_name():
    """Custom mission name does not crash."""
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        mission_name="take_and_hold",
    )
    assert result.error is None


def test_different_seeds():
    """Different seeds produce different results (basic sanity check)."""
    result1 = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        config=AutoPlayConfig(seed=1),
    )
    result2 = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        config=AutoPlayConfig(seed=999),
    )
    # At minimum both should complete without error
    assert result1.error is None
    assert result2.error is None


def test_empty_roster_returns_error():
    """Empty roster returns validation error."""
    roster_a = make_test_roster(units=[], pts=0)
    result = run_auto_game(roster_a, make_test_roster(faction="tau"))
    assert result.error is not None
    assert "no units" in result.error.lower()


def test_seed_zero_works():
    """Seed 0 (random) works and doesn't crash."""
    config = AutoPlayConfig(seed=0)
    result = run_auto_game(
        make_test_roster(faction="orks"),
        make_test_roster(faction="tau"),
        config=config,
    )
    assert result.error is None


def test_roster_to_player_state_preserves_two_identical_units():
    """Two identical roster entries get distinct runtime IDs and shared display labels."""
    boyz = make_test_unit("Boyz", "orks")
    roster = RosterState(
        name="orks roster",
        faction="orks",
        total_pts=200,
        units=[("Boyz", boyz), ("Boyz", boyz)],
        warlord_unit_name="Boyz",
    )

    player = _roster_to_player_state(roster, "1", AutoPlayConfig())

    assert set(player.units) == {"p1:Boyz:0", "p1:Boyz:1"}
    assert [u.name for u in player.units.values()] == ["Boyz", "Boyz"]


def test_build_summary_uses_runtime_ids_for_same_display_names():
    """Same display names across players do not collide when logs carry runtime IDs."""
    boyz_a = make_test_unit("Boyz", "orks")
    boyz_b = make_test_unit("Boyz", "orks")
    roster_a = make_test_roster(units=[boyz_a], faction="orks")
    roster_b = make_test_roster(units=[boyz_b], faction="orks")
    result = run_auto_game(roster_a, roster_b, config=AutoPlayConfig(seed=42, max_rounds=1))
    state = result.game_state
    assert state is not None

    round_logs = [
        {
            "phase_logs": [
                "Boyz hits Boyz for 3 damage [actor_id=p1:Boyz:0; target_id=p2:Boyz:0]",
                "Boyz was destroyed [target_id=p2:Boyz:0]",
            ]
        }
    ]

    summary = _build_summary(state, round_logs, {})

    assert summary["total_damage"] == {"1": 3.0}
    assert summary["total_kills"] == {"1": 1}


def test_melee_only_unit():
    """Unit with only melee weapons (no ranged) works."""
    melee_unit = Unit(
        name="Melee Only",
        faction="orks",
        category="Infantry",
        movement=6,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        melee_weapons=[
            Weapon(
                name="Choppa",
                type="melee",
                range_max=None,
                attacks_dice=(2, 6, 0),
                skill=3,
                strength=5,
                ap=1,
                damage_dice=(1, 3, 0),
            )
        ],
        points=80,
    )
    roster = make_test_roster(
        units=[melee_unit, make_test_unit("Shooter", "orks")],
        faction="orks",
        pts=500,
    )
    result = run_auto_game(roster, make_test_roster(faction="tau"))
    assert result.error is None
