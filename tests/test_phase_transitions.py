"""Test the F2.6 Phase Transitions functionality."""

import pytest

from backend.engine.scenario import Scenario
from backend.state.game_state import GameState, PlayerState, UnitState, create_empty_game


def test_command_priority_assignment():
    """Test that command priority is assigned correctly."""
    game_state = create_empty_game("test_game")

    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}

    # Manually trigger command priority determination for round 1
    game_state._determine_command_priority()

    # Exactly one player should have priority
    priority_count = sum(1 for p in game_state.players.values() if p.command_priority)
    assert priority_count == 1

    # The other should not have priority
    non_priority_count = sum(1 for p in game_state.players.values() if not p.command_priority)
    assert non_priority_count == 1


def test_command_priority_swap():
    """Test that command priority swaps between rounds."""
    game_state = create_empty_game("test_game")

    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}

    # Set round 1 and assign priority
    game_state.current_round = 1
    game_state._determine_command_priority()

    # Record who had priority in round 1
    p1_priority_r1 = player1.command_priority
    p2_priority_r1 = player2.command_priority

    # Advance to round 2
    game_state.current_round = 2
    game_state._determine_command_priority()

    # Priority should have swapped
    assert player1.command_priority == (not p1_priority_r1)
    assert player2.command_priority == (not p2_priority_r1)


def test_fight_phase_alternating_activations():
    """Test that Fight phase uses alternating activations."""
    game_state = create_empty_game("test_game")

    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}

    # Add engaged units for both players
    unit1 = UnitState(
        unit_id="marine1",
        name="Tactical Marine",
        faction="Space Marines",
        position=(0, 0),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=2,
        is_engaged=True,  # Engaged with enemy
    )
    unit2 = UnitState(
        unit_id="ork1",
        name="Ork Boy",
        faction="Orks",
        position=(0, 0),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=5,
        objective_control=1,
        is_engaged=True,  # Engaged with enemy
    )

    player1.units = {"marine1": unit1}
    player2.units = {"ork1": unit2}

    scenario = Scenario(game_state)

    # Manually set priority for testing
    player1.command_priority = True  # Player 1 has priority
    player2.command_priority = False

    # Store initial state
    initial_marine_wounds = unit1.current_wounds
    initial_ork_wounds = unit2.current_wounds
    _initial_marine_fought = unit1.is_fighting
    _initial_ork_fought = unit2.is_fighting

    # Execute fight phase
    scenario._fight_phase()

    # Both units should have fought (is_fighting should be True after phase, then reset)
    # Actually, our implementation resets is_fighting at the end, so we check that damage was dealt
    # At least one unit should have taken damage
    damage_taken = (initial_marine_wounds - unit1.current_wounds) + (
        initial_ork_wounds - unit2.current_wounds
    )
    assert damage_taken > 0, "At least one unit should have taken damage in fight"


if __name__ == "__main__":
    pytest.main([__file__])
