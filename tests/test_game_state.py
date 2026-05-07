"""Test the game state management."""

import numpy as np
import pytest

from backend.state.game_state import (
    GamePhase,
    GameState,
    PlayerState,
    TerrainType,
    UnitState,
    create_empty_game,
    create_standard_map,
)


def test_unit_state_properties():
    """Test UnitState properties."""
    unit = UnitState(
        unit_id="test_unit",
        name="Test Marine",
        faction="Space Marines",
        position=(1, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=2,
    )

    assert unit.is_alive
    assert unit.wounds_per_model == 4.0

    # Test damaged unit
    unit.current_wounds = 0
    assert not unit.is_alive
    assert unit.wounds_per_model == 0


def test_player_state_properties():
    """Test PlayerState properties."""
    player = PlayerState(
        player_id="player1",
        name="Test Player",
        faction="Space Marines",
        command_points=8,
        victory_points=5,
    )

    # Add units
    unit1 = UnitState(
        unit_id="unit1",
        name="Marine",
        faction="Space Marines",
        position=(0, 0),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=2,
    )
    unit2 = UnitState(
        unit_id="unit2",
        name="Terminator",
        faction="Space Marines",
        position=(1, 1),
        current_wounds=6,
        max_wounds=6,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=3,
        is_warlord=True,
    )

    player.units = {"unit1": unit1, "unit2": unit2}

    assert player.total_objective_control == 5  # 2 + 3
    assert player.warlord_unit == unit2


def test_game_state_initialization():
    """Test GameState initialization."""
    game = create_empty_game("test_game", "Test Mission")

    assert game.game_id == "test_game"
    assert game.mission_name == "Test Mission"
    assert game.current_round == 1
    assert game.current_phase == GamePhase.COMMAND
    assert game.map_width == 6
    assert game.map_height == 4
    assert game.terrain_map.shape == (4, 6)
    assert np.all(game.terrain_map == TerrainType.OPEN_GROUND)


def test_game_state_unit_operations():
    """Test unit operations in GameState."""
    game = create_empty_game("test_game")

    # Add players
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game.players = {"p1": player1, "p2": player2}

    # Add units
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
    )
    unit2 = UnitState(
        unit_id="ork1",
        name="Ork Boy",
        faction="Orks",
        position=(5, 3),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=5,
        objective_control=1,
    )

    player1.units = {"marine1": unit1}
    player2.units = {"ork1": unit2}

    # Test finding units
    found_unit = game.get_unit_at_position(0, 0)
    assert found_unit == unit1

    found_unit = game.get_unit_at_position(5, 3)
    assert found_unit == unit2

    found_unit = game.get_unit_at_position(1, 1)
    assert found_unit is None

    # Test moving units
    assert game.move_unit("marine1", (1, 1))
    assert unit1.position == (1, 1)
    assert unit1.has_moved

    # Test invalid moves
    assert not game.move_unit("marine1", (5, 3))  # Position occupied
    assert not game.move_unit("marine1", (-1, 0))  # Out of bounds
    assert not game.move_unit("marine1", (1, 1))  # Same position

    # Test dealing damage
    assert game.deal_damage("ork1", 2)
    assert unit2.current_wounds == 2
    assert unit2.is_alive

    assert game.deal_damage("ork1", 3)
    assert unit2.current_wounds == 0
    assert not unit2.is_alive


def test_game_state_victory_points():
    """Test victory points tracking."""
    game = create_empty_game("test_game")

    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game.players = {"p1": player1, "p2": player2}

    # Add victory points
    game.add_victory_points("p1", 3)
    game.add_victory_points("p2", 5)
    game.add_victory_points("p1", 2)

    assert player1.victory_points == 5
    assert player2.victory_points == 5

    # is_game_over triggered by round limit only (not VP cap)
    assert not game.is_game_over

    # Winner determined when VP differ
    game.current_round = game.max_rounds + 1  # force end
    assert game.is_game_over
    assert game.winner is None  # 5-5 tie


def test_game_state_phases():
    """Test phase transitions."""
    game = create_empty_game("test_game")

    assert game.current_round == 1
    assert game.current_phase == GamePhase.COMMAND

    # Advance through phases
    game.next_phase()
    assert game.current_phase == GamePhase.MOVEMENT

    game.next_phase()
    assert game.current_phase == GamePhase.SHOOTING

    game.next_phase()
    assert game.current_phase == GamePhase.CHARGE

    game.next_phase()
    assert game.current_phase == GamePhase.FIGHT

    # Next phase should start new round
    game.next_phase()
    assert game.current_round == 2  # new round
    assert game.current_phase == GamePhase.COMMAND


def test_standard_map_creation():
    """Test standard map creation."""
    terrain_map = create_standard_map()

    assert terrain_map.shape == (4, 6)
    assert terrain_map[0, 5] == TerrainType.DANGEROUS_TERRAIN
    assert terrain_map[1, 2] == TerrainType.DIFFICULT_TERRAIN
    assert terrain_map[2, 3] == TerrainType.DIFFICULT_TERRAIN
    assert terrain_map[0, 0] == TerrainType.OPEN_GROUND


def test_game_summary():
    """Test game summary generation."""
    game = create_empty_game("test_game", "Test Mission")
    game.current_round = 3
    game.current_phase = GamePhase.SHOOTING

    player1 = PlayerState("p1", "Alice", "Space Marines", victory_points=7)
    player2 = PlayerState("p2", "Bob", "Orks", victory_points=4)
    game.players = {"p1": player1, "p2": player2}

    summary = game.get_game_summary()

    assert summary["game_id"] == "test_game"
    assert summary["mission"] == "Test Mission"
    assert summary["round"] == 3
    assert summary["phase"] == "shooting"
    assert summary["players"]["p1"]["vp"] == 7
    assert summary["players"]["p2"]["vp"] == 4
    assert not summary["is_game_over"]
    assert summary["winner"] is None
