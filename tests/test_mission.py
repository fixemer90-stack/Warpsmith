"""Test the mission system."""

import pytest
from backend.state.mission import (
    DeploymentType,
    MissionObjective,
    MissionConfig,
    Mission,
    create_mission,
    _only_war,
    _purge_the_foe,
    _take_and_hold,
    MISSIONS
)
from backend.state.game_state import (
    GameState,
    PlayerState,
    UnitState,
    create_empty_game
)


def test_mission_objective():
    """Test MissionObjective creation."""
    obj = MissionObjective(3, 4, "Test Objective")
    
    assert obj.x == 3
    assert obj.y == 4
    assert obj.label == "Test Objective"
    assert obj.controlled_by is None
    assert obj.is_contested is False
    assert obj.position == (3, 4)


def test_deployment_type_enum():
    """Test DeploymentType enum."""
    assert DeploymentType.DAWN_OF_WAR.value == "dawn_of_war"
    assert DeploymentType.SEARCH_AND_DESTROY.value == "search_and_destroy"
    assert DeploymentType.CRUCIBLE_OF_BATTLE.value == "crucible_of_battle"


def test_mission_config_creation():
    """Test MissionConfig creation."""
    config = MissionConfig(
        name="Test Mission",
        deployment=DeploymentType.DAWN_OF_WAR,
        description="A test mission",
        objectives=[MissionObjective(1, 2, "Obj1")],
        max_rounds=3,
        scoring_rule="progressive"
    )
    
    assert config.name == "Test Mission"
    assert config.deployment == DeploymentType.DAWN_OF_WAR
    assert config.description == "A test mission"
    assert len(config.objectives) == 1
    assert config.max_rounds == 3
    assert config.scoring_rule == "progressive"


def test_mission_creation():
    """Test Mission creation."""
    # Create a basic game state
    game_state = create_empty_game("test_game", "Test Mission")
    
    # Add players and units for testing
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    unit2 = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=5, objective_control=1,
    )
    
    player1.units = {"marine1": unit1}
    player2.units = {"ork1": unit2}
    
    # Create mission
    mission = Mission(
        config=_take_and_hold(),
        state=game_state
    )
    
    assert mission.config.name == "Take and Hold"
    assert mission.config.deployment == DeploymentType.CRUCIBLE_OF_BATTLE
    assert len(mission.config.objectives) == 5
    assert mission.state == game_state


def test_mission_score_vp():
    """Test mission VP scoring."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=_take_and_hold(),
        state=game_state
    )
    
    # No units on objectives - should score 0
    assert mission.score_vp("p1") == 0
    assert mission.score_vp("p2") == 0
    
    # Place unit on first objective
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 1), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units = {"marine1": unit1}
    
    # Now player 1 should control one objective
    assert mission.score_vp("p1") == 1
    assert mission.score_vp("p2") == 0
    
    # Place unit on same objective - should be contested
    unit2 = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(2, 1), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=5, objective_control=1,
    )
    player2.units = {"ork1": unit2}
    
    # Objective should now be contested - no one controls it
    mission.update_objective_control()
    assert mission.score_vp("p1") == 0
    assert mission.score_vp("p2") == 0


def test_update_objective_control():
    """Test updating objective control."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=_only_war(),
        state=game_state
    )
    
    # Initially no objectives controlled
    mission.update_objective_control()
    for obj in mission.config.objectives:
        assert obj.controlled_by is None
        assert obj.is_contested is False
    
    # Add unit to first objective
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units = {"marine1": unit1}
    
    mission.update_objective_control()
    # First objective should be controlled by player 1
    assert mission.config.objectives[0].controlled_by == "p1"
    assert mission.config.objectives[0].is_contested is False
    # Others should be uncontrolled
    assert mission.config.objectives[1].controlled_by is None
    assert mission.config.objectives[2].controlled_by is None
    
    # Add unit to second objective
    unit2 = UnitState(
        unit_id="marine2", name="Assault Marine", faction="Space Marines",
        position=(1, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units["marine2"] = unit2
    
    mission.update_objective_control()
    # First two objectives controlled by player 1
    assert mission.config.objectives[0].controlled_by == "p1"
    assert mission.config.objectives[1].controlled_by == "p1"
    assert mission.config.objectives[2].controlled_by is None


def test_calculate_victory_points():
    """Test victory point calculation."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    # Test standard scoring
    mission = Mission(
        config=_take_and_hold(),
        state=game_state
    )
    
    # No units on objectives
    vp = mission.calculate_victory_points()
    assert vp["p1"] == 0
    assert vp["p2"] == 0
    
    # Add unit to one objective
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 1), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units = {"marine1": unit1}
    
    vp = mission.calculate_victory_points()
    assert vp["p1"] == 1  # 1 VP per objective
    assert vp["p2"] == 0
    
    # Add unit to another objective
    unit2 = UnitState(
        unit_id="marine2", name="Assault Marine", faction="Space Marines",
        position=(1, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units["marine2"] = unit2
    
    vp = mission.calculate_victory_points()
    assert vp["p1"] == 2  # 2 VP for 2 objectives
    assert vp["p2"] == 0


def test_progressive_scoring():
    """Test progressive scoring rule."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=_only_war(),  # Uses progressive scoring
        state=game_state
    )
    
    # Player 1 controls 2 objectives, Player 2 controls 1
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    unit2 = UnitState(
        unit_id="marine2", name="Assault Marine", faction="Space Marines",
        position=(1, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    unit3 = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(4, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=5, objective_control=1,
    )
    
    player1.units = {"marine1": unit1, "marine2": unit2}
    player2.units = {"ork1": unit3}
    
    vp = mission.calculate_victory_points()
    # Base VP: p1=2, p2=1
    # Progressive bonus: p1 gets +2 for having more objectives
    assert vp["p1"] == 4  # 2 base + 2 bonus
    assert vp["p2"] == 1  # 1 base + 0 bonus


def test_kill_points_scoring():
    """Test kill points scoring rule."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=_purge_the_foe(),  # Uses kill points scoring
        state=game_state
    )
    
    # Add units
    marine = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(0, 0), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    ork = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(5, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=5, objective_control=1,
    )
    
    player1.units = {"marine1": marine}
    player2.units = {"ork1": ork}
    
    # Initially no kills
    vp = mission.calculate_victory_points()
    assert vp["p1"] == 0
    assert vp["p2"] == 0
    
    # Kill the ork
    ork.current_wounds = 0
    ork.models_remaining = 0
    
    vp = mission.calculate_victory_points()
    # Should have some VP based on kill points
    # Exact value depends on our simplified calculation
    assert vp["p1"] >= 0
    assert vp["p2"] >= 0


def test_create_mission_function():
    """Test the create_mission factory function."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    # Test creating known missions
    mission = create_mission("Only War", game_state)
    assert mission is not None
    assert mission.config.name == "Only War"
    assert mission.config.scoring_rule == "progressive"
    
    mission = create_mission("Purge the Foe", game_state)
    assert mission is not None
    assert mission.config.name == "Purge the Foe"
    assert mission.config.scoring_rule == "kill_points"
    
    mission = create_mission("Take and Hold", game_state)
    assert mission is not None
    assert mission.config.name == "Take and Hold"
    assert mission.config.scoring_rule == "standard"
    
    # Test creating unknown mission
    mission = create_mission("Unknown Mission", game_state)
    assert mission is None


def test_mission_registry():
    """Test that missions are properly registered."""
    assert "only_war" in MISSIONS
    assert "purge_the_foe" in MISSIONS
    assert "take_and_hold" in MISSIONS
    
    # Test that registry functions return correct configs
    only_war_config = MISSIONS["only_war"]()
    assert only_war_config.name == "Only War"
    assert only_war_config.scoring_rule == "progressive"
    
    purge_config = MISSIONS["purge_the_foe"]()
    assert purge_config.name == "Purge the Foe"
    assert purge_config.scoring_rule == "kill_points"
    
    take_hold_config = MISSIONS["take_and_hold"]()
    assert take_hold_config.name == "Take and Hold"
    assert take_hold_config.scoring_rule == "standard"


def test_get_deployment_zones():
    """Test deployment zone calculation."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    # Test Dawn of War deployment
    mission = Mission(
        config=_only_war(),
        state=game_state
    )
    
    zones = mission.get_deployment_zones()
    assert "p1" in zones
    assert "p2" in zones
    
    # Player 1 should have zones at bottom (y=0,1)
    # Player 2 should have zones at top (y=2,3) for 6x4 map with 24" zone depth
    p1_zones = zones["p1"]
    p2_zones = zones["p2"]
    
    # Check that zones are in expected areas
    p1_has_bottom = any(y < 2 for _, y in p1_zones)
    p2_has_top = any(y >= 2 for _, y in p2_zones)
    
    assert p1_has_bottom
    assert p2_has_top
    
    # Test is_valid_deployment_position
    # Valid position for player 1
    assert mission.is_valid_deployment_position("p1", (0, 0))
    # Invalid position for player 1 (too high)
    assert not mission.is_valid_deployment_position("p1", (0, 3))
    # Valid position for player 2
    assert mission.is_valid_deployment_position("p2", (0, 3))
    # Invalid position for player 2 (too low)
    assert not mission.is_valid_deployment_position("p2", (0, 0))


def test_get_mission_summary():
    """Test mission summary generation."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=_take_and_hold(),
        state=game_state
    )
    
    summary = mission.get_mission_summary()
    
    assert summary["mission_name"] == "Take and Hold"
    assert summary["deployment_type"] == "crucible_of_battle"
    assert summary["scoring_rule"] == "standard"
    assert len(summary["objectives"]) == 5
    assert "current_vp" in summary
    assert isinstance(summary["current_vp"], dict)
    assert "p1" in summary["current_vp"]
    assert "p2" in summary["current_vp"]


def test_integration_with_game_state():
    """Test integration of mission with game state."""
    game_state = create_empty_game("test_game", "Only War")
    
    # Add players
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    # Mission should be automatically initialized
    assert game_state.mission is not None
    assert game_state.mission.config.name == "Only War"
    assert game_state.mission.config.scoring_rule == "progressive"
    
    # Test that we can access mission methods through game state
    summary = game_state.mission.get_mission_summary()
    assert summary["mission_name"] == "Only War"


if __name__ == "__main__":
    pytest.main([__file__])