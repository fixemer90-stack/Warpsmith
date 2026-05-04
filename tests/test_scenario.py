"""Test the game loop scenario."""

import pytest

from backend.engine.scenario import Scenario
from backend.state.game_state import GameState, PlayerState, UnitState, create_empty_game


def test_scenario_creation():
    """Test Scenario creation."""
    game_state = create_empty_game("test_game")
    scenario = Scenario(game_state)

    assert scenario.state == game_state
    assert scenario.log == []


def test_run_round():
    """Test running a single round."""
    game_state = create_empty_game("test_game")

    # Add players
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}

    scenario = Scenario(game_state)

    # Run one round
    initial_round = game_state.current_round
    scenario.run_round()

    # Should have advanced to round 2
    assert game_state.current_round == initial_round + 1

    # Should have gone through all phases and ended on COMMAND
    assert game_state.current_phase == game_state.current_phase.COMMAND


def test_command_phase_cp_generation():
    """Test that command phase generates command points."""
    game_state = create_empty_game("test_game")

    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}

    scenario = Scenario(game_state)

    initial_cp_p1 = player1.command_points
    initial_cp_p2 = player2.command_points

    # Execute command phase directly
    scenario._command_phase()

    # Each player should have gained 1 CP
    assert player1.command_points == initial_cp_p1 + 1
    assert player2.command_points == initial_cp_p2 + 1


def test_get_state_summary():
    """Test getting state summary from scenario."""
    game_state = create_empty_game("test_game", "Test Mission")
    scenario = Scenario(game_state)

    summary = scenario.get_state_summary()

    assert "game_id" in summary
    assert "mission" in summary
    assert "round" in summary
    assert "phase" in summary
    assert "players" in summary


if __name__ == "__main__":
    pytest.main([__file__])
