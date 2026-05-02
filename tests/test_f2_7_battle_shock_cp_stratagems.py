"""Test the F2.7 Battle-shock, CP Generation, and Stratagems functionality."""

import pytest
import numpy as np
from backend.engine.scenario import Scenario
from backend.engine.stratagems import stratagem_registry
from backend.state.game_state import (
    GameState,
    PlayerState,
    UnitState,
    create_empty_game
)


def test_battle_shock_above_half_strength():
    """Test that units at or above half strength do not take battle-shock tests."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    game_state.players = {"p1": player1}
    
    # Unit at full strength (2/2 models)
    unit_full = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(0, 0), current_wounds=4, max_wounds=4,
        models_remaining=2, models_total=2, leadership=6,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player1.units = {"marine1": unit_full}
    
    scenario = Scenario(game_state)
    
    # Before morale phase
    assert unit_full.is_battle_shocked == False
    
    # Execute morale phase
    scenario._morale_phase()
    
    # Unit should not have taken battle-shock test and should remain unshocked
    assert unit_full.is_battle_shocked == False


def test_battle_shock_below_half_snake_eyes():
    """Test that snake eyes (2) causes battle-shock regardless of leadership."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    game_state.players = {"p1": player1}
    
    # Unit below half strength (1/2 models)
    unit = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(0, 0), current_wounds=2, max_wounds=4,
        models_remaining=1, models_total=2, leadership=10,  # High leadership
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player1.units = {"marine1": unit}
    
    scenario = Scenario(game_state)
    
    # Mock random to always return snake eyes
    import random
    original_randint = random.randint
    random.randint = lambda a, b: 1  # Always return 1 (so 1+1=2)
    
    try:
        # Execute morale phase
        scenario._morale_phase()
        
        # Unit should have failed battle-shock
        assert unit.is_battle_shocked == True
    finally:
        # Restore original random function
        random.randint = original_randint


def test_battle_shock_below_half_boxcars():
    """Test that boxcars (12) prevents battle-shock regardless of leadership."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    game_state.players = {"p1": player1}
    
    # Unit below half strength (1/2 models) with low leadership
    unit = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(0, 0), current_wounds=2, max_wounds=4,
        models_remaining=1, models_total=2, leadership=2,  # Low leadership
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player1.units = {"marine1": unit}
    
    scenario = Scenario(game_state)
    
    # Mock random to always return boxcars
    import random
    original_randint = random.randint
    random.randint = lambda a, b: 6  # Always return 6 (so 6+6=12)
    
    try:
        # Execute morale phase
        scenario._morale_phase()
        
        # Unit should have passed battle-shock
        assert unit.is_battle_shocked == False
    finally:
        # Restore original random function
        random.randint = original_randint


def test_battle_shock_normal_roll():
    """Test battle-shock with normal dice roll."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    game_state.players = {"p1": player1}
    
    # Unit below half strength (1/2 models) with leadership 7
    unit = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(0, 0), current_wounds=2, max_wounds=4,
        models_remaining=1, models_total=2, leadership=7,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player1.units = {"marine1": unit}
    
    scenario = Scenario(game_state)
    
    # Mock random to return 3 and 4 (total 7)
    import random
    call_count = 0
    def mock_randint(a, b):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return 3  # First die
        else:
            return 4  # Second die
    
    original_randint = random.randint
    random.randint = mock_randint
    
    try:
        # Execute morale phase
        scenario._morale_phase()
        
        # Roll is 7, leadership is 7, so roll >= LD -> pass (not shocked)
        assert unit.is_battle_shocked == False
    finally:
        # Restore original random function
        random.randint = original_randint


def test_cp_generation_with_warlord():
    """Test that players with warlords generate 2 CP, others 1."""
    game_state = create_empty_game("test_game")
    
    # Player with warlord
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    warlord_unit = UnitState(
        unit_id="warlord1", name="Captain", faction="Space Marines",
        position=(0, 0), current_wounds=5, max_wounds=5,
        models_remaining=1, models_total=1, leadership=9,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
        is_warlord=True,  # This is a warlord
    )
    player1.units = {"warlord1": warlord_unit}
    player1.command_points = 0
    
    # Player without warlord
    player2 = PlayerState("p2", "Player 2", "Orks")
    regular_unit = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(5, 5), current_wounds=3, max_wounds=3,
        models_remaining=1, models_total=1, leadership=5,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player2.units = {"ork1": regular_unit}
    player2.command_points = 0
    
    game_state.players = {"p1": player1, "p2": player2}
    
    scenario = Scenario(game_state)
    
    # Execute command phase
    scenario._command_phase()
    
    # Player with warlord should have 2 CP (1 base + 1 warlord)
    assert player1.command_points == 2
    # Player without warlord should have 1 CP (1 base)
    assert player2.command_points == 1


def test_cp_generation_with_leviant_cap():
    """Test that CP generation respects the Leviathan cap of 10."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    warlord_unit = UnitState(
        unit_id="warlord1", name="Captain", faction="Space Marines",
        position=(0, 0), current_wounds=5, max_wounds=5,
        models_remaining=1, models_total=1, leadership=9,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
        is_warlord=True,
    )
    player1.units = {"warlord1": warlord_unit}
    player1.command_points = 9  # Already high
    
    player2 = PlayerState("p2", "Player 2", "Orks")
    regular_unit = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(5, 5), current_wounds=3, max_wounds=3,
        models_remaining=1, models_total=1, leadership=5,
        objective_control=0,
        is_engaged=False, is_fighting=False, is_battle_shocked=False,
    )
    player2.units = {"ork1": regular_unit}
    player2.command_points = 9  # Already high
    
    game_state.players = {"p1": player1, "p2": player2}
    
    scenario = Scenario(game_state)
    
    # Execute command phase
    scenario._command_phase()
    
    # Both should be capped at 10
    # Player 1: 9 + min(2, 10-9) = 9 + 1 = 10
    # Player 2: 9 + min(1, 10-9) = 9 + 1 = 10
    assert player1.command_points == 10
    assert player2.command_points == 10


def test_stratagem_registry_has_core_stratagems():
    """Test that the stratagem registry has the expected core stratagems."""
    expected_stratagems = {
        "Command Re-roll",
        "Insane Bravery", 
        "Counter-Offensive",
        "Tank Shock"
    }
    
    actual_stratagems = set(stratagem_registry._stratagems.keys())
    assert expected_stratagems.issubset(actual_stratagems)


def test_command_re_roll_stratagem():
    """Test that Command Re-roll stratagem can be retrieved and has correct properties."""
    stratagem = stratagem_registry.get("Command Re-roll")
    assert stratagem is not None
    assert stratagem.name == "Command Re-roll"
    assert stratagem.cp_cost == 1
    assert stratagem.phase == "any"


def test_insane_bravery_stratagem():
    """Test that Insane Bravery stratagem can be retrieved and has correct properties."""
    stratagem = stratagem_registry.get("Insane Bravery")
    assert stratagem is not None
    assert stratagem.name == "Insane Bravery"
    assert stratagem.cp_cost == 1
    assert stratagem.phase == "morale"


def test_counter_offensive_stratagem():
    """Test that Counter-Offensive stratagem can be retrieved and has correct properties."""
    stratagem = stratagem_registry.get("Counter-Offensive")
    assert stratagem is not None
    assert stratagem.name == "Counter-Offensive"
    assert stratagem.cp_cost == 2
    assert stratagem.phase == "fight"


def test_tank_shock_stratagem():
    """Test that Tank Shock stratagem can be retrieved and has correct properties."""
    stratagem = stratagem_registry.get("Tank Shock")
    assert stratagem is not None
    assert stratagem.name == "Tank Shock"
    assert stratagem.cp_cost == 1
    assert stratagem.phase == "charge"


def test_stratagem_cp_deduction():
    """Test that using a stratagem deducts CP from the active player."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player1.command_points = 5
    game_state.players = {"p1": player1}
    game_state.active_player = "p1"  # Set active player
    
    # Use a stratagem that costs 1 CP
    original_cp = player1.command_points
    stratagem_registry.execute(game_state, "Command Re-roll")
    
    # CP should be reduced by 1
    assert player1.command_points == original_cp - 1


def test_stratagem_insufficient_cp():
    """Test that using a stratagem fails when player doesn't have enough CP."""
    game_state = create_empty_game("test_game")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player1.command_points = 0  # No CP
    game_state.players = {"p1": player1}
    game_state.active_player = "p1"  # Set active player
    
    # Try to use a stratagem that costs 1 CP
    with pytest.raises(ValueError, match="Not enough CP"):
        stratagem_registry.execute(game_state, "Command Re-roll")


def test_stratagem_wrong_phase():
    """Test that stratagems have correct phase restrictions."""
    # Insane Bravery should only be usable in morale phase
    insane_bravery = stratagem_registry.get("Insane Bravery")
    assert insane_bravery is not None
    assert insane_bravery.phase == "morale"
    
    # It should NOT be available in shooting phase
    # We don't have a direct method to check this, but we can verify the phase property


if __name__ == "__main__":
    pytest.main([__file__])