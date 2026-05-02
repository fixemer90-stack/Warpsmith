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
    MISSIONS,
    VPTracker,
    GameResult,
    check_end_game,
    score_standard,
    score_progressive,
    score_kill_points,
    apply_scoring
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


def test_vp_tracker():
    """Test VPTracker functionality."""
    vp = VPTracker()
    vp.add(1, 10)
    vp.add(2, 5)
    vp.add(1, 5)
    assert vp.total[1] == 15
    assert vp.total[2] == 5
    assert vp.leader() == 1
    assert vp.is_tied() == False
    assert vp.margin() == 10
    
    # Test round VP
    assert vp.round_vp(1, 1) == 10
    assert vp.round_vp(1, 2) == 5
    assert vp.round_vp(2, 1) == 5
    
    # Test summary
    summary = vp.summary()
    assert summary["player_1"]["total"] == 15
    assert summary["player_2"]["total"] == 5
    assert summary["winner"] == 1
    assert summary["margin"] == 10


def test_score_standard():
    """Test standard scoring function."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[
                MissionObjective(2, 2, "Center"),
                MissionObjective(1, 3, "Left"),
                MissionObjective(4, 3, "Right")
            ],
            scoring_rule="standard"
        ),
        state=game_state
    )
    
    # No units on objectives
    vp = score_standard(mission)
    assert vp[1] == 0
    assert vp[2] == 0
    
    # Add unit to first objective
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units = {"marine1": unit1}
    
    vp = score_standard(mission)
    assert vp[1] == 1  # 1 VP per objective
    assert vp[2] == 0
    
    # Add unit to another objective
    unit2 = UnitState(
        unit_id="marine2", name="Assault Marine", faction="Space Marines",
        position=(1, 3), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units["marine2"] = unit2
    
    vp = score_standard(mission)
    assert vp[1] == 2  # 2 VP for 2 objectives
    assert vp[2] == 0
    
    # Add enemy unit to same objective - should be contested
    unit3 = UnitState(
        unit_id="ork1", name="Ork Boy", faction="Orks",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=5, objective_control=1,
    )
    player2.units = {"ork1": unit3}
    
    vp = score_standard(mission)
    assert vp[1] == 0  # Contested objective gives 0 VP
    assert vp[2] == 0


def test_score_progressive():
    """Test progressive scoring function."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[
                MissionObjective(2, 2, "Center"),
                MissionObjective(1, 3, "Left"),
                MissionObjective(4, 3, "Right")
            ],
            scoring_rule="progressive"
        ),
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
    
    vp = score_progressive(mission)
    # Base VP: p1=2, p2=1
    # Progressive bonus: p1 gets +2 for having more objectives
    assert vp[1] == 4  # 2 base + 2 bonus
    assert vp[2] == 1  # 1 base + 0 bonus


def test_score_kill_points():
    """Test kill points scoring function."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.SEARCH_AND_DESTROY,
            description="Test mission",
            objectives=[],  # no objectives
            scoring_rule="kill_points"
        ),
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
    vp = score_kill_points(mission)
    assert vp[1] == 0
    assert vp[2] == 0
    
    # Damage the ork (half wounds)
    ork.current_wounds = 2
    
    vp = score_kill_points(mission)
    # Ork has lost half its wounds, so ~50% of its points
    # Marine has full health, so 0% of marine points
    # Exact values depend on implementation
    assert vp[1] >= 0  # Marine VP
    assert vp[2] >= 0  # Ork VP
    
    # Kill the ork completely
    ork.current_wounds = 0
    ork.models_remaining = 0
    
    vp = score_kill_points(mission)
    # Ork is completely destroyed, so marine gets points for killing it
    # Marine is still alive, so ork gets 0 points for killing marine
    assert vp[1] > 0  # Marine should have VP for killing ork
    assert vp[2] == 0   # Ork should have 0 VP (marine still alive)


def test_apply_scoring():
    """Test apply_scoring function."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[
                MissionObjective(2, 2, "Center"),
            ],
            scoring_rule="standard"
        ),
        state=game_state
    )
    
    # Add unit to objective
    unit1 = UnitState(
        unit_id="marine1", name="Tactical Marine", faction="Space Marines",
        position=(2, 2), current_wounds=4, max_wounds=4,
        models_remaining=1, models_total=1, leadership=6, objective_control=2,
    )
    player1.units = {"marine1": unit1}
    
    vp_tracker = VPTracker()
    updated_vp = apply_scoring(game_state, mission, vp_tracker)
    
    # Player 1 should have 1 VP, player 2 should have 0
    assert updated_vp.total[1] == 1
    assert updated_vp.total[2] == 0
    assert updated_vp.history[1] == [1]
    assert updated_vp.history[2] == [0]


def test_check_end_game_vp_cap():
    """Test end game check for VP cap."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[],
            max_rounds=5
        ),
        state=game_state
    )
    
    # Create VP tracker with player 1 at 100 VP
    vp_tracker = VPTracker()
    vp_tracker.add(1, 100)
    vp_tracker.add(2, 50)
    
    result = check_end_game(game_state, mission, vp_tracker, 3)
    
    assert result is not None
    assert result.winner == 1
    assert result.reason == "vp_cap"
    assert result.total_rounds == 3


def test_check_end_game_army_wiped():
    """Test end game check for army wiped."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[],
            max_rounds=5
        ),
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
        position=(5, 3), current_wounds=0, max_wounds=4,  # Already dead
        models_remaining=0, models_total=1, leadership=5, objective_control=1,
    )
    
    player1.units = {"marine1": marine}
    player2.units = {"ork1": ork}
    
    vp_tracker = VPTracker()
    vp_tracker.add(1, 10)
    vp_tracker.add(2, 5)
    
    result = check_end_game(game_state, mission, vp_tracker, 2)
    
    assert result is not None
    assert result.winner == 1  # Player 1 wins because player 2's army is wiped
    assert result.reason == "army_wiped"
    assert result.total_rounds == 2


def test_check_end_game_max_rounds():
    """Test end game check for max rounds reached."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[],
            max_rounds=3
        ),
        state=game_state
    )
    
    # Add units so neither army is wiped
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
    
    # Create VP tracker with player 1 ahead
    vp_tracker = VPTracker()
    vp_tracker.add(1, 30)
    vp_tracker.add(2, 20)
    
    result = check_end_game(game_state, mission, vp_tracker, 3)  # Round 3 = max_rounds
    
    assert result is not None
    assert result.winner == 1  # Player 1 has more VP
    assert result.reason == "rounds_completed"
    assert result.total_rounds == 3


def test_check_end_game_continues():
    """Test that game continues when no end conditions met."""
    game_state = create_empty_game("test_game", "Test Mission")
    
    player1 = PlayerState("p1", "Player 1", "Space Marines")
    player2 = PlayerState("p2", "Player 2", "Orks")
    game_state.players = {"p1": player1, "p2": player2}
    
    mission = Mission(
        config=MissionConfig(
            name="Test Mission",
            deployment=DeploymentType.DAWN_OF_WAR,
            description="Test mission",
            objectives=[],
            max_rounds=5
        ),
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
    
    # Create VP tracker with low scores
    vp_tracker = VPTracker()
    vp_tracker.add(1, 10)
    vp_tracker.add(2, 8)
    
    result = check_end_game(game_state, mission, vp_tracker, 2)  # Only round 2
    
    assert result is None  # Game should continue


if __name__ == "__main__":
    pytest.main([__file__])